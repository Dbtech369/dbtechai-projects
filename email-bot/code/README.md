# Modular Email Demo Bot

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env        # fill in real credentials
cp company_profile.example.yaml company_profile.yaml   # edit per target
```

For Gmail as the watched inbox: enable 2-Step Verification on the
throwaway account, then generate an **App Password** (not the account
password) for `EMAIL_APP_PASSWORD`.

## Run

```bash
python email_bot.py --config company_profile.yaml --once       # one test pass
python email_bot.py --config company_profile.yaml --interval 30 # keep running
```

## Swapping targets

Don't touch `email_bot.py`. Make a new YAML per company
(`apex_plumbing.yaml`, `joes_towing.yaml`, ...) and point `--config`
at it. Each target also needs its own throwaway inbox in `.env` (or
extend the script to loop over multiple .env-equivalents if you're
running several demos concurrently — flag if you want that next).

## What it does NOT do

- Never auto-sends. Every reply lands in the Drafts folder only.
- Never touches the Seen flag, so it won't mess with anyone reading
  the same inbox.
- If the IMAP server rejects the Drafts append (some providers lock
  this down), it falls back to writing a local `.eml` file in
  `drafts_backup/` instead of failing silently.

## Known gaps to fix before this touches a real client's live inbox

- Polling, not IMAP IDLE — fine for a demo inbox, not for a busy
  production mailbox.
- No retry/backoff on the Gemini/Hermes call beyond a single attempt.
- No rate limiting if a target re-sends multiple test emails quickly.
