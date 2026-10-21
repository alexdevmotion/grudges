# README demo

The animation is an edited walkthrough, not a real-time recording. It loops for 18 seconds and has a [static alternative](assets/demo.png). No paid model calls were made to produce it.

## What is real

1. **Capture:** a temporary Git repository contained a tiny amount-formatting fixture. The prompt hook ran before a deliberately incorrect edit. `grudges save --session demo --note "Keep the amount editable until blur."` saved an exact starting state. The displayed output is real, with the generated ID replaced by `DEMO_ID`. No user project or agent session is included.
2. **Replay:** the starter-pack nop and oracle counts come from the release validation's individual Harbor receipts: 0/8 and 8/8 solved, no errors. These are controls on the bundled pack, not a replay of the capture fixture, a model comparison or a speed claim. Progress logs and waiting time are omitted.
3. **Compare:** the final scene shows next-step command examples. `MODEL_A`, `MODEL_B`, `YOUR_MODEL_ID` and `path/to/task` are placeholders. This scene reports no measured model results. Author and review a task with `grudges build` before replaying your own capture.

## Text transcript

```console
$ grudges save --session demo --note "Keep the amount editable until blur."
saved grudge DEMO_ID · exact starting state · demo-repo
episode starts at: 'Format the amount on blur.'

$ grudges run --pack starter -a nop -k 1
nop: fixed 0/8 · attempts 0/8 · no errors

$ grudges run --pack starter -a oracle -k 1
oracle: fixed 8/8 · attempts 8/8 · no errors

$ grudges run path/to/task -a codex -m MODEL_A -m MODEL_B -k 3
$ grudges run path/to/task -a codex -m YOUR_MODEL_ID --rules ./AGENTS.md -k 3
```

## Render

The sanitized inputs are in [demo-data.json](assets/demo-data.json); the renderer is [scripts/render_demo.py](../scripts/render_demo.py). Use Python with Pillow and the DejaVu Sans font family installed:

```bash
python scripts/render_demo.py
```

This regenerates `docs/assets/demo.gif` and `demo.png`. Rendering does not run Grudges, Docker or any model. To validate the underlying control results yourself, run the nop/oracle commands above and inspect the receipts.
