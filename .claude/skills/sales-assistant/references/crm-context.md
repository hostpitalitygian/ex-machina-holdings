# CRM Context — Prometheus iQ ClickUp Sales & CRM
This file contains the exact IDs, field names, and structural context needed to query the Sales & CRM space without searching. Use these values directly in tool calls.
---
## User Identity
| Person | ID | Email |
|---|---|---|
| Gian (primary user) | `10713437` | gian@prometheusiq.io |
| Paula Lopez | `75476326` | paula@prometheusiq.io |
| Ryan Anderson | `95384247` | ryan@prometheusiq.io |
---
## Workspace & Space IDs
| Entity | ID |
|---|---|
| Workspace | `8511499` |
| Sales & CRM Space | `90174601817` |
---
## List IDs — Sales & CRM
| List | ID | Purpose |
|---|---|---|
| Leads | `901711737403` | Individual prospect companies being qualified |
| Deals | `901711737409` | Active deals in progress |
| Accounts | `901711737408` | Existing customer accounts |
| Contacts | `901711737402` | Individual contact records |
---
## Lead Statuses (Leads list)
These are the ClickUp statuses on lead tasks — not the same as Sales Stage (which is a custom field):
| Status | Meaning |
|---|---|
| `new lead` | Just entered the pipeline, not yet contacted or qualified |
| `engaged` | Active conversation in progress |
| `unqualified - follow-up` | Didn't qualify now but worth revisiting |
---
## Sales Stage Custom Field
**Field name:** Sales Stage
**Field ID:** `9f481349-2315-4aba-b527-204b138d352e`
**Type:** Dropdown
This field tracks where in the sales process the deal stands. It is separate from the ClickUp task status.
| Stage Name | Meaning for Prometheus iQ |
|---|---|
| Lead Qualification | Gathering basic info — is this prospect worth pursuing? |
| New Deal | Qualified and entered as an active deal opportunity |
| Discovery | Active discovery call(s) in progress — understanding their pain |
| Proposal | Proposal being prepared or already sent |
| Negotiation | Pricing/terms discussion underway |
| Contract Pending | Agreement reached, waiting on signature |
| Won | Closed — customer |
| Lost | Deal ended without closing |
---
## Key Custom Fields (available on both Leads and Deals)
| Field Name | Type | What it contains |
|---|---|---|
| Contact Name | short_text | Primary contact's full name |
| Job Title | short_text | Contact's title (e.g., CEO, VP Operations) |
| Email | email | Contact's email address |
| Phone | phone | Contact's phone number |
| Deal Value (ARR) | currency (USD) | Annual recurring revenue value of the deal |
| Value | currency (USD) | Alternative deal value field |
| Probability % | number | Estimated close probability (0–100) |
| Lead Source | dropdown | How the lead came in: Search, Content, Social Media, Email Marketing, Paid Advertising, Event, Referral |
| Industry | dropdown | Prospect's industry (Hospitality is most relevant for STR operators) |
| PMS | text | Which Property Management System they use — CRITICAL for positioning Prometheus iQ integrations |
| Property Count | dropdown | How many STR properties they manage — key for qualifying deal size |
| Drip Campaign | checkbox | Whether this lead is enrolled in a drip email sequence |
---
## Task Description Structure
Each Lead task uses a standard template with two key sections:
**Notes section** — Free-form context about the prospect. This is where Gian captures:
- Company background
- How the lead came in
- Prior relationship context (e.g., "Past HMG client returning")
- Key facts relevant to the sale
**Qualification Questions section** — BANT-style Q&A table:
- Is this lead a duplicate or part of a larger opportunity?
- Is the company still in business?
- How did you hear about us?
- What problems are you trying to solve?
- Is this problem a priority right now? Why?
- How have you tried to solve this problem in the past?
- Are you considering other solutions or companies?
- Do you have a budget for this solution?
- Who makes buying decisions at your company?
- When do you expect to make the purchasing decision?
- Do you anticipate any challenges that would keep you from moving forward?
- What is your preferred method of contact?
**Lead Qualification Framework** — BANT scoring table:
- Budget: Does their budget fit our price range?
- Authority: Can this contact influence or make the buying decision?
- Need: How urgently do they need revenue intelligence?
- Timeline: How quickly are they looking to buy?
---
## Task Comments
Comments are where **call notes and meeting updates** live. ClickUp's built-in guidance says: "Capture updates that benefit from historical tracking (e.g. attempted contacts or meeting notes) as a comment."
When pulling context for a deal, always retrieve comments with `clickup_get_task_comments` — this is where the real sales intelligence is. Comments are chronological; the most recent ones show current status.
---
## Prometheus iQ Context (for email drafting and closing plays)
**Product:** AI revenue intelligence platform for short-term rental (STR) property managers.
**ICP (Ideal Customer Profile):** STR operators managing 10–65 properties. Price-sensitive. Need to optimize pricing and revenue without hiring a full revenue management team.
**Core value prop:** Prometheus iQ gives STR operators the revenue intelligence of a professional RM team at a fraction of the cost. It integrates with their PMS to surface pricing opportunities, demand signals, and competitive benchmarks automatically.
**PMS integrations are a key buying signal.** Always note what PMS a prospect uses — it tells you whether the integration is live, in progress, or a barrier to close.
**Pricing context:** STR operators are price-sensitive. Lead with ROI and revenue uplift, not feature lists. The conversation is: "You'll earn back the subscription cost in the first month."
**Key differentiators to reference in emails:**
- Direct PMS integration (no manual data exports)
- Revenue intelligence built specifically for STR — not a generic analytics tool
- Founder-led company — Gian speaks the same language as operators
---
## Active Leads Assigned to Gian (as of last pull)
| Company | Status | Priority | Due Date | Notes |
|---|---|---|---|---|
| PMI Mountain Collection | engaged | high | April 2025 | Past HMG client returning. Contact: Linda Hoffman, CEO. ARR: $25,560. Probability: 50% |
| Beach Please Tulum | engaged | normal | April 2025 | No comments yet — needs first follow-up |
*These are cached for context — always pull fresh data at the start of a session.*
---
## Active Deals Assigned to Gian (as of last pull)
| Task | Status |
|---|---|
| Define and coordinate PMS integration validation before announcing new partnerships | Open |
| Send current Prometheus user list to Paula for personalized email outreach | Open |
*Note: These appear to be action tasks rather than deal records. Check if new deal records exist at time of query.*
