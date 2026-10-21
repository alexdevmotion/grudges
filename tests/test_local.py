import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from grudges import local, run, card


class LocalTest(unittest.TestCase):
    def task(self, root):
        task = Path(root) / 'task'
        (task / 'environment/repo').mkdir(parents=True)
        (task / 'tests').mkdir()
        (task / 'solution').mkdir()
        (task / 'solution/solve.sh').write_text('true')
        (task / 'task.toml').write_text('[task]\nname="test/task"\n')
        (task / 'environment/Dockerfile').write_text('FROM python:3.13-slim\nWORKDIR /app\nCOPY repo/ /app/\n')
        (task / 'environment/repo/app.py').write_text('broken = True\n')
        (task / 'instruction.md').write_text('Fix app.py')
        (task / 'tests/test.sh').write_text('exit 0')
        return task

    def test_environment_preserves_login_location_not_api_credentials(self):
        env = {'HOME':'/user','CODEX_HOME':'/config/codex','CLAUDE_CONFIG_DIR':'/config/claude',
               'OPENAI_API_KEY':'placeholder','ANTHROPIC_API_KEY':'placeholder',
               'CODEX_API_KEY':'placeholder','CLAUDE_CODE_OAUTH_TOKEN':'placeholder',
               'ANTHROPIC_BASE_URL':'https://invalid','CLAUDE_CODE_USE_BEDROCK':'1'}
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(local.environment(), {k:env[k] for k in ('HOME','CODEX_HOME','CLAUDE_CONFIG_DIR')})

    def test_commands_keep_auth_native_and_restrict_permissions(self):
        c = local.command('local-codex','model','high')
        self.assertIn('forced_login_method="chatgpt"',c)
        self.assertIn('workspace-write',c)
        self.assertNotIn('--dangerously-bypass-approvals-and-sandbox',c)
        c = local.command('local-claude','opus')
        self.assertIn('--restricted',c)
        self.assertNotIn('--bare',c)
        self.assertNotIn('--dangerously-skip-permissions',c)
        self.assertIn('Read,Edit,Write,Glob,Grep',c)
        self.assertIn('claudeai',c[c.index('--settings')+1])

    def test_requires_explicit_trust_before_any_process(self):
        with patch.object(local.subprocess,'run') as proc:
            with self.assertRaisesRegex(ValueError,'trust-local'):
                local.replay([], 'local-codex', [])
            proc.assert_not_called()

    def test_auth_rejects_api_login(self):
        with patch.object(local.shutil,'which',return_value='/bin/agent'), patch.object(local.subprocess,'run') as proc:
            proc.return_value = subprocess.CompletedProcess([],0,'', 'Logged in using an API key')
            with self.assertRaisesRegex(ValueError,'subscription'):
                local.authenticate('local-codex',{})
            proc.return_value = subprocess.CompletedProcess([],0,json.dumps({'loggedIn':True,'authMethod':'api_key','apiProvider':'firstParty'}),'')
            with self.assertRaisesRegex(ValueError,'subscription'):
                local.authenticate('local-claude',{})

    def test_unsupported_layout_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=self.task(tmp)
            local.validate_task(t)
            (t/'task.toml').write_text('[environment]\ndocker_image="prebuilt"')
            with self.assertRaises(ValueError):local.validate_task(t)
            (t/'task.toml').write_text('')
            (t/'environment/repo/link').symlink_to('/tmp')
            with self.assertRaises(ValueError):local.validate_task(t)

    def test_structured_output_requires_success_not_just_exit_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'agent.json'
            p.write_text('{"type":"turn.completed","usage":{"output_tokens":23}}\n')
            self.assertEqual(local.agent_result('local-codex',p)['output_tokens'],23)
            p.write_text('{"type":"turn.failed"}\n')
            self.assertEqual(local.agent_result('local-codex',p)['status'],'agent_error')
            p.write_text('{"type":"thread.started"}\n')
            with self.assertRaises(ValueError):local.agent_result('local-codex',p)
            p.write_text('{"type":"system","subtype":"init","apiKeySource":"none"}\n'+json.dumps({'type':'result','subtype':'success','is_error':False,'permission_denials':[{}]}))
            self.assertEqual(local.agent_result('local-claude',p)['permission_denials'],1)
            p.write_text('{"type":"system","subtype":"init","apiKeySource":"none"}\n'+json.dumps({'type':'result','subtype':'success','is_error':False,'modelUsage':{'claude-opus-test':{}}}))
            self.assertEqual(local.agent_result('local-claude',p)['resolved_model'],'claude-opus-test')

    def test_claude_runtime_requires_subscription_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'agent.json'
            for source in ('user', 'env', None):
                output.write_text(json.dumps({'type':'system','subtype':'init','apiKeySource':source}) + '\n' +
                                  json.dumps({'type':'result','subtype':'success'}))
                with self.assertRaisesRegex(ValueError, 'subscription'):
                    local.agent_result('local-claude', output)

    def test_controls_require_failure_then_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.task(tmp)
            for i, outcomes in enumerate((['failed', 'solved'], ['solved'], ['failed', 'grader_error'])):
                trial = Path(tmp) / str(i)
                trial.mkdir()
                with patch.object(local, 'verify', side_effect=outcomes) as verify:
                    if i == 0:
                        local.controls(task, 'image', trial, {}, 30)
                        self.assertEqual([c.kwargs['oracle'] for c in verify.call_args_list], [False, True])
                    else:
                        with self.assertRaisesRegex(ValueError, 'control returned'):
                            local.controls(task, 'image', trial, {}, 30)

    def test_claude_root_rules_are_explicit_even_with_settings_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            task = self.task(tmp)
            workspace = task / 'environment/repo'
            baseline = local.prompt_for(task, workspace, 'local-claude')
            self.assertNotIn('RULES_CANARY', baseline)
            (workspace / 'CLAUDE.md').write_text('RULES_CANARY: create the marker')
            prompt = local.prompt_for(task, workspace, 'local-claude')
            self.assertIn('Project instructions (root CLAUDE.md):\nRULES_CANARY', prompt)
            self.assertIn('Fix app.py', prompt)
            self.assertIn('file read/edit tools only', prompt)

    def exercise(self, failure=None, runner="local-codex"):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup)
        task=self.task(tmp.name)
        phases=[]
        def execute(cmd,cwd,env,log,timeout,prompt=None):
            phases.append(cmd)
            if cmd[0]=='docker':
                if failure=='setup-timeout':raise subprocess.TimeoutExpired(cmd,timeout)
                return 0
            if cmd[0]=='git':return 0
            self.assertFalse((cwd/'tests').exists())
            self.assertFalse((cwd/'solution').exists())
            if failure=='agent-timeout':raise subprocess.TimeoutExpired(cmd,timeout)
            if failure == 'symlink':
                (cwd/'escape').symlink_to('/tmp')
            if runner == 'local-claude':
                self.assertIn('file read/edit tools only', prompt)
                log.write_text('{"type":"system","subtype":"init","apiKeySource":"none"}\n'
                               '{"type":"result","subtype":"success"}\n')
            else:
                log.write_text('{"type":"turn.completed"}\n')
            return 1 if failure=='agent-error' else 0
        with patch.dict(os.environ,{'GRUDGES_HOME':str(Path(tmp.name)/'data')}), \
             patch.object(local,'authenticate',return_value='test-version'), \
             patch.object(local.subprocess,'run',return_value=subprocess.CompletedProcess([],0)), \
             patch.object(local,'execute',side_effect=execute), \
             patch.object(local,'controls',side_effect=ValueError('invalid controls') if failure == 'controls' else None), \
             patch.object(local,'verify',return_value='solved',side_effect=KeyboardInterrupt if failure == 'interrupt-verifier' else None):
            directory,result=local.replay([task],runner,['test-model'],attempts=2,rules='A rule',trust_local=True)
        self.assertEqual(json.loads((directory/'results.json').read_text()),result)
        self.assertEqual((task/'environment/repo/app.py').read_text(),'broken = True\n')
        self.assertFalse((task/'environment/repo/AGENTS.md').exists())
        return result

    def test_claude_replay_completes_both_setups(self):
        self.assertTrue(self.exercise(runner='local-claude')['complete'])

    def test_invalid_controls_stop_before_agent_usage(self):
        result = self.exercise('controls')
        self.assertEqual([r['status'] for r in result['records']], ['infra_error','missing','missing','missing'])
        self.assertTrue(all(r['output_tokens'] is None for r in result['records']))

    def test_agent_symlink_is_not_exported(self):
        result = self.exercise('symlink')
        self.assertEqual(result['records'][0]['status'], 'infra_error')
        self.assertIn('symlinks', result['records'][0]['exception'])

    def test_verifier_interrupt_preserves_error_receipt(self):
        result = self.exercise('interrupt-verifier')
        self.assertTrue(result['interrupted'])
        self.assertEqual(result['records'][0]['status'], 'infra_error')
        self.assertFalse(result['complete'])

    def test_both_setups_complete_and_subscription_reported(self):
        r=self.exercise()
        self.assertEqual(len(r['records']),4)
        self.assertTrue(r['complete'])
        self.assertEqual([x['setup'] for x in r['records']], ['as captured','with rules']*2)
        self.assertTrue(all(s['billing']=='subscription' for s in r['summary'].values()))
        self.assertIn('subscription usage',card.render(r))
        self.assertNotIn('$0.00',card.render(r))

    def test_cli_errors_stop_queue_and_preserve_missing_attempts(self):
        r=self.exercise('agent-error')
        self.assertEqual([x['status'] for x in r['records']],['agent_error','missing','missing','missing'])
        self.assertEqual(sum(s['fixed'] for s in r['summary'].values()),0)

    def test_setup_timeout_is_not_a_model_failure(self):
        self.assertEqual(self.exercise('setup-timeout')['records'][0]['status'],'infra_error')

    def test_agent_timeout_stops_without_scoring_unknown_failure(self):
        r=self.exercise('agent-timeout')
        self.assertEqual([x['status'] for x in r['records']],['infra_error','missing','missing','missing'])

    def test_verifier_has_no_network_and_readonly_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            t=self.task(tmp);trial=Path(tmp)/'trial';trial.mkdir()
            def execute(cmd,cwd,env,log,timeout):
                self.assertEqual(cmd[cmd.index('--network')+1], 'none')
                self.assertEqual(cmd[cmd.index('--user')+1], f'{os.getuid()}:{os.getgid()}')
                mounts=[cmd[i+1] for i,v in enumerate(cmd) if v=='--mount']
                self.assertTrue(all('readonly' in m for m in mounts if 'dst=/tests' in m))
                (trial/'verifier/reward.txt').write_text('1')
                return 1
            with patch.object(local,'execute',side_effect=execute),patch.object(local.subprocess,'run'):
                self.assertEqual(local.verify(t,t/'environment/repo','image',trial,{},30),'solved')

if __name__=='__main__':unittest.main()
