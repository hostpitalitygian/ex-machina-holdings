"""
Prometheus iQ — Morning Briefing (single-shot, no tool loop)

Architecture: fetch all data directly via REST (zero Claude tokens),
then make ONE Claude call to synthesize. Total input: ~1k tokens.
"""
import os
import sys
import json
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
os.environ.setdefault("CLAUDE_MODEL", "claude-sonnet-4-6")

import anthropic
import resend
from orchestrator import (
    get_tasks,
    get_mercury_accounts,
    get_mercury_transactions,
    LEADS_LIST,
    DEALS_LIST,
    WORKSPACE_ID,
)

OPERATIONS_LIST  = "901709230262"
FUNDRAISING_LIST = "901709230268"
INVESTOR_LIST    = "901708451528"


# ── Data formatters (no Claude tokens) ────────────────────────────────────────

def _fmt_tasks(data: dict, limit: int = 12) -> str:
    tasks = data.get("tasks", [])
    if not tasks:
        err = data.get("error")
        return f"(error: {err})" if err else "(empty)"
    lines = []
    for t in tasks[:limit]:
        name      = t.get("name", "?")
        status    = t.get("status", {}).get("status", "?")
        assignees = ", ".join(a.get("username", "?") for a in t.get("assignees", []))
        due_ms    = t.get("due_date")
        due_str   = ""
        if due_ms:
            try:
                due_str = " | due " + datetime.fromtimestamp(int(due_ms) / 1000).strftime("%-m/%-d")
            except Exception:
                pass
        lines.append(f"  [{status}] {name} ({assignees or 'unassigned'}){due_str}")
    if len(tasks) > limit:
        lines.append(f"  ...+{len(tasks) - limit} more")
    return "\n".join(lines)


def _fmt_accounts(data: dict) -> str:
    accounts = data.get("accounts", [])
    if not accounts:
        err = data.get("error")
        return f"(error: {err})" if err else "(no accounts)"
    lines = []
    for a in accounts:
        name    = a.get("name", "?")
        balance = a.get("currentBalance")
        cur     = a.get("currency", "USD")
        if isinstance(balance, (int, float)):
            lines.append(f"  {name}: {cur} {balance:,.2f}")
        else:
            lines.append(f"  {name}: (balance unavailable)")
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    required = ["ANTHROPIC_API_KEY", "RESEND_API_KEY", "REPORT_TO"]
    missing  = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[briefing] Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    today = date.today().strftime("%A, %B %-d, %Y")
    model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
    print(f"[briefing] Fetching live data for {today} (model: {model})...")

    # ── 1. Fetch all data via direct REST — zero Claude tokens ─────────────────
    leads_raw       = get_tasks(LEADS_LIST)
    deals_raw       = get_tasks(DEALS_LIST)
    ops_raw         = get_tasks(OPERATIONS_LIST)
    fundraising_raw = get_tasks(FUNDRAISING_LIST)
    investor_raw    = get_tasks(INVESTOR_LIST)
    accounts_raw    = get_mercury_accounts()

    # ── 2. Compact text summaries ──────────────────────────────────────────────
    data_block = f"""LEADS
{_fmt_tasks(leads_raw)}

DEALS
{_fmt_tasks(deals_raw)}

GIAN PRIORITIES (OPS)
{_fmt_tasks(ops_raw)}

FUNDRAISING
{_fmt_tasks(fundraising_raw)}

INVESTOR OUTREACH
{_fmt_tasks(investor_raw)}

MERCURY ACCOUNTS
{_fmt_accounts(accounts_raw)}"""

    print(f"[briefing] Data ready ({len(data_block)} chars). Calling Claude...")

    # ── 3. Single Claude call — no tools, no loop ──────────────────────────────
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=model,
        max_tokens=3000,
        system=(
            "You are Prometheus iQ, Gian's AI chief of staff. "
            "Turn the live data below into a sharp CEO morning briefing. "
            "Sections: SALES, COO, CFO, then one bold FOCUS recommendation. "
            "Flag anything overdue or stuck. Be direct, no filler."
        ),
        messages=[{
            "role": "user",
            "content": f"Today: {today}\n\n{data_block}\n\nWrite the morning briefing."
        }],
    )
    result = resp.content[0].text
    print(f"[briefing] Generated ({resp.usage.input_tokens} in / {resp.usage.output_tokens} out tokens).")

    # ── 4. Send via Resend ─────────────────────────────────────────────────────
    resend.api_key = os.environ["RESEND_API_KEY"]
    resend_from    = os.environ.get("RESEND_FROM", "Prometheus iQ <communications@prometheusiq.io>")
    report_to      = os.environ["REPORT_TO"]
    subject        = f"Prometheus iQ — Morning Briefing | {today}"

    email_resp = resend.Emails.send({
        "from":    resend_from,
        "to":      [report_to],
        "subject": subject,
        "text":    result,
    })
    print(f"[briefing] Email sent → {report_to} (id: {email_resp.get('id', '?')})")


if __name__ == "__main__":
    main()
