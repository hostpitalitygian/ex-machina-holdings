#!/usr/bin/env bash
# Prometheus iQ — Agent Farm one-command deploy
# Usage (from the cloned repo root):  bash deploy.sh
# Usage (first-time, no clone yet):   see README — clone first, then run this
set -euo pipefail

# ── 0. Must be run from inside the repo ───────────────────────────────────────
if [ ! -f "docker-compose.yml" ]; then
  echo "ERROR: Run this script from the repo root (where docker-compose.yml lives)."
  exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Prometheus iQ — Agent Farm Deploy                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── 1. Pull latest from origin/main ───────────────────────────────────────────
echo "→ Pulling latest code..."
git pull origin main

# ── 2. Ensure .env exists ─────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
  echo ""
  echo "ERROR: No .env file found."
  echo "  Copy the template and fill in your secrets:"
  echo ""
  echo "    cp .env.example .env"
  echo "    nano .env"
  echo ""
  exit 1
fi

# ── 3. Install Docker + Compose plugin if missing ─────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "→ Docker not found — installing..."
  curl -fsSL https://get.docker.com | sh
  # Add current user to docker group so we don't need sudo next run
  usermod -aG docker "$USER" 2>/dev/null || true
  echo "   Docker installed. You may need to log out and back in for group membership."
fi

# Verify compose plugin (ships with Docker Engine 20.10+)
if ! docker compose version &>/dev/null; then
  echo "ERROR: 'docker compose' plugin not available. Upgrade Docker Engine >= 20.10."
  exit 1
fi

# ── 4. Build image + start container ──────────────────────────────────────────
echo "→ Building image..."
docker compose build --pull

echo "→ Starting container (detached)..."
docker compose up -d

# ── 5. Health check ───────────────────────────────────────────────────────────
echo "→ Waiting for /health..."
for i in $(seq 1 12); do
  if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    break
  fi
  sleep 5
done

echo ""
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null || echo '{"status":"unreachable"}')
echo "   Health: $HEALTH"
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Agent Farm is live on :8000                       ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║   Logs:       docker compose logs -f                ║"
echo "║   Stop:       docker compose down                   ║"
echo "║   Restart:    docker compose restart                ║"
echo "║   Redeploy:   bash deploy.sh                        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
