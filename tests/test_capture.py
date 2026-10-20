import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from grudges import hook, save, snapshot


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class Repo:
    """Throwaway git repo with one commit, plus an isolated GRUDGES_HOME."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.path = base / "repo"
        self.path.mkdir()
        self.home = base / "home"
        os.environ["GRUDGES_HOME"] = str(self.home)
        git(self.path, "init", "-q", "-b", "main")
        git(self.path, "config", "user.email", "t@example.com")
        git(self.path, "config", "user.name", "t")
        (self.path / "app.py").write_text("x = 1\n")
        (self.path / ".gitignore").write_text("secret.env\n")
        git(self.path, "add", "-A")
        git(self.path, "commit", "-qm", "init")
        self.transcript = base / "session.jsonl"
        self.transcript.write_text('{"type":"user"}\n')

    def prompt(self, text, session="s1", **extra):
        payload = {"session_id": session, "transcript_path": str(self.transcript), "cwd": str(self.path),
                   "hook_event_name": "UserPromptSubmit", "prompt": text, **extra}
        out = io.StringIO()
        with redirect_stdout(out):
            code = hook.main(io.StringIO(json.dumps(payload)))
        return code, out.getvalue()

    def close(self):
        os.environ.pop("GRUDGES_HOME", None)
        self.tmp.cleanup()


class SnapshotTest(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.close()

    def test_captures_dirty_and_untracked_without_touching_index_or_tree(self):
        (self.r.path / "app.py").write_text("x = 2\n")
        (self.r.path / "new.py").write_text("y = 1\n")
        (self.r.path / "secret.env").write_text("KEY=1\n")
        git(self.r.path, "add", "app.py")
        status_before = git(self.r.path, "status", "--porcelain")

        snap = snapshot.take(self.r.path)

        self.assertTrue(snap["dirty"])
        self.assertEqual(git(self.r.path, "show", f"{snap['commit']}:app.py"), "x = 2")
        self.assertEqual(git(self.r.path, "show", f"{snap['commit']}:new.py"), "y = 1")
        files = git(self.r.path, "ls-tree", "-r", "--name-only", snap["commit"]).split()
        self.assertNotIn("secret.env", files)  # ignored files stay out
        self.assertEqual(git(self.r.path, "status", "--porcelain"), status_before)
        self.assertEqual(snap["head"], git(self.r.path, "rev-parse", "HEAD"))

    def test_dirty_submodule_is_captured_and_linked_from_parent(self):
        sub_src = Path(self.r.tmp.name) / "sub-src"
        sub_src.mkdir()
        git(sub_src, "init", "-q", "-b", "main")
        (sub_src / "lib.py").write_text("v = 1\n")
        git(sub_src, "add", "-A")
        git(sub_src, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "-qm", "sub")
        git(self.r.path, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(sub_src), "sub")
        git(self.r.path, "commit", "-qm", "add sub")
        (self.r.path / "sub" / "lib.py").write_text("v = 2\n")

        snap = snapshot.take(self.r.path)

        sub = snap["submodules"]["sub"]
        self.assertTrue(snap["dirty"] and sub["dirty"])
        self.assertEqual(git(self.r.path / "sub", "show", f"{sub['commit']}:lib.py"), "v = 2")
        gitlink = git(self.r.path, "rev-parse", f"{snap['commit']}:sub")
        self.assertEqual(gitlink, sub["commit"])
        self.assertEqual(git(self.r.path, "status", "--porcelain"), "M sub")

        g = save.save(cwd=self.r.path, note="n", session="none")
        self.assertEqual(git(self.r.path / "sub", "show", f"refs/grudges/{g['id']}/after:lib.py"), "v = 2")

        dest = Path(self.r.tmp.name) / "export"
        snapshot.export(self.r.path, g["after"]["commit"], dest)
        self.assertEqual((dest / "sub" / "lib.py").read_text(), "v = 2\n")
        self.assertEqual((dest / "app.py").read_text(), "x = 1\n")
        self.assertFalse((dest / ".git").exists())

    def test_skips_huge_untracked_content(self):
        (self.r.path / "dump.bin").write_bytes(b"0" * 2048)
        with self.assertRaises(snapshot.TooLarge):
            snapshot.take(self.r.path, max_untracked_bytes=1024)
        self.assertEqual(git(self.r.path, "status", "--porcelain"), "?? dump.bin")

    def test_clean_tree_is_not_dirty(self):
        self.assertFalse(snapshot.take(self.r.path)["dirty"])

    def test_outside_git_returns_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(snapshot.take(Path(d)))


class HookTest(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.close()

    def test_records_checkpoint_silently(self):
        code, out = self.r.prompt("fix the bug")
        self.assertEqual((code, out), (0, ""))
        entries = save.checkpoints("s1")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["transcript_offset"], self.r.transcript.stat().st_size)
        self.assertEqual(entries[0]["prompt_head"], "fix the bug")
        self.assertTrue(entries[0]["commit"])

    def test_grudge_prompt_is_marked_and_not_snapshotted(self):
        self.r.prompt("/grudge it broke")
        self.r.prompt("$grudge again")
        entries = save.checkpoints("s1")
        self.assertTrue(all(e["is_grudge"] for e in entries))
        self.assertTrue(all(e.get("commit") is None for e in entries))

    def test_oversized_repo_is_recorded_as_skipped(self):
        from unittest import mock
        with mock.patch.object(snapshot, "take", side_effect=snapshot.TooLarge("2 GB untracked")):
            self.assertEqual(self.r.prompt("go")[0], 0)
        e = save.checkpoints("s1")[-1]
        self.assertIsNone(e["commit"])
        self.assertEqual(e["skipped"], "2 GB untracked")

    def test_never_fails(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(hook.main(io.StringIO("not json")), 0)
            self.assertEqual(hook.main(io.StringIO(json.dumps({"session_id": "s", "cwd": "/nonexistent"}))), 0)
        self.assertEqual(out.getvalue(), "")


class SaveTest(unittest.TestCase):
    def setUp(self):
        self.r = Repo()

    def tearDown(self):
        self.r.close()

    def test_pins_exact_base_of_failing_request_and_after_state(self):
        self.r.prompt("first request")
        (self.r.path / "app.py").write_text("x = 2\n")  # agent work on request 1
        self.r.prompt("second request")                 # base of the failing request
        base_commit = save.checkpoints("s1")[-1]["commit"]
        (self.r.path / "app.py").write_text("x = 3  # wrong\n")  # failed attempt
        with self.r.transcript.open("a") as f:
            f.write('{"type":"assistant"}\n')
        self.r.prompt("/grudge should have kept x = 2")

        g = save.save(cwd=self.r.path, note="should have kept x = 2", session="s1")

        self.assertTrue(g["base"]["exact"])
        self.assertEqual(g["base"]["commit"], base_commit)
        self.assertEqual(git(self.r.path, "show", f"refs/grudges/{g['id']}/base:app.py"), "x = 2")
        self.assertEqual(git(self.r.path, "show", f"refs/grudges/{g['id']}/after:app.py"), "x = 3  # wrong")
        self.assertEqual(g["request"]["prompt_head"], "second request")
        gdir = save.grudge_dir(g["id"])
        self.assertEqual((gdir / "transcript.jsonl").read_text(), self.r.transcript.read_text())
        self.assertEqual(json.loads((gdir / "grudge.json").read_text())["note"], "should have kept x = 2")

    def test_back_selects_earlier_request(self):
        self.r.prompt("first request")
        first = save.checkpoints("s1")[-1]["commit"]
        self.r.prompt("second request")
        g = save.save(cwd=self.r.path, note="n", session="s1", back=2)
        self.assertEqual(g["base"]["commit"], first)

    def test_without_checkpoint_falls_back_to_head(self):
        g = save.save(cwd=self.r.path, note="n", session="unknown", transcript=self.r.transcript)
        self.assertFalse(g["base"]["exact"])
        self.assertEqual(g["base"]["head"], git(self.r.path, "rev-parse", "HEAD"))

    def test_session_is_inferred_from_latest_checkpoint_in_repo(self):
        self.r.prompt("work", session="abc")
        g = save.save(cwd=self.r.path, note="n")
        self.assertEqual(g["session_id"], "abc")

    def test_skipped_latest_request_does_not_reuse_older_exact_snapshot(self):
        from unittest import mock
        self.r.prompt("earlier successful capture")
        with mock.patch.object(snapshot, "take", side_effect=RuntimeError("snapshot failed")):
            self.r.prompt("latest uncaptured request")
        g = save.save(cwd=self.r.path, note="n", session="s1")
        self.assertFalse(g["base"]["exact"])

    def test_invalid_selection_fails_before_pinning(self):
        self.r.prompt("only request")
        for back in (0, 2):
            with self.assertRaises(ValueError):
                save.save(cwd=self.r.path, note="n", session="s1", back=back)
        self.assertFalse(git(self.r.path, "for-each-ref", "refs/grudges"))


if __name__ == "__main__":
    unittest.main()
