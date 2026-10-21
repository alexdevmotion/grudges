import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from grudges import cli


class CliTest(unittest.TestCase):
    def test_bundled_pack_is_resolved(self):
        for name, count in (("starter", 8), ("starter-intent", 6)):
            self.assertEqual(len(list(cli.pack_path(name).glob("*/task.toml"))), count)

    def test_card_before_any_run_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"GRUDGES_HOME": tmp}):
            out = io.StringIO()
            with contextlib.redirect_stderr(out):
                self.assertEqual(cli.main(["card"]), 2)
            self.assertIn("no completed run", out.getvalue())

    def test_invalid_attempts_fail_before_runner(self):
        with patch.object(cli.run, "replay") as replay, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                cli.main(["run", "--pack", "starter", "-a", "nop", "-k", "0"])
            self.assertEqual(raised.exception.code, 2)
            replay.assert_not_called()

    def test_error_results_return_nonzero_but_a_failed_task_is_valid(self):
        for status, code in (("failed", 0), ("infra_error", 2)):
            result = {"harbor_exit_code": 0, "records": [{"status": status}], "summary": {
                "nop": {"fixed": 0, "n_tasks": 1, "attempts_solved": 0,
                        "attempts_scored": int(status == "failed"),
                        "errors": {} if status == "failed" else {status: 1}}}}
            with patch.object(cli.run, "replay", return_value=(Path("/tmp/receipt"), result)), \
                 patch.object(cli.card, "write", return_value=Path("/tmp/card.html")), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["run", "--pack", "starter", "-a", "nop"]), code)

    def test_interrupted_or_incomplete_local_run_returns_nonzero(self):
        for fields in ({'interrupted': True}, {'complete': False}):
            result = {'records': [{'status': 'missing'}], 'summary': {}, **fields}
            with patch.object(cli.local, 'replay', return_value=(Path('/tmp/receipt'), result)), \
                 patch.object(cli.card, 'write', return_value=Path('/tmp/card.html')), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(['run','--pack','starter','--runner','local-claude','--trust-local']), 2)

    def test_bare_run_uses_native_subscription_and_one_demo_attempt(self):
        result = {'records':[{'status':'solved'}], 'summary':{}, 'complete':True}
        with patch.object(cli.shutil, 'which', return_value='/bin/codex'), \
             patch.object(cli.local, 'replay', return_value=(Path('/tmp/receipt'), result)) as native, \
             patch.object(cli.run, 'replay') as harbor, \
             patch.object(cli.card, 'write'), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['run']), 0)
            self.assertEqual(native.call_args.args[1], 'local-codex')
            self.assertEqual(native.call_args.args[0][0].name, 'blur-formatting')
            self.assertEqual(native.call_args.kwargs['attempts'], 1)
            harbor.assert_not_called()

    def test_claude_agent_selects_native_claude(self):
        result = {'records':[{'status':'solved'}], 'summary':{}, 'complete':True}
        with patch.object(cli.local, 'replay', return_value=(Path('/tmp/receipt'), result)) as native, \
             patch.object(cli.card, 'write'), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['run','--agent','claude']), 0)
            self.assertEqual(native.call_args.args[1], 'local-claude')

    def test_build_defaults_to_installed_codex(self):
        with patch.object(cli.shutil, 'which', return_value='/bin/codex'), \
             patch.object(cli.build, 'prepare', return_value=(Path('/tmp/build'), 'brief')), \
             patch.object(cli.build, 'launch') as launch, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(['build','example']), 0)
            launch.assert_called_once_with('codex', 'brief', Path('/tmp/build'))
