# Usage

## Run with your subscription

```bash
uvx --from git+https://github.com/alexdevmotion/grudges@v0.3.0a1 grudges run
```

No arguments runs one starter task once. Codex is selected if installed, otherwise Claude. Sign in beforehand with `codex login` or `claude auth login`. Grudges rejects API logins for native runs and never automatically switches to API billing.

```bash
grudges run --agent claude
grudges run path/to/task
grudges run --pack starter
grudges run --pack starter-intent
grudges run path/to/task --rules ./AGENTS.md -k 3
grudges run path/to/task --agent claude --rules ./CLAUDE.md
```

`-m MODEL` selects a model your subscription supports; omit it for the CLI default. Repeat `-m` to compare models. `--effort` forwards the CLI effort setting. Runs are sequential. `--runner local-codex` and `--runner local-claude` remain compatible aliases; `--trust-local` is no longer required.

Requirements: Linux, Git, and a recent signed-in official CLI. uv provides the Python runtime. Bundled tasks use only Python's standard library and Bash. No Docker daemon or Harbor installation is needed. Custom tasks may have additional documented host dependencies.

## How local verification works

Grudges freezes task inputs, checks that the baseline fails and the reference fix passes, then launches the agent in a fresh temporary source workspace. After it exits, Grudges grades a disposable candidate copy using the task's local verifier. Neither the original task nor the captured candidate is modified by grading. Rules setups run back to back for each attempt.

Everything runs on your host. Use reviewed tasks: verification commands are executable code, have host access, and are not network-isolated. Codex uses its native workspace sandbox and shell. Claude uses restricted file tools; Grudges includes root `CLAUDE.md` in its prompt because restricted mode does not auto-load it. `@import` directives are not expanded. Tool profiles and host settings differ, so these are not isolated cross-agent benchmarks.

## Write a native task

```text
my-task/
  task.toml
  instruction.md
  environment/repo/       # starting source, copied for each attempt
  tests/verify.py          # kept outside the agent workspace
  solution/solve.sh        # reference fix
```

Add explicit local commands to `task.toml`:

```toml
[task]
name = "my-task"

[local]
verify = ["{python}", "{task}/tests/verify.py"]
solve = ["bash", "{task}/solution/solve.sh"]
```

Commands are argument arrays, not shell strings. They run with the disposable repository as their working directory. `{python}` is Grudges' Python interpreter; `{task}` and `{workspace}` resolve to absolute paths. `GRUDGES_TASK` and `GRUDGES_WORKSPACE` also expose those paths to subprocesses. Never hardcode `/app` in native scripts. Dockerfiles are optional and ignored by native replay.

The verifier exits **0 for solved**, **1 for failed**, and **any other code for a verifier error**. The reference command must exit 0. Use exit 2 for missing dependencies or broken test infrastructure. Dependencies must already be installed; Grudges does not install arbitrary task dependencies. Symlinks and nested Git metadata are rejected. Container-only tasks need an explicit local verifier or the alternative Harbor route below.

## Capture your own failure

```bash
grudges install
# In Claude Code: /grudge what the correct outcome should have been
# In Codex:       $grudge what the correct outcome should have been
grudges requests
grudges list
grudges build GRUDGE_ID --shareable
```

Installation adds a prompt hook and skill to your local agent configuration. Existing config is backed up; unrelated hooks and edited skills are preserved. Codex may ask you to approve the hook. `grudges install --uninstall` removes managed hooks and unchanged managed skills.

Before each request, capture snapshots tracked and non-ignored untracked files using a temporary Git index. Saving pins the starting and failed states under `refs/grudges/` and copies the session transcript into `~/.grudges`. Your working tree, normal index and branches are preserved. Missing or failed checkpoints are labeled approximate. Avoid concurrent writers while capturing; filesystem snapshots are not atomic across files. Large snapshots are skipped.

Task building fetches a pinned [evals-from-sessions](https://github.com/ibragim-bad/evals-from-sessions) authoring skill and launches your chosen local agent interactively. Review the reconstruction and verifier before accepting the task. `--shareable` requests fresh code and names; it is not an automatic privacy guarantee. `--print` prints the authoring brief without launching the agent, but still prepares files and fetches the skill.

## Read results

Each run writes `results.json`, `card.html`, candidates and verifier logs under `~/.grudges/runs/`. `grudges card` regenerates the latest card. `--titles titles.json` supplies public task titles.

Cards show solved/scored attempts, errors and missing attempts. Majority-fixed requires all planned attempts scored and a strict majority solved. Native timeouts remain unscored because provider retries cannot be distinguished from model work. Authentication and infrastructure errors stop the queue; remaining attempts stay missing. CLI exit 2 signals execution errors or interruption; valid task failures return 0. Subscription costs are unavailable, never inferred from API prices.

## Privacy and limits

Snapshots and transcripts can contain secrets, including files later deleted. Keep `~/.grudges`, Git refs and raw receipts private. Authoring and replay send code to the chosen provider. Cards omit raw paths and prompts, but review their visible labels before sharing. No telemetry or hosted service is included. macOS and Windows are not validated.

## Alternative: API and container replay

Install Harbor 0.24.0 and run Docker with Compose and Buildx. Set the provider API key in the environment, then explicitly select Harbor:

```bash
grudges run path/to/task --runner harbor -a codex -m MODEL_ID -k 3
grudges run path/to/task --runner harbor -a claude-code -m MODEL_ID
grudges run --pack starter --runner harbor -a nop
grudges run --pack starter --runner harbor -a oracle
```

API runs incur provider charges. Native subscription credentials are not forwarded. Harbor requires its task layout, Dockerfile and `tests/test.sh`; it ignores the native `[local]` commands. Rules comparisons require source-built `COPY repo/` tasks and reject prebuilt `docker_image` tasks. Harbor agent timeouts count as scored failures. For compatibility, `-a nop` and `-a oracle` select Harbor automatically.

## Development

```bash
python3 -m pip install -e . build
python3 -m unittest discover -s tests -v
python3 -m build
python3 scripts/check_dist.py dist
```

See [CONTRIBUTING.md](../CONTRIBUTING.md) and [RELEASING.md](../RELEASING.md).
