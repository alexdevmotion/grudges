import argparse
import json
import os
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from . import build, card, hook, install, local, run, save, snapshot, store


def _default_claude_dirs():
    dirs = [Path.home() / ".claude"]
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        dirs.append(Path(os.environ["CLAUDE_CONFIG_DIR"]).expanduser())
    return dirs


def cmd_save(a):
    g = save.save(cwd=Path.cwd(), note=a.note, session=a.session, back=a.back)
    exact = "exact starting state" if g["base"]["exact"] else "starting state NOT exact (hook had no checkpoint; HEAD used)"
    print(f"saved grudge {g['id']} · {exact} · {Path(g['repo']['root']).name}")
    if g["request"]["prompt_head"]:
        print(f"episode starts at: {g['request']['prompt_head']!r}")


def cmd_requests(a):
    root = snapshot.repo_root(Path.cwd())
    session = a.session or os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not (session and save.requests(session, root)):
        session = save._latest_session_for(root)
    reqs = save.requests(session, root) if session else []
    if not reqs:
        print("no recorded requests for this repo (is the hook installed? run: grudges install)")
        return
    for back, e in enumerate(reversed(reqs[-a.limit:]), start=1):
        print(f"--back {back}: {e['prompt_head']}")


def cmd_list(a):
    rows = []
    for gdir in sorted(store.subdir("grudges").iterdir()):
        f = gdir / "grudge.json"
        if f.exists():
            g = json.loads(f.read_text())
            status = "built" if (gdir / "task" / "task.toml").exists() else g["status"]
            rows.append(f"{g['id']}  {status:<9} {'exact' if g['base']['exact'] else 'approx'}  "
                        f"{Path(g['repo']['root']).name:<18} {g['note'][:70]}")
    print("\n".join(rows) if rows else "no grudges yet; type /grudge in your agent when it gets something wrong")


def cmd_show(a):
    print((save.grudge_dir(a.id) / "grudge.json").read_text())


def cmd_run(a):
    if a.runner == "harbor" and not a.model and a.agent not in ("nop", "oracle"):
        raise SystemExit("grudges: pass at least one -m MODEL")
    rules = a.rules.read_text() if a.rules else None
    tasks = list(a.tasks)
    if a.pack:
        tasks.append(pack_path(a.pack))
    if not tasks:
        raise SystemExit("grudges: provide task directories or --pack starter / starter-intent")
    if a.runner == "harbor":
        run_dir, result = run.replay(tasks, a.agent, a.model, attempts=a.attempts, effort=a.effort,
                                     concurrency=a.concurrency or 4, rules=rules)
    else:
        if a.concurrency not in (None, 1):
            raise ValueError("subscription runners are sequential; use --concurrency 1")
        if a.agent != "codex":
            raise ValueError("--agent selects Harbor agents; choose --runner local-codex or local-claude")
        run_dir, result = local.replay(tasks, a.runner, a.model, attempts=a.attempts, effort=a.effort,
                                      rules=rules, trust_local=a.trust_local)
    for label, s in result["summary"].items():
        errs = ", ".join(f"{n} {k}" for k, n in s["errors"].items()) or "no errors"
        print(f"{label}: fixed {s['fixed']}/{s['n_tasks']} · attempts {s['attempts_solved']}/{s['attempts_scored']} · {errs}")
    print(f"results: {run_dir / 'results.json'}")
    print(f"card: {card.write(run_dir)}")
    return 2 if (result.get("harbor_exit_code", 0) or result.get("interrupted")
                 or not result.get("complete", True) or not result["records"] or
                 any(s["errors"] for s in result["summary"].values())) else 0


def pack_path(name):
    """Installed wheels carry the same packs as the source checkout."""
    bundled = Path(__file__).parent / "packs" / name
    source = Path(__file__).resolve().parents[2] / "packs" / name
    for path in (bundled, source):
        if path.is_dir():
            return path
    raise ValueError(f"bundled pack unavailable: {name}; reinstall from the release wheel")


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def cmd_build(a):
    work, brief = build.prepare(a.id, shareable=a.shareable)
    if a.print:
        print(brief)
        return
    print(f"starting {a.agent} in {work} (brief: {work / 'BRIEF.md'})")
    build.launch(a.agent, brief, work)


def cmd_card(a):
    runs = [p for p in store.subdir("runs").iterdir() if (p / "results.json").is_file()]
    if not a.run and not runs:
        raise ValueError("no completed run found; run a task or pass a run directory")
    run_dir = a.run or max(runs, key=lambda p: p.name)
    titles = json.loads(Path(a.titles).read_text()) if a.titles else None
    print(card.write(run_dir, titles))


def cmd_install(a):
    binary = shutil.which("grudges") or sys.argv[0]
    claude_dirs = a.claude_dir or _default_claude_dirs()
    codex = None if a.no_codex else Path.home() / ".codex"
    lines = (install.uninstall(claude_dirs, codex) if a.uninstall else install.install(binary, claude_dirs, codex))
    print("\n".join(lines))
    if not a.uninstall and codex:
        print("codex: approve the new hook when Codex asks you to review hooks.json")


def main(argv=None):
    p = argparse.ArgumentParser(prog="grudges", description="Save the tasks your coding agent failed. Re-run them on every new model.")
    try:
        installed_version = version("grudges")
    except PackageNotFoundError:
        installed_version = "development (not installed)"
    p.add_argument("--version", action="version", version=f"grudges {installed_version}")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("hook", help="UserPromptSubmit hook entry point (reads JSON on stdin)")

    s = sub.add_parser("save", help="save the current failure")
    s.add_argument("--note", required=True, help="what the correct outcome should have been")
    s.add_argument("--back", type=positive, default=1, help="episode starts N requests back (default 1)")
    s.add_argument("--session", help="session id (default: inferred)")

    r = sub.add_parser("requests", help="recent requests in this repo, for choosing --back")
    r.add_argument("--session")
    r.add_argument("--limit", type=positive, default=8)

    sub.add_parser("list", help="list saved grudges")
    sh = sub.add_parser("show", help="print a grudge's metadata")
    sh.add_argument("id")

    rn = sub.add_parser("run", help="replay tasks with Harbor or a local subscription CLI")
    rn.add_argument("tasks", nargs="*", type=Path, help="task directories or pack directories")
    rn.add_argument("--pack", choices=["starter", "starter-intent"], help="run a bundled example pack")
    rn.add_argument("-a", "--agent", default="codex")
    rn.add_argument("-m", "--model", action="append", default=[], help="repeatable; local runners default to their CLI model")
    rn.add_argument("-k", "--attempts", type=positive, default=3)
    rn.add_argument("--effort")
    rn.add_argument("-n", "--concurrency", type=positive, default=None, help="parallel Harbor trials (default 4); local runners use 1")
    rn.add_argument("--runner", choices=["harbor", "local-codex", "local-claude"], default="harbor", help="Harbor API replay or installed subscription CLI")
    rn.add_argument("--trust-local", action="store_true", help="acknowledge local tasks run on your host; use reviewed tasks only")
    rn.add_argument("--rules", type=Path, help="compare tasks as captured against a copy with your project rules")

    b = sub.add_parser("build", help="turn a grudge into a Harbor task with your agent")
    b.add_argument("id")
    b.add_argument("--agent", default="claude", choices=["claude", "codex"])
    b.add_argument("--shareable", action="store_true", help="re-author with new code and names so it can be published")
    b.add_argument("--print", action="store_true", help="print the brief instead of starting the agent")

    c = sub.add_parser("card", help="render a shareable HTML card for a run (default: latest)")
    c.add_argument("run", nargs="?", type=Path)
    c.add_argument("--titles", help="JSON file mapping task name to a public title")

    i = sub.add_parser("install", help="register the hook and /grudge skill for Claude Code and Codex")
    i.add_argument("--claude-dir", action="append", type=Path, help="Claude config dir (repeatable; default ~/.claude)")
    i.add_argument("--no-codex", action="store_true")
    i.add_argument("--uninstall", action="store_true")

    a = p.parse_args(argv)
    if a.cmd == "hook":
        return hook.main()
    try:
        return {"save": cmd_save, "requests": cmd_requests, "list": cmd_list, "show": cmd_show, "build": cmd_build, "run": cmd_run, "card": cmd_card, "install": cmd_install}[a.cmd](a) or 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"grudges: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
