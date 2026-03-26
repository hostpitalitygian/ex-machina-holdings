"""
Prometheus iQ — Live Agent Server
Expose your CEO agent as an HTTP API callable from anywhere.

Quick start:
  pip install -r requirements.txt
  cp .env.example .env        # fill in ANTHROPIC_API_KEY, GMAIL_*, API_SECRET_TOKEN
  bash start.sh               # starts uvicorn on :8000
  ngrok http 8000             # exposes public URL — paste into ClickUp automation

Endpoints:
  GET  /health                          — status check
  POST /run          (Bearer auth)      — sync: run any command, get result + email
  POST /webhook/clickup                 — async: ClickUp automation trigger

ClickUp automation tag → command mapping:
  run:briefing   → morning-briefing
  run:pipeline   → pipeline
  run:coo        → c-suite coo
  run:cfo        → c-suite cfo
  run:cpo        → c-suite cpo
  run:cmo        → c-suite cmo
  run:deal-<co>  → deal <co>   (e.g. run:deal-hostaway)
"""
import os
import sys
import json
import hmac
import hashlib
from datetime import date
from pathlib import Path
from typing import Optional

import resend
import anthropic
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Header
from pydantic import BaseModel
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# ── Bootstrap ─────────────────────────────────────────────────────────────────
# Load .env from project root regardless of where uvicorn is launched
load_dotenv(Path(__file__).parent.parent / ".env")

# Make orchestrator importable
sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import run_agent, LEADS_LIST, DEALS_LIST, WORKSPACE_ID

# ── Config ────────────────────────────────────────────────────────────────────
API_SECRET_TOKEN       = os.environ.get("API_SECRET_TOKEN", "")
CLICKUP_WEBHOOK_SECRET = os.environ.get("CLICKUP_WEBHOOK_SECRET", "")
RESEND_API_KEY         = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM            = os.environ.get("RESEND_FROM", "Prometheus iQ <reports@yourdomain.com>")
REPORT_TO              = os.environ.get("REPORT_TO", "")          # your email address
REPORT_CLICKUP_TASK    = os.environ.get("REPORT_CLICKUP_TASK", "") # optional: post to a ClickUp task too

# ── Scheduler config ──────────────────────────────────────────────────────────
BRIEFING_HOUR   = int(os.environ.get("BRIEFING_HOUR", "7"))
BRIEFING_MINUTE = int(os.environ.get("BRIEFING_MINUTE", "0"))
BRIEFING_TZ     = os.environ.get("BRIEFING_TZ", "America/Puerto_Rico")

OPERATIONS_LIST  = "901709230262"
FUNDRAISING_LIST = "901709230268"
INVESTOR_LIST    = "901708451528"

app = FastAPI(title="Prometheus iQ CEO Agent", version="1.0.0")


@app.on_event("startup")
def start_scheduler():
    """Schedule the daily morning briefing via Resend."""
    if os.environ.get("BRIEFING_ENABLED", "true").lower() == "false":
        print("[scheduler] Skipped — BRIEFING_ENABLED=false")
        return
    if not all([RESEND_API_KEY, REPORT_TO]):
        print("[scheduler] Skipped — set RESEND_API_KEY and REPORT_TO to enable scheduled briefings")
        return
    scheduler = BackgroundScheduler(timezone=BRIEFING_TZ)
    scheduler.add_job(
        _background_run,
        CronTrigger(hour=BRIEFING_HOUR, minute=BRIEFING_MINUTE, timezone=BRIEFING_TZ),
        args=["morning-briefing", ""],
        id="morning-briefing",
        replace_existing=True,
    )
    scheduler.start()
    print(f"[scheduler] Morning briefing scheduled at {BRIEFING_HOUR:02d}:{BRIEFING_MINUTE:02d} {BRIEFING_TZ}")


# ── Auth ──────────────────────────────────────────────────────────────────────
def verify_bearer(authorization: Optional[str]) -> None:
    """Verify Bearer token. No-ops if API_SECRET_TOKEN is not configured."""
    if not API_SECRET_TOKEN:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    provided = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(provided.encode(), API_SECRET_TOKEN.encode()):
        raise HTTPException(status_code=403, detail="Invalid token")


# ── Delivery (Resend email + optional ClickUp comment fallback) ───────────────
def send_email(subject: str, body: str) -> bool:
    """
    Send via Resend (resend.com). Free tier: 3k emails/month.
    Requires RESEND_API_KEY + REPORT_TO in .env.
    """
    if not all([RESEND_API_KEY, REPORT_TO]):
        print("[email] Skipped — set RESEND_API_KEY and REPORT_TO in .env")
        return False
    try:
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({
            "from":    RESEND_FROM,
            "to":      [REPORT_TO],
            "subject": subject,
            "text":    body,
        })
        print(f"[email] Sent: {subject}")
        return True
    except Exception as e:
        print(f"[email] Error: {e}")
        return False


def post_to_clickup(comment: str) -> bool:
    """
    Fallback: post report as a comment on a ClickUp task.
    Set REPORT_CLICKUP_TASK to any task ID you want reports posted to.
    """
    if not REPORT_CLICKUP_TASK:
        return False
    from orchestrator import create_task_comment
    result = create_task_comment(REPORT_CLICKUP_TASK, comment)
    ok = "error" not in result
    print(f"[clickup] {'Posted' if ok else 'Failed'}: {result}")
    return ok


def deliver(subject: str, body: str) -> bool:
    """Try email first; fall back to ClickUp comment."""
    delivered = send_email(subject, body)
    if not delivered:
        delivered = post_to_clickup(f"**{subject}**\n\n{body}")
    return delivered


# ── Claude client ─────────────────────────────────────────────────────────────
def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        base_url=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
    )


# ── Dispatcher ────────────────────────────────────────────────────────────────
def dispatch(client: anthropic.Anthropic, command: str, args: str = "") -> str:
    """Route a command string to the correct skill + prompt. Returns text result."""
    today = date.today().strftime("%A, %B %-d, %Y")

    if command == "morning-briefing":
        return run_agent(
            client, "ceo-orchestrator",
            f"Today is {today}. Give me my full morning briefing. "
            f"Run all C-Suite personas: "
            f"(1) SALES: Leads [{LEADS_LIST}] and Deals [{DEALS_LIST}] — overdue or stuck, "
            f"(2) COO: My priorities [{OPERATIONS_LIST}] + team assignments for Paula [75476326] and Ryan [95384247], "
            f"(3) CFO: Pull Mercury accounts (get_mercury_accounts) for cash position, "
            f"then transactions (get_mercury_transactions) for burn rate. "
            f"Also check Fundraising [901709230268] and Investor Outreach [901708451528]. "
            f"(4) Search ClickUp Docs for recent meeting notes (search_docs). "
            f"Synthesize into a CEO-level brief with ONE focus recommendation.",
        )

    if command == "pipeline":
        return run_agent(
            client, "sales-assistant",
            f"Run a Pipeline Check. Pull live data: Leads [{LEADS_LIST}], "
            f"Deals [{DEALS_LIST}]. Flag overdue + stuck items (no activity 5+ days). "
            f"Recommend the single most important follow-up right now.",
        )

    if command == "deal":
        if not args:
            return "Error: 'deal' requires a company name in args."
        return run_agent(
            client, "sales-assistant",
            f"Deal Deep Dive on {args}. Search ClickUp workspace [{WORKSPACE_ID}] "
            f"for all tasks and leads related to '{args}'. Pull full deal context, "
            f"stage, last contact, open items, and decision-maker info.",
        )

    if command == "c-suite":
        mode = (args or "coo").lower()
        prompts = {
            "coo": (
                f"Activate COO mode. Operations Snapshot for {today}: "
                f"pull priority list [{OPERATIONS_LIST}] for urgent/due tasks, "
                f"flag any blockers or scheduling conflicts."
            ),
            "cfo": (
                f"Activate CFO mode. Fundraising Readiness report: "
                f"pull Fundraising tasks [{FUNDRAISING_LIST}] and "
                f"Investor Outreach [{INVESTOR_LIST}]. "
                f"Surface the three numbers: cash position, monthly burn, current ARR. "
                f"If data isn't in ClickUp, flag the gap."
            ),
            "cpo": (
                "Activate CPO mode. Product Status: "
                "pull Active Work [901709169714], Bugs [901709230603], "
                "Users [901709190382]. Flag Priority 1 bugs affecting active customers."
            ),
            "cmo": (
                "Activate CMO mode. Content & Brand status: "
                "pull LinkedIn [901709237676], Instagram [901709251937], "
                "Email Outreach [901709235907], Beta Ambassadors [901708706835]. "
                "What's live, what's due, what's the next content priority."
            ),
        }
        return run_agent(client, "c-suite", prompts.get(mode, prompts["coo"]))

    return f"Unknown command: '{command}'. Options: morning-briefing, pipeline, deal, c-suite"


# ── Request models ─────────────────────────────────────────────────────────────
class RunRequest(BaseModel):
    command: str   # morning-briefing | pipeline | deal | c-suite
    args: str = "" # company name for 'deal'; coo/cfo/cpo/cmo for 'c-suite'
    email: bool = True


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    """Quick health check — no auth required."""
    return {
        "status":           "ok",
        "agent":            "Prometheus iQ CEO Command Center",
        "email_configured": bool(RESEND_API_KEY and REPORT_TO),
        "auth_configured":  bool(API_SECRET_TOKEN),
        "clickup_webhook":  bool(CLICKUP_WEBHOOK_SECRET),
    }


@app.post("/run")
def run_command(body: RunRequest, authorization: Optional[str] = Header(None)):
    """
    Synchronous endpoint — run any agent command and get the result back.
    Also emails the result if email=true and Gmail is configured.

    Example:
      curl -X POST https://your-ngrok-url/run \\
        -H 'Authorization: Bearer YOUR_TOKEN' \\
        -H 'Content-Type: application/json' \\
        -d '{"command": "morning-briefing", "email": true}'
    """
    verify_bearer(authorization)
    client = get_client()
    result = dispatch(client, body.command, body.args)

    delivered = False
    if body.email:
        today   = date.today().strftime("%A, %B %-d, %Y")
        subject = f"Prometheus iQ — {body.command.replace('-', ' ').title()} | {today}"
        delivered = deliver(subject, result)

    return {"status": "ok", "command": body.command, "delivered": delivered, "result": result}


@app.post("/webhook/clickup", status_code=202)
async def webhook_clickup(
    request: Request,
    background_tasks: BackgroundTasks,
    command: Optional[str] = None,  # ?command=morning-briefing  (URL override)
    args: Optional[str] = None,
):
    """
    ClickUp Automation webhook — responds 202 immediately, runs agent in background.

    Two trigger modes:
      1. URL param:  POST /webhook/clickup?command=morning-briefing
         (use this in ClickUp Automation → Webhook action, append ?command=morning-briefing)

      2. Tag-based:  Add tag 'run:briefing', 'run:pipeline', 'run:coo', etc. to a task.
         ClickUp fires taskTagUpdated event; server parses the tag automatically.

    After the agent runs, results are emailed to GMAIL_TO.
    """
    body_bytes = await request.body()

    # Verify ClickUp HMAC signature when secret is configured
    if CLICKUP_WEBHOOK_SECRET:
        sig      = request.headers.get("X-Signature", "")
        expected = hmac.new(
            CLICKUP_WEBHOOK_SECRET.encode(), body_bytes, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=403, detail="Invalid webhook signature")

    # Resolve command — URL param wins, then fall back to tag parsing
    if not command:
        try:
            payload          = json.loads(body_bytes) if body_bytes else {}
            command, args    = _parse_clickup_tags(payload)
        except Exception:
            command, args = "", ""

    if not command:
        return {"status": "ignored", "reason": "No command found in payload or URL params"}

    background_tasks.add_task(_background_run, command, args or "")
    return {"status": "accepted", "command": command}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _parse_clickup_tags(payload: dict) -> tuple[str, str]:
    """
    Parse a ClickUp taskTagUpdated webhook payload and return (command, args).
    Looks for tags in the format run:<shorthand>.
    """
    for item in payload.get("history_items", []):
        name = item.get("data", {}).get("name", "").lower().strip()
        if not name.startswith("run:"):
            continue
        tag = name.removeprefix("run:")
        if tag == "briefing":
            return "morning-briefing", ""
        if tag == "pipeline":
            return "pipeline", ""
        if tag in ("coo", "cfo", "cpo", "cmo"):
            return "c-suite", tag
        if tag.startswith("deal-"):
            company = tag.removeprefix("deal-").replace("-", " ")
            return "deal", company
    return "", ""


def _background_run(command: str, args: str) -> None:
    """Background task: dispatch to agent, then email the result."""
    client = get_client()
    result = dispatch(client, command, args)
    if result:
        today   = date.today().strftime("%A, %B %-d, %Y")
        subject = f"Prometheus iQ — {command.replace('-', ' ').title()} | {today}"
        deliver(subject, result)
