# Starter pack

Eight small, re-authored, headless Python 3.13 tasks. Each is a fresh behavioral analogue of an authorized private session; no original repository code, transcript, customer data or provenance is included. All tasks are labelled **routine**: requirements are explicit; the work is finding and repairing the relevant implementation across a few modules. Human completion times and current-model difficulty are unmeasured. Some seeds are historical bug repairs or user-requested improvements rather than a proven correction of the source agent's own work.

From the repository root, with Docker, Harbor and your own supported API credentials configured:

```sh
grudges run packs/starter -m A -m B -k 3
```

Replace A/B with supported model ids. The run writes a results card with these public titles. The pack is a functional example, not a model ranking benchmark; do not promise a particular time to complete it.

Each task uses a digest-pinned Python slim image and the standard library. Verifiers use only local files and subprocesses and download nothing. The setup allowlist permits agent installation; the agent-phase allowlist is limited to `api.openai.com`. Source repositories, accounts, browsers and live services are unnecessary. Tests and reference solutions are outside the image build context's copied repository and are supplied only in their Harbor phases.

| Directory | Your grudge | Language | Mistake captured |
|---|---|---|---|
| `dispatch-delay` | Keep the older delay visible when a newer dispatch appears | Python | Newest-row selection hides an actionable older delay; date meanings must survive projection. |
| `extension-calendar` | Cancel the old expiry charge without losing accrued interest | Python | Keeping an off-calendar charge, fixing just one schedule consumer, or dropping straddling-period interest. |
| `refund-visibility` | Hide screening from customers while keeping the refund blocked | Python | Fixing one public label while API, legacy view, email still exposes internal review. |
| `cancel-notice` | Show one cancellation notice and leave it dismissed | Python | Acknowledgement alone misses colliding sibling identities and repeated cancellation notices. |
| `saved-amount` | Skip the amount prompt from the hero too | Python | Fixing only the estimate entry point, or manufacturing a new estimate that bypasses submitted-request protection. |
| `estimate-prefill` | Use the estimate immediately and keep the stale-save warning | Python | Removing alert text without merging values, or removing unrelated stale-save protection. |
| `blur-formatting` | Format amounts on blur without submitting the separators | Python | Formatting canonical state or focused input instead of the blurred display. |
| `native-language-menu` | Let visitors recognize their language in both menus | Python | Translating option names into the current UI locale, or fixing visible text without pronunciation/accessibility. |

## Validation receipts

Initial mechanical validation completed with **113 final-version trials and zero infrastructure exceptions**. Those checks used nop and oracle agents. A separately written alternative passes for every task; no independent reviewer/model authored those alternatives.

| Task | Version | Nop fails | Oracle passes | Near-misses rejected | Alternative | Image leak probe |
|---|---|---|---|---|---|---|
| `dispatch-delay` | 1.0.0 | 5/5 | 5/5 | 3/3 | 1/1 | clean |
| `extension-calendar` | 1.0.0 | 5/5 | 5/5 | 4/4 | 1/1 | clean |
| `refund-visibility` | 1.0.1 | 5/5 | 5/5 | 3/3 | 1/1 | clean |
| `cancel-notice` | 1.0.0 | 5/5 | 5/5 | 3/3 | 1/1 | clean |
| `saved-amount` | 1.0.0 | 5/5 | 5/5 | 3/3 | 1/1 | clean |
| `estimate-prefill` | 1.0.0 | 5/5 | 5/5 | 3/3 | 1/1 | clean |
| `blur-formatting` | 1.0.0 | 5/5 | 5/5 | 3/3 | 1/1 | clean |
| `native-language-menu` | 1.0.0 | 5/5 | 5/5 | 3/3 | 1/1 | clean |

Each trial receipt was checked for its reward and `exception_info=null`. Whole-pack gitleaks 8.30.1 and forbidden-source-string scans are clean. All eight built images have one fresh initial commit, no remotes/tags/stashes/hooks or future history, and no hidden evaluator/reference directories. Python/shell syntax and document checks pass. Card-title aliases were checked through the existing renderer using actual Harbor task names.

Task-tree SHA-256 receipt (sorted relative-file SHA-256 map, compact JSON with default separators): `27f404d7683e2554e0bc3a6278ba596e038f0eea5c0b03057bab9c527bdd89ae`. Private job receipts and provenance are intentionally excluded from this pack.

Subsequent local model calibration does not establish representative model quality. These tasks remain subject to human review; the language-menu task is especially simple. The cancellation task uses an explicitly synthetic keyed-child reconciler, not browser or framework conformance testing. The refund task is 1.0.1 because a source-agent-chosen template-preparation change was removed from its requirements and grading after the final baseline audit.

## License and credit

These tasks are Copyright 2026 Alex Constantin, licensed under [Apache-2.0](LICENSE).

The authoring method and verifier skeleton were adapted from [evals-from-sessions](https://github.com/ibragim-bad/evals-from-sessions/tree/4e85a197f0b0f822461457af3056a63fb39aad93), pinned at `4e85a197f0b0f822461457af3056a63fb39aad93`, MIT. Its notice follows; it applies to those adapted portions, not a relicensing of the newly authored tasks.

```text
MIT License

Copyright (c) 2026 Ibragim Badertdinov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Release fixture correction

`refund-visibility` 1.0.2 aligns the ordinary customer template catalog with the identifier already required by the instruction and emitted by mail. The table and task-tree hash above describe the historical 1.0.1 inputs; they do not attest to this revised tree. The exact public output contract and verifier are unchanged.
