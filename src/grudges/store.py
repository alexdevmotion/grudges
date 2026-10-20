"""Local storage under $GRUDGES_HOME (default ~/.grudges), private to the user."""

import json
import os
from pathlib import Path


def home():
    path = Path(os.environ.get("GRUDGES_HOME") or Path.home() / ".grudges")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def subdir(name):
    path = home() / name
    path.mkdir(mode=0o700, exist_ok=True)
    return path


def append_jsonl(path, record):
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, "a") as f:
        f.write(json.dumps(record) + "\n")


def read_jsonl(path):
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a torn write must not hide the rest of the log
    return records


def write_json(path, record):
    tmp = path.with_suffix(".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(record, f, indent=2)
        f.write("\n")
    tmp.replace(path)
