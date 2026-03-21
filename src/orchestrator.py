"""
Prometheus iQ CEO Agent Orchestrator
Autonomous multi-agent system — run via: python src/orchestrator.py [command]
Commands:
  morning-briefing          Full CEO morning briefing
  pipeline                  Sales pipeline check
  deal <company>            Deal deep dive + negotiation strategy
  c-suite <coo|cfo|cpo|cmo> C-Suite mode (COO/CFO/CPO/CMO)
"""
import anthropic
import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import date
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────────────
SKILLS_DIR = Path(__file__).parent.parent / ".claude" / "skills"
MODEL = "claude-opus-4-6"
CLICKUP_BASE = "https://api.clickup.com/api/v2"
MERCURY_BASE = "https://api.mercury.com/api/v1"

WORKSPACE_ID = "8511499"
LEADS_LIST = "901711737403"
DEALS_LIST = "901711737409"
GIAN_USER_ID = "10713437"


# ── ClickUp REST helpers ──────────────────────────────────────────────────────
def _clickup_request(path: str, method: str = "GET", body: Optional[dict] = None) -> dict:
    token = os.environ.get("CLICKUP_API_TOKEN", "")
    if not token:
        return {"error": "CLICKUP_API_TOKEN not set — live data unavailable"}

    url = f"{CLICKUP_BASE}{path}"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


def get_tasks(list_id: str, include_closed: bool = False) -> dict:
    """GET /list/{list_id}/task"""
    params = "?include_closed=true" if include_closed else ""
    return _clickup_request(f"/list/{list_id}/task{params}")


def get_task(task_id: str) -> dict:
    """GET /task/{task_id}"""
    return _clickup_request(f"/task/{task_id}")


def get_task_comments(task_id: str) -> dict:
    """GET /task/{task_id}/comment"""
    return _clickup_request(f"/task/{task_id}/comment")


def search_tasks(workspace_id: str, query: str) -> dict:
    """GET /team/{workspace_id}/task?search_query={query}"""
    import urllib.parse
    q = urllib.parse.quote(query)
    return _clickup_request(f"/team/{workspace_id}/task?search_query={q}")


def search_docs(workspace_id: str, query: str) -> dict:
    """Search ClickUp Docs by keyword. Returns doc/page IDs and names."""
    import urllib.parse
    q = urllib.parse.quote(query)
    return _clickup_request(f"/workspaces/{workspace_id}/docs?search_query={q}&limit=10")


def get_doc_page(workspace_id: str, doc_id: str, page_id: str) -> dict:
    """GET the content of a specific ClickUp Doc page."""
    return _clickup_request(f"/workspaces/{workspace_id}/docs/{doc_id}/pages/{page_id}")


def create_task_comment(task_id: str, comment_text: str) -> dict:
    """POST /task/{task_id}/comment"""
    return _clickup_request(
        f"/task/{task_id}/comment",
        method="POST",
        body={"comment_text": comment_text},
    )


# ── Mercury REST helpers ─────────────────────────────────────────────────────
def _mercury_request(path: str) -> dict:
    token = os.environ.get("MERCURY_API_TOKEN", "")
    if not token:
        return {"error": "MERCURY_API_TOKEN not set — financial data unavailable. Add your Mercury API token to .env to enable CFO mode."}

    url = f"{MERCURY_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
    except Exception as e:
        return {"error": str(e), "url": url}


def get_mercury_accounts() -> dict:
    """Get all Mercury bank accounts with current balances."""
    return _mercury_request("/accounts")


def get_mercury_transactions(account_id: str, limit: str = "100", offset: str = "0") -> dict:
    """Get recent transactions for a Mercury account. Use to calculate burn rate."""
    return _mercury_request(f"/account/{account_id}/transactions?limit={limit}&offset={offset}")


# Tool registry — maps tool name → callable
TOOLS: dict = {
    "get_tasks": get_tasks,
    "get_task": get_task,
    "get_task_comments": get_task_comments,
    "search_tasks": search_tasks,
    "create_task_comment": create_task_comment,
    "search_docs": search_docs,
    "get_doc_page": get_doc_page,
    "get_mercury_accounts": get_mercury_accounts,
    "get_mercury_transactions": get_mercury_transactions,
}

# Tool schemas for the API
TOOL_SCHEMAS = [
    {
        "name": "get_tasks",
        "description": "Get all tasks from a ClickUp list.",
        "input_schema": {
            "type": "object",
            "properties": {
                "list_id": {"type": "string", "description": "ClickUp list ID"},
                "include_closed": {"type": "boolean", "description": "Include closed tasks"},
            },
            "required": ["list_id"],
        },
    },
    {
        "name": "get_task",
        "description": "Get details of a specific ClickUp task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "ClickUp task ID"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "get_task_comments",
        "description": "Get all comments on a ClickUp task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "ClickUp task ID"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "search_tasks",
        "description": "Search tasks across the ClickUp workspace.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "ClickUp workspace/team ID"},
                "query": {"type": "string", "description": "Search query string"},
            },
            "required": ["workspace_id", "query"],
        },
    },
    {
        "name": "create_task_comment",
        "description": "Post a comment on a ClickUp task.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "ClickUp task ID"},
                "comment_text": {"type": "string", "description": "Comment text to post"},
            },
            "required": ["task_id", "comment_text"],
        },
    },
    {
        "name": "search_docs",
        "description": "Search ClickUp Docs by keyword. Use this to find meeting notes, strategy docs, or any document by name or content. Returns doc IDs and page IDs needed for get_doc_page.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "ClickUp workspace ID"},
                "query": {"type": "string", "description": "Search keywords (e.g. 'meeting notes Ryan sprint')"},
            },
            "required": ["workspace_id", "query"],
        },
    },
    {
        "name": "get_doc_page",
        "description": "Get the full content of a specific ClickUp Doc page. Always prefer this over Gmail/Gemini notes for meeting context.",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_id": {"type": "string", "description": "ClickUp workspace ID"},
                "doc_id": {"type": "string", "description": "ClickUp Doc ID (from search_docs results)"},
                "page_id": {"type": "string", "description": "Page ID within the doc (from search_docs results)"},
            },
            "required": ["workspace_id", "doc_id", "page_id"],
        },
    },
    {
        "name": "get_mercury_accounts",
        "description": "Get all Mercury bank accounts with current balances. Use this in CFO mode to pull the live cash position. Returns account IDs needed for get_mercury_transactions.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_mercury_transactions",
        "description": "Get recent transactions for a Mercury bank account. Use to calculate monthly burn rate (sum outflows over 90 days, divide by 3). Also useful for spotting unusual expenses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Mercury account ID (from get_mercury_accounts)"},
                "limit": {"type": "string", "description": "Number of transactions to fetch (default '100')"},
                "offset": {"type": "string", "description": "Pagination offset (default '0')"},
            },
            "required": ["account_id"],
        },
    },
]


# ── Skill loading ─────────────────────────────────────────────────────────────
def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter (--- ... ---) from skill files."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content.strip()


def build_system_prompt(skill_name: str, extra_context: str = "") -> str:
    """Build full system prompt: skill SKILL.md + all references/*.md files."""
    skill_file = SKILLS_DIR / skill_name / "SKILL.md"
    if not skill_file.exists():
        raise FileNotFoundError(f"Skill not found: {skill_name} (looked in {skill_file})")

    prompt = strip_frontmatter(skill_file.read_text())

    # Append reference files
    refs_dir = SKILLS_DIR / skill_name / "references"
    if refs_dir.exists():
        for ref_file in sorted(refs_dir.glob("*.md")):
            prompt += f"\n\n---\n## Reference: {ref_file.stem}\n{ref_file.read_text().strip()}"

    # Append ClickUp availability note
    if not os.environ.get("CLICKUP_API_TOKEN"):
        prompt += (
            "\n\n---\n## Note: Autonomous Mode (No Live ClickUp Data)\n"
            "CLICKUP_API_TOKEN is not set. You cannot make live ClickUp API calls. "
            "Use your knowledge of the workspace structure and key IDs from the reference "
            "files to provide the best possible guidance. Flag clearly where live data "
            "would change your answer."
        )

    if extra_context:
        prompt += f"\n\n---\n## Additional Context\n{extra_context}"

    return prompt


# ── Agent runner ──────────────────────────────────────────────────────────────
def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a ClickUp tool and return result as JSON string."""
    fn = TOOLS.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = fn(**tool_input)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


def run_agent(
    client: anthropic.Anthropic,
    skill_name: str,
    user_message: str,
    extra_context: str = "",
    use_tools: bool = True,
) -> str:
    """
    Run a skill agent with the tool-use agentic loop.
    Streams output to stdout and returns the final text response.
    """
    system = build_system_prompt(skill_name, extra_context)
    messages = [{"role": "user", "content": user_message}]
    tools = TOOL_SCHEMAS if use_tools else []

    max_iterations = 10
    for iteration in range(max_iterations):
        kwargs = {
            "model": MODEL,
            "max_tokens": 16000,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                print(text, end="", flush=True)
            response = stream.get_final_message()

        # Append assistant response to history
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            print()  # trailing newline
            return next(
                (b.text for b in response.content if b.type == "text"), ""
            )

        if response.stop_reason != "tool_use":
            print()
            return next(
                (b.text for b in response.content if b.type == "text"), ""
            )

        # Execute all tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n[tool: {block.name}({json.dumps(block.input)[:80]}...)]", flush=True)
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        messages.append({"role": "user", "content": tool_results})

    print()
    return "[Max iterations reached]"


# ── Command handlers ──────────────────────────────────────────────────────────
def cmd_morning_briefing(client: anthropic.Anthropic) -> None:
    today = date.today().strftime("%A, %B %-d, %Y")
    print(f"\n{'='*60}")
    print(f"CEO MORNING BRIEFING — {today}")
    print(f"{'='*60}\n")

    run_agent(
        client,
        "ceo-orchestrator",
        (
            f"Today is {today}. Give me my full morning briefing. "
            f"Run all C-Suite personas: "
            f"(1) SALES: Leads [{LEADS_LIST}] and Deals [{DEALS_LIST}] — overdue or stuck, "
            f"(2) COO: My priorities [901709230262] + team assignments for Paula [75476326] and Ryan [95384247], "
            f"(3) CFO: Pull Mercury accounts (get_mercury_accounts) for cash position, "
            f"then transactions (get_mercury_transactions) for burn rate. "
            f"Also check Fundraising [901709230268] and Investor Outreach [901708451528]. "
            f"(4) Search ClickUp Docs for recent meeting notes (search_docs). "
            f"Synthesize into a CEO-level brief with ONE focus recommendation."
        ),
    )


def cmd_pipeline(client: anthropic.Anthropic) -> None:
    print(f"\n{'='*60}")
    print("PIPELINE CHECK")
    print(f"{'='*60}\n")

    run_agent(
        client,
        "sales-assistant",
        (
            f"Run a Pipeline Check. Pull live data from ClickUp: "
            f"Leads list [{LEADS_LIST}] and Deals list [{DEALS_LIST}]. "
            f"Flag overdue items, stuck deals (no activity in 5+ days), "
            f"and recommend the single most important follow-up action right now."
        ),
    )


def cmd_deal(client: anthropic.Anthropic, company: str) -> None:
    print(f"\n{'='*60}")
    print(f"DEAL DEEP DIVE — {company}")
    print(f"{'='*60}\n")

    print("[ Sales Intelligence ]")
    sales_context = run_agent(
        client,
        "sales-assistant",
        (
            f"Run a Deal Deep Dive on {company}. "
            f"Search ClickUp for any tasks or leads related to '{company}' "
            f"in workspace [{WORKSPACE_ID}]. "
            f"Pull all relevant deal context: stage, last contact, open items, "
            f"decision maker info. Give me the full picture."
        ),
    )

    print(f"\n{'─'*60}")
    print("[ Negotiation Strategy ]")
    run_agent(
        client,
        "deal-architect",
        f"Build a negotiation strategy for closing {company}. Context from sales intelligence:\n\n{sales_context}",
        use_tools=False,  # deal-architect works from context, not live ClickUp
    )


def cmd_c_suite(client: anthropic.Anthropic, mode: str) -> None:
    mode = mode.lower()
    valid_modes = {"coo", "cfo", "cpo", "cmo"}
    if mode not in valid_modes:
        print(f"Error: mode must be one of {', '.join(sorted(valid_modes))}")
        sys.exit(1)

    mode_labels = {"coo": "Operations & Scheduling", "cfo": "Financial Position", "cpo": "Product & Customers", "cmo": "Content & Brand"}
    print(f"\n{'='*60}")
    print(f"C-SUITE — {mode.upper()} MODE: {mode_labels[mode]}")
    print(f"{'='*60}\n")

    mode_prompts = {
        "coo": (
            "Activate COO mode. Give me an Operations Snapshot: "
            "pull Gian's priority list [901709230262] for urgent/due tasks, "
            "check what Cesia [901709232251] and team are working on, "
            "and flag any scheduling conflicts or blockers."
        ),
        "cfo": (
            "Activate CFO mode. Give me the Fundraising Readiness report: "
            "pull Fundraising tasks [901709230268] and Investor Outreach list [901708451528]. "
            "Surface the three numbers: cash position, monthly burn, current ARR. "
            "If data isn't in ClickUp, flag the gap and recommend the next step."
        ),
        "cpo": (
            "Activate CPO mode. Give me the Product Status report: "
            "pull Active Work [901709169714], Bugs & Reliability [901709230603], "
            "and User Base [901709190382]. "
            "Flag any bugs affecting active customers as Priority 1."
        ),
        "cmo": (
            "Activate CMO mode. Give me the Content & Distribution status: "
            "pull LinkedIn [901709237676], Instagram Prometheus [901709251937], "
            "Email Outreach [901709235907], and Beta Ambassadors [901708706835]. "
            "Identify what content is live, what's due, and the next content priority."
        ),
    }

    run_agent(client, "c-suite", mode_prompts[mode])


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY is required.")
        print("Set it with: export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    client = anthropic.Anthropic(api_key=api_key, base_url=base_url)

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "morning-briefing":
        cmd_morning_briefing(client)

    elif command == "pipeline":
        cmd_pipeline(client)

    elif command == "deal":
        if len(sys.argv) < 3:
            print("Usage: python src/orchestrator.py deal <company-name>")
            sys.exit(1)
        company = " ".join(sys.argv[2:])
        cmd_deal(client, company)

    elif command == "c-suite":
        if len(sys.argv) < 3:
            print("Usage: python src/orchestrator.py c-suite <coo|cfo|cpo|cmo>")
            sys.exit(1)
        cmd_c_suite(client, sys.argv[2])

    else:
        print(f"Unknown command: {command}")
        print("Available: morning-briefing, pipeline, deal <company>, c-suite <coo|cfo|cpo|cmo>")
        sys.exit(1)


if __name__ == "__main__":
    main()
