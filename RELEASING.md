# Release checklist

GitHub releases require owner authorization. PyPI publication and launch messages require separate authorization.

1. Run tests on Python 3.11 and 3.13. Build wheel and sdist; run `scripts/check_dist.py`. Install the wheel outside the checkout and verify the CLI and both bundled packs.
2. Check baseline/reference controls and individual rewards. For runner changes, test the affected live CLI, including a rules canary. Do not infer model quality from these smoke tests.
3. Check cards at desktop and mobile widths. Keep errors, missing attempts and unavailable costs visible.
4. Scan release files and the intended public Git history for secrets. Never include captures, raw sessions, credentials or private research. Preserve the original development checkout and its history.
5. Update the version, changelog, README install URL and `RELEASE-CHECKS.md`. Open a focused PR; require passing CI before merge.
6. Tag the exact merged commit. Build artifacts from that commit, attach wheel/sdist and SHA-256 checksums to a GitHub prerelease, then download and verify them in a fresh environment.

The public repository is `alexdevmotion/grudges`. The alpha is distributed through GitHub, not PyPI. Keep claims limited to the documented platforms, task layouts and evidence.
