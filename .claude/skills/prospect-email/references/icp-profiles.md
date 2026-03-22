# ICP Profiles — Prometheus iQ

These profiles define the ideal customer segments for Prometheus iQ.
The Prospect Email Agent uses these to segment leads and select the right email angle.

> **Source:** Derived from sales strategy and CRM data. Update this file when the
> full sales strategy doc is available or when new segments emerge from field data.

---

## Core ICP Definition

**Who Prometheus iQ is built for:**
STR (short-term rental) property managers and operators managing **10–65 properties**
who need professional-grade revenue intelligence without hiring a full RM team.

**Why they buy:**
They're leaving money on the table because their pricing is manual, reactive, or
based on gut feel. They can't afford a dedicated revenue manager but they're competing
against operators who have one.

**Why they stay:**
Direct PMS integration means no manual work. The platform surfaces insights they
couldn't see before — demand spikes, comp set pricing, seasonal patterns — and
translates them into actionable pricing decisions.

---

## ICP Segments

### ICP 1: The Growing Operator
**Profile:**
- 15–40 properties
- Managing growth and feeling the scaling pain
- Pricing is inconsistent across their portfolio
- PMS: Guesty, Hospitable, OwnerRez (most common)
- Pain: "I'm spending too much time on pricing and I'm still not confident I'm right"

**What they respond to:**
- Revenue uplift framing ("operators like you see X% improvement")
- Time-saving angle ("automated recommendations, not more dashboards")
- Peer validation ("other operators on [their PMS] are already using this")

**Tone:** Peer-to-peer. Gian speaks the same language — mention the STR grind directly.

**CTA type:** Low-friction — "15-minute call to see if it fits your portfolio"

---

### ICP 2: The Professional Manager
**Profile:**
- 40–65 properties
- Operates more like a business, has staff
- May already use some pricing tools (Wheelhouse, PriceLabs) but finds them limited
- Looking for competitive intelligence, not just base pricing
- PMS: Guesty Pro, LiveRez, Track

**What they respond to:**
- Competitive intelligence angle ("know what your comp set is doing in real time")
- Portfolio-level view ("one dashboard across all your markets")
- Integration depth ("connects directly to [their PMS], no exports")

**Tone:** Professional, data-forward. Reference their scale — they think in portfolio terms.

**CTA type:** Demo request — "I'll show you what your market looks like inside the platform"

---

### ICP 3: The PMS-Migrator / Tech Evaluator
**Profile:**
- In the process of switching PMS or evaluating new tools
- Actively building their tech stack
- More tech-savvy than average STR operator
- May have more than 65 properties but fits profile otherwise

**What they respond to:**
- Integration-first messaging ("built to work alongside your PMS, not replace it")
- Timing angle ("if you're already rethinking your stack, add revenue intelligence now")
- Future-proof framing ("most operators add this after they're settled on a PMS — you can start right")

**Tone:** Tech-savvy peer. Skip the basics, go straight to integration and stack positioning.

**CTA type:** Technical demo — "let me show you how the integration actually works"

---

### ICP 4: The Boutique / Hospitality Operator
**Profile:**
- Manages fewer than 15 properties but in premium/boutique segment
- Higher ADR, lower volume — revenue per property matters more
- May not self-identify as "STR operator" — uses words like "vacation rental", "boutique stays"
- Industry tag: Hospitality

**What they respond to:**
- Premium positioning ("built for operators who care about revenue quality, not just occupancy")
- ADR and RevPAR framing, not just occupancy
- White-glove experience angle

**Tone:** Elevated. Less "grind", more "craft of hospitality".

**CTA type:** Introductory call — "I'd love to learn about your properties before showing you the platform"

---

### ICP 5: Past / Returning Contact
**Profile:**
- Previous interaction with Gian or team (past HMG client, prior demo, old lead)
- Has context on the company — don't treat them as cold
- May have churned, paused, or gone quiet

**What they respond to:**
- Acknowledgment of the prior relationship ("we've evolved a lot since we last spoke")
- What's new angle ("since [last interaction], we've added [X]")
- Re-engagement without awkwardness

**Tone:** Warm and direct. Don't pretend they're a new lead.

**CTA type:** "Worth a quick catch-up?" — low pressure, references shared history

---

### No Data — Generic Outreach
**Profile:**
- Prospect is in the CRM but has no call notes, no BANT data, and minimal custom fields filled
- Or is a cold contact not yet in ClickUp

**Approach:**
- Use the generic template from `email-structure.md`
- Personalize only name and company
- Goal: get a reply or a call, not to close

**Tone:** Short, curious, easy to respond to.

**CTA type:** Single open question — "What's your current setup for pricing?" or "Are you managing pricing manually right now?"

---

## Segmentation Decision Logic

Use this decision tree when assigning a lead to an ICP:

1. Is there a prior relationship or past interaction? → **ICP 5: Returning Contact**
2. Is their industry "Hospitality" with <15 properties? → **ICP 4: Boutique**
3. Are they in a PMS migration or actively evaluating tools? → **ICP 3: Tech Evaluator**
4. Do they have 40–65 properties? → **ICP 2: Professional Manager**
5. Do they have 15–40 properties? → **ICP 1: Growing Operator**
6. Property count unknown or <15 with no hospitality signal → **No Data / Generic**

When in doubt between two ICPs, default to the one with the more specific email angle.
A slightly wrong ICP is better than a generic email.
