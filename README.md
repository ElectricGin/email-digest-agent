# Email Digest Agent

Fetches new Gmail messages across 3 personal accounts, feeds them to a Claude Code
scheduled routine for summarization, and writes digests into the Obsidian vault.

## One-time setup (per Google account, 3 times total)

1. Fill in real addresses in `%USERPROFILE%\.claude\secrets\email-digest\accounts.json`
   (see Task 1, Step 4 of the implementation plan).
2. Go to https://console.cloud.google.com/ and create a project (or reuse one project
   for all 3 accounts — a single OAuth client works across multiple consenting accounts).
3. Enable the "Gmail API" for the project (APIs & Services -> Library -> search "Gmail API" -> Enable).
4. Configure the OAuth consent screen (APIs & Services -> OAuth consent screen):
   - User type: External
   - Add your 3 Gmail addresses as test users (since this app won't be verified/published).
5. Create credentials (APIs & Services -> Credentials -> Create Credentials -> OAuth client ID):
   - Application type: Desktop app
   - Download the resulting JSON as `client_secret.json` in this project directory.
6. For each of the 3 accounts, run:
   ```
   python setup_oauth.py --client-secret client_secret.json --account-label personal1
   python setup_oauth.py --client-secret client_secret.json --account-label personal2
   python setup_oauth.py --client-secret client_secret.json --account-label personal3
   ```
   Each run opens a browser — log into that specific Gmail account and click Allow.
   **You may see a warning that the app isn't verified — click "Advanced" -> "Go to
   (app name), unsafe" since this is your own app.** This writes a token file to
   `%USERPROFILE%\.claude\secrets\email-digest\<label>-token.json`.
7. Verify: `dir %USERPROFILE%\.claude\secrets\email-digest\` should show 3 `*-token.json`
   files and `accounts.json` with real addresses.

## Install

```
pip install -r requirements.txt
```

## Run tests

```
pytest tests/ -v
```
