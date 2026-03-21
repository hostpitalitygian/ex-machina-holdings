"""
Prometheus iQ — Standalone Morning Briefing
Run by GitHub Actions every morning at 7:00 AM AST.
All config comes from environment variables (GitHub Secrets).
"""
import os
import sys
from datetime import date
from pathlib import Path

# Make src importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import anthropic
import resend
from orchestrator import run_agent, LEADS_LIST, DEALS_LIST, WORKSPACE_ID

OPERATIONS_LIST  = "901709230262"
FUNDRAISING_LIST = "901709230268"
INVESTOR_LIST    = "901708451528"


def main():
    # ── Env checks ──────────────────────────────────────────────────────────
    required = ["ANTHROPIC_API_KEY", "RESEND_API_KEY", "REPORT_TO"]
    missing  = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"[briefing] Missing required env vars: {', '.join(missing)}")
        sys.exit(1)

    # ── Run briefing ─────────────────────────────────────────────────────────
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    today  = date.today().strftime("%A, %B %-d, %Y")

    print(f"[briefing] Running morning briefing for {today}...")
    result = run_agent(
        client, "ceo-orchestrator",
        f"Today is {today}. Give me my full morning briefing. "
        f"Run all C-Suite personas: "
        f"(1) SALES: Leads [{LEADS_LIST}] and Deals [{DEALS_LIST}] — overdue or stuck, "
        f"(2) COO: My priorities [{OPERATIONS_LIST}] + team assignments for Paula [75476326] and Ryan [95384247], "
        f"(3) CFO: Pull Mercury accounts (get_mercury_accounts) for cash position, "
        f"then transactions (get_mercury_transactions) for burn rate. "
        f"Also check Fundraising [{FUNDRAISING_LIST}] and Investor Outreach [{INVESTOR_LIST}]. "
        f"(4) Search ClickUp Docs for recent meeting notes (search_docs). "
        f"Synthesize into a CEO-level brief with ONE focus recommendation.",
    )

    # ── Send via Resend ──────────────────────────────────────────────────────
    resend.api_key = os.environ["RESEND_API_KEY"]
    resend_from    = os.environ.get("RESEND_FROM", "Prometheus iQ <onboarding@resend.dev>")
    report_to      = os.environ["REPORT_TO"]
    subject        = f"Prometheus iQ — Morning Briefing | {today}"

    response = resend.Emails.send({
        "from":    resend_from,
        "to":      [report_to],
        "subject": subject,
        "text":    result,
    })
    print(f"[briefing] Email sent → {report_to} (id: {response.get('id', '?')})")


if __name__ == "__main__":
    main()
