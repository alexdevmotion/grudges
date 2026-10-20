"""Register the UserPromptSubmit hook and the /grudge skill for Claude Code and Codex.

Edits are merged into existing config (never replaced) and a one-time backup
of each modified file is kept next to it as *.grudges-bak.
"""

import json
import hashlib
import shlex
import shutil
from importlib import resources
from pathlib import Path

def _hook_command(binary):
    return f"{shlex.quote(str(binary))} hook"


def _ours(hook):
    try:
        parts = shlex.split(hook.get("command", ""))
    except ValueError:
        return False
    return len(parts) == 2 and Path(parts[0]).name == "grudges" and parts[1] == "hook"


def _load(path):
    return json.loads(path.read_text()) if path.exists() and path.read_text().strip() else {}


def _write(path, data):
    backup = path.with_name(path.name + ".grudges-bak")
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)
    path.write_text(json.dumps(data, indent=2) + "\n")


def _has_hook(groups):
    return any(_ours(h) for g in groups for h in g.get("hooks", []))


def add_hook(config_path, binary):
    data = _load(config_path)
    groups = data.setdefault("hooks", {}).setdefault("UserPromptSubmit", [])
    if _has_hook(groups):
        return False
    groups.append({"hooks": [{"type": "command", "command": _hook_command(binary), "timeout": 10}]})
    config_path.parent.mkdir(parents=True, exist_ok=True)
    _write(config_path, data)
    return True


def remove_hook(config_path):
    if not config_path.exists():
        return False
    data = _load(config_path)
    groups = data.get("hooks", {}).get("UserPromptSubmit", [])
    if not _has_hook(groups):
        return False
    kept = []
    for g in groups:
        ours = [h for h in g.get("hooks", []) if _ours(h)]
        if not ours:
            kept.append(g)  # untouched, including the user's own empty groups
        elif len(ours) < len(g["hooks"]):
            kept.append({**g, "hooks": [h for h in g["hooks"] if h not in ours]})
    data["hooks"]["UserPromptSubmit"] = kept
    _write(config_path, data)
    return True


def install_skill(skills_dir):
    target = skills_dir / "grudge"
    if target.is_symlink():
        raise ValueError(f"refusing to overwrite linked skill: {target}")
    target.mkdir(parents=True, exist_ok=True)
    source = resources.files("grudges") / "skill" / "SKILL.md"
    skill = target / "SKILL.md"
    marker = target / ".grudges-managed.json"
    text = source.read_text()
    if skill.is_symlink() or marker.is_symlink():
        raise ValueError(f"refusing to overwrite linked skill files: {target}")
    if skill.exists() and skill.read_text() == text and not marker.exists():
        return target  # An identical manually installed skill remains user-owned.
    if skill.exists() and skill.read_text() != text:
        expected = _load(marker).get("sha256")
        if hashlib.sha256(skill.read_bytes()).hexdigest() != expected:
            raise ValueError(f"existing grudge skill was created or edited separately; preserve it before installing: {skill}")
    skill.write_text(text)
    marker.write_text(json.dumps({"sha256": hashlib.sha256(skill.read_bytes()).hexdigest()}) + "\n")
    return target


def targets(claude_dirs, codex_dir):
    for d in claude_dirs:
        yield "claude-code", Path(d) / "settings.json", Path(d) / "skills"
    if codex_dir:
        yield "codex", Path(codex_dir) / "hooks.json", Path(codex_dir) / "skills"


def install(binary, claude_dirs, codex_dir):
    lines = []
    for harness, config, skills in targets(claude_dirs, codex_dir):
        skill = install_skill(skills)
        added = add_hook(config, binary)
        lines.append(f"{harness}: hook {'added to' if added else 'already in'} {config}; skill at {skill}")
    return lines


def uninstall(claude_dirs, codex_dir):
    lines = []
    for harness, config, skills in targets(claude_dirs, codex_dir):
        removed = remove_hook(config)
        skill = skills / "grudge"
        marker, document = skill / ".grudges-managed.json", skill / "SKILL.md"
        if not skill.is_symlink() and not marker.is_symlink() and not document.is_symlink() and marker.exists() and document.exists():
            if _load(marker).get("sha256") == hashlib.sha256(document.read_bytes()).hexdigest():
                document.unlink()
                marker.unlink()
                if not any(skill.iterdir()):
                    skill.rmdir()
            else:
                lines.append(f"{harness}: preserved edited skill at {skill}")
        elif skill.exists():
            lines.append(f"{harness}: preserved unmanaged skill at {skill}")
        lines.append(f"{harness}: hook {'removed from' if removed else 'not found in'} {config}")
    return lines
