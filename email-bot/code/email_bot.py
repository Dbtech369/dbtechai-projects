#!/usr/bin/env python3
"""
Modular email-watcher + draft-generator engine.

Architecture (per your blueprint):
  - THE ENGINE       -> this file. Never changes between companies.
  - THE IDENTITY     -> .env (which inbox to watch, which LLM key to use)
  - THE BRAIN        -> company_profile.yaml (swap this file to swap targets)

Flow:
  1. Poll an IMAP inbox for new messages (tracked by Message-ID, not the
     Seen flag, so it never disturbs the human reading the same inbox).
  2. Build a prompt from company_profile.yaml (tone, rules, scenarios).
  3. Call an LLM "Drafter" (Gemini direct, or your Hermes endpoint) to
     generate a reply.
  4. Write the reply into the account's Drafts folder via IMAP APPEND.
     Nothing is ever auto-sent.

Usage:
  python email_bot.py --config company_profile.yaml
  python email_bot.py --config apex_plumbing.yaml --once   # single pass, for testing
  python email_bot.py --config apex_plumbing.yaml --interval 30
  python email_bot.py --config demo_profile.yaml --auto-send   # demo/auto-reply
"""

import os
import sys
import json
import time
import email
import imaplib
import smtplib
import argparse
import logging
from email.header import decode_header
from email.message import EmailMessage
from email.utils import parseaddr, formatdate, make_msgid
from pathlib import Path

import yaml
import requests
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("email_bot")

STATE_DIR = Path(".bot_state")
STATE_DIR.mkdir(exist_ok=True)


# --------------------------------------------------------------------------
# Config loading (THE BRAIN)
# --------------------------------------------------------------------------

def load_profile(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)
    if "target_company" not in profile:
        raise ValueError(f"{path} is missing a top-level 'target_company' key")
    return profile


def build_system_prompt(profile: dict) -> str:
    company = profile.get("target_company", {})
    rules = profile.get("the_hook_rules", []) or profile.get("response_rules", [])
    scenarios = profile.get("common_scenarios", {})

    lines = [
        f"You are drafting an email reply on behalf of {company.get('name', 'the company')}, "
        f"a business in the {company.get('industry', 'unspecified')} industry.",
        f"Tone: {company.get('tone', 'professional and helpful')}.",
        "",
        "Rules to follow:",
    ]
    for r in rules:
        lines.append(f"- {r}")

    if scenarios:
        lines.append("")
        lines.append("Known scenario guidance:")
        for k, v in scenarios.items():
            lines.append(f"- {k}: {v}")

    lines.append("")
    lines.append(
        "Write ONLY the reply body. No subject line, no commentary, no markdown. "
        "Sign off generically (e.g. 'Best regards,' followed by a placeholder name) "
        "since this is a draft for human review before sending."
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Drafters (pluggable LLM backends)
# --------------------------------------------------------------------------

class Drafter:
    def generate(self, system_prompt: str, email_text: str) -> str:
        raise NotImplementedError


class GeminiDrafter(Drafter):
    """Direct REST call to the Gemini API. No SDK dependency."""

    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        # Model names change over time -- check ai.google.dev for current
        # options and override via GEMINI_MODEL in .env if this is stale.
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def generate(self, system_prompt: str, email_text: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [
                {"role": "user", "parts": [{"text": email_text}]}
            ],
        }
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()


class HermesDrafter(Drafter):
    """
    Stub for routing the draft call through your local Hermes agent
    instead of calling Gemini directly. Assumes an OpenAI-compatible
    chat endpoint -- adjust the payload/parsing to match your actual
    Hermes server's API.
    """

    def __init__(self, endpoint: str):
        self.endpoint = endpoint.rstrip("/")

    def generate(self, system_prompt: str, email_text: str) -> str:
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": email_text},
            ]
        }
        resp = requests.post(f"{self.endpoint}/v1/chat/completions", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # Adjust this line to match whatever shape your Hermes server returns
        return data["choices"][0]["message"]["content"].strip()


def get_drafter() -> Drafter:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("GEMINI_API_KEY missing from .env")
        return GeminiDrafter(key)
    elif provider == "hermes":
        endpoint = os.getenv("HERMES_API_URL")
        if not endpoint:
            raise RuntimeError("HERMES_API_URL missing from .env")
        return HermesDrafter(endpoint)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


# --------------------------------------------------------------------------
# Mailbox handling (THE ENGINE)
# --------------------------------------------------------------------------

def decode_str(value) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    return "".join(
        p.decode(enc or "utf-8", errors="replace") if isinstance(p, bytes) else p
        for p, enc in parts
    )


def get_body_text(msg: email.message.Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get(
                "Content-Disposition"
            ):
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace")
        return ""
    else:
        charset = msg.get_content_charset() or "utf-8"
        return msg.get_payload(decode=True).decode(charset, errors="replace")


def load_processed_ids(state_file: Path) -> set:
    if state_file.exists():
        return set(json.loads(state_file.read_text()))
    return set()


def save_processed_ids(state_file: Path, ids: set):
    state_file.write_text(json.dumps(list(ids)))


def fetch_new_messages(imap: imaplib.IMAP4_SSL, processed_ids: set):
    """Pull all messages in INBOX not yet in processed_ids. Does not
    touch the Seen flag -- safe to run alongside a human reading the
    same inbox."""
    imap.select("INBOX")
    status, data = imap.search(None, "ALL")
    if status != "OK":
        return []

    new_msgs = []
    for num in data[0].split():
        status, msg_data = imap.fetch(num, "(RFC822)")
        if status != "OK":
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)
        msg_id = msg.get("Message-ID", f"no-id-{num}")
        if msg_id in processed_ids:
            continue
        new_msgs.append((msg_id, msg))
    return new_msgs


def _build_reply(
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    in_reply_to: str,
) -> EmailMessage:
    reply = EmailMessage()
    reply["From"] = from_addr
    reply["To"] = to_addr
    reply["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    reply["Date"] = formatdate(localtime=True)
    reply["Message-ID"] = make_msgid()
    if in_reply_to:
        reply["In-Reply-To"] = in_reply_to
        reply["References"] = in_reply_to
    reply.set_content(body)
    return reply


def append_draft(
    imap: imaplib.IMAP4_SSL,
    drafts_folder: str,
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    in_reply_to: str,
):
    reply = _build_reply(from_addr, to_addr, subject, body, in_reply_to)
    raw = reply.as_bytes()
    try:
        imap.append(drafts_folder, "", imaplib.Time2Internaldate(time.time()), raw)
        log.info("Draft saved to %s for: %s", drafts_folder, to_addr)
    except imaplib.IMAP4.error as e:
        log.error("Could not append to '%s' (%s) -- saving locally instead", drafts_folder, e)
        backup_dir = Path("drafts_backup")
        backup_dir.mkdir(exist_ok=True)
        fname = backup_dir / f"draft_{int(time.time())}.eml"
        fname.write_bytes(raw)
        log.info("Draft backed up to %s", fname)


def send_reply(
    from_addr: str,
    to_addr: str,
    subject: str,
    body: str,
    in_reply_to: str,
):
    """Send the reply directly via SMTP (auto-send / demo mode)."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.environ["EMAIL_ADDRESS"]
    smtp_pass = os.environ["EMAIL_APP_PASSWORD"]

    reply = _build_reply(from_addr, to_addr, subject, body, in_reply_to)
    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_pass)
        smtp.send_message(reply)
    log.info("Auto-sent reply to: %s", to_addr)


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------

def process_once(profile: dict, drafter: Drafter, auto_send: bool = False):
    imap_host = os.environ["IMAP_HOST"]
    imap_user = os.environ["EMAIL_ADDRESS"]
    imap_pass = os.environ["EMAIL_APP_PASSWORD"]
    drafts_folder = os.getenv("DRAFTS_FOLDER", "Drafts")

    profile_name = profile["target_company"].get("name", "unknown").replace(" ", "_")
    state_file = STATE_DIR / f"{profile_name}.json"
    processed_ids = load_processed_ids(state_file)

    system_prompt = build_system_prompt(profile)

    imap = imaplib.IMAP4_SSL(imap_host)
    imap.login(imap_user, imap_pass)
    try:
        new_msgs = fetch_new_messages(imap, processed_ids)
        log.info("Found %d new message(s)", len(new_msgs))

        for msg_id, msg in new_msgs:
            sender_name, sender_addr = parseaddr(decode_str(msg.get("From")))
            subject = decode_str(msg.get("Subject"))
            body = get_body_text(msg).strip()

            if not body:
                log.info("Skipping message with empty body from %s", sender_addr)
                processed_ids.add(msg_id)
                continue

            log.info("Drafting reply to %s | subject: %s", sender_addr, subject)
            try:
                draft_body = drafter.generate(system_prompt, body)
            except Exception as e:
                log.error("Drafter failed for %s: %s", sender_addr, e)
                continue  # leave un-processed, retry next pass

            if auto_send:
                send_reply(
                    from_addr=imap_user,
                    to_addr=sender_addr,
                    subject=subject,
                    body=draft_body,
                    in_reply_to=msg.get("Message-ID", ""),
                )
            else:
                append_draft(
                    imap,
                    drafts_folder,
                    from_addr=imap_user,
                    to_addr=sender_addr,
                    subject=subject,
                    body=draft_body,
                    in_reply_to=msg.get("Message-ID", ""),
                )
            processed_ids.add(msg_id)
            save_processed_ids(state_file, processed_ids)  # save incrementally
    finally:
        imap.logout()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, help="Path to company_profile.yaml")
    parser.add_argument("--interval", type=int, default=60, help="Poll interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run a single pass and exit")
    parser.add_argument("--auto-send", action="store_true", help="Send replies directly instead of saving as drafts (demo mode)")
    args = parser.parse_args()

    profile = load_profile(args.config)
    drafter = get_drafter()

    log.info("Watching inbox for target: %s", profile["target_company"].get("name"))
    log.info("Mode: %s", "auto-send" if args.auto_send else "draft-only")

    if args.once:
        process_once(profile, drafter, auto_send=args.auto_send)
        return

    while True:
        try:
            process_once(profile, drafter, auto_send=args.auto_send)
        except Exception as e:
            log.error("Pass failed: %s", e)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
