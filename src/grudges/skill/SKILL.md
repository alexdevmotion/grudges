---
name: grudge
description: Save the coding-agent failure that just happened as a replayable grudge (exact starting code, failed attempt and session copy). Use when the user types /grudge or $grudge, or asks to save, bookmark or remember this failure for re-running on future models.
---

# Save a grudge

The user is telling you that you (or an earlier agent turn) got something wrong and wants
the incident preserved so future models and setups can be re-tested on it. Be fast: this
should take one command and a two-line reply.

1. **Note.** Use the text the user wrote after `/grudge` as the note, verbatim. If they wrote
   nothing, write one sentence stating what the correct outcome should have been, based on
   their corrections in this conversation, not on your own attempt.
2. **Episode start.** By default the grudge starts at the user's most recent request before
   `/grudge`. If the failure clearly began earlier (the user had to correct you over several
   requests), run `grudges requests` and pick how many requests back the episode started.
3. Run:

   ```bash
   grudges save --note "<note>" [--back N]
   ```

4. Reply with the grudge id and whether the starting state is exact, in at most two lines.

Do not try to fix the problem, edit files, commit, or summarize the session beyond the note,
unless the user asks. Everything stays on this machine under `~/.grudges` and `refs/grudges/`.
