# Contributing

Use Python 3.11+ and run the development commands in [docs/usage.md](docs/usage.md#development). Keep changes focused and add regression coverage when behavior changes. Never include captured sessions, credentials, private source code or raw provider receipts in a contribution.

A new task needs an explicit interface, a deterministic verifier, a reference solution, and fairness notes separating stated requirements from reasonable inferences. Do not grade later preferences as if the original request stated them. Add explicit `[local]` verify/solve commands. Validate baseline failure, reference success and plausible near misses; inspect each receipt. Native controls require no Docker or provider credits. Live-model validation must be separately budgeted.

Keep task changes versioned and old validation receipts clearly tied to their original inputs. Contribution of a task does not establish broad model quality or customer demand.
