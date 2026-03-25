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
| **Peer-Triggered Agent** | Invoked by another skill at the end of a workflow | `prospect-email` (post-sales-assistant) |
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

### 2. Prospect Email Agent (Live)

**Purpose:** Batch personalized outbound email campaigns to sales prospects.

**Type:** Peer-Triggered — activated by `sales-assistant` after Gian approves outreach.

**Invocation pattern:**
```
sales-assistant (pipeline review + Gian approves outreach)
    → sales-assistant invokes prospect-email skill
        → Prospect Email Agent runs autonomously
```

**Full Workflow:**

**Step 1 — Batch pull all leads**
Pull entire Leads list from ClickUp (`901711737403`). For each lead, fetch the full
task (description, BANT, custom fields) + all comments (call notes, meeting history).
Do not go lead-by-lead interactively — run everything in batch before doing anything else.

**Step 2 — Build each lead's profile**
Extract: company, contact info, PMS, property count, industry, deal value, BANT answers,
call notes, and data richness classification (RICH / PARTIAL / SPARSE).

**Step 3 — Segment into ICPs**
Group leads into ICP buckets using `references/icp-profiles.md`:
- ICP 1: Growing Operator (15–40 properties)
- ICP 2: Professional Manager (40–65 properties)
- ICP 3: Tech Evaluator / PMS Migrator
- ICP 4: Boutique / Hospitality Operator
- ICP 5: Past / Returning Contact
- No Data: Generic Outreach

**Step 4 — Craft personalized emails**
Using `references/email-structure.md`:
- RICH leads → fully personalized (call notes, pain points, PMS, BANT timeline)
- PARTIAL leads → semi-personalized (available fields + ICP inference)
- SPARSE leads → generic template for their ICP bucket
Each email includes a Personalization Map annotation showing which lines used live data
vs. template defaults and where personalization was injected.

**Step 5 — Present + report for approval**
Present all emails grouped by ICP. At the end, produce an ICP Report detailing:
- ICPs identified + lead count per segment
- Email structure and angle used per ICP
- Personalization injection points
- Coverage breakdown (RICH / PARTIAL / SPARSE)
Add every drafted email to the lead's ClickUp task as a comment and @mention Gian.
Wait for explicit approval before sending anything.

**Step 6 — Send via Resend (post-approval)**
Send from: `communications@prometheusiq.io`
Reply-to: `gian@prometheusiq.io`
Send sequentially, confirm each send. Uses `RESEND_API_KEY` from `.env`.

**Step 7 — Post-send actions**
- Log sent email as ClickUp comment on the lead's task (@mention Gian)
- If lead status is `new lead` → update to `engaged`
- Cold prospects not yet in CRM: send email, then flag for Gian's attention.
  After Gian confirms positive response → invoke `project-navigator` to create lead task.

---

### 3. Project Navigator (Planned)

**Purpose:** Creates lead tasks in the appropriate ClickUp space when a cold prospect
responds positively to outreach and is ready to enter the CRM.

**Trigger:** Invoked by Gian (or eventually by `prospect-email`) after confirming a
positive reply from a cold prospect.

**Scope:**
- Determine correct ClickUp Space and List based on lead context
- Create a properly structured lead task (description, BANT template, custom fields)
- Assign to Gian and set initial status to `new lead`
- Log the origin (outbound email → positive reply) in task comments

**Status:** Planned — build begins after Prospect Email Agent is battle-tested.

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
| ClickUp | CRM + PM + Chat | `mcp__e4ae1068-c27a-42da-aa33-333134d7d3a9__*` |
| Gmail | Inbox + Drafts | `mcp__7df30b20-bbf2-4f86-b1e3-68ba0d4d57a0__*` |
| Google Calendar | Scheduling | `mcp__9df9ec5e-11f5-4538-993b-7fc0189be9d0__*` |
| Canva | Design + Content | `mcp__5d6fd19a-3274-4857-a500-594d63ce3251__*` |
| Resend | Transactional email send | REST API via WebFetch — key: `RESEND_API_KEY` in `.env` |

**Resend send address:** `communications@prometheusiq.io` (must be verified in Resend dashboard)
**Resend reply-to:** `gian@prometheusiq.io`

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
| Prospect Email Agent | Peer-Triggered | `prospect-email/SKILL.md` | Live | `sales-assistant` |
| Project Navigator | Peer-Triggered | `project-navigator/SKILL.md` | Planned | `prospect-email` / Gian |

---

## Workspace Quick Reference
- Gian's user ID: `10713437`
- Gian's email: `gian@prometheusiq.io`
- ClickUp Workspace: `8511499`
- Sales & CRM Space: `90174601817` → Leads `901711737403` | Deals `901711737409`
- OPERATIONS Space: `90173105553` → Gianrené Priorities `901709230262`
- Core Team channel: `83r0b-16677`
- Primary model: `claude-sonnet-4-6`
- Outbound email sender: `communications@prometheusiq.io` (Resend — domain must be verified)
