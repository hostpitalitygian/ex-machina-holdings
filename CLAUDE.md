# Prometheus iQ — Agent Creation Farm

This repository is **Gian's agent creation farm** under Ex Machina Holdings.
It hosts, builds, and ships AI agents across all business domains — not just CEO-level orchestration.
Agents here can be autonomous, skill-triggered, event-driven, or peer-invoked by other skills.

---

## Agent Architecture Types

| Type | Description | Example |
|------|-------------|---------|
| **Orchestrator** | Routes across domains, synthesizes multi-agent output | `ceo-orchestrator` |
| **Skill Agent** | Invoked directly by Gian via `/skill` | `sales-assistant`, `c-suite` |
| **Peer-Triggered Agent** | Invoked by another skill at the end of a workflow | Email Sender (post-sales-assistant) |
| **Autonomous Agent** | Runs on a schedule or webhook without human prompt | Morning briefing via GitHub Actions |

---

## Active Agents

### 1. CEO Command Center (Live)

Gian's AI chief of staff. At the start of every session, automatically run the
morning briefing via the `ceo-orchestrator` skill unless Gian specifies a different task.

**Skills:**
- `/ceo-orchestrator` — Morning briefing, cross-domain routing, full company snapshot
- `/sales-assistant` — Pipeline, leads, deals, email drafts, closing plays
- `/deal-architect` — Negotiation strategy (sales, partnerships, fundraising)
- `/c-suite` — COO / CFO / CPO / CMO modes

**Default Behavior:**
On session start: run `/ceo-orchestrator` with the message "Give me my morning briefing."
Exception: if Gian opens with a specific request, address that instead.

---

### 2. Prospect Email Agent (In Design)

**Purpose:** Send personalized outbound emails to sales prospects.

**Trigger:** Peer-invoked — this agent activates **after** Gian has discussed the outreach
process with `/sales-assistant`. The sales assistant surfaces the prospect, the context,
and the angle; then hands off to this agent to compose and send via Gmail.

**Invocation pattern:**
```
sales-assistant (surfaces prospect + talking points)
    → Gian approves outreach
        → Prospect Email Agent (drafts + sends personalized email via Gmail MCP)
```

**Scope:**
- Pull prospect data from ClickUp CRM (Leads list `901711737403`)
- Personalize email body based on lead context, industry, and last interaction
- Send via Gmail MCP or save as draft for Gian's review (configurable)
- Log outreach back to ClickUp as a task comment or status update

**Status:** Designing — build begins next session.

---

## Agent Creation Farm — Standards

### Folder Structure
Every agent follows this layout:

```
.claude/
  skills/
    <agent-name>/
      SKILL.md              # Trigger conditions, persona, output format
      references/           # Domain-specific context files
  hooks/
    session-start.sh        # Auto-runs on every session
  settings.json             # Permissions + hook wiring
src/
  <agent-name>.py           # Autonomous/server-side logic (if needed)
CLAUDE.md                   # This file — master context
```

### MCP Connectors (always live)
| Connector | Purpose | Permission Pattern |
|-----------|---------|-------------------|
| ClickUp | CRM + Slack + PM | `mcp__e4ae1068-c27a-42da-aa33-333134d7d3a9__*` |
| Gmail | Inbox + Drafts + Send | `mcp__7df30b20-bbf2-4f86-b1e3-68ba0d4d57a0__*` |
| Google Calendar | Scheduling | `mcp__9df9ec5e-11f5-4538-993b-7fc0189be9d0__*` |
| Canva | Design + Content | `mcp__5d6fd19a-3274-4857-a500-594d63ce3251__*` |

### Session Hook Standard
`session-start.sh` must:
1. Install Python deps silently (`anthropic` required for autonomous orchestration)
2. Print a context banner Claude reads to orient the session
3. Exit cleanly (`set -euo pipefail`)

### Skill (SKILL.md) Standard
Each skill file must define:
- **Persona** — who Claude is acting as
- **Trigger conditions** — exact phrases and intent patterns
- **Data sources** — which MCPs to query and in what order
- **Output format** — headers, bullets, tables, tone
- **Handoff / escalation** — when and how to invoke a peer agent or route elsewhere

### Settings Standard
`settings.json` must:
- Allow `Skill` tool unconditionally
- Allow all four MCP connector patterns with `*` wildcard
- Wire `SessionStart` hook to `.claude/hooks/session-start.sh`
- Use schema: `https://json.schemastore.org/claude-code-settings.json`

### Branch Convention
- Feature branches: `claude/<agent-name>-<session-id>`
- Never push to main without a tested skill + hook

---

## Agent Inventory

| Agent | Type | Skill File | Status | Invoked By |
|-------|------|-----------|--------|------------|
| CEO Orchestrator | Orchestrator | `ceo-orchestrator/SKILL.md` | Live | Session start / Gian |
| Sales Assistant | Skill Agent | `sales-assistant/SKILL.md` | Live | Gian |
| Deal Architect | Skill Agent | `deal-architect/SKILL.md` | Live | Gian |
| C-Suite | Skill Agent | `c-suite/SKILL.md` | Live | Gian |
| Prospect Email Agent | Peer-Triggered | `prospect-email/SKILL.md` | In Design | `sales-assistant` |

---

## Workspace Quick Reference
- Gian's user ID: `10713437`
- ClickUp Workspace: `8511499`
- Sales & CRM Space: `90174601817` → Leads `901711737403` | Deals `901711737409`
- OPERATIONS Space: `90173105553` → Gianrené Priorities `901709230262`
- Core Team channel: `83r0b-16677`
- Primary model: `claude-sonnet-4-6`
