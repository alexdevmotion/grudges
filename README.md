# grudges

Save the tasks your coding agent failed. Replay them on another model—or check whether your project rules help.

**Local alpha, 0.1.0a1.** Not yet published to PyPI. Linux is the tested platform. The example packs demonstrate the workflow; they are not a representative model leaderboard.

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

Live runs cost money. Codex and Claude Code replay require provider API keys; subscription credentials are not forwarded. Each run freezes task copies and records its configuration before execution. Rules comparisons support the `environment/repo` plus `COPY repo/` Dockerfile layout and the Codex/Claude Code harnesses. Prebuilt `docker_image` tasks are rejected for rules comparisons because they would bypass the modified files. The comparison is **as captured** versus **with rules**: the baseline can already contain rules. The supplied text replaces the root harness rules file in the second copy; it does not remove other instruction files.

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

Cards show solved/scored attempts, errors and missing attempts. A task is majority-fixed only when all planned attempts are scored and strictly more than half solve it. Agent timeouts count as scored failures; provider, infrastructure and grader errors do not. Partial cost totals are labeled. A whole-task reward cannot identify which individual requirement failed. Inspect verifier receipts for that detail. CLI exit 2 signals setup/execution errors; a valid scored task failure returns 0.

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

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) and [RELEASING.md](RELEASING.md). Apache-2.0; adapted portions retain their MIT notice in [NOTICE](NOTICE). Execution uses [Harbor](https://github.com/harbor-framework/harbor).
