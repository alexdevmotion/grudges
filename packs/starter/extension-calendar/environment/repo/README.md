# Lease accounts
`ledger` and `preview` are independent schedule consumers. `calendar_rules` defines
the normal billing dates, while `accrual` computes components for a date interval.
The CLI presents both views and the next scheduled debit. There are no persistence
or service integrations.
