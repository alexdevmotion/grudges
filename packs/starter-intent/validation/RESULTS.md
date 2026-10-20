# Intent pack validation

Fresh Harbor nop/oracle validation, 15 October 2026. Each individual `result.json` and its SHA-256 was re-read; all 73 trials have the expected reward and `exception_info=null`. Process exit codes were recorded but were not used as proof. No models, simulated users or other authoring/review agents ran.

| Kept task | Nop fails | Oracle passes | Near miss rejected |
|---|---:|---:|---:|
| blur-formatting | 5/5 | 5/5 | 1/1 |
| cancel-notice | 5/5 | 5/5 | 1/1 |
| dispatch-delay | 5/5 | 5/5 | 1/1 |
| estimate-prefill | 5/5 | 5/5 | 1/1 |
| native-language-menu | 5/5 | 5/5 | 1/1 |
| saved-amount | 5/5 | 5/5 | 1/1 |

Excluded diagnostics accept both behaviors after arbitrary checks are removed:

| Excluded task | Original implementation accepted (nop) | Corrected implementation accepted (oracle) |
|---|---:|---:|
| extension-calendar | 1/1 | 1/1 |
| refund-visibility | 1/1 | 1/1 |

The actual excluded task verifier entry points are disabled and produce no reward. The diagnostic copies deliberately use the normal test runner against the surviving checks; they are not scored benchmark tasks.

Three additional oracle acceptance controls pass: saved-amount permits extra form fields; native-language-menu permits active-locale metadata and code suffixes; blur-formatting permits unformatted initial/untouched fields and commitments, formatted refocus, and four-digit Polish grouping. This checks that removed preferences really are ungraded.

Near misses use handwritten re-authored code only. Cancellation retains colliding child identities with working acknowledgement memory; saved-amount fixes only estimate entry; dispatch-delay retains newest-only selection; estimate-prefill removes alert text without applying conflicting values; blur-formatting leaves display raw; native-language-menu leaves current-locale translations. The last four are feature/bug surrogates, not proven original failed agent fixes.

Receipt files:
- [intent-nop JSON receipt](intent-nop-receipt.json), [job result](jobs/intent-nop/result.json).
- [intent-oracle JSON receipt](intent-oracle-receipt.json), [job result](jobs/intent-oracle/result.json).
- [intent-near-misses JSON receipt](intent-near-misses-receipt.json), [job result](jobs/intent-near-misses/result.json).
- [excluded-original JSON receipt](excluded-original-receipt.json), [job result](jobs/excluded-original/result.json).
- [excluded-corrected JSON receipt](excluded-corrected-receipt.json), [job result](jobs/excluded-corrected/result.json).
- [fairness-acceptance-controls JSON receipt](fairness-acceptance-controls-receipt.json), [job result](jobs/fairness-acceptance-controls/result.json).

Source custody and syntax/document checks: [final-checks.json](final-checks.json). Original starter hashes: [source-checksums.json](source-checksums.json). Final task/document hashes: [pack-checksums.json](pack-checksums.json). The copied environment and solution trees match starter byte-for-byte; starter itself is unchanged. Only the new pack directory was created; no commit was made.

Gitleaks is run over the whole new pack, including validation copies and raw job logs, using the supplied local binary. See [gitleaks.json](gitleaks.json). No privacy claim beyond the recorded scan and source review is implied.

Reproduction: `run_validation.py` runs the six-task nop/oracle checks and excluded diagnostics; `fairness_controls.py` runs acceptance controls. Both refuse to overwrite an existing job/variant directory. Their outputs are local evidence and must not be supplied to a future model as instructions. The scripts set the required DOCKER_CONFIG and use no authentication injection.
