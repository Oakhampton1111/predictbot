# Quick Start Guide

This guide will help you get PredictBot Stack running in under 15 minutes.

## Prerequisites

### Required Software

| Software | Minimum Version | Check Command |
|----------|-----------------|---------------|
| Docker | 20.10+ | `docker --version` |
| Docker Compose | 2.0+ | `docker compose version` |
| Git | 2.0+ | `git --version` |
| Python | 3.9+ | `python --version` |

### System Requirements

| Profile | RAM | CPU | Disk | GPU |
|---------|-----|-----|------|-----|
| Minimal | 4GB | 2 cores | 10GB | - |
| Full (no AI) | 8GB | 4 cores | 20GB | - |
| Full (with Ollama) | 16GB | 4 cores | 50GB | NVIDIA 8GB+ |

### API Keys Required

You'll need API keys for the platforms you want to trade on:

| Platform | Required For | How to Get |
|----------|--------------|------------|
| Polymarket | Arbitrage, MM, Spike | Wallet private key (MetaMask) |
| Kalshi | Arbitrage, AI Trading | [kalshi.com/settings/api](https://kalshi.com/settings/api) |
| Manifold | Market Making | [manifold.markets/api](https://manifold.markets/api) |
| OpenAI | AI Trading | [platform.openai.com](https://platform.openai.com) |
| Anthropic | AI Trading (optional) | [console.anthropic.com](https://console.anthropic.com) |

See [API Setup Guide](api-setup.md) for detailed instructions.

---

## Step 1: Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/yourusername/predictbot-stack.git
cd predictbot-stack

# Initialize all submodules (trading modules)
git submodule update --init --recursive
```

**Expected output:**
```
Cloning into 'predictbot-stack'...
Submodule 'modules/polymarket_arb' registered...
Submodule 'modules/kalshi_ai' registered...
...
Submodule path 'modules/polymarket_arb': checked out '...'
```

---

## Step 2: Run Setup Script

```bash
# Make setup script executable
chmod +x scripts/setup.sh

# Run setup
./scripts/setup.sh
```

The setup script will:
- Create necessary directories (`logs/`, `data/`)
- Copy configuration templates
- Check Docker installation
- Verify submodules are initialized

---

## Step 3: Configure Environment

```bash
# Copy the environment template
cp .env.template .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

### Minimum Configuration for First Run

For a basic test run, you only need to set:

```bash
# .env - Minimum configuration

# IMPORTANT: Keep dry run enabled for testing!
DRY_RUN=1

# Database (required)
POSTGRES_PASSWORD=your_secure_password_here

# Admin Portal (required)
ADMIN_PASSWORD=your_admin_password_here
NEXTAUTH_SECRET=generate_a_random_32_char_string

# At least one platform API key
# For Polymarket:
POLY_PRIVATE_KEY=your_wallet_private_key
POLY_RPC_URL=https://polygon-rpc.com

# OR for Kalshi:
KALSHI_API_KEY=your_kalshi_api_key
KALSHI_API_SECRET=your_kalshi_api_secret

# For AI features (optional for first run):
OPENAI_API_KEY=sk-your-openai-key
```

### Generate Secure Secrets

```bash
# Generate NEXTAUTH_SECRET
openssl rand -base64 32

# Generate POSTGRES_PASSWORD
openssl rand -base64 24

# Generate ADMIN_PASSWORD
openssl rand -base64 16
```

---

## Step 4: Validate Configuration

```bash
# Validate config.yml syntax and values
python scripts/validate_config.py

# Validate secrets are properly set
python scripts/validate_secrets.py
```

**Expected output:**
```
✓ Configuration file valid
✓ All required secrets present
✓ API key format valid
⚠ Warning: DRY_RUN is enabled (paper trading mode)
```

---

## Step 5: Build Docker Images

```bash
# Build all images (first time takes 5-10 minutes)
docker compose build

# Or build specific profile
docker compose --profile full build
```

**Tip:** If you encounter build errors, check:
- Docker daemon is running: `docker info`
- Sufficient disk space: `docker system df`
- Network connectivity for pulling base images

---

## Step 6: Start Services (Dry Run Mode)

For your first run, start with the minimal profile:

```bash
# Start core services only (recommended for first run)
docker compose --profile full up -d
```

Or use the start script:

```bash
./scripts/start.sh --profile full --dry-run
```

### Available Profiles

| Profile | Services | Use Case |
|---------|----------|----------|
| `full` | All services | Production deployment |
| `arbitrage` | Arbitrage bot only | Test arbitrage strategy |
| `market-making` | MM bots only | Test market making |
| `ai-trading` | AI + MCP + Polyseer | Test AI trading |
| `spike-trading` | Spike bot only | Test spike strategy |
| `monitoring` | Prometheus, Grafana, Loki | Monitoring only |
| `admin` | Admin Portal only | Dashboard only |

---

## Step 7: Verify Services Are Running

```bash
# Check all containers are healthy
docker compose ps

# Or use health check script
./scripts/health-check.sh
```

**Expected output:**
```
NAME                    STATUS              PORTS
predictbot-orchestrator healthy             0.0.0.0:8080->8080/tcp
predictbot_postgres     healthy             0.0.0.0:5432->5432/tcp
predictbot_redis        healthy             0.0.0.0:6379->6379/tcp
predictbot_admin        healthy             0.0.0.0:3003->3000/tcp
predictbot_grafana      healthy             0.0.0.0:3002->3000/tcp
...
```

---

## Step 8: Access the Admin Portal

Open your browser and navigate to:

**http://localhost:3003**

Login with:
- **Username:** `admin` (or value of `ADMIN_USERNAME`)
- **Password:** Your `ADMIN_PASSWORD` value

### Admin Portal Pages

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | `/` | System overview, P&L summary |
| Positions | `/positions` | Current positions across platforms |
| Trades | `/trades` | Trade history and details |
| Strategies | `/strategies` | Enable/disable strategies |
| AI Insights | `/ai` | AI agent decisions and reasoning |
| Alerts | `/alerts` | Alert history and configuration |
| Settings | `/settings` | System configuration |
| Logs | `/logs` | Real-time log viewer |

---

## Step 9: View Monitoring Dashboards

### Grafana (Metrics & Dashboards)

**http://localhost:3002**

Default credentials:
- **Username:** `admin`
- **Password:** `admin` (or value of `GRAFANA_PASSWORD`)

Pre-configured dashboards:
- System Overview
- Trading Performance
- AI Insights
- Risk Dashboard

### Prometheus (Raw Metrics)

**http://localhost:9090**

Useful queries:
```promql
# Total trades today
sum(trades_total{job="orchestrator"})

# Current P&L
predictbot_pnl_total

# Service health
up{job=~"predictbot.*"}
```

---

## Step 10: View Logs

### Via Docker Compose

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f orchestrator

# Last 100 lines
docker compose logs --tail=100 orchestrator
```

### Via Grafana (Loki)

1. Open Grafana: http://localhost:3002
2. Go to Explore (compass icon)
3. Select "Loki" data source
4. Query: `{container_name=~"predictbot.*"}`

### Via Admin Portal

1. Open Admin Portal: http://localhost:3003
2. Navigate to Logs page
3. Filter by service, level, or search text

---

## Verifying Everything Works

### 1. Check Orchestrator Health

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "postgres": "connected",
    "redis": "connected",
    "event_bus": "active"
  },
  "dry_run": true
}
```

### 2. Check AI Orchestrator Health

```bash
curl http://localhost:8081/health
```

Expected response:
```json
{
  "status": "healthy",
  "agents": ["scanner", "research", "sentiment", "risk", "execution", "supervisor"],
  "llm_providers": ["openai", "ollama"]
}
```

### 3. Check Admin Portal API

```bash
curl http://localhost:3003/api/health
```

Expected response:
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected"
}
```

---

## Common Issues and Solutions

### Issue: Container fails to start

```bash
# Check container logs
docker compose logs <service-name>

# Check if port is already in use
netstat -tulpn | grep <port>

# Restart specific service
docker compose restart <service-name>
```

### Issue: Database connection failed

```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check connection
docker compose exec postgres pg_isready -U predictbot

# View PostgreSQL logs
docker compose logs postgres
```

### Issue: API key validation failed

```bash
# Re-run secrets validation
python scripts/validate_secrets.py --verbose

# Check .env file permissions
ls -la .env
```

### Issue: Out of memory

```bash
# Check Docker memory usage
docker stats

# Reduce memory limits in docker-compose.yml
# Or start with minimal profile
docker compose --profile minimal up -d
```

---

## Next Steps

1. **Read the full documentation:**
   - [Configuration Reference](configuration.md) - All configuration options
   - [Deployment Guide](deployment.md) - Production deployment
   - [Testing Guide](testing.md) - Testing strategies

2. **Configure your strategies:**
   - Edit `config/config.yml` for strategy parameters
   - Start with conservative settings

3. **Set up alerts:**
   - Configure Slack/Discord webhooks
   - Set up email notifications

4. **When ready for live trading:**
   - Thoroughly test in dry-run mode
   - Start with minimal capital
   - Set `DRY_RUN=0` in `.env`
   - Monitor closely for the first few days

---

## Quick Reference Commands

```bash
# Start all services
./scripts/start.sh --profile full

# Stop all services
./scripts/stop.sh

# View logs
docker compose logs -f

# Check health
./scripts/health-check.sh

# Backup data
./scripts/backup.sh

# Restart a service
docker compose restart <service-name>

# Rebuild and restart
docker compose up -d --build <service-name>

# Enter container shell
docker compose exec <service-name> /bin/sh

# View resource usage
docker stats
```

---

**Need help?** Check the [Troubleshooting Guide](troubleshooting.md) or open an issue on GitHub.
