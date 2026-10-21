# Usage and behavior

## Try a pack

From this checkout, with Python 3.11+ and Git:

```bash
uv tool install .
grudges --version
uv tool install 'harbor==0.24.0'
# Requires a running Docker daemon with Compose and Buildx.
grudges run --pack starter -a nop -k 1
grudges run --pack starter -a oracle -k 1
```

These controls make no model API calls: nop checks the starting implementation; oracle runs the reference solution. Docker may download images. The wheel includes eight explicit starter tasks and six intent tasks (`--pack starter-intent`). Read each pack's README and FAIRNESS notes before interpreting results.

For a model run, set `OPENAI_API_KEY` in your environment and choose a model available to your account:

```bash
grudges run --pack starter -a codex -m YOUR_MODEL_ID -k 3
grudges run path/to/task -a codex -m YOUR_MODEL_ID --rules ./AGENTS.md
```

Harbor model runs incur API charges and require provider API keys. Subscription credentials are not forwarded into Harbor. Each run freezes task copies and records its configuration before execution. Rules comparisons support the `environment/repo` plus `COPY repo/` Dockerfile layout and the Codex/Claude Code harnesses. Prebuilt `docker_image` tasks are rejected for rules comparisons because they would bypass the modified files. The comparison is **as captured** versus **with rules**: the baseline can already contain rules. The supplied text replaces the root harness rules file in the second copy; it does not remove other instruction files.

## Subscription runners

Use `--runner local-codex` or `--runner local-claude` with `--trust-local`. They launch the installed official CLI on your host using its existing ChatGPT or Claude subscription login. API login is rejected, provider/key environment overrides are removed, and there is no API fallback. Grudges never reads, copies, or exports login tokens. Allowance limits still apply; cost is labeled unavailable, never $0.

```bash
codex login  # or: claude auth login
grudges run path/to/task --runner local-codex --trust-local -k 1
grudges run path/to/task --runner local-claude --trust-local -m sonnet -k 1
grudges run path/to/task --runner local-claude --trust-local --rules ./CLAUDE.md -k 3
```

Requirements: Linux, Git, Docker, and a recent CLI. Codex must support `--ephemeral`; Claude must support `--restricted` and `--permission-prompts`. `-m` is optional and otherwise uses the CLI default; choose a model your plan supports. `--effort` forwards the CLI's effort setting. Local runs are sequential; `--agent` is for Harbor only.

Supported tasks have `environment/repo`, an explicit `COPY repo/ /app/`, `WORKDIR /app`, `tests/test.sh`, and `solution/solve.sh`. Prebuilt images, symlinks and nested Git metadata are rejected. Baseline must fail and the reference solution must pass using the same verifier mount arrangement before any model attempt. Tasks requiring hidden build artifacts beneath `/app` may fail this gate. The verifier must work without network access and write a binary reward to `/logs/verifier/reward.txt`.

Every attempt gets a fresh temporary source workspace. Candidates are preserved locally; verification runs in Docker with no network and a disposable writable copy. Task text referring to `/app` is mapped to the temporary working directory for the agent. Restricted Claude does not auto-load project instructions, so Grudges explicitly includes the root `CLAUDE.md` in its prompt for both baseline and rules setups; `@import` directives are not expanded and nested instruction discovery is not guaranteed. CLI versions, requested models, tool profiles and rules hashes are recorded. Claude's reported model usage is retained; Codex's requested model is not independently verified.

Local mode is for **trusted tasks only**. Codex uses its workspace sandbox and shell; Claude uses restricted Read/Edit/Write/Glob/Grep tools and cannot run tests itself. Host tools, global instructions and CLI configuration may affect results. An agent can potentially discover verifier inputs elsewhere on the host. Do not treat these results as isolated benchmarks, compare the two tool profiles as equivalent, or use this mode for hostile tasks. Credentials remain in their normal location and are not mounted into Docker.

Authentication, quota and incomplete-output errors stop the queue, preserve receipts, and leave remaining attempts missing. Local timeouts are unscored infrastructure errors because a timeout alone cannot distinguish model work from provider retries. No automatic retry spends additional allowance.

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

Each run writes `results.json` and `card.html` under `~/.grudges/runs/`. `grudges card` renders the latest run, or pass a run directory. `--titles titles.json` supplies public task titles.

Cards show solved/scored attempts, errors and missing attempts. A task is majority-fixed only when all planned attempts are scored and strictly more than half solve it. Harbor agent timeouts count as scored failures; local timeouts remain unscored; provider, infrastructure and grader errors do not. Partial cost totals are labeled. A whole-task reward cannot identify which individual requirement failed. Inspect verifier receipts for that detail. CLI exit 2 signals setup/execution errors; a valid scored task failure returns 0.

## Privacy and limits

Capture is local, but snapshots and transcripts can contain secrets or private code—even when the current files are later deleted. Git ignore rules do not exclude already tracked secrets. Keep `~/.grudges`, Git refs, build workspaces and raw Harbor results private. Building and replaying tasks can send code to the configured provider. Docker tasks execute code; review unfamiliar tasks before running them.

Cards omit raw paths, prompts and run metadata, and use neutral task names when public titles are unavailable. Still review titles, model names and all visible content before sharing. No telemetry or hosted service is included. macOS and Windows have not been validated.

## Development and license

```bash
python3 -m pip install -e . build
python3 -m unittest discover -s tests -v
python3 -m build
python3 scripts/check_dist.py dist
```

See [CONTRIBUTING.md](../CONTRIBUTING.md), [SECURITY.md](../SECURITY.md) and [RELEASING.md](../RELEASING.md). Apache-2.0; adapted portions retain their MIT notice in [NOTICE](../NOTICE). Execution uses [Harbor](https://github.com/harbor-framework/harbor).
