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
