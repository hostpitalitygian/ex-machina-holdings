#!/bin/bash
set -euo pipefail

# Install Python dependency for autonomous orchestrator
pip install anthropic --quiet --break-system-packages 2>/dev/null \
  || pip install anthropic --quiet

# Print context banner — Claude reads this at session start
echo "=== CEO SESSION START — Prometheus iQ ==="
echo "Date: $(date '+%A, %B %-d, %Y')"
echo "MCP: ClickUp ✓ | Gmail ✓ | GCal ✓ | Canva ✓"
echo "Skills: ceo-orchestrator | sales-assistant | deal-architect | c-suite"
echo "Run /ceo-orchestrator for morning briefing."
echo "========================================="
