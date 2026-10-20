"""UserPromptSubmit hook for Claude Code and Codex.

Records a checkpoint per user request: the exact working-tree snapshot and
the transcript offset where the request begins. Contract: print nothing
(hook stdout is injected into the agent's context), never block, exit 0.
"""

import json
import os
import sys
import time
import traceback

from . import snapshot, store

GRUDGE_PREFIXES = ("/grudge", "$grudge")


def _safe_name(session_id):
    return "".join(c for c in session_id if c.isalnum() or c in "-_") or "unknown"


def checkpoint_path(session_id):
    return store.subdir("checkpoints") / f"{_safe_name(session_id)}.jsonl"


def record(payload):
    session_id = payload.get("session_id")
    cwd = payload.get("cwd")
    if not session_id or not cwd or not os.path.isdir(cwd):
        return
    prompt = (payload.get("prompt") or "").strip()
    is_grudge = prompt.startswith(GRUDGE_PREFIXES)
    transcript = payload.get("transcript_path")
    entry = {
        "ts": time.time(),
        "session_id": session_id,
        "harness": "codex" if "turn_id" in payload else "claude-code",
        "model": payload.get("model"),
        "turn_id": payload.get("turn_id"),
        "cwd": cwd,
        "transcript_path": transcript,
        # A transcript that does not exist yet means this is the first request: offset 0.
        "transcript_offset": os.path.getsize(transcript) if transcript and os.path.exists(transcript) else 0,
        "prompt_head": prompt[:120],
        "is_grudge": is_grudge,
        "commit": None,
    }
    if not is_grudge:
        try:
            snap = snapshot.take(cwd, message=f"grudges checkpoint {session_id}")
        except Exception as e:
            root = snapshot.repo_root(cwd)
            entry.update(root=str(root) if root else None, skipped=str(e) if isinstance(e, snapshot.TooLarge) else type(e).__name__)
            store.append_jsonl(checkpoint_path(session_id), entry)
            return
        if snap is None:
            return  # not a git repo: nothing replayable to record
        entry.update(root=snap["root"], head=snap["head"], commit=snap["commit"], dirty=snap["dirty"],
                     submodules=snap["submodules"])
    else:
        root = snapshot.repo_root(cwd)
        entry["root"] = str(root) if root else None
    store.append_jsonl(checkpoint_path(session_id), entry)


def main(stdin=None):
    try:
        record(json.load(stdin or sys.stdin))
    except Exception:
        try:
            with open(store.home() / "hook-errors.log", "a") as f:
                f.write(traceback.format_exc())
        except Exception:
            pass
    return 0
