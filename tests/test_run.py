import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import hashlib
import os

from grudges import run

SPIKE_JOBS = Path(os.environ["GRUDGES_TEST_RECEIPTS"]) if os.environ.get("GRUDGES_TEST_RECEIPTS") else None


def trial(task="t1", model="gpt-x", reward=None, exc=None, tokens=(100, 50)):
    return {
        "task_name": task,
        "trial_name": f"{task}__abc",
        "config": {"agent": {"name": "codex", "model_name": model}},
        "agent_info": {"name": "codex", "version": "1.2.3", "model_info": {"name": model}},
        "agent_result": {"n_input_tokens": tokens[0], "n_output_tokens": tokens[1], "cost_usd": None},
        "verifier_result": {"rewards": {"reward": reward}} if reward is not None else None,
        "exception_info": {"exception_type": exc, "exception_message": "boom"} if exc else None,
        "started_at": "2026-10-15T08:08:10.000000Z",
        "finished_at": "2026-10-15T08:08:40.000000Z",
    }


class ClassifyTest(unittest.TestCase):
    def test_statuses(self):
        cases = {
            "solved": trial(reward=1.0),
            "failed": trial(reward=0.0),
            "timeout": trial(exc="AgentTimeoutError"),
            "provider_error": trial(exc="ApiRateLimitError"),
            "grader_error": trial(exc="VerifierTimeoutError"),
            "infra_error": trial(exc="RuntimeError"),
        }
        crashed_in_setup = trial(exc="NonZeroAgentExitCodeError")
        crashed_in_setup["agent_execution"] = None
        crashed_while_working = trial(exc="NonZeroAgentExitCodeError")
        crashed_while_working["agent_execution"] = {"started_at": "2026-10-15T08:08:15Z"}
        cases_extra = {"infra_error": crashed_in_setup, "failed": crashed_while_working}
        for status, t in cases_extra.items():
            self.assertEqual(run.classify(t)["status"], status, status)
        for status, t in cases.items():
            self.assertEqual(run.classify(t)["status"], status, status)

    def test_invalid_rewards_are_grader_errors(self):
        for reward in ("1", float("nan"), float("inf")):
            self.assertEqual(run.classify(trial(reward=reward))["status"], "grader_error")

    def test_malformed_receipt_fails_clearly(self):
        with tempfile.TemporaryDirectory() as d:
            receipt = Path(d) / "trial" / "result.json"
            receipt.parent.mkdir()
            receipt.write_text("{partial")
            with self.assertRaisesRegex(SystemExit, "invalid trial receipt"):
                run.collect(d)

    def test_record_fields(self):
        r = run.classify(trial(reward=1.0))
        self.assertEqual((r["task"], r["model"], r["agent"]), ("t1", "gpt-x", "codex"))
        self.assertEqual(r["seconds"], 30.0)
        self.assertEqual(r["output_tokens"], 50)


class SummarizeTest(unittest.TestCase):
    def test_errors_are_excluded_from_score(self):
        records = [run.classify(t) for t in [
            trial("a", reward=1.0), trial("a", reward=1.0), trial("a", reward=0.0),
            trial("b", reward=0.0), trial("b", exc="ApiOverloadedError"), trial("b", exc="AgentTimeoutError"),
        ]]
        s = run.summarize(records)["codex · gpt-x"]
        self.assertEqual(s["tasks"]["a"]["solved"], 2)
        self.assertEqual(s["tasks"]["a"]["scored"], 3)
        self.assertEqual(s["tasks"]["b"]["scored"], 2)  # provider error not scored
        self.assertEqual(s["fixed"], 1)                 # majority of scored attempts
        self.assertEqual(s["errors"], {"provider_error": 1})
        self.assertEqual(s["n_tasks"], 2)


class SpikeReceiptsTest(unittest.TestCase):
    @unittest.skipUnless(SPIKE_JOBS and SPIKE_JOBS.exists(), "optional integration receipts not configured")
    def test_real_harbor_receipts(self):
        statuses = lambda job: {r["status"] for r in run.collect(SPIKE_JOBS / job)}
        self.assertEqual(statuses("feedback-oracle-buildx"), {"solved"})
        self.assertEqual(statuses("feedback-nop-buildx"), {"failed"})
        self.assertEqual(statuses("feedback-nop"), {"infra_error"})


class DatasetTest(unittest.TestCase):
    def test_dataset_copies_tasks_by_name(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for name in ("one", "two"):
                (d / "src" / name).mkdir(parents=True)
                (d / "src" / name / "task.toml").write_text("")
            ds = run.make_dataset([d / "src" / "one", d / "src" / "two"], d / "ds")
            self.assertEqual(sorted(p.name for p in ds.iterdir()), ["one", "two"])
            with self.assertRaises(SystemExit):
                run.make_dataset([d / "src"], d / "ds2")  # not a task dir


class ExpandTest(unittest.TestCase):
    def test_pack_dir_expands_to_tasks_and_titles_are_collected(self):
        with tempfile.TemporaryDirectory() as d:
            pack = Path(d) / "pack"
            for name in ("b", "a"):
                (pack / name).mkdir(parents=True)
                (pack / name / "task.toml").write_text("")
            (pack / "README.md").write_text("")
            (pack / "titles.json").write_text('{"a": "Title A"}')
            tasks = run.expand([pack])
            self.assertEqual([t.name for t in tasks], ["a", "b"])
            self.assertEqual(run.titles_for(tasks), {"a": "Title A"})
            self.assertEqual([t.name for t in run.expand([pack / "a"])], ["a"])


class PreflightTest(unittest.TestCase):
    def test_no_network_task_is_rejected_for_real_agents(self):
        with tempfile.TemporaryDirectory() as d:
            t = Path(d) / "t"
            t.mkdir()
            (t / "task.toml").write_text('[agent]\ntimeout_sec = 60\n[environment]\nnetwork_mode = "no-network"\n')
            problems = run.preflight([t], agent="codex")
            self.assertEqual(len(problems), 1)
            self.assertIn("cannot install", problems[0])
            self.assertEqual(run.preflight([t], agent="oracle"), [])


class RulesTest(unittest.TestCase):
    def test_rules_file_replaces_the_tasks_own_and_source_is_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            task = Path(d) / "t"
            (task / "environment" / "repo").mkdir(parents=True)
            (task / "task.toml").write_text("")
            (task / "environment" / "Dockerfile").write_text("FROM python:3\nCOPY repo/ /app/\n")
            (task / "environment" / "repo" / "AGENTS.md").write_text("old rules")
            out = run.with_rules(task, "my rules", "codex", Path(d) / "ruled" / "t")
            self.assertEqual((out / "environment" / "repo" / "AGENTS.md").read_text(), "my rules")
            self.assertEqual((task / "environment" / "repo" / "AGENTS.md").read_text(), "old rules")
            claude = run.with_rules(task, "my rules", "claude-code", Path(d) / "ruled-c" / "t")
            self.assertEqual((claude / "environment" / "repo" / "CLAUDE.md").read_text(), "my rules")

    def test_task_without_repo_dir_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "t").mkdir()
            with self.assertRaises(SystemExit):
                run.with_rules(Path(d) / "t", "r", "codex", Path(d) / "out")

    def test_setup_is_part_of_the_label(self):
        r = dict(run.classify(trial(reward=1.0)), setup="with rules")
        self.assertEqual(list(run.summarize([r])), ["codex · gpt-x · with rules"])


class KeysTest(unittest.TestCase):
    def test_bare_and_assignment_formats(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "openai.env").write_text("sk-proj-abc\n")
            Path(d, "other.env").write_text("# note\nexport ANTHROPIC_API_KEY='sk-ant-x'\nFOO=bar\n")
            self.assertEqual(run.load_keys(d), {"OPENAI_API_KEY": "sk-proj-abc", "ANTHROPIC_API_KEY": "sk-ant-x", "FOO": "bar"})


class ReliabilityTest(unittest.TestCase):
    def task(self, root, name="t"):
        task = Path(root) / name
        (task / "environment" / "repo").mkdir(parents=True)
        (task / "task.toml").write_text('[agent]\ntimeout_sec = 60\n')
        (task / "environment" / "Dockerfile").write_text("FROM python:3\nCOPY repo/ /app/\n")
        (task / "instruction.md").write_text("original")
        return task

    def test_snapshot_is_independent_and_collisions_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            task = self.task(d)
            ds = run.make_dataset([task], Path(d) / "ds")
            (task / "instruction.md").write_text("changed")
            self.assertFalse((ds / "t").is_symlink())
            self.assertEqual((ds / "t" / "instruction.md").read_text(), "original")
            other = self.task(Path(d) / "other")
            for tasks in ([], [task, task], [task, other]):
                with self.assertRaises(SystemExit):
                    run.expand(tasks)

    def test_receipt_names_come_from_frozen_task_config(self):
        with tempfile.TemporaryDirectory() as d:
            task = self.task(d)
            (task / "task.toml").write_text('[task]\nname = "pack/t"\n')
            receipt = run.classify(trial(task="pack/t", model="x", reward=1))
            missing = run._missing_records([receipt], [task], ["x", "y"], 3, "codex", None)
            with self.assertRaisesRegex(SystemExit, "ambiguous"):
                run._missing_records([receipt] * 4, [task], ["x"], 3, "codex", None)
            with self.assertRaisesRegex(SystemExit, "ambiguous"):
                run._missing_records([receipt], [task], ["other"], 3, "codex", None)
            self.assertEqual(len(missing), 5)
            self.assertEqual({r["task"] for r in missing}, {"pack/t"})
            other = self.task(d, "other")
            (other / "task.toml").write_text('[task]\nname = "pack/t"\n')
            with self.assertRaisesRegex(SystemExit, "collision"):
                run.expand([task, other])

    def test_symlink_rules_cannot_write_outside_copy(self):
        with tempfile.TemporaryDirectory() as d:
            task = self.task(d)
            outside = Path(d) / "outside"
            outside.write_text("keep")
            (task / "environment" / "repo" / "AGENTS.md").symlink_to(outside)
            with self.assertRaisesRegex(SystemExit, "symlinks"):
                run.with_rules(task, "replace", "codex", Path(d) / "out")
            self.assertEqual(outside.read_text(), "keep")
            with self.assertRaisesRegex(SystemExit, "symlinks"):
                run.make_dataset([task], Path(d) / "ds")

    def test_unsupported_rules_harness_and_layout(self):
        with tempfile.TemporaryDirectory() as d:
            task = self.task(d)
            with self.assertRaisesRegex(SystemExit, "harness"):
                run.with_rules(task, "", "oracle", Path(d) / "out")
            (task / "environment" / "Dockerfile").write_text("FROM scratch")
            with self.assertRaisesRegex(SystemExit, "layout"):
                run.with_rules(task, "", "codex", Path(d) / "out")

    def test_validation_precedes_subprocess(self):
        with tempfile.TemporaryDirectory() as d, patch.object(run.subprocess, "run") as proc:
            task = self.task(d)
            for kwargs in ({"models": []}, {"models": [""]}, {"models": ["x", "x"]},
                           {"attempts": 0}, {"attempts": -1}, {"concurrency": 0}):
                args = {"models": ["x"], **kwargs}
                with self.assertRaises(SystemExit):
                    run.replay([task], "codex", **args)
            proc.assert_not_called()

    def test_rules_reject_prebuilt_image_before_execution(self):
        with tempfile.TemporaryDirectory() as d, patch.object(run.subprocess, "run") as launch:
            task = self.task(d)
            (task / "task.toml").write_text('[environment]\ndocker_image = "example/prebuilt:latest"\n')
            with self.assertRaisesRegex(SystemExit, "prebuilt"):
                run.replay([task], "codex", ["test-model"], rules="a rule")
            launch.assert_not_called()

    def test_controls_accept_no_model_and_record_missing_attempts(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {"GRUDGES_HOME": d}), patch.object(run, "load_keys", return_value={}):
            task = self.task(Path(d) / "source")
            with patch.object(run.subprocess, "run", return_value=type("Exit", (), {"returncode": 0})()) as launch:
                _, result = run.replay([task], "nop", [], attempts=1)
            self.assertNotIn("-m", launch.call_args.args[0])
            self.assertEqual(result["records"][0]["status"], "missing")
            self.assertIsNone(result["records"][0]["model"])

    def test_native_auth_fails_closed_and_strips_consumer_fallbacks(self):
        unsafe = {"CODEX_FORCE_AUTH_JSON": "1", "CODEX_AUTH_JSON_PATH": "/secret",
                  "CLAUDE_FORCE_OAUTH": "1", "CLAUDE_CODE_OAUTH_TOKEN": "consumer",
                  "ANTHROPIC_AUTH_TOKEN": "consumer"}
        with patch.dict(os.environ, unsafe, clear=True), patch.object(run, "load_keys", return_value={}):
            for agent in ("codex", "claude-code"):
                with self.assertRaisesRegex(SystemExit, "requires"):
                    run.replay_env(agent)
            with patch.dict(os.environ, OPENAI_API_KEY="api", ANTHROPIC_API_KEY="api"):  # gitleaks:allow (test placeholders)
                for agent in ("codex", "claude-code"):
                    env = run.replay_env(agent)
                    self.assertFalse(set(unsafe) & set(env))
                    self.assertEqual(env["OPENAI_API_KEY"], "api")

    def test_empty_rules_runs_both_frozen_setups_and_records_missing_trials(self):
        with tempfile.TemporaryDirectory() as d, patch.dict(os.environ, {"GRUDGES_HOME": d, "OPENAI_API_KEY": "test"}), patch.object(run, "load_keys", return_value={}):
            task = self.task(Path(d) / "source")
            (task / "environment" / "repo" / "AGENTS.md").write_text("captured rules")
            datasets = []

            def launch(cmd, **kwargs):
                dataset = Path(cmd[cmd.index("-p") + 1])
                datasets.append(dataset)
                self.assertEqual((dataset / "t" / "instruction.md").read_text(), "original")
                (task / "instruction.md").write_text("moving source")
                return type("Exit", (), {"returncode": 0})()

            with patch.object(run.subprocess, "run", side_effect=launch):
                directory, result = run.replay([task], "codex", ["x", "y"], rules="")
            self.assertEqual(len(datasets), 2)
            self.assertEqual((datasets[0] / "t/environment/repo/AGENTS.md").read_text(), "captured rules")
            self.assertEqual((datasets[1] / "t/environment/repo/AGENTS.md").read_text(), "")
            self.assertEqual((task / "environment/repo/AGENTS.md").read_text(), "captured rules")
            self.assertTrue(result["rules"])
            self.assertFalse(result["complete"])
            self.assertEqual(result["rules_sha256"], hashlib.sha256(b"").hexdigest())
            self.assertEqual(json.loads((directory / "config.json").read_text()), result["config"])
            self.assertEqual(len(result["summary"]), 4)
            self.assertEqual(len(result["records"]), 12)
            for summary in result["summary"].values():
                self.assertEqual((summary["n_tasks"], summary["fixed"], summary["missing_attempts"]), (1, 0, 3))
            with patch.object(run.subprocess, "run", return_value=type("Exit", (), {"returncode": 0})()):
                second, _ = run.replay([task], "codex", ["x"])
            self.assertNotEqual(directory, second)

    def test_errors_do_not_establish_stable_success_and_costs_include_errors(self):
        rs = [run.classify(trial(reward=1)), run.classify(trial(exc="ApiRateLimitError")),
              run.classify(trial(exc="ApiRateLimitError"))]
        for r, cost in zip(rs, (0, 1, 2)):
            r["cost_usd"] = cost
        s = run.summarize(rs)["codex · gpt-x"]
        self.assertEqual(s["fixed"], 0)
        self.assertEqual(s["attempts_scored"], 1)
        self.assertEqual(s["cost_usd"], 3)
        self.assertTrue(s["cost_complete"])
        self.assertFalse(s["complete"])
        self.assertEqual(run.summarize(rs[:1])["codex · gpt-x"]["cost_usd"], 0)
        self.assertEqual(run._median([10, 20]), 15)
        self.assertEqual(run._median([10, 20, 30]), 20)
        self.assertIsNone(run._median([]))


if __name__ == "__main__":
    unittest.main()
