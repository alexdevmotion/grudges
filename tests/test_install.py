import json
import tempfile
import unittest
from pathlib import Path

from grudges import install

EXISTING = {
    "model": "opus",
    "hooks": {
        "UserPromptSubmit": [{"hooks": []}],
        "Stop": [{"hooks": [{"type": "command", "command": "/x/reap.sh", "timeout": 10}]}],
    },
}


class InstallTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.claude = Path(self.tmp.name) / "claude"
        self.codex = Path(self.tmp.name) / "codex"
        self.claude.mkdir()
        (self.claude / "settings.json").write_text(json.dumps(EXISTING))

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_merges_is_idempotent_and_uninstall_restores(self):
        install.install("/bin/grudges", [self.claude], self.codex)
        install.install("/bin/grudges", [self.claude], self.codex)
        data = json.loads((self.claude / "settings.json").read_text())
        self.assertEqual(data["model"], "opus")
        self.assertEqual(data["hooks"]["Stop"], EXISTING["hooks"]["Stop"])
        commands = [h["command"] for g in data["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        self.assertEqual(commands, ["/bin/grudges hook"])
        self.assertTrue((self.claude / "skills/grudge/SKILL.md").exists())
        codex = json.loads((self.codex / "hooks.json").read_text())
        self.assertEqual(codex["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"], "/bin/grudges hook")
        self.assertTrue((self.claude / "settings.json.grudges-bak").exists())

        install.uninstall([self.claude], self.codex)
        self.assertEqual(json.loads((self.claude / "settings.json").read_text()), EXISTING)
        self.assertFalse((self.claude / "skills/grudge").exists())

    def test_paths_with_spaces_and_unrelated_commands(self):
        import shlex
        config = self.claude / "settings.json"
        data = json.loads(config.read_text())
        data["hooks"]["UserPromptSubmit"].append({"hooks": [{"command": "echo grudges hook"}]})
        config.write_text(json.dumps(data))
        install.install("/a path/grudges", [self.claude], None)
        install.install("/a path/grudges", [self.claude], None)
        groups = json.loads(config.read_text())["hooks"]["UserPromptSubmit"]
        commands = [h["command"] for g in groups for h in g["hooks"]]
        self.assertEqual(len(commands), 2)
        self.assertEqual(shlex.split(commands[1]), ["/a path/grudges", "hook"])
        install.uninstall([self.claude], None)
        self.assertIn("echo grudges hook", config.read_text())

    def test_identical_unmanaged_skill_stays_unmanaged(self):
        skill = self.claude / "skills/grudge/SKILL.md"
        skill.parent.mkdir(parents=True)
        original = (install.resources.files("grudges") / "skill/SKILL.md").read_text()
        skill.write_text(original)
        install.install("/bin/grudges", [self.claude], None)
        self.assertFalse((skill.parent / ".grudges-managed.json").exists())
        install.uninstall([self.claude], None)
        self.assertEqual(skill.read_text(), original)

    def test_existing_custom_skill_is_not_overwritten(self):
        skill = self.claude / "skills/grudge/SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("my custom skill")
        with self.assertRaises(ValueError):
            install.install("/bin/grudges", [self.claude], None)
        self.assertEqual(skill.read_text(), "my custom skill")
        self.assertEqual(json.loads((self.claude / "settings.json").read_text()), EXISTING)

    def test_uninstall_preserves_edits_and_extra_files(self):
        install.install("/bin/grudges", [self.claude], self.codex)
        edited = self.claude / "skills/grudge/SKILL.md"
        edited.write_text("my changes")
        extra = self.codex / "skills/grudge/notes.txt"
        extra.write_text("keep me")
        install.uninstall([self.claude], self.codex)
        self.assertEqual(edited.read_text(), "my changes")
        self.assertEqual(extra.read_text(), "keep me")


if __name__ == "__main__":
    unittest.main()
