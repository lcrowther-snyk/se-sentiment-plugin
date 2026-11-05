#!/usr/bin/env python3
"""Validate an SE sentiment proposal and post it to the Slack approval workflow.

Usage:
  python send_proposal.py proposals.json            # dry run (default): validate + show payloads
  python send_proposal.py proposals.json --send     # post to the Slack webhook
  python send_proposal.py --check                   # setup: is the webhook configured?

proposals.json is a list of objects:
  {
    "se_user": "U0123ABCD",            # SE's Slack user ID (gets the DM, clicks Approve)
    "opp_id": "006000000000001AAA",    # 15 or 18 char Opportunity ID
    "opp_name": "Acme - New Business",
    "colour": "Green",                 # Green | Yellow | Red | Gray
    "status_note": "21/10 CL - ...",   # <= 1000 chars
    "status_date": "2026-10-21",       # YYYY-MM-DD
    "current": "Yellow, 03/10",        # optional, shown in the DM
    "rationale": "Why ...",            # optional, shown in the DM
    "evidence_url": "https://..."      # optional, shown in the DM
  }

The webhook URL is read from SE_SENTIMENT_WEBHOOK or ../config.json and is never printed.
Only the fields above are sent; anything else is rejected, so nothing outside the
SE sentiment fields can reach Salesforce through this script.
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date

SENT_FIELDS = {"se_user", "opp_id", "opp_name", "colour", "status_note", "status_date",
               "current", "rationale", "evidence_url", "set_eval_dates", "tech_decision"}
TECH_DECISIONS = {"Win", "Loss", "Undecided"}
ALLOWED = SENT_FIELDS | {"se_name"}   # se_name is display-only (pilot mode), never sent as-is
REQUIRED = {"se_user", "opp_id", "colour", "status_note", "status_date"}
COLOURS = {"Green", "Yellow", "Red", "Gray"}
MAX_NOTE = 1000
MAX_PER_RUN = 25
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def load_config():
    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    try:
        with open(cfg) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def webhook_url():
    url = os.environ.get("SE_SENTIMENT_WEBHOOK") or load_config().get("webhook_url", "")
    if not url.startswith("https://hooks.slack.com/triggers/"):
        sys.exit("No Slack webhook configured. This copy was installed without the team config: ask your SE lead for the current se-sentiment .plugin file and reinstall it.")
    return url


def validate(p, i):
    errs = []
    extra = set(p) - ALLOWED
    if extra:
        errs.append(f"unexpected fields {sorted(extra)}")
    missing = REQUIRED - set(p)
    if missing:
        errs.append(f"missing {sorted(missing)}")
    oid = str(p.get("opp_id", ""))
    if not (oid.startswith("006") and len(oid) in (15, 18) and oid.isalnum()):
        errs.append(f"opp_id '{oid}' is not a 15/18-char Opportunity ID")
    if not re.fullmatch(r"[UW][A-Z0-9]{6,}", str(p.get("se_user", ""))):
        errs.append("se_user must be a Slack user ID like U0123ABCD")
    if p.get("colour") not in COLOURS:
        errs.append(f"colour must be one of {sorted(COLOURS)}")
    note = str(p.get("status_note", ""))
    if not note.strip():
        errs.append("status_note is empty")
    if len(note) > MAX_NOTE:
        errs.append(f"status_note is {len(note)} chars (max {MAX_NOTE})")
    if EMAIL_RE.search(note):
        errs.append("status_note contains an email address; remove personal data")
    if str(p.get("set_eval_dates", "no")) not in ("no", "start", "end", "both"):
        errs.append("set_eval_dates must be 'no', 'start', 'end' or 'both'")
    td = p.get("tech_decision")
    if td is not None and td not in TECH_DECISIONS:
        errs.append(f"tech_decision must be one of {sorted(TECH_DECISIONS)}")
    if str(p.get("set_eval_dates", "no")) in ("end", "both") and td is None:
        errs.append("setting Evaluation End needs tech_decision (Win/Loss/Undecided; use Undecided if unsure)")
    try:
        d = date.fromisoformat(str(p.get("status_date", "")))
        if d > date.today():
            errs.append("status_date is in the future")
    except ValueError:
        errs.append("status_date must be YYYY-MM-DD")
    return [f"#{i} ({oid or '?'}): {e}" for e in errs]


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if args == ["--check"]:  # setup: is the team config present? never prints the URL
        webhook_url()
        print("OK: team Slack workflow is configured.")
        return
    send = "--send" in args
    path = [a for a in args if not a.startswith("--")][0]
    with open(path) as f:
        proposals = json.load(f)
    if isinstance(proposals, dict):
        proposals = [proposals]
    if len(proposals) > MAX_PER_RUN:
        sys.exit(f"{len(proposals)} proposals; max {MAX_PER_RUN} per run.")

    errors = [e for i, p in enumerate(proposals) for e in validate(p, i)]
    if errors:
        print("Validation failed, nothing sent:")
        print("\n".join("  " + e for e in errors))
        sys.exit(1)

    cfg = load_config()
    pilot = bool(cfg.get("pilot_mode")) and "--live" not in args
    pilot_to = cfg.get("pilot_recipient", "")
    if pilot and not re.fullmatch(r"[UW][A-Z0-9]{6,}", pilot_to):
        sys.exit("pilot_mode is on but pilot_recipient in config.json is not a Slack user ID.")

    payloads = []
    for p in proposals:
        pl = {k: str(v) for k, v in p.items() if k in SENT_FIELDS}
        if pilot:
            who = p.get("se_name") or p["se_user"]
            pl["opp_name"] = f"[PILOT for {who}] {pl.get('opp_name', '')}"
            pl["se_user"] = pilot_to
        payloads.append(pl)
    if pilot:
        print(f"PILOT MODE: all drafts go to {pilot_to} (pass --live to send to the real SEs).")
    for k in ("current", "rationale", "evidence_url", "opp_name"):
        for pl in payloads:
            pl.setdefault(k, "")
    for pl in payloads:
        pl.setdefault("set_eval_dates", "no")  # safe default: never touch eval dates unless asked
        pl.setdefault("tech_decision", "")     # only used when the end date is written

    if not send:
        print(f"DRY RUN: {len(payloads)} proposal(s) valid. Would send:")
        print(json.dumps(payloads, indent=2))
        return

    url = webhook_url()
    ok = 0
    for pl in payloads:
        req = urllib.request.Request(url, data=json.dumps(pl).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read().decode()[:200]
                status = r.status
        except Exception as e:  # report once, no retry loop
            status, body = "error", str(e)[:200]
        good = status == 200 and '"ok":true' in body.replace(" ", "")
        ok += good
        print(f"{'SENT' if good else 'FAILED'} {pl['opp_id']} {pl.get('opp_name','')} -> {status}")
        time.sleep(1)
    print(f"{ok}/{len(payloads)} sent for approval. Salesforce changes only when the SE taps Approve.")
    if ok < len(payloads):
        sys.exit(2)


if __name__ == "__main__":
    main()
