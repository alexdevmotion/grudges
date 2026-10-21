"""Render run results as a shareable, self-contained HTML card.

Only selected labels, supplied titles and aggregate outcomes are exported.
Review titles and labels before sharing; they may contain private information.
Up to six setups use a 1200x630 social block; larger reports expand.
"""

import html
import json
import re
from pathlib import Path

MARK = {"solved": "●", "failed": "○", "timeout": "◷"}
ERROR_MARK = "×"


def _tally(n_tasks, fixed, width=560, height=64):
    """Pencil tally: one stroke per task, a red strike through each settled one."""
    gap = min(28, (width - 40) / max(n_tasks + n_tasks // 5, 1))
    parts = []
    for i in range(n_tasks):
        x = 20 + i * gap + (i // 5) * gap  # small gap after every five, like a hand tally
        tilt = (i * 7 % 5) - 2
        parts.append(f'<line x1="{x}" y1="10" x2="{x + tilt}" y2="{height - 8}" class="stroke"/>')
        if i < fixed:
            parts.append(f'<line x1="{x - 9}" y1="{height - 18}" x2="{x + 10}" y2="16" class="strike"/>')
    return f'<svg viewBox="0 0 {width} {height}" class="tally" aria-hidden="true">{"".join(parts)}</svg>'


HARNESS_NAMES = {"local-codex": "local Codex", "local-claude": "local Claude Code", "codex": "Codex", "claude-code": "Claude Code", "opencode": "OpenCode", "terminus-2": "Terminus"}


def _who(label):
    """'codex · gpt-6-luna[ · with rules]' -> model as the name, harness (and setup) as the qualifier."""
    agent, _, rest = label.partition(" · ")
    if not rest:
        return html.escape(agent)
    model, _, setup = rest.partition(" · ")
    where = f"in {HARNESS_NAMES.get(agent, agent)}" + (f", {setup}" if setup else "")
    return f"{html.escape(model)}<small>{html.escape(where)}</small>"


def _spend(s):
    parts = []
    if s.get("billing") == "subscription":
        parts.append("subscription usage · USD cost unavailable")
    elif s.get("cost_usd") is not None:
        parts.append(f"${s['cost_usd']:.2f}" + (" known cost (partial)" if s.get("cost_complete") is False else ""))
    else:
        parts.append("cost unavailable")
    if s.get("median_seconds") is not None:
        parts.append(f"{max(1, round(s['median_seconds'] / 60))} min median")
    return ", ".join(parts)


def _n(count, noun):
    return f"{count} {noun}{'s' * (count != 1)}"


def _counts(attempts, expected, missing=None):
    solved = attempts.count("solved")
    scored = sum(a in MARK for a in attempts)
    errors = len(attempts) - scored - attempts.count("missing")
    if missing is None:
        missing = max(0, expected - len(attempts))
    missing += attempts.count("missing")
    note = f"{_n(errors, 'error')} · {missing} missing"
    if not scored:
        note += " · no scored attempts"
    return solved, scored, note


def render(result, titles=None):
    """Render aggregate evidence; supplied titles and configuration labels need review."""
    titles = {**result.get("titles", {}), **(titles or {})}
    summary = result["summary"]
    tasks = sorted({t for s in summary.values() for t in s.get("tasks", {})})
    n_tasks = max(len(tasks), len(result.get("tasks", [])),
                  max((s.get("n_tasks", 0) for s in summary.values()), default=0))
    expected = result.get("attempts", 0)
    e = html.escape

    def counts(label):
        attempts = [a for t in summary[label].get("tasks", {}).values() for a in t.get("attempts", [])]
        task_results = summary[label].get("tasks", {})
        missing = sum(max(0, expected - len(t.get("attempts", []))) for t in task_results.values())
        missing += expected * max(0, n_tasks - len(task_results))
        return _counts(attempts, expected * n_tasks, missing)

    def rank(label):
        solved, scored, _ = counts(label)
        cost = summary[label].get("cost_usd")
        return (-(solved / scored) if scored else float("inf"),
                cost if cost is not None else float("inf"), label)

    configs = sorted(summary, key=rank)
    if result.get("rules"):
        configs = sorted(summary, key=lambda k: (k.rsplit(" · ", 1)[0],
                         0 if k.rsplit(" · ", 1)[-1] in {"as captured", "without rules"} else 1, k))
    rows = []
    for label in configs:
        s = summary[label]
        solved, scored, note = counts(label)
        fixed = sum(1 for t in s.get("tasks", {}).values()
                    if (c := _counts(t.get("attempts", []), expected))[1] >= max(expected, 1)
                    and c[1] == len(t.get("attempts", [])) and c[0] * 2 > c[1])
        rows.append(
            f'<div class="row"><div class="who">{_who(label)}</div>'
            f'<div class="secondary">{_tally(n_tasks, fixed)}'
            f'<span>{fixed} of {n_tasks} majority-fixed tasks</span></div>'
            f'<div class="score"><b>{solved}/{scored}</b> solved/scored'
            f'<span>{e(note)}</span><span>{e(_spend(s))}</span></div></div>')

    source = result.get("source", "own")
    if source.startswith("pack:"):
        pack = source.split(":", 1)[1]
        pack_name = f"{pack} pack" if re.fullmatch(r"[\w-]+", pack) else "selected pack"
        subject = f"{_n(n_tasks, 'task')} from the {pack_name}"
    else:
        subject = f"{_n(n_tasks, 'task')} my coding agent failed"
    footer = (f"{expected} planned attempts per task/setup. Errors excluded from scored; missing = planned but unreported. "
              "Majority-fixed = all planned attempts scored and more than half solved.")
    if result.get("runner", "").startswith("local-"):
        footer += " Trusted local CLI run; host configuration may affect results. Not equivalent to isolated Harbor runs."
    body = []
    for i, t in enumerate(tasks + [None] * (n_tasks - len(tasks)), 1):
        cells = []
        for c in configs:
            attempts = summary[c].get("tasks", {}).get(t, {}).get("attempts", [])
            solved, scored, note = _counts(attempts, expected)
            marks = "".join(MARK.get(a, "–" if a == "missing" else ERROR_MARK) for a in attempts)
            cells.append(f'<td><strong>{solved}/{scored} solved/scored</strong>'
                         f'<small>{e(note)}</small><span class="marks">{marks}</span></td>')
        body.append(f'<tr><th scope="row">{e(titles.get(t) or f"Task {i}")}</th>{"".join(cells)}</tr>')
    return TEMPLATE.format(
        title=e(f"{_n(n_tasks, 'grudge')}, {_n(len(configs), 'setup')}"),
        headline=e(f"{subject}. Do my rules improve results?" if result.get("rules")
                   else f"{subject}. Here are the replay results."),
        rows="".join(rows) or '<p>No attempts reported. No scored results available.</p>', footer=e(footer),
        density=" compact" * (len(configs) > 3) + " dense" * (len(configs) > 4)
                + " expanded" * (len(configs) > 6),
        head="".join(f'<th scope="col">{_who(c)}</th>' for c in configs), body="".join(body),
        legend=e("● solved  ○ failed  ◷ timed out  × error  – missing (both excluded). Failed and timed-out attempts are scored."),
    )


def write(run_dir, titles=None):
    result = json.loads((Path(run_dir) / "results.json").read_text())
    out = Path(run_dir) / "card.html"
    out.write_text(render(result, titles))
    return out


TEMPLATE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
:root {{ --paper:#E6ECF1; --ink:#16243A; --graphite:#5E6B78; --grid:#C6D3DE; --pencil:#B3261E; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#F5F8FA; color:var(--ink); font:16px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; font-variant-numeric:tabular-nums; }}
.card {{ width:1200px; height:630px; padding:56px 64px 44px; background:var(--paper);
  display:flex; flex-direction:column; }}
.brand {{ font-weight:800; font-size:22px; letter-spacing:-.3px; color:var(--graphite); }}
h1 {{ font-size:46px; line-height:1.08; letter-spacing:-1.2px; margin:14px 0 34px; max-width:1000px; font-weight:800; }}
.tally {{ width:100%; max-width:560px; height:auto; display:block; }}
.compact {{ padding-top:44px; padding-bottom:36px; }}
.compact h1 {{ font-size:40px; margin-bottom:20px; }}
.compact .rows {{ gap:8px; }}
.compact .row + .row {{ padding-top:8px; }}
.compact .tally {{ max-width:470px; }}
.compact .score b {{ font-size:34px; }}
.dense {{ padding-top:28px; padding-bottom:24px; }}
.dense footer {{ font-size:14px; }}
.dense .score {{ line-height:1.2; }}
.dense h1 {{ font-size:34px; margin:10px 0 14px; }}
.dense .rows {{ gap:4px; }}
.dense .row + .row {{ padding-top:4px; }}
.dense .who {{ font-size:19px; }}
.dense .who small {{ font-size:13px; }}
.dense .tally {{ max-width:380px; }}
.dense .score {{ font-size:17px; }}
.dense .score b {{ font-size:26px; }}
.dense .score span {{ font-size:12px; }}
.rows {{ display:flex; flex-direction:column; gap:14px; flex:1; }}
.row {{ display:grid; grid-template-columns:240px minmax(0,1fr) 340px; align-items:center; gap:24px; }}
.who {{ overflow-wrap:anywhere; font-size:24px; font-weight:750; line-height:1.15; }}
.who small {{ display:block; font-size:16px; font-weight:400; color:var(--graphite); }}
.row + .row {{ border-top:1px solid var(--grid); padding-top:14px; }}
.score {{ font-size:22px; color:var(--graphite); text-align:right; }}
.score b {{ font-size:40px; color:var(--ink); font-weight:800; }}
.score span {{ display:block; font-size:16px; }}
.stroke {{ stroke:var(--ink); stroke-width:4; stroke-linecap:round; }}
.strike {{ stroke:var(--pencil); stroke-width:5; stroke-linecap:round; }}
footer {{ font-size:16px; color:var(--graphite); max-width:1000px; }}
.details {{ max-width:1200px; padding:32px 64px 64px; }}
table {{ border-collapse:collapse; width:100%; }}
th, td {{ text-align:left; padding:8px 12px; border-bottom:1px solid var(--grid); }}
td {{ font-size:16px; min-width:200px; }}
td small {{ display:block; color:var(--graphite); }}
.marks {{ font-size:20px; letter-spacing:4px; overflow-wrap:anywhere; }}
.secondary {{ color:var(--graphite); font-size:13px; }}
.secondary .tally {{ max-height:38px; }}
.expanded {{ height:auto; min-height:630px; }}
.expanded footer {{ margin-top:24px; }}
.table-scroll {{ overflow-x:auto; }}
thead th {{ font-weight:650; overflow-wrap:anywhere; }}
th small {{ display:block; font-weight:400; color:var(--graphite); }}
tbody th {{ font-weight:400; }}
.legend {{ color:var(--graphite); margin-top:12px; }}
@media (max-width:1199px) {{
  .card {{ width:100%; height:auto; min-height:630px; padding:32px 24px; }}
  .row {{ grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:12px; }}
  .secondary {{ grid-column:1; grid-row:2; }}
  .score {{ grid-column:2; grid-row:1 / 3; }}
  .details {{ padding:24px; }}
  h1 {{ font-size:34px; }}
  footer {{ margin-top:24px; }}
}}
@media (max-width:600px) {{
  .row {{ grid-template-columns:1fr; }}
  .score {{ text-align:left; grid-column:1; grid-row:2; }}
  .secondary {{ grid-row:3; }}
  .who {{ font-size:22px; }}
}}
</style>
<main>
<section class="card{density}" aria-label="Results card">
  <div class="brand">grudges</div>
  <h1>{headline}</h1>
  <div class="rows">{rows}</div>
  <footer>{footer}</footer>
</section>
<section class="details">
  <p>Whole-task rewards only: these results do not establish whether a specific failure, such as a customer-data leak, disappeared. Review titles and labels before sharing.</p>
  <div class="table-scroll"><table><thead><tr><th>Task</th>{head}</tr></thead><tbody>{body}</tbody></table></div>
  <p class="legend">{legend}</p>
</section>
</main>
</html>
"""
