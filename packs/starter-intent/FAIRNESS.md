# Intent-track fairness audit

This track asks whether an implementation does what the user meant on the first try, from the request they actually gave. It does **not** treat a later preference as a hidden requirement. The source wording is privately evidenced; instructions here are fresh domain analogues, not transcript excerpts. Read this before authorizing any model run.

**Decision: six kept, two excluded.** Only `cancel-notice` among the kept tasks has a clear correction of the source agent's own implementation. `saved-amount` is a scope extension/generalization with a source first-fix analogue. The other four kept tasks are bug/feature seeds without a proven own-work correction. They must not be advertised as six demonstrated judgment failures.

“Stated” means the re-authored original request states the behavior; interface-only checks are also marked stated, explicitly identified below. “Inferable” means the request plus the supplied repository supports it. “Arbitrary” means an equally reasonable implementation could choose otherwise; those checks are removed. The interface supplies serialization, types, units and arithmetic conventions without supplying the disputed product decision. Existing calendar/accrual conventions are disclosed because withholding arithmetic would manufacture failure.

Each table row counts **one logical check family**, not one fixture or scalar assertion. A row's fixture/path selector covers every corresponding assertion in `tests/cases.json` and `tests/verify.py`; “all” includes every locale, mode and repeated event. Where a fixture combines stated and inferable checks, the rows separate its paths. No behavior is justified solely by a later source result or by the oracle. Source citations below point only to existing private provenance files; those files contain the original session/line pointers. No source wording is included here.

| Task | Decision | Stated | Inferable | Arbitrary removed |
|---|---|---:|---:|---:|
| dispatch-delay | kept: bug seed | 2 | 5 | 0 |
| extension-calendar | excluded | 4 | 3 | 2 |
| refund-visibility | excluded | 3 | 3 | 4 |
| cancel-notice | kept: own-work correction analogue | 2 | 5 | 0 |
| saved-amount | kept: scope inference, not proven original omission | 2 | 6 | 1 |
| estimate-prefill | kept: feature seed | 3 | 5 | 0 |
| blur-formatting | kept: feature seed | 2 | 3 | 3 |
| native-language-menu | kept: feature seed | 2 | 3 | 2 |
| **Total (including excluded diagnostic families)** | | **20** | **33** | **12** |
| **Kept tasks only** | | **13** | **27** | **6** |

## dispatch-delay — kept

Original wording source: private provenance (kept by the maintainer, not published). This is the original bug report plus its fix authorization; there is no earlier agent mistake established. The near miss is the observed newest-row bug, not an attributed failed agent fix.

| Check family / fixture selector | Classification | Evidence or removal |
|---|---|---|
| `older revised entry survives`: selected delayed row | stated | Request: delayed dispatch warning is missing when another dispatch exists. |
| All: CLI, JSON types, summary keys and `arrival=planned` mapping | stated (Interface) | `instruction.md`, Interface. |
| `input order independent`; queued/moving/retry state cases: unresolved revised rows remain actionable | inferable | `environment/repo/domain.py:1` groups these states as UNPAID; request identifies a delay hidden by a newer row. |
| complete state case: old completed revision has no special priority | inferable | `domain.py:1-2` excludes complete from both actionable classes. |
| late/blocked state cases; `overdue precedence and sequence` | inferable | `selection.py:4-5` already puts OVERDUE ahead of ordinary rows; `domain.py:2` defines the class. |
| `id breaks sequence tie`; all within-class selection | inferable | `selection.py:5` already orders by sequence then id. |
| `groups and complete fallback`, `empty`; all date preservation | inferable | `service.py:5-8` groups and sorts; `projection.py:1-3` independently preserves the three date meanings. |

All original fixtures and grader checks retained. No invented original/corrected contrast.

**Reviewer fix after the first model run (2026-10-15):** every model failed this task 12/12. The cause was a vocabulary gap introduced by re-authoring, not intent. Nothing in the instruction or the repository said that a `revised` date means a delay, or that the warning is driven by the summary's `revised` field (in the source application the frontend made that link). The stronger models reasonably read "delayed" as `state: late`. The Interface now states that mapping. It is presentation vocabulary, not the fix: which row to select is still for the solver to find. After the rerun, all models still failed two checks the same way. On review:
- `state complete` (a completed dispatch loses delay priority) is **reclassified arbitrary and removed**. In the source, that status policy was the source agent's own choice, not the user's. The only repository hint, an unused `UNPAID` set in `domain.py`, was introduced by re-authoring, so it cannot justify inferability.
- `overdue precedence and sequence` is **kept**. The existing `selection.py` already ranks late/blocked rows first, and the user asked for no change to that. Breaking it is a regression, not a hidden preference. Every model broke it.

## extension-calendar — excluded

Original wording source: private provenance (kept by the maintainer, not published). Use the original extension feature request, not the later complaint about the old-expiry row. Its exact contractual maximum and rate are configurable inputs in the re-authored model; no original contractual constants are exposed.

| Check family / fixture selector | Classification | Evidence or removal |
|---|---|---|
| All: CLI, schema, dates, integer cents, next-date definition | stated (Interface) | `instruction.md`, Interface. |
| All: move principal to extended expiry; ordinary expiry when unextended | stated | Request: extension updates schedule and moves final principal. |
| All: base and extra interest for all elapsed days | stated | Request: update calculations for additional interest; numeric accrual convention disclosed in Interface. |
| `half up component rounding`, all period arithmetic | stated (Interface) | Explicit units, day basis, intervals and rounding; `accrual.py:4-11` is unchanged and already implements it. |
| All: retain normal billing boundaries and final expiry once | inferable | `calendar_rules.py:5-11` constructs exactly those dates. It does not decide whether consumers add a separate old-expiry cut. |
| All: ledger and preview agreement | inferable | `README.md:2-4` identifies two consumers of the same schedule. |
| All: next follows the actual returned schedule; no duplicate or unsorted dates | inferable | `service.py:4-5`; `calendar_rules.py:6-11` uses a sorted set. |
| Extended cases: prohibit an additional off-calendar original-expiry row, including `next skips old expiry` | arbitrary — removed | Original request moves principal, not necessarily already-earned interest. `ledger.py:7-8` and `preview.py:7-8` explicitly retain that interest boundary. |
| Extended cases: require the exact merged-period row amounts/array lengths in starter expectations | arbitrary — removed | These depend on prohibiting the extra boundary. Either calendar uses the same disclosed per-period arithmetic. |

`tests/verify.py` now checks only retained invariants against each actual returned interval. It accepts the ordinary calendar with or without an additional original-expiry cut, while checking full accrual and final principal. The unused exact expected arrays were removed from `cases.json`. The original mistake and the oracle both pass these diagnostics. Thus the intent distinction is lost; the task is excluded, not made difficult by an unstated calendar preference.

## refund-visibility — excluded

Original wording source: private provenance (kept by the maintainer, not published). Use the original suspicious-refund feature and staff-notification request, not the later instruction to preserve the customer label. The small repository supplies already-classified states; it cannot test the full source risk engine.

| Check family / fixture selector | Classification | Evidence or removal |
|---|---|---|
| All: CLI, snapshot/view schema, tokens, monetary units | stated (Interface) | `instruction.md`, Interface; output shape does not dictate screening visibility. |
| All snapshot `.internal`: stored state, screening hold, staff reason notification | stated | Request requires human review and clear staff notifications with reasons; `staff.py:1-2` is existing policy. |
| Receipt `.gross/.fee/.net`, identifiers and core field types | stated (Interface) | Explicit cents, subtraction and receipt field names; `mail.py:2-3`. |
| queued/sent/rejected/void: API and view behavior/labels | inferable | Existing `states.py:3-4`, `customer.py:1-7`; unrelated states need no change. |
| All receipt base fields and email null for other states | inferable | `mail.py:2-6` already provides these; no change to ordinary receipts is requested. |
| All unreviewed/terminal `.internal` behavior | inferable | Preserve existing execution policy in `staff.py:1-2`. |
| screened snapshots `.api.state=queued` | arbitrary — removed | Original feature permits exposing a review status. |
| screened snapshots `.view.state/.label=queued` | arbitrary — removed | No original request to hide the customer badge. |
| legacy view `.state/.label=queued` | arbitrary — removed | Customer normalization policy is likewise unspecified. Only the output object shape remains checked. |
| Receipt exact key sets, particularly forbidding screening/reason fields for screened refunds | arbitrary — removed | Neither harmless receipt additions nor whether customer confirmation mentions review is specified. Core receipt values remain checked. |

After removal, the exposed-review implementation and oracle both pass. Excluded because it no longer distinguishes the source mistake. `op=prepare` remains ungraded, as in starter; it was an implementation choice, not an original user requirement.

## cancel-notice — kept

Original wording source: private provenance (kept by the maintainer, not published). The instruction uses the initial stale-message report, without mentioning the later duplicate-message correction or key collisions.

| Check family / fixture selector | Classification | Evidence or removal |
|---|---|---|
| All action/close sequences: acknowledgement clears old notice and prevents resurrection | stated | Request: message goes away after the first action or closing the panel. |
| All: CLI, snapshots, child shape/order, closed empty children, form ids | stated (Interface) | `instruction.md`, Interface; current form identity comes from `panel.py:12-13`. |
| Dismiss sequences: dismissal is an acknowledgement | inferable | `panel.py:17-20` treats dismiss/action/close alike. |
| Sequences ending with two different cancels: only current notice and form survive | inferable | Dismissed messages must actually disappear. `panel.py:15-19` stores a single notice; `reconcile.py:4-9` explains retained ambiguous siblings. |
| Both modes obey the same behavior | inferable | `service.py:4-5` and `panel.py` share lifecycle code; `widgets.py:1-5` handles both. |
| Unavailable storage: acknowledgement survives within the same running panel | inferable | Request is unconditional about dismissal; `storage.py:3` already has instance memory. This is in-session behavior, not persistence across process/browser restarts. |
| First unacknowledged cancellation may show, new id may show, active/draft forms stay available | inferable | Existing `panel.py:11-16`, `widgets.py:1-5`. An always-hidden notice would remove existing functionality beyond the reported stale-message bug. |

All starter checks retained. Near miss: working acknowledgement memory with colliding sibling identities retained. It fails the original dismissal request, as well as repeated-cancel sequences. This is a synthetic keyed-child renderer, not a React/browser reproduction; the source's second fix itself lacked repeated-cancel automated/browser proof. The inference about in-session fallback is reasonable but stronger than the source agent's delivered fallback; review it explicitly.

## saved-amount — kept, with scope caveat

Original wording source: private provenance (kept by the maintainer, not published). Use the initial dashboard/known-amount request. Do not say that the user explicitly named both entry buttons before the first fix; they did not.

| Check family / fixture selector | Classification | Evidence or removal |
|---|---|---|
| Avoid the redundant amount dialog when applying with an already-known amount | stated | The request states this condition. Whether the hero should also find saved values is classified separately below. |
| All: CLI, route/field names, units, types | stated (Interface) | `instruction.md`, Interface. |
| Hero uses saved draft/submitted values; hero ignores unrelated estimate | inferable | `README.md:2-4` splits dashboard routing from application resumption; `repository.py:4-5` exposes saved sources; `dashboard.py:5-6` limits explicit estimates to estimate entry. |
| Saved draft before submitted; invalid draft falls through | inferable | `repository.py:1-5` and `application.py:6-9` already implement precedence/usable amount rules. |
| Positive submitted request resumes submitted id instead of becoming a blank form | inferable | `application.py:8-9` is the existing submitted guard. |
| Explicit estimate precedence and financial/contact values | inferable | `dashboard.py:5-6`; `application.py:4-5,12`. |
| Missing contacts do not block an already-known amount; profile values survive | inferable | Request's condition is the amount, not contact completeness; `application.py:12` carries contacts, including null. |
| Null/zero/negative unknown amounts still use dialog | inferable | `repository.py:1-2`; existing dialog shape in `dashboard.py:7`. |
| Form rejects every extra field via `$keys` | arbitrary — removed | No original prohibition on harmless additional fields; the interface lists required fields only. |

**Skeptical reading:** the original screenshot targeted one dashboard button; the later hero instruction could be a new scope request. Kept because the broad original wording plus an already-present saved-source resolver makes dashboard-wide application reasonable to infer. This is not proof that the original agent ignored an explicit hero requirement. A stricter interpretation should exclude this task, not rewrite the prompt to mention the hero. Near miss is the source first-fix analogue that changes only estimate entry; in this small fixture it equals the initial implementation.

## estimate-prefill — kept, feature seed

Original wording source: private provenance (kept by the maintainer, not published). The initial diagnostic question alone requests information, not a fix. The first actionable feature direction removes the choice panel and asks to prefill, rejecting an offered replacement notice. There is no proven own-work correction here.

| Check family / fixture selector | Classification | Evidence or removal |
|---|---|---|
| Estimate values apply immediately instead of a choice | stated | Request: remove the choice and prefill from estimate. |
| No estimate-choice or replacement informational alert | stated | Request: remove it completely; no alert needed. |
| All: CLI, supported fields, missing vs null, units, revisions/output types | stated (Interface) | `instruction.md`, Interface; `README.md:3` distinguishes missing/null. |
| Estimate overlays finance only; saved contact data remains | inferable | `schema.py:1-3`; `merge.py:4-8` already separates FINANCE from CONTACT. |
| Session overrides saved/estimate, including explicit null/zero | inferable | `merge.py:9` already overlays present session fields last without truthiness filtering. |
| Missing estimate fields preserve saved values; zero/null count as present | inferable | `README.md:3`; `merge.py:6,8` uses key presence and direct values. |
| Stale-save conflict and alert remain | inferable | The request names the estimate-choice panel; independent `revision.py:1-3` and `service.py:5-7` provide optimistic saving. |
| Saved-only, session-only, no-data and partial-estimate cases | inferable | Existing `merge.py:4-9` and schema initialize supported keys and support absent sources. |

All starter checks retained. Near miss removes alert text but leaves conflicting estimate values unapplied; this is a synthetic partial fix, not an attributed original failed delivery.

## blur-formatting — kept, feature seed

Original wording source: private provenance (kept by the maintainer, not published). Only the amount/income formatting item is re-authored; unrelated field-height and copy changes are outside this fixture. No own-work correction is proven.

| Check family / fixture selector | Classification | Evidence or removal |
|---|---|---|
| All explicit/implicit blurs of amount/income: grouped blurred display | stated | Request names requested amount and monthly income, formatted when focus is lost. |
| All: CLI, events, snapshot count, canonical string shape, separator convention | stated (Interface) | `instruction.md`, Interface; `formatting.py:1,3-8` supplies separators and three-digit grouping. |
| Submit preserves current canonical values and exact integer precision | inferable | `README.md:2-4`; `payload.py:1-2`; formatting display must not change submitted value. |
| Input, locale and focus events keep submission null except submit | inferable | Existing `service.py:7-9` and `editor.py:4-10`. |
| Repeated events, empty/zero and locale changes preserve values | inferable | `editor.py:6-10`, `formatting.py:4`, `payload.py:1-2`; only after-blur displays are checked. |
| Display formatting for commitments | arbitrary — removed | The request names only amount and monthly income. Canonical commitments submission is still preserved as existing behavior. |
| Initial formatting before any blur, formatting untouched fields, and exact plain-digit refocus display | arbitrary — removed | “On blur” does not specify initial/refocus presentation. `formatting.py` can format values but does not establish when to do so. Only relevant fields after a blur are checked. |
| Four-digit Polish values must remain ungrouped | arbitrary — removed | The starter oracle adds this threshold; existing `formatting.py:3-8` groups four digits. Neither the original request nor repository requires the special threshold. |

Expected `display` dictionaries now contain only graded fields at that event; the existing comparator ignores unmentioned fields. Submission values and snapshot lengths remain checked. Near miss leaves raw display everywhere; it is a synthetic no-format bug, not an attributed source-agent error. This headless test does not verify visual caret behavior or a real browser's blur event.

## native-language-menu — kept, feature seed

Original wording source: private provenance (kept by the maintainer, not published). This is the initial feature request; no own-work correction is proven.

| Check family / fixture selector | Classification | Evidence or removal |
|---|---|---|
| Every option text is its own native name, independent of active locale | stated | Request: each language's name in its own language; `locales.py:1` supplies native strings. |
| All: CLI, option/trigger shapes, codes, boolean selected | stated (Interface) | `instruction.md`, Interface. |
| Registry order/codes and selected current locale remain | inferable | Existing `desktop.py:6`, `mobile.py:5`, ordered `locales.py:1`. |
| Both desktop and mobile show native names | inferable | Unqualified language dropdown request; `README.md:2-4` identifies two adapters. |
| Compact trigger and surrounding translated switch control unchanged | inferable | `service.py:6-7`, `catalogs.py:1-6`; only option names were requested to change. |
| `lang` must equal each target locale | arbitrary — removed | Good accessibility improvement, but the original request only specifies displayed names; existing code uses active locale. Do not hide a new metadata requirement in this task. |
| `accessible` must equal the native name exactly, with no code suffix | arbitrary — removed | The request does not prohibit a code suffix or specify screen-reader wording. |

Only `lang` and `accessible` expected-value checks were removed. These fields remain documented in the interface. Near miss retains current-locale translations, reproducing the existing bug; it is not evidence of a failed source-agent attempt.

## Validation and boundaries

See `validation/RESULTS.md` and its JSON receipts for fresh Harbor nop/oracle evidence. Each kept task must have five nop rewards of 0, five oracle rewards of 1, and a near-miss oracle reward of 0, all with `exception_info=null`. Reward JSON, not process exit status, establishes the result. Excluded tasks have separate diagnostics demonstrating that original and corrected behaviors are both accepted. Their actual `tests/test.sh` produces **no reward**, so an accidental Harbor run cannot score them as valid tasks. Exclusion metadata alone is not enforced by Harbor; always filter the dataset.

The original environment and solution trees are copied byte-for-byte. Descriptions and instruction headings were made neutral so corrected titles do not leak withheld behavior through `task.toml`. `titles.json` preserves the requested starter titles as presentation metadata; do not prepend those titles to agent prompts. No model, simulated user or additional authoring/review agent was run. No subscription login is passed to containers. The four weaker seeds measure ordinary feature/bug implementation, not a novel intent failure. Small repository size and source-session context loss remain major limits; no claim about model separation follows from mechanical validation.
