"""Trusted local CLI replay. Credentials stay with the installed agent.

Agent workspaces are separate from verifier inputs, but not a host security
boundary. Host commands grade a disposable candidate copy after the CLI has exited.
"""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

from . import run, store

RUNNERS = {"local-codex": "codex", "local-claude": "claude"}


def environment():
    """Keep native login locations; remove API, provider and injected-token overrides."""
    allowed = {"HOME", "PATH", "USER", "LOGNAME", "SHELL", "LANG", "LC_ALL", "TERM",
               "TMPDIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_RUNTIME_DIR",
               "CODEX_HOME", "CLAUDE_CONFIG_DIR", "SSL_CERT_FILE", "SSL_CERT_DIR",
               "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy",
               "NODE_EXTRA_CA_CERTS"}
    return {k: v for k, v in os.environ.items() if k in allowed}


def command(runner, model, effort=None):
    if runner == "local-codex":
        cmd = ["codex", "exec", "--json", "--ephemeral", "--sandbox", "workspace-write",
               "-c", 'approval_policy="never"', "-c", 'forced_login_method="chatgpt"',
               "-c", 'model_provider="openai"', "-c", 'sandbox_workspace_write.network_access=false']
        if effort:
            cmd += ["-c", f"model_reasoning_effort={json.dumps(effort)}"]
        if model:
            cmd += ["-m", model]
        return cmd + ["-"]
    cmd = ["claude", "-p", "--output-format", "stream-json", "--verbose", "--restricted",
           "--permission-mode", "acceptEdits", "--permission-prompts", "none",
           "--tools", "Read,Edit,Write,Glob,Grep", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
           "--setting-sources", "", "--settings", '{"forceLoginMethod":"claudeai","disableAllHooks":true}',
           "--no-session-persistence"]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    return cmd


def prompt_for(task, workspace, runner):
    prompt = ("Any instruction referring to /app means "
              "your current working directory here, not the host /app.\n\n")
    if runner == "local-claude":
        # Restricted Claude does not auto-load CLAUDE.md, even with project setting sources.
        rules = workspace / "CLAUDE.md"
        if rules.is_file():
            prompt += "Project instructions (root CLAUDE.md):\n" + rules.read_text() + "\n\n"
    prompt += (task / "instruction.md").read_text()
    prompt += "\n\nWork only in this repository. Implement the requested change. Hidden verification runs separately after you finish."
    if runner == "local-claude":
        prompt += "\nThis replay exposes file read/edit tools only; do not try to run shell commands."
    return prompt


def authenticate(runner, env):
    binary = RUNNERS[runner]
    if not shutil.which(binary):
        raise ValueError(f"install {binary} and sign in with your subscription first")
    args = (["codex", "-c", 'forced_login_method="chatgpt"', "login", "status"]
            if runner == "local-codex" else ["claude", "auth", "status", "--json"])
    p = subprocess.run(args, env=env, capture_output=True, text=True, timeout=30)
    if runner == "local-codex":
        valid = p.returncode == 0 and "Logged in using ChatGPT" in p.stdout + p.stderr
    else:
        try:
            auth = json.loads(p.stdout)
            valid = (p.returncode == 0 and auth.get("loggedIn") is True
                     and auth.get("authMethod") == "claude.ai" and auth.get("apiProvider") == "firstParty")
        except (ValueError, AttributeError):
            valid = False
    if not valid:
        raise ValueError(f"{binary} must be signed in with its subscription; no API fallback is allowed")
    help_args = [binary, "exec", "--help"] if runner == "local-codex" else [binary, "--help"]
    help_text = subprocess.run(help_args, env=env, capture_output=True, text=True, timeout=30).stdout
    required = ("--ephemeral", "--json", "--sandbox") if runner == "local-codex" else ("--restricted", "--permission-prompts", "--no-session-persistence")
    if not all(flag in help_text for flag in required):
        raise ValueError(f"update {binary}: required local replay flags are unavailable")
    return subprocess.run([binary, "--version"], env=env, capture_output=True, text=True, check=True, timeout=30).stdout.strip()


def validate_task(task):
    cfg = tomllib.loads((task / "task.toml").read_text())
    if not (task / "environment/repo").is_dir():
        raise ValueError(f"{task.name}: missing environment/repo")
    for key in ("verify", "solve"):
        argv = cfg.get("local", {}).get(key)
        if not isinstance(argv, list) or not argv or any(not isinstance(v, str) or not v for v in argv):
            raise ValueError(f"{task.name}: add [local] {key} argv to task.toml for Docker-free replay; "
                             "use --runner harbor for container-only tasks")
    if not (task / "instruction.md").is_file():
        raise ValueError(f"{task.name}: missing instruction.md")
    for p in task.rglob("*"):
        if p.is_symlink() or p.name == ".git":
            raise ValueError(f"{task.name}: materialize links and remove nested Git metadata before replay")
    return cfg


def execute(cmd, cwd, env, log, timeout, prompt=None):
    """Private logs; kill the whole process group on timeout or interruption."""
    with log.open("w") as out, log.with_suffix(".stderr").open("w") as err:
        p = subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.PIPE,
                             stdout=out, stderr=err, text=True, start_new_session=True)
        try:
            p.communicate(prompt, timeout=timeout)
        except BaseException:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
            raise
    return p.returncode


def agent_result(runner, path):
    if path.stat().st_size > 32 * 1024 * 1024:
        raise ValueError("agent output exceeded 32 MiB")
    raw = path.read_text()
    if runner == "local-claude":
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
        if init.get("apiKeySource") != "none":
            raise ValueError("Claude did not confirm native subscription authentication")
        data = next((e for e in reversed(events) if e.get("type") == "result"), {})
        if data.get("is_error") or data.get("subtype") != "success":
            return {"status": "agent_error"}
        usage = data.get("usage") or {}
        models = list((data.get("modelUsage") or {}).keys())
        return {"status": "completed", "resolved_model": ",".join(models) or None,
                "permission_denials": len(data.get("permission_denials") or []),
                "input_tokens": sum(usage.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")),
                "cached_input_tokens": usage.get("cache_read_input_tokens"), "output_tokens": usage.get("output_tokens")}
    events = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if any(e.get("type") in ("error", "turn.failed") for e in events):
        return {"status": "agent_error"}
    finished = [e for e in events if e.get("type") == "turn.completed"]
    if not finished:
        raise ValueError("Codex did not emit turn.completed")
    usage = finished[-1].get("usage") or {}
    return {"status": "completed", "input_tokens": usage.get("input_tokens"),
            "cached_input_tokens": usage.get("cached_input_tokens"), "output_tokens": usage.get("output_tokens")}


def verify(task, workspace, trial, env, timeout, oracle=False):
    candidate = trial / "verifier-workspace"
    shutil.copytree(workspace, candidate)
    cfg = validate_task(task)["local"]
    env = {**env, "GRUDGES_WORKSPACE": str(candidate), "GRUDGES_TASK": str(task)}
    def argv(key):
        return [arg.replace("{task}", str(task)).replace("{workspace}", str(candidate))
                .replace("{python}", sys.executable) for arg in cfg[key]]
    try:
        if oracle and execute(argv("solve"), candidate, env, trial / "solution.log", timeout):
            return "grader_error"
        code = execute(argv("verify"), candidate, env, trial / "verifier.log", timeout)
        (trial / "verifier-exit-code").write_text(str(code))
        return {0: "solved", 1: "failed"}.get(code, "grader_error")
    except (ValueError, OSError, subprocess.TimeoutExpired):
        return "grader_error"


def controls(task, trial, env, timeout):
    """Check baseline and reference through the same local verifier as candidates."""
    for label, expected in (("baseline", "failed"), ("oracle", "solved")):
        folder = trial / label
        folder.mkdir()
        actual = verify(task, task / "environment/repo", folder, env, timeout, oracle=label == "oracle")
        if actual != expected:
            raise ValueError(f"{label} control returned {actual}, expected {expected}; inspect {folder}")


def replay(task_dirs, runner, models, attempts=1, effort=None, rules=None, trust_local=True):
    if not sys.platform.startswith("linux"):
        raise ValueError("local runners currently support Linux hosts only")
    if type(attempts) is not int or attempts < 1:
        raise ValueError("attempts must be positive")
    if runner not in RUNNERS:
        raise ValueError("unknown local runner")
    models = list(models) or [None]
    if len(set(models)) != len(models) or any(m is not None and (not isinstance(m, str) or not m.strip() or m != m.strip()) for m in models):
        raise ValueError("models must be nonempty and unique")
    tasks = run.expand(task_dirs)
    for task in tasks:
        validate_task(task)
    env = environment()
    version = authenticate(runner, env)
    directory = Path(tempfile.mkdtemp(prefix=time.strftime("%Y%m%d-%H%M%S-local-"), dir=store.subdir("runs")))
    frozen = run.make_dataset(tasks, directory / "tasks")
    setups = [("as captured", frozen)]
    agent = "codex" if runner == "local-codex" else "claude-code"
    if rules is not None:
        ruled = directory / "tasks-with-rules"
        for task in frozen.iterdir():
            dest = ruled / task.name
            run._copy_task(task, dest)
            (dest / "environment/repo" / run.RULES_FILES[agent]).write_text(rules)
        setups.append(("with rules", ruled))
    records = []
    for task_name in sorted(t.name for t in frozen.iterdir()):
        for model in models:
            for attempt in range(attempts):
                for setup, dataset in setups:
                    task = dataset / task_name
                    records.append(dict(task=run._task_name(task), trial=f"trial-{len(records)+1:04d}",
                        agent=runner, agent_version=version, model=model or "CLI default", setup=setup if rules is not None else None,
                        status="missing", seconds=None, input_tokens=None, output_tokens=None, cost_usd=None, billing="subscription",
                        task_dir=str(task), attempt=attempt+1))
    result = dict(run_id=directory.name, runner=runner, agent=runner, models=models, attempts=attempts,
                  rules=rules is not None, source=run.source_of(tasks), titles=run.titles_for(tasks),
                  tasks=[str(t) for t in tasks], records=records,
                  config=dict(runner=runner, agent_version=version, models=models, attempts=attempts, effort=effort,
                              tool_profile="workspace shell" if runner == "local-codex" else "file editing only",
                              concurrency=1, billing="subscription", isolation="trusted host workspace and local verifier",
                              rules_sha256=hashlib.sha256(rules.encode()).hexdigest() if rules is not None else None))
    store.write_json(directory / "config.json", result["config"])
    started = time.monotonic()
    def persist():
        result.update(summary=run.summarize(records), complete=all(r["status"] in run.SCORED for r in records),
                      wall_seconds=round(time.monotonic()-started, 1))
        store.write_json(directory / "results.json", result)
    persist()
    checked = set()
    try:
        for record in records:
            task = Path(record["task_dir"])
            cfg = validate_task(task)
            trial = directory / record["trial"]
            trial.mkdir(mode=0o700)
            tick = time.monotonic()
            phase = "setup"
            try:
                if task not in checked:
                    print(f"Checking {record['task']} ({record['setup'] or 'as captured'})…", flush=True)
                    controls(task, trial, env, float(cfg.get("verifier", {}).get("timeout_sec", 120)))
                    checked.add(task)
                record["setup_seconds"] = round(time.monotonic()-tick, 1)
                tick = time.monotonic()
                with tempfile.TemporaryDirectory(prefix="grudges-work-") as tmp:
                    workspace = Path(tmp) / "repo"
                    shutil.copytree(task / "environment/repo", workspace)
                    if execute(["git", "-c", "core.hooksPath=/dev/null", "init", "--template="], workspace, env, trial / "git.log", 30):
                        raise RuntimeError("git init failed; see git.log")
                    prompt = prompt_for(task, workspace, runner)
                    print(f"Running {RUNNERS[runner]} · {record['model']} · attempt {record['attempt']}…", flush=True)
                    phase = "agent"
                    code = execute(command(runner, record["model"] if record["model"] != "CLI default" else None, effort),
                                   workspace, env, trial / "agent.json", float(cfg.get("agent", {}).get("timeout_sec", 1200)), prompt)
                    if code:
                        record.update(status="agent_error", exception=f"CLI exit {code}")
                    else:
                        record.update(agent_result(runner, trial / "agent.json"))
                    if record["status"] == "completed":
                        if any(p.is_symlink() for p in workspace.rglob("*")):
                            raise ValueError("agent produced symlinks; refusing candidate export")
                        shutil.copytree(workspace, trial / "candidate", ignore=shutil.ignore_patterns(".git"))
                        phase = "verifier"
                        record["status"] = verify(task, trial / "candidate", trial, env,
                                                  float(cfg.get("verifier", {}).get("timeout_sec", 120)))
            except subprocess.TimeoutExpired:
                record.update(status="infra_error", exception=f"{phase} timeout; completion unverified")
            except (ValueError, OSError, RuntimeError) as exc:
                record.update(status="infra_error", exception=str(exc))
            finally:
                record["seconds"] = round(time.monotonic()-tick, 1)
                persist()
            print(f"{record['trial']}: {record['task']} · {record['status']}", flush=True)
            if record["status"] not in run.SCORED:
                break  # Do not burn allowance after an authentication/quota/runner failure.
    except KeyboardInterrupt:
        result["interrupted"] = True
        for record in records:
            if record["status"] == "completed":
                record.update(status="infra_error", exception="verification interrupted")
        persist()
    finally:
        persist()
    return directory, result
