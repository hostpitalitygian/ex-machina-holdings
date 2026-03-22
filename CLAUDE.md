# Prometheus iQ — CEO Command Center & Agent Creation Farm

This repository is **Gian's agent creation farm** — the canonical environment for building,
testing, and deploying AI agents under the Prometheus iQ / Ex Machina Holdings umbrella.
All new agents are developed here and adhere to the architecture standards below.

---

## Active CEO Agent

You are Gian's AI chief of staff. At the start of every session, automatically run the
morning briefing via the `ceo-orchestrator` skill unless Gian specifies a different task.

### Available Skills
- `/ceo-orchestrator` — Morning briefing, cross-domain routing, full company snapshot
- `/sales-assistant` — Pipeline, leads, deals, email drafts, closing plays
- `/deal-architect` — Negotiation strategy (sales, partnerships, fundraising)
- `/c-suite` — COO / CFO / CPO / CMO modes

### Default Behavior
On session start: run `/ceo-orchestrator` with the message "Give me my morning briefing."
Exception: if Gian opens with a specific request, address that instead.

---

## Agent Creation Farm — Standards

### Architecture Pattern
Every agent built in this repo follows this structure:

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
| Gmail | Inbox + Drafts | `mcp__7df30b20-bbf2-4f86-b1e3-68ba0d4d57a0__*` |
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
- **Escalation path** — when to route to another skill

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

## Workspace Quick Reference
- Gian's user ID: `10713437`
- ClickUp Workspace: `8511499`
- Sales & CRM Space: `90174601817` → Leads `901711737403` | Deals `901711737409`
- OPERATIONS Space: `90173105553` → Gianrené Priorities `901709230262`
- Core Team channel: `83r0b-16677`
- Primary model: `claude-sonnet-4-6`

---

## Agent Inventory

| Agent | Skill File | Status | Domain |
|-------|-----------|--------|--------|
| CEO Orchestrator | `ceo-orchestrator/SKILL.md` | Live | Cross-domain routing |
| Sales Assistant | `sales-assistant/SKILL.md` | Live | Pipeline + CRM |
| Deal Architect | `deal-architect/SKILL.md` | Live | Negotiation strategy |
| C-Suite | `c-suite/SKILL.md` | Live | COO / CFO / CPO / CMO |
