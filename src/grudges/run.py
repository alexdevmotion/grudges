"""Replay tasks across models with Harbor and turn trial receipts into results.

Scoring contract: only `solved`, `failed` and `timeout` attempts count toward a
model's score. Provider, grader and infrastructure errors are reported next to
the score, never silently dropped and never counted as model failures.
"""

import hashlib
import json
import math
import os
import re
import shutil
import statistics
import tempfile
import subprocess
import time
import tomllib
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from . import store

SCORED = ("solved", "failed", "timeout")
_PROVIDER = {"AgentAuthenticationError", "UnknownApiError"}
_GRADER = {"AddTestsDirError", "DownloadVerifierDirError", "RewardFileEmptyError",
           "RewardFileNotFoundError", "VerifierOutputParseError", "VerifierTimeoutError"}
# A crash or refusal is the agent's own outcome on the task, so it scores as failed.
_AGENT_FAILED = {"NonZeroAgentExitCodeError", "AgentSafetyRefusalError"}


def _status(t):
    exc = (t.get("exception_info") or {}).get("exception_type")
    if exc:
        if exc == "AgentTimeoutError":
            return "timeout"
        if exc.startswith("Api") or exc in _PROVIDER:
            return "provider_error"
        if exc in _GRADER:
            return "grader_error"
        if exc in _AGENT_FAILED:
            # Only once the agent was actually working; a crash while installing it is infra.
            return "failed" if (t.get("agent_execution") or {}).get("started_at") else "infra_error"
        return "infra_error"
    reward = ((t.get("verifier_result") or {}).get("rewards") or {}).get("reward")
    if not isinstance(reward, (int, float)) or not math.isfinite(reward):
        return "grader_error"
    return "solved" if reward >= 1.0 else "failed"


def _seconds(t):
    try:
        start = datetime.fromisoformat(t["started_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(t["finished_at"].replace("Z", "+00:00"))
        return round((end - start).total_seconds(), 1)
    except (KeyError, TypeError, ValueError):
        return None


def classify(t):
    agent_cfg = (t.get("config") or {}).get("agent") or {}
    info = t.get("agent_info") or {}
    usage = t.get("agent_result") or {}
    return {
        "task": t.get("task_name"),
        "trial": t.get("trial_name"),
        "agent": info.get("name") or agent_cfg.get("name"),
        "agent_version": info.get("version"),
        "model": agent_cfg.get("model_name") or (info.get("model_info") or {}).get("name"),
        "status": _status(t),
        "exception": (t.get("exception_info") or {}).get("exception_type"),
        "seconds": _seconds(t),
        "input_tokens": usage.get("n_input_tokens"),
        "output_tokens": usage.get("n_output_tokens"),
        "cost_usd": usage.get("cost_usd"),
    }


def collect(job_dir, setup=None):
    """Classify every trial receipt in a Harbor job directory, tagged with its setup."""
    records = []
    for p in sorted(Path(job_dir).glob("*/result.json")):
        try:
            records.append({**classify(json.loads(p.read_text())), "setup": setup})
        except (ValueError, TypeError, AttributeError) as exc:
            raise SystemExit(f"grudges: invalid trial receipt {p}: {type(exc).__name__}") from exc
    return records


def config_label(r):
    label = f"{r['agent']} · {r['model']}" if r.get("model") else r["agent"]
    return f"{label} · {r['setup']}" if r.get("setup") else label


def summarize(records):
    out = {}
    by_config = defaultdict(list)
    for r in records:
        by_config[config_label(r)].append(r)
    for label, rs in by_config.items():
        tasks = defaultdict(lambda: {"solved": 0, "scored": 0, "attempts": []})
        for r in rs:
            t = tasks[r["task"]]
            t["attempts"].append(r["status"])
            if r["status"] in SCORED:
                t["scored"] += 1
                t["solved"] += r["status"] == "solved"
        scored = [r for r in rs if r["status"] in SCORED]
        out[label] = {
            "tasks": dict(tasks),
            "n_tasks": len(tasks),
            # Stable success requires every planned attempt to be scored and a strict majority solved.
            "fixed": sum(1 for t in tasks.values() if t["scored"] == len(t["attempts"])
                         and t["solved"] * 2 > len(t["attempts"])),
            "complete": all(r["status"] in SCORED for r in rs),
            "missing_attempts": sum(r["status"] == "missing" for r in rs),
            "attempts_solved": sum(r["status"] == "solved" for r in scored),
            "attempts_scored": len(scored),
            "errors": dict(Counter(r["status"] for r in rs if r["status"] not in SCORED)),
            "median_seconds": _median([r["seconds"] for r in scored if r["seconds"] is not None]),
            "output_tokens": _sum_known(rs, "output_tokens"),
            "cost_usd": _sum_known(rs, "cost_usd"),
            "cost_complete": all(r["cost_usd"] is not None for r in rs),
        }
    return out


def _median(xs):
    return statistics.median(xs) if xs else None


def _sum_known(records, key):
    values = [r[key] for r in records if r[key] is not None]
    return sum(values) if values else None


def expand(paths):
    """Task dirs as given, or a pack dir expanded to its task subdirs (sorted)."""
    tasks = []
    for path in map(Path, paths):
        if (path / "task.toml").exists():
            tasks.append(path)
        elif path.is_dir():
            tasks.extend(sorted(p for p in path.iterdir() if (p / "task.toml").exists()))
        else:
            raise SystemExit(f"grudges: {path} is neither a task nor a pack directory")
    _validate_tasks(tasks)
    return tasks


def titles_for(task_dirs):
    """Public titles from each pack's titles.json, keyed by task directory name."""
    titles = {}
    for parent in {Path(t).resolve().parent for t in task_dirs}:
        f = parent / "titles.json"
        if f.exists():
            titles.update(json.loads(f.read_text()))
    return titles


def source_of(task_dirs):
    """'own' when every task was built from the user's grudges, else 'pack:<name>'."""
    own = store.subdir("grudges").resolve()
    parents = {Path(t).resolve().parent for t in task_dirs}
    if all(own in Path(t).resolve().parents for t in task_dirs):
        return "own"
    return "pack:" + "+".join(sorted(p.name for p in parents))


def _task_name(task):
    config = tomllib.loads((Path(task) / "task.toml").read_text())
    return (config.get("task") or {}).get("name", Path(task).name)


def _validate_tasks(tasks):
    if not tasks:
        raise SystemExit("grudges: provide at least one task")
    names, paths, receipt_names = set(), set(), set()
    for task in map(Path, tasks):
        if not (task / "task.toml").is_file():
            raise SystemExit(f"grudges: {task} is not a Harbor task (no task.toml)")
        name = _task_name(task)
        if not isinstance(name, str) or not name.strip():
            raise SystemExit(f"grudges: {task}: task name must be nonempty")
        if task.name in names or task.resolve() in paths or name in receipt_names:
            raise SystemExit(f"grudges: duplicate task or task-name collision: {task}")
        receipt_names.add(name)
        names.add(task.name)
        paths.add(task.resolve())


def _copy_task(task, dest):
    # Reject links rather than retain moving inputs or follow links outside the task.
    if any(p.is_symlink() for p in Path(task).rglob("*")):
        raise SystemExit(f"grudges: {task}: symlinks in task inputs are unsupported; materialize them first")
    shutil.copytree(task, dest, symlinks=False)


def make_dataset(task_dirs, dataset_dir):
    task_dirs = list(map(Path, task_dirs))
    _validate_tasks(task_dirs)
    dataset_dir = Path(dataset_dir)
    dataset_dir.mkdir(parents=True)
    for task in task_dirs:
        _copy_task(task, dataset_dir / task.name)
    return dataset_dir


CONFIG_DIR = Path.home() / ".config" / "grudges"


def load_keys(config_dir=None):
    """Provider keys from ~/.config/grudges/*.env: `KEY=value` lines, or one bare `sk-...` key.

    Replays always use API keys. Subscription logins (ChatGPT/Claude OAuth) must not be
    copied into containers: refresh tokens rotate, and the host login gets revoked.
    """
    keys = {}
    for f in sorted(Path(config_dir or CONFIG_DIR).glob("*.env")):
        for line in f.read_text().splitlines():
            line = line.strip().removeprefix("export ").strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                keys[k.strip()] = v.strip().strip("'\"")
            elif line.startswith("sk-ant-"):
                keys["ANTHROPIC_API_KEY"] = line
            elif line.startswith("sk-"):
                keys["OPENAI_API_KEY"] = line
    return keys


def preflight(task_dirs, agent):
    """Problems that would turn every trial into an infra error; empty when fine."""
    if agent in ("nop", "oracle"):
        return []
    problems = []
    for task in map(Path, task_dirs):
        config = tomllib.loads((task / "task.toml").read_text())
        if (config.get("environment") or {}).get("network_mode") == "no-network":
            problems.append(f"{task.name}: [environment] network_mode is no-network, so {agent} cannot install "
                            "itself or reach its model. Use an allowlist: install hosts for [environment], "
                            "only the model endpoint for [agent].")
    return problems


# Where each harness reads project rules, relative to the repository root.
RULES_FILES = {"codex": "AGENTS.md", "claude-code": "CLAUDE.md"}


def with_rules(task, rules, agent, dest):
    """Copy of `task` whose repository carries `rules` as the agent's project rules file.

    Expects the evals-from-sessions layout, where the Dockerfile copies environment/repo
    into the image. The rules replace any rules file the task already has: the question
    is whether your current rules make the agent get it right.
    """
    task, dest = Path(task), Path(dest)
    _validate_rules_layout(task, agent)
    _copy_task(task, dest)
    (dest / "environment" / "repo" / RULES_FILES[agent]).write_text(rules)
    return dest


def _validate_rules_layout(task, agent):
    if agent not in RULES_FILES:
        raise SystemExit(f"grudges: --rules does not support harness {agent}")
    dockerfile = Path(task) / "environment" / "Dockerfile"
    if (not (Path(task) / "environment" / "repo").is_dir()
            or not dockerfile.is_file()
            or not re.search(r"(?im)^COPY\s+repo/?\s+\S+", dockerfile.read_text())):
        raise SystemExit(f"grudges: {Path(task).name}: --rules requires environment/repo and a Dockerfile COPY repo/ layout")
    config = tomllib.loads((Path(task) / "task.toml").read_text())
    if (config.get("environment") or {}).get("docker_image"):
        raise SystemExit("grudges: --rules requires a source-built environment, not a prebuilt docker_image")


def replay_env(agent):
    env = {**load_keys(), **os.environ}
    # Harbor's native adapters also accept OAuth and Anthropic auth-token fallbacks.
    for var in ("CODEX_FORCE_AUTH_JSON", "CODEX_AUTH_JSON_PATH", "CLAUDE_FORCE_OAUTH",
                "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_AUTH_TOKEN",
                "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY"):
        env.pop(var, None)
    key = {"codex": "OPENAI_API_KEY", "claude-code": "ANTHROPIC_API_KEY"}.get(agent)
    if key and not env.get(key, "").strip():
        raise SystemExit(f"grudges: {agent} requires {key}; consumer authentication is never used")
    return env


def _missing_records(records, task_dirs, models, attempts, agent, setup):
    counts = Counter((r["task"], r["model"]) for r in records)
    expected = {(_task_name(task), model) for task in task_dirs for model in models}
    if any(pair not in expected or count > attempts for pair, count in counts.items()):
        raise SystemExit("grudges: unexpected task/model or excess receipts; refusing an ambiguous summary")
    return [dict(task=_task_name(task), trial=None, agent=agent, agent_version=None,
                 model=model, status="missing", exception=None, seconds=None,
                 input_tokens=None, output_tokens=None, cost_usd=None, setup=setup)
            for task in task_dirs for model in models
            for _ in range(max(0, attempts - counts[_task_name(task), model]))]


def replay(task_dirs, agent, models, attempts=3, effort=None, concurrency=4, rules=None):
    """Run every task on every model. With `rules` (a rules file's text), run twice:
    once as captured and once with that rules file, so the card shows whether the rules fix it.
    """
    task_dirs = expand(task_dirs)
    models = list(models)
    if not models and agent in ("nop", "oracle"):
        models = [None]
    if not models or any(not isinstance(m, str) or not m.strip() or m != m.strip() for m in models if not (m is None and agent in ("nop", "oracle"))) or len(set(models)) != len(models):
        raise SystemExit("grudges: provide nonempty, unique models")
    if any(type(n) is not int or n <= 0 for n in (attempts, concurrency)):
        raise SystemExit("grudges: attempts and concurrency must be positive integers")
    if rules is not None:
        for task in task_dirs:
            _validate_rules_layout(task, agent)
    env = replay_env(agent)
    problems = preflight(task_dirs, agent)
    if problems:
        raise SystemExit("grudges: refusing to run:\n  " + "\n  ".join(problems))
    run_dir = Path(tempfile.mkdtemp(prefix=time.strftime("%Y%m%d-%H%M%S-"), dir=store.subdir("runs")))
    run_id = run_dir.name
    jobs = [(agent, make_dataset(task_dirs, run_dir / "tasks"), "as captured" if rules is not None else None)]
    if rules is not None:
        ruled = run_dir / "tasks-with-rules"
        ruled.mkdir(parents=True)
        for t in task_dirs:
            with_rules(run_dir / "tasks" / Path(t).name, rules, agent, ruled / Path(t).name)
        jobs.append((f"{agent}-rules", ruled, "with rules"))
    pinned_config = {
        "agent": agent, "models": models, "attempts": attempts, "concurrency": concurrency,
        "expected_tasks": [_task_name(t) for t in (run_dir / "tasks").iterdir()],
        "effort": effort, "rules_sha256": hashlib.sha256(rules.encode()).hexdigest() if rules is not None else None,
        "task_configs": {t.name: tomllib.loads((run_dir / "tasks" / t.name / "task.toml").read_text()) for t in task_dirs},
    }
    store.write_json(run_dir / "config.json", pinned_config)
    started = time.time()
    records, exit_codes = [], []
    for job_name, dataset, setup in jobs:
        cmd = ["harbor", "run", "-p", str(dataset), "-a", agent, "-k", str(attempts),
               "-n", str(concurrency),
               "-o", str(run_dir / "jobs"), "--job-name", job_name, "-q", "-y"]
        for m in models:
            if m is not None:
                cmd += ["-m", m]
        if effort:
            cmd += ["--effort", effort]
        exit_codes.append(subprocess.run(cmd, env=env).returncode)
        receipts = collect(run_dir / "jobs" / job_name, setup)
        records += receipts + _missing_records(receipts, list(dataset.iterdir()), models, attempts, agent, setup)
    result = {
        "run_id": run_id,
        "agent": agent,
        "models": models,
        "attempts": attempts,
        "rules": rules is not None,
        "rules_sha256": pinned_config["rules_sha256"],
        "config": pinned_config,
        "harbor_exit_code": max(exit_codes),
        "wall_seconds": round(time.time() - started, 1),
        "tasks": [str(Path(t).resolve()) for t in task_dirs],
        "titles": titles_for(task_dirs),
        "source": source_of(task_dirs),
        "records": records,
        "summary": summarize(records),
        "complete": all(r["status"] in SCORED for r in records),
    }
    store.write_json(run_dir / "results.json", result)
    return run_dir, result
