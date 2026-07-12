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

3a. For each `[Deadline]` or `[Reminder]` bullet identified in Step 3, create a matching Google
    Calendar event using the `mcp__claude_ai_Google_Calendar__create_event` tool (confirmed via
    Task 10, Step 1 — note: the connector is authorized as the personal1 account, so events land
    on that account's primary calendar):
    - `summary`: the short description from the bullet (e.g. "Chem lab report due").
    - Date/time: parse from the email's date/subject/snippet. If the email specifies a time,
      set `startTime` to it (ISO 8601, e.g. `2026-07-17T15:00:00`) and `endTime` one hour
      later unless the email implies a duration. If only a date is mentioned (no time), create
      an all-day event: `allDay: true`, `startTime` = that date at `T00:00:00`, `endTime` =
      the NEXT day at `T00:00:00` (verified convention — renders as a single all-day event).
    - If the year is ambiguous (e.g. "due Friday" with no explicit date), infer the nearest
      upcoming occurrence relative to today's date rather than skipping the event.
    - Skip creating an event for anything vague enough that you can't pin down at least a date
      (e.g. "sometime next month") — mention it in the digest text instead, don't guess a date
      just to force an event to exist.
    - **Skip creating an event if the email itself IS a calendar invite** — judge this from
      subject and sender only (that's all the data `gmail_fetch.py` actually returns; it
      fetches headers + snippet, not attachment info, so don't rely on ".ics attachment" as a
      signal — it isn't visible to you). Look for subjects starting with "Invitation:",
      "Invite:", "RSVP:", "You're invited:", or a sender clearly in the business of sending
      event invites (e.g. a band program, Eventbrite, Google Calendar's own invite
      notifications). Gmail/Google Calendar already auto-adds real invites like these on its
      own; creating a second event for the same thing produces a duplicate. Still mention it
      in the digest text as a heads-up, just don't create the redundant event.
    - If you genuinely can't tell whether something is a native invite from subject/sender
      alone, err toward creating the event anyway — a rare duplicate is a smaller problem than
      silently dropping a real deadline.
    - **Cancellations/reschedules (rare, but watch for them):** if an email clearly announces
      that a previously known event is cancelled or moved (e.g. "rehearsal cancelled",
      "meeting moved to Tuesday"), flag it in the digest with a `[Cancelled]` or
      `[Rescheduled]` prefix. Then use `mcp__claude_ai_Google_Calendar__search_events` to look
      for the matching calendar event: if **exactly one** event clearly matches by title and
      date, delete it (`mcp__claude_ai_Google_Calendar__delete_event`) for a cancellation, or
      update its time (`mcp__claude_ai_Google_Calendar__update_event`) for a reschedule. If
      zero or multiple candidates match, or you're at all unsure, change nothing on the
      calendar — the digest flag is enough. Never guess at deleting calendar data.
      Two hard limits on this rule:
      - Only an **organizer/sender announcement that the event itself** is cancelled or moved
        counts. "I can't attend" / "I have a conflict" — especially in mail **Aiden himself
        sent** (from one of his own 3 addresses) — is a personal attendance change, NOT an
        event cancellation: flag it in the digest, leave the calendar alone.
      - Never delete or modify an event based on outgoing mail (From: one of Aiden's own
        addresses) at all. Outgoing mail may be summarized for context, nothing more.

4. Write the digest into the vault:
   `python write_digest.py --vault-wiki-dir <vault_wiki_dir> --run-date <today, YYYY-MM-DD> --run-label "<run_label>" < digest_body.md`
   where `<run_label>` is `"7:30am Digest"`, `"4:00pm Digest"`, or `"On-Demand Digest"`
   depending on why this routine is running.

5. Update state for each of the 3 accounts:
   `python record_last_run.py --state-path <state_file> --account-email <email> --epoch <current unix epoch>`

5a. Send a push notification via the `PushNotification` tool with a one-line teaser of the
    digest (e.g. "3 new items, 1 deadline flagged — check today's digest"). If the tool
    reports the mobile push wasn't sent, don't retry and don't treat it as an error — the
    wiki page via Obsidian Sync is the fallback delivery path.

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

> Note (2026-07-12): the push step was originally dropped when Pre-Flight Check 2 found
> Remote Control unpaired. Aiden paired Remote Control later the same day (test then returned
> "Mobile push requested"), so the step is restored above as Step 5a. Whether a headless
> scheduled session can deliver through the pairing is verified by the first scheduled run —
> if it consistently can't, Obsidian Sync alone is still fine.
