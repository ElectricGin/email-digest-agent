# Email Digest Routine

Run this procedure exactly. Never put email subjects/snippets/summaries directly inside a
shell command argument or a `python -c` string — always write them to a file first and pipe
via stdin, since they can contain characters that break shell quoting.

Fixed paths:
- Project dir: `C:\Users\sb737\Documents\email-digest-agent`
- Secrets dir: `C:\Users\sb737\.claude\secrets\email-digest`
- Vault wiki dir: `C:\Users\sb737\Documents\Obsidian\Claudy\wiki`
- Accounts file: `<secrets_dir>\accounts.json`
- State file: `<secrets_dir>\state.json`

All commands below run with the project dir as the working directory.

## Steps

1. Load the account map: read `<accounts_file>` (label -> email), e.g.
   `{"personal1": "a@gmail.com", "personal2": "b@gmail.com", "personal3": "c@gmail.com"}`.

2. For each label/email pair:
   a. Get the last-run epoch:
      `python print_last_run.py --state-path <state_file> --account-email <email>`
   b. Fetch new messages:
      `python gmail_fetch.py --token-path <secrets_dir>\<label>-token.json --since-epoch <epoch from 2a>`
      This prints a JSON list of new messages (id, from, subject, date, snippet) to stdout.

3. Summarize the results **separately per account** — never merge items from different
   addresses into one undifferentiated list. Use this exact structure, one `###` subsection
   per account email, in the same order as `accounts.json`:

   ```markdown
   ### a@gmail.com
   - [Deadline] Chem lab report due Friday — from teacher@school.edu
   - New message from friend@example.com: "let's hang out this weekend"

   ### b@gmail.com
   - Nothing notable.

   ### c@gmail.com
   - [Reminder] Package delivery scheduled today, 2-4pm
   ```

   Rules for each account's bullets:
   - Call out anything that reads as a deadline, reminder, or action item — prefix it
     `[Deadline]` or `[Reminder]`.
   - Skip pure noise (routine receipts, generic promos) unless something in one stands out.
   - If an account has nothing worth surfacing, write `- Nothing notable.` under its heading
     rather than omitting the heading — so it's always clear all 3 accounts were checked.
   - Keep each account's section short — this should be readable in under a minute total.

   Write this summary as markdown to a temp file, e.g. `digest_body.md`, using the Write tool.

4. Write the digest into the vault:
   `python write_digest.py --vault-wiki-dir <vault_wiki_dir> --run-date <today, YYYY-MM-DD> --run-label "<run_label>" < digest_body.md`
   where `<run_label>` is `"7:30am Digest"`, `"4:00pm Digest"`, or `"On-Demand Digest"`
   depending on why this routine is running.

5. Update state for each of the 3 accounts:
   `python record_last_run.py --state-path <state_file> --account-email <email> --epoch <current unix epoch>`

6. Check retention:
   `python find_stale.py --personal-dir <vault_wiki_dir>\Personal`
   This prints a JSON list of stale page paths (may be empty).

7. For each stale page path returned in Step 6:
   a. Parse the date from its filename (`email-digest-YYYY-MM-DD.md` -> `YYYY-MM-DD`).
   b. Read the page's content (Read tool).
   c. Condense it into a few compact bullet points and write them to a temp file, e.g.
      `weekly_entry.md`, using the Write tool.
   d. Run:
      `python finalize_rollup.py --personal-dir <vault_wiki_dir>\Personal --page-path "<stale page path>" --page-date <date from 7a> < weekly_entry.md`
      This merges the condensed entry into that page's ISO week's summary file (creating it if
      it's the first page from that week, appending if not) and deletes the daily page.

> Note (2026-07-12): the plan's original Step 6 sent a phone push via the `PushNotification`
> tool. Pre-Flight Check 2 found Remote Control is not paired ("Mobile push not sent —
> Remote Control inactive"), so per the plan's fallback that step is dropped and delivery
> relies on the wiki page + Obsidian Sync. If Remote Control gets paired later, re-add a push
> step after Step 5 with a one-line teaser of the digest.
