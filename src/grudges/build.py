"""Turn a saved grudge into a Harbor task with the evals-from-sessions skill.

grudges supplies what that skill otherwise has to reconstruct: the selected
episode, the exact base tree at the start of the failing request, and the
failed attempt (a ready-made negative control). Authoring, validation and the
human checkpoints follow the upstream skill (MIT, pinned below).
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

from . import save, snapshot, store

UPSTREAM = "https://github.com/ibragim-bad/evals-from-sessions"
PINNED = "4e85a197f0b0f822461457af3056a63fb39aad93"


def vendor_skill():
    path = store.subdir("vendor") / "evals-from-sessions"
    if not path.exists():
        subprocess.run(["git", "clone", "-q", UPSTREAM, str(path)], check=True)
    if snapshot.git(path, "rev-parse", "HEAD") != PINNED:
        subprocess.run(["git", "-c", "advice.detachedHead=false", "checkout", "-q", PINNED], cwd=path, check=True)
    return path / "skills" / "evals-from-sessions" / "SKILL.md"


def prepare(grudge_id, shareable=False):
    gdir = save.grudge_dir(grudge_id)
    g = json.loads((gdir / "grudge.json").read_text())
    root = Path(g["repo"]["root"])
    work = gdir / "build"
    for name, commit in (("base", g["base"]["commit"]), ("after", g["after"]["commit"])):
        if commit and not (work / name).exists():
            snapshot.export(root, commit, work / name)
    skill = vendor_skill()
    brief = BRIEF.format(
        id=grudge_id, note=g["note"], skill=skill, gdir=gdir, work=work,
        transcript=gdir / "transcript.jsonl" if g["transcript"]["copy"] else "(not captured)",
        offset=g["request"]["transcript_offset"] or 0,
        prompt_head=g["request"]["prompt_head"] or "(unknown)",
        base_line=(f"`{work / 'base'}` is the exact tree at the start of the failing request, uncommitted "
                   "changes and submodules included. Use it as the task repository instead of `git archive` "
                   "of a parent commit. It contains no git history, so no future history can leak."
                   if g["base"]["exact"] else
                   f"The exact base was NOT captured (the hook had not run). HEAD at capture time was "
                   f"`{g['base']['head']}` in `{root}`; reconstruct the base from the transcript, as the "
                   "skill describes, and record that it is reconstructed."),
        mode="shareable" if shareable else "private",
        task_dir=gdir / "task",
    )
    (work / "BRIEF.md").write_text(brief)
    return work, brief


def launch(agent, brief, cwd):
    binary = shutil.which(agent)
    if not binary:
        raise SystemExit(f"grudges: `{agent}` not found on PATH")
    os.chdir(cwd)
    os.execv(binary, [binary, brief])


BRIEF = """Turn grudge {id} into a verified Harbor task.

Follow the evals-from-sessions skill at {skill} in **{mode}** mode, with these
differences, because grudges already captured the episode at the moment it failed:

- **Skip steps 0 and 1.** The user selected this episode by typing /grudge. Do not
  re-inventory the session. Still run gitleaks on the transcript copy before reading it.
- **Episode:** the transcript copy is {transcript}. The failing request starts at byte
  offset {offset} (it begins: "{prompt_head}"). Earlier content is context only.
- **The user's note on what should have happened:** "{note}". It is the primary
  requirement. Quote it in provenance.md.
- **Base state:** {base_line}
- **Failed attempt:** `{work}/after` is the working tree when the user typed /grudge.
  It is a mandatory near-miss: the verifier must fail it. Record its diff from base in
  provenance.md as the observed failure mode.
- **Reference solution:** if the session later reached an outcome the user accepted, use
  that change. Otherwise, write a reference that satisfies the note and label it
  "authored reference" in provenance.md.
- **Output:** write the task to {task_dir}. Network: never `no-network` (agents must
  install themselves). Use an allowlist: `[agent]` only the model endpoint (api.openai.com
  for Codex); `[environment]` adds install hosts (deb.debian.org, raw.githubusercontent.com,
  github.com, objects.githubusercontent.com, nodejs.org, registry.npmjs.org). Never inject
  subscription logins into containers.
- **Difficulty honesty:** never state a must-be-discovered item in the instruction (e.g.
  naming the faulty file or function). If you narrow the repository to a few files,
  that removes the search, so label the task `routine`.
- Keep both human checkpoints. Stop and ask the user in this chat.
- When validation passes, tell the user to replay it with:
  `grudges run {task_dir} -m <model> -m <model>`
"""
