"""Point-in-time snapshots of a working tree, without touching it.

A snapshot is a commit object containing every tracked and untracked,
non-ignored file exactly as it is on disk. It is built through a temporary
copy of the index, so the user's index, working tree and refs are unchanged.
The commit stays unreferenced (git prunes it after ~2 weeks) until `save`
pins it under refs/grudges/.
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_IDENTITY = {
    "GIT_AUTHOR_NAME": "grudges",
    "GIT_AUTHOR_EMAIL": "grudges@localhost",
    "GIT_COMMITTER_NAME": "grudges",
    "GIT_COMMITTER_EMAIL": "grudges@localhost",
}


def git(cwd, *args, env=None):
    result = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True,
        env={**os.environ, **(env or {})},
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.strip()


MAX_UNTRACKED_BYTES = 100 * 1024 * 1024
MAX_UNTRACKED_FILES = 5000


class TooLarge(Exception):
    """Untracked, non-ignored content too big to snapshot on every prompt."""


def _check_untracked(root, max_bytes, max_files):
    out = subprocess.run(["git", "ls-files", "-o", "--exclude-standard", "-z"], cwd=root,
                         capture_output=True, check=True).stdout
    paths = [p for p in out.decode(errors="replace").split("\0") if p]
    if len(paths) > max_files:
        raise TooLarge(f"{len(paths)} untracked files in {root}")
    total = 0
    for p in paths:
        try:
            total += (root / p).stat().st_size
        except OSError:
            continue
        if total > max_bytes:
            raise TooLarge(f"over {max_bytes // (1024 * 1024)} MB untracked in {root}")


def repo_root(cwd):
    try:
        return Path(git(cwd, "rev-parse", "--show-toplevel"))
    except (RuntimeError, FileNotFoundError, NotADirectoryError):
        return None


def take(cwd, message="grudges snapshot", max_untracked_bytes=MAX_UNTRACKED_BYTES,
         max_untracked_files=MAX_UNTRACKED_FILES):
    """Snapshot the repo containing `cwd`; None when it is not a git repo.

    Raises TooLarge rather than hashing huge untracked content (datasets, build
    output that is not gitignored) into the object store on every prompt.
    """
    root = repo_root(cwd)
    if root is None:
        return None
    _check_untracked(root, max_untracked_bytes, max_untracked_files)
    try:
        head = git(root, "rev-parse", "--verify", "-q", "HEAD")
    except RuntimeError:
        head = None  # unborn branch

    # Submodules first: each snapshot lives in the submodule's own object store,
    # and the parent's gitlink points at it, so the parent commit describes everything.
    submodules = {}
    for path in _submodule_paths(root):
        if (root / path / ".git").exists():
            sub = take(root / path, message, max_untracked_bytes, max_untracked_files)
            if sub is not None:
                submodules[path] = sub

    index = Path(git(root, "rev-parse", "--path-format=absolute", "--git-path", "index"))
    with tempfile.TemporaryDirectory(prefix="grudges-") as tmp:
        tmp_index = Path(tmp) / "index"
        if index.exists():
            # copy2 keeps the index mtime: git relies on it to detect "racily clean" entries
            # (same-size edits within the same second). A fresh mtime makes it trust stale stats.
            shutil.copy2(index, tmp_index)  # reuse the stat cache: fast on large repos
        env = {"GIT_INDEX_FILE": str(tmp_index)}
        git(root, "add", "-A", env=env)
        for path, sub in submodules.items():
            git(root, "update-index", "--cacheinfo", f"160000,{sub['commit']},{path}", env=env)
        tree = git(root, "write-tree", env=env)

    head_tree = git(root, "rev-parse", f"{head}^{{tree}}") if head else None
    dirty = tree != head_tree
    if dirty:
        parents = ["-p", head] if head else []
        commit = git(root, "commit-tree", tree, *parents, "-m", message, env=_IDENTITY)
    else:
        commit = head  # clean (submodules included, via their gitlinks): HEAD is the snapshot
    return {"root": str(root), "head": head, "commit": commit, "tree": tree, "dirty": dirty,
            "submodules": submodules}


def _submodule_paths(root):
    staged = git(root, "ls-files", "-s")
    return [line.split("\t", 1)[1] for line in staged.splitlines() if line.startswith("160000 ")]


def pin(snap, ref):
    """Keep a snapshot (and its submodule snapshots) from being garbage-collected."""
    git(snap["root"], "update-ref", ref, snap["commit"])
    for sub in (snap.get("submodules") or {}).values():
        pin(sub, ref)


def export(root, commit, dest):
    """Write a snapshot's files (submodules included, no .git) into `dest`."""
    root, dest = Path(root), Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(["git", "archive", commit], cwd=root, capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    for line in git(root, "ls-tree", "-r", commit).splitlines():
        meta, path = line.split("\t", 1)
        mode, kind, sub_commit = meta.split()
        if kind == "commit":  # gitlink: the submodule's own object store holds it
            export(root / path, sub_commit, dest / path)
