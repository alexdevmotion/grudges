# Local release validation — 0.2.0a1

21 October 2026. Linux; GitHub prerelease preparation.

- Python 3.11 and 3.13: 78 tests passed, one optional external-receipt test skipped.
- All 14 bundled tasks passed local baseline/reference controls (28 offline Docker verifier runs): broken inputs fail and reference solutions pass through the actual local-runner mounts and UID.
- Live subscription replay passed for Codex CLI 0.163.0 (`gpt-6.1-sol`) and Claude Code (`sonnet`). Each completed a one-attempt, two-setup comparison on `starter/blur-formatting`.
- Both rules canaries were absent from baseline candidates and present only in the rules candidates; all four final task attempts solved. This verifies rule delivery and replay mechanics, not rule effectiveness or model quality.
- Restricted Claude did not automatically load root `CLAUDE.md` in direct canary tests. The runner now explicitly includes it in the prompt; unit and live tests cover that behavior.
- Review fixes include reward-file grading despite nonzero verifier exit, writable disposable verification copies, host UID permissions, paired setup ordering, subscription receipts, timing, interruption and conservative error handling.
- Desktop (1280px) and mobile (390px) cards checked in a browser; no page overflow at 390px. Subscription cost and trusted-host limitations remain visible.
- Release packaging and fresh installed-wheel checks cover both packs and CLI entry points. Source secret scan passed. Raw model transcripts and credentials are excluded from the release.

Subscription tests consumed plan allowance. Local runners use different tool profiles and do not isolate the agent from the host; they are not equivalent to isolated Harbor evaluations. API replay remains available. Local subscription mode supports Linux and the documented source-task layout only.

---

# Local release validation — 0.1.0a1

20 October 2026. Linux only. Pre-publication validation record. See the GitHub release for publication status.

- Python 3.11 and 3.13: 59 unit tests passed, one optional external-receipt test skipped. The installed wheel also passed the suite outside the checkout.
- Wheel and source distribution checked for both complete packs, license notices and absence of capture/cache artifacts.
- Installed-wheel capture, install and uninstall smoke checks passed in temporary directories without modifying user agent settings.
- Harbor 0.24.0 / Docker 29.1.3: all 28 individual nop/oracle receipts checked, each with null exception information. Starter: nop 0/8 solved, oracle 8/8. Intent: nop 0/6, oracle 6/6. Includes refund fixture 1.0.2.
- Report browser checks: six setups fit the desktop card at 1200×630; 360px mobile view has no page overflow; eight setups expand without cropping. Errors, missing attempts and unavailable/zero costs remain visible.
- Gitleaks 8.30.1 source and existing-history scans found no secrets. An explicit test-placeholder suppression is scoped to one line.
- Independent review found a prebuilt-image rules bypass and unmanaged-skill ownership bug. Both have regression coverage and are fixed.

No paid model calls occurred during this validation. No live native-harness rules comparison was rerun. The private historical rules experiment has unresolved input fairness issues and is excluded from release claims. Example-task controls establish verifier mechanics, not model quality or customer demand. macOS and Windows remain unvalidated. CI configuration is prepared but has not run on GitHub.

The source ZIP is a clean snapshot for a future initial public import. It excludes Git history, the preexisting local lockfile and all private experiment artifacts. The original working repository and its history remain intact; do not push that history as the public release. See RELEASING.md for the owner approval and publication steps.
