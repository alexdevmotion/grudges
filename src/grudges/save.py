"""Save a failure: pin the base and after states and keep a copy of the session."""

import os
import secrets
import shutil
import time
from pathlib import Path

from . import hook, snapshot, store


def checkpoints(session_id):
    return store.read_jsonl(hook.checkpoint_path(session_id))


def grudge_dir(grudge_id):
    if not grudge_id or Path(grudge_id).name != grudge_id or grudge_id in (".", ".."):
        raise ValueError("grudge id must be a single directory name")
    return store.subdir("grudges") / grudge_id


def _latest_session_for(root):
    """Most recently active session whose checkpoints belong to this repo."""
    best = None
    for path in store.subdir("checkpoints").glob("*.jsonl"):
        entries = [e for e in store.read_jsonl(path) if e.get("root") == str(root)]
        if entries and (best is None or entries[-1]["ts"] > best[0]):
            best = (entries[-1]["ts"], entries[-1]["session_id"])
    return best[1] if best else None


def requests(session_id, root):
    """Non-grudge requests of a session in this repo, oldest first."""
    return [e for e in checkpoints(session_id)
            if not e["is_grudge"] and e.get("root") == str(root)]


def save(cwd, note, session=None, back=1, transcript=None):
    if back < 1:
        raise ValueError("--back must be positive")
    if not note.strip():
        raise ValueError("--note must describe the expected outcome")
    root = snapshot.repo_root(cwd)
    if root is None:
        raise SystemExit("grudges: not inside a git repository")
    if not session:
        env_session = os.environ.get("CLAUDE_CODE_SESSION_ID")
        # The env session wins only if its hook ran here (e.g. wrappers may skip user hooks).
        session = env_session if env_session and requests(env_session, root) else _latest_session_for(root)
        session = session or env_session
    reqs = requests(session, root) if session else []
    if reqs and back > len(reqs):
        raise ValueError(f"--back {back} exceeds the {len(reqs)} recorded requests")
    selected = reqs[-back] if back <= len(reqs) else None
    base_entry = selected if selected and selected.get("commit") else None

    grudge_id = time.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(2)
    after = snapshot.take(root, message=f"grudges after {grudge_id}")
    snapshot.pin(after, f"refs/grudges/{grudge_id}/after")
    if base_entry:
        base = {"exact": True, "commit": base_entry["commit"], "head": base_entry["head"],
                "dirty": base_entry["dirty"], "submodules": base_entry.get("submodules") or {}}
        snapshot.pin({**base, "root": base_entry["root"]}, f"refs/grudges/{grudge_id}/base")
    else:
        # No checkpoint (hook not installed yet): HEAD is the best guess; the
        # build step must reconstruct the true base from the transcript.
        base = {"exact": False, "commit": None, "head": after["head"], "dirty": None}

    transcript = Path(transcript or (base_entry or (reqs[-1] if reqs else {})).get("transcript_path") or "")
    gdir = grudge_dir(grudge_id)
    gdir.mkdir(mode=0o700)
    copied = None
    if transcript.is_file():
        # Agents delete old sessions (Claude Code: 30 days by default), so keep a copy.
        shutil.copyfile(transcript, gdir / "transcript.jsonl")
        os.chmod(gdir / "transcript.jsonl", 0o600)
        copied = "transcript.jsonl"

    remote = None
    try:
        remote = snapshot.git(root, "remote", "get-url", "origin")
    except RuntimeError:
        pass
    grudge = {
        "id": grudge_id,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "note": note,
        "repo": {"root": str(root), "remote": remote},
        "session_id": session,
        "harness": (base_entry or {}).get("harness"),
        "model": (base_entry or {}).get("model"),
        "request": {
            "prompt_head": base_entry["prompt_head"] if base_entry else None,
            "transcript_offset": base_entry["transcript_offset"] if base_entry else None,
            "requests_in_episode": back if base_entry else None,
        },
        "transcript": {"source": str(transcript) if copied else None, "copy": copied},
        "base": base,
        "after": {"commit": after["commit"], "head": after["head"], "dirty": after["dirty"],
                  "submodules": after["submodules"]},
        "refs": {"base": f"refs/grudges/{grudge_id}/base" if base_entry else None,
                 "after": f"refs/grudges/{grudge_id}/after"},
        "status": "captured",
    }
    store.write_json(gdir / "grudge.json", grudge)
    return grudge
