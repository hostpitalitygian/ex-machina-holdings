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
import smtplib
from datetime import date
from pathlib import Path
from email.mime.text import MIMEText
from typing import Optional

import anthropic
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Header
from pydantic import BaseModel
from dotenv import load_dotenv

# ── Bootstrap ─────────────────────────────────────────────────────────────────
# Load .env from project root regardless of where uvicorn is launched
load_dotenv(Path(__file__).parent.parent / ".env")

# Make orchestrator importable
sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import run_agent, LEADS_LIST, DEALS_LIST, WORKSPACE_ID

# ── Config ────────────────────────────────────────────────────────────────────
API_SECRET_TOKEN       = os.environ.get("API_SECRET_TOKEN", "")
CLICKUP_WEBHOOK_SECRET = os.environ.get("CLICKUP_WEBHOOK_SECRET", "")
GMAIL_FROM             = os.environ.get("GMAIL_FROM", "")
GMAIL_TO               = os.environ.get("GMAIL_TO", "")
GMAIL_APP_PASSWORD     = os.environ.get("GMAIL_APP_PASSWORD", "")

OPERATIONS_LIST  = "901709230262"
FUNDRAISING_LIST = "901709230268"
INVESTOR_LIST    = "901708451528"

app = FastAPI(title="Prometheus iQ CEO Agent", version="1.0.0")


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


# ── Email ─────────────────────────────────────────────────────────────────────
def send_email(subject: str, body: str) -> bool:
    """Send a plain-text email via Gmail SMTP (App Password auth)."""
    if not all([GMAIL_FROM, GMAIL_TO, GMAIL_APP_PASSWORD]):
        print("[email] Skipped — set GMAIL_FROM, GMAIL_TO, GMAIL_APP_PASSWORD in .env")
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"]    = GMAIL_FROM
        msg["To"]      = GMAIL_TO
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
            srv.login(GMAIL_FROM, GMAIL_APP_PASSWORD)
            srv.sendmail(GMAIL_FROM, [GMAIL_TO], msg.as_string())
        print(f"[email] Sent: {subject}")
        return True
    except Exception as e:
        print(f"[email] Error: {e}")
        return False


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
            f"Pull live data from ClickUp: "
            f"(1) Leads [{LEADS_LIST}] — overdue or stuck, "
            f"(2) Deals [{DEALS_LIST}] — anything needing attention, "
            f"(3) My priorities [{OPERATIONS_LIST}]. "
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
        "email_configured": bool(GMAIL_APP_PASSWORD),
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

    emailed = False
    if body.email:
        today   = date.today().strftime("%A, %B %-d, %Y")
        subject = f"Prometheus iQ — {body.command.replace('-', ' ').title()} | {today}"
        emailed = send_email(subject, result)

    return {"status": "ok", "command": body.command, "emailed": emailed, "result": result}


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
        send_email(subject, result)
