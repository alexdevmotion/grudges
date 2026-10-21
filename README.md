<div align="center">

# grudges

### Turn agent mistakes into regression tests.

Check whether a new model or project rule fixes the mistakes your coding agent already made.

Uses your Codex or Claude subscription.

[![CI](https://github.com/alexdevmotion/grudges/actions/workflows/ci.yml/badge.svg)](https://github.com/alexdevmotion/grudges/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/alexdevmotion/grudges?include_prereleases&color=e9a745)](https://github.com/alexdevmotion/grudges/releases)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

[Get started](#get-started) · [Capture a failure](#capture-the-next-failure) · [Test your rules](#test-your-rules) · [Docs](docs/usage.md)

<picture>
<source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/demo.png">
<img src="docs/assets/demo.gif" alt="Grudges demo: capture a failure, replay with your subscription, and compare project rules." width="900">
</picture>

<sub>Edited walkthrough: local capture and subscription replay. [Static version](docs/assets/demo.png) · [Demo source & transcript](docs/demo.md)</sub>

</div>

**Capture the mistake → build a test you review → replay it → inspect what passed.**

For example: your agent keeps breaking amount formatting. Save that failure once, then test whether a new `AGENTS.md` rule prevents it on a fresh attempt.

## Get started

Already signed in to Codex or Claude Code? Run one bundled task:

```bash
uvx --from git+https://github.com/alexdevmotion/grudges@v0.3.0a1 grudges run
```

Or install once:

```bash
uv tool install git+https://github.com/alexdevmotion/grudges@v0.3.0a1
grudges run
```

Grudges chooses your installed CLI (Codex if both are present), checks the broken input and reference fix, runs one attempt, and prints a results card. It uses your subscription allowance.

```bash
grudges run --agent claude       # choose Claude
grudges run path/to/task         # replay your own task
grudges run --pack starter       # all eight starter tasks
```

This first run uses a bundled example; capture and build your own failures below.

Requires [uv](https://docs.astral.sh/uv/), Git, and a signed-in recent Codex or Claude CLI. The bundled tasks use Python and Bash. Linux required for this alpha. Task code and verification run locally: use tasks you trust. [Details](docs/usage.md).

## Capture the next failure

Your agent fixed the wrong thing. Save the starting code and failed attempt so you can test it again:

```bash
grudges install
```

Then, inside your agent:

```text
Claude Code → /grudge The amount should stay editable until blur.
Codex       → $grudge The amount should stay editable until blur.
```

```bash
grudges list
grudges build GRUDGE_ID
```

Building opens an authoring session. Review the reconstructed task and verifier, then run the task path it prints. Capture preserves your working tree, index and branches. Add `--shareable` when you intend to publish a task; it requests fresh code and names, not automatic privacy clearance.

## Test your rules

```bash
grudges run path/to/task --rules ./AGENTS.md
grudges run path/to/task --agent claude --rules ./CLAUDE.md
```

Each comparison runs the task **as captured** and **with rules** in fresh workspaces. The second setup replaces the root rules file. Existing baseline rules remain intact.

Want more evidence? Repeat attempts or choose models supported by your subscription:

```bash
grudges run path/to/task --rules ./AGENTS.md -k 3
grudges run path/to/task -m MODEL_A -m MODEL_B
```

## Keep receipts

Every run saves `results.json`, candidate code, verifier output and `card.html` under `~/.grudges/runs/`. Cards show solved/scored attempts, errors and missing attempts. A task is majority-fixed only when all planned attempts are scored and more than half solve it. Subscription cost is unavailable, not zero.

The [eight starter tasks](packs/starter/README.md) and [six intent tasks](packs/starter-intent/README.md) demonstrate the workflow. They are not a model leaderboard. Codex has a workspace shell; Claude uses restricted file-editing tools. Host configuration can affect results. [Usage and limits](docs/usage.md).

Capture stays local, but code sent to an agent goes to its provider. Keep snapshots and raw sessions private. [Security](SECURITY.md) · [License](LICENSE)

## Alternative: API replay with Harbor

For container-based tasks or API-funded evaluations, install [Harbor](https://github.com/harbor-framework/harbor) and Docker separately:

```bash
uv tool install 'harbor==0.24.0'
# Set your provider API key in the environment.
grudges run path/to/task --runner harbor -a codex -m YOUR_MODEL_ID
```

This route incurs API charges and requires Docker with Compose and Buildx. Subscription credentials are never copied into containers. [Advanced usage](docs/usage.md#alternative-api-and-container-replay).

Task authoring builds on [evals-from-sessions](https://github.com/ibragim-bad/evals-from-sessions). Apache-2.0; adapted portions retain their notices in [NOTICE](NOTICE).
