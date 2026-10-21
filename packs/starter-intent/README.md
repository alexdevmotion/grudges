# Starter intent track

This track measures **doing what the user meant on the first try, from the request they actually gave**. It uses re-authored original requests and grades only behavior that was stated or reasonably inferable from the request and repository. It never grades a later arbitrary preference.

Read [FAIRNESS.md](FAIRNESS.md) before any model run. Six variants are kept; `extension-calendar` and `refund-visibility` are excluded because their distinguishing expectations are later preferences. Four kept tasks are ordinary bug/feature seeds without a proven source-agent correction; `saved-amount` has a material scope-inference caveat. Only `cancel-notice` is a clear own-work-correction analogue. Differences on this small selected pack are not evidence of general model superiority.

Each task is an offline Python CLI. Environments and reference solutions are unchanged from `../starter`; instructions and fairness-gated tests differ. Corrected starter titles are retained only for result cards, not agent instructions. Source material stays private. The copied code/license notices are in [LICENSE](LICENSE); the method and verifier skeleton derive from the MIT-licensed evals-from-sessions project, pinned in the original starter README.

Initial mechanical validation used Harbor `nop` and `oracle`, with five attempts each per kept task and one hand-authored near miss per task. Fresh rewards and exception checks are recorded in [validation/RESULTS.md](validation/RESULTS.md). Later calibration prompted the task-specific corrections recorded in FAIRNESS.md; the validation summary describes the initial mechanical checks. No credentials or subscription sessions are mounted into the containers.

Run locally with your signed-in Codex or Claude CLI:

```sh
grudges run --pack starter-intent
```

The two excluded tasks (extension-calendar, refund-visibility) are not shipped: once their only distinguishing checks were classified as arbitrary later preferences, they could no longer separate the original mistake from the corrected behaviour. FAIRNESS.md documents why. `validation/RESULTS.md` summarizes the nop, oracle and near-miss receipts.

## Native replay update (0.3.0a1)

Task patch versions were incremented for portable workspace paths and explicit `[local]` commands. All six current baselines fail and reference solutions pass through native verification. Earlier Harbor receipt tables and hashes describe their original task versions, not this revised tree. Requirements and expected outputs are unchanged.
