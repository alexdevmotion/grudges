# README demo

The 18-second animation is an edited walkthrough, not a real-time recording. A [static alternative](assets/demo.png) is available.

- Capture uses the existing synthetic amount-formatting fixture. Its output is real, with the saved ID replaced by `DEMO_ID`; no private project or session appears.
- Replay shows a real native `starter/blur-formatting` run using Codex `gpt-6.1-sol`, low effort, one attempt. Baseline and reference checks passed, then the agent solved the task. Subscription allowance was consumed. Waiting time is condensed and summary text shortened.
- Compare shows example commands, not measured evidence that rules improve results. `path/to/task` is a placeholder.

Sanitized inputs: [demo-data.json](assets/demo-data.json). Rebuild with Python, Pillow and DejaVu Sans fonts:

```bash
python3 scripts/render_demo.py
```

Rendering itself does not call a model. To replay the measured example:

```bash
grudges run -m gpt-6.1-sol --effort low
```

This is a workflow smoke test, not a model benchmark or speed claim.
