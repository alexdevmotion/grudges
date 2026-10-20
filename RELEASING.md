# Release checklist

Target: `alexdevmotion/grudges`, version `0.1.0a1`. The owner authorized the initial GitHub release. Future releases require owner approval. GitHub publication does not authorize uploading to PyPI or sending launch messages.

1. Run unit tests, build wheel and sdist, and run `scripts/check_dist.py`. Install the wheel in a fresh environment outside the checkout; verify `--version`, capture and both bundled packs.
2. Run nop/oracle controls and inspect individual receipts. Check desktop and narrow-screen cards, including errors, missing attempts and more than six configurations.
3. Scan candidate files and the intended public Git history for secrets. The prepared source ZIP excludes Git history. Use it for a fresh public initial import after approval, preserving the original development repository privately. Do not push the old development history: it contains attribution trailers prohibited by the repository policy. Do not publish private research, sessions, receipts or the historical rules-trial card.
4. Review NOTICE, task fairness notes, README commands and platform limitations. Configure a private vulnerability-reporting channel and repository rules under the owner's account.
5. After approval, create/push the reviewed public history, tag the exact release commit, and attach the checked wheel/sdist with SHA-256 checksums to the release. PyPI publication requires separate account/name verification and authorization; no automatic publishing workflow is configured.
6. Test installation from the actual published artifact before announcing it. Record the public commit, artifact hashes and smoke-test results.

Do not claim general model rankings from the example pack or repaired-input results from historical rescoring. External alpha usage and repaired rules-trial calibration remain separate validation steps.
