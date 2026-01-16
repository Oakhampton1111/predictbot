# Installation Guide

Complete guide to installing and configuring the PredictBot trading stack.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Installation](#detailed-installation)
4. [Configuration](#configuration)
5. [First Run](#first-run)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Disk | 10 GB | 20 GB |
| OS | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04 LTS |

### Required Software

1. **Docker** (20.10+)
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # Add user to docker group
   sudo usermod -aG docker $USER
   
   # Verify installation
   docker --version
   ```

2. **Docker Compose** (2.0+)
   ```bash
   # Usually included with Docker Desktop
   # Or install separately:
   sudo apt-get install docker-compose-plugin
   
   # Verify installation
   docker compose version
   ```

3. **Git**
   ```bash
   sudo apt-get install git
   git --version
   ```

4. **Python 3.10+** (for validation scripts)
   ```bash
   sudo apt-get install python3 python3-pip
   pip3 install pyyaml
   ```

### Required Accounts

Before installation, create accounts on:

- [ ] [Polymarket](https://polymarket.com/) - Crypto prediction market
- [ ] [Kalshi](https://kalshi.com/) - Regulated event exchange
- [ ] [Manifold Markets](https://manifold.markets/) - Play-money market
- [ ] [OpenAI](https://platform.openai.com/) - For AI trading (optional)

See [API Setup Guide](api-setup.md) for detailed instructions.

---

## Quick Start

For experienced users who want to get started quickly:

```bash
# 1. Clone repository
git clone https://github.com/yourusername/predictbot-stack.git
cd predictbot-stack

# 2. Initialize submodules
git submodule update --init --recursive

# 3. Configure environment
cp .env.template .env
nano .env  # Edit with your API keys

# 4. Copy config
cp config/config.example.yml config/config.yml

# 5. Validate configuration
python3 scripts/validate_secrets.py
python3 scripts/validate_config.py

# 6. Build and start (dry run mode)
docker compose --profile full build
docker compose --profile full up -d

# 7. Check status
docker compose ps
docker compose logs -f
```

---

## Detailed Installation

### Step 1: Clone the Repository

```bash
# Clone the main repository
git clone https://github.com/yourusername/predictbot-stack.git
cd predictbot-stack

# Initialize all submodules (trading bot components)
git submodule update --init --recursive
```

This will download:
- Polymarket arbitrage bot (Rust)
- Polymarket market maker (Python)
- Polymarket spike bot (Python)
- Kalshi AI trading bot (Python)
- Manifold market maker (Node.js)
- MCP server (Rust)
- Polyseer research assistant (TypeScript)

### Step 2: Create Environment File

```bash
# Copy the template
cp .env.template .env

# Set secure permissions
chmod 600 .env

# Edit with your credentials
nano .env
```

**Required variables to set:**

```bash
# Polymarket (if using arbitrage, MM, or spike)
POLY_PRIVATE_KEY=0x...  # Your wallet private key
POLY_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_ID

# Kalshi (if using arbitrage or AI trading)
KALSHI_API_KEY=your_key
KALSHI_API_SECRET=your_secret

# Manifold (if using Manifold MM)
MANIFOLD_API_KEY=your_key
MANIFOLD_USERNAME=your_username

# AI Services (if using AI trading)
OPENAI_API_KEY=sk-...

# IMPORTANT: Keep dry run enabled initially!
DRY_RUN=1
```

### Step 3: Create Strategy Configuration

```bash
# Copy example config
cp config/config.example.yml config/config.yml

# Edit strategy parameters
nano config/config.yml
```

Key settings to review:
- `global.total_bankroll` - Your total trading capital
- `arbitrage.min_profit` - Minimum profit threshold
- `risk_management.global.max_daily_loss` - Daily loss limit

### Step 4: Validate Configuration

```bash
# Validate secrets
python3 scripts/validate_secrets.py --verbose

# Validate strategy config
python3 scripts/validate_config.py --config config/config.yml
```

Both scripts should show ✅ for successful validation.

### Step 5: Build Docker Images

```bash
# Build all images (this may take 10-15 minutes)
docker compose --profile full build

# Or build specific profiles:
docker compose --profile arbitrage build
docker compose --profile market-making build
docker compose --profile ai-trading build
```

### Step 6: Start Services

```bash
# Start all services
docker compose --profile full up -d

# Or start specific strategies:
docker compose --profile arbitrage up -d      # Arbitrage only
docker compose --profile market-making up -d  # Market making only
docker compose --profile ai-trading up -d     # AI trading only
```

### Step 7: Verify Startup

```bash
# Check container status
docker compose ps

# View logs
docker compose logs -f

# Check specific service
docker compose logs -f kalshi-ai
```

---

## Configuration

### Profile Options

| Profile | Services Included |
|---------|-------------------|
| `full` | All services |
| `arbitrage` | Polymarket-Kalshi arbitrage bot |
| `market-making` | Polymarket MM + Manifold MM |
| `ai-trading` | Kalshi AI + MCP server + Polyseer |
| `spike-trading` | Polymarket spike bot |

### Environment Variables Reference

See [.env.template](../.env.template) for complete list.

### Strategy Configuration Reference

See [config.example.yml](../config/config.example.yml) for all options.

---

## First Run

### Dry Run Testing

**Always start with DRY_RUN=1!**

1. Ensure `.env` has `DRY_RUN=1`
2. Start services
3. Monitor logs for 24-48 hours
4. Verify no errors occur
5. Check that strategies are detecting opportunities

```bash
# Watch for arbitrage opportunities
docker compose logs -f polymarket-arb | grep -i "opportunity\|arb"

# Watch AI trading decisions
docker compose logs -f kalshi-ai | grep -i "trade\|signal"
```

### Switching to Live Trading

**Only after successful dry run testing:**

1. Stop all services
   ```bash
   docker compose down
   ```

2. Update environment
   ```bash
   # Edit .env
   DRY_RUN=0
   ```

3. Set conservative limits
   ```bash
   MAX_DAILY_LOSS=20.0  # Start small
   ```

4. Restart with one strategy first
   ```bash
   docker compose --profile arbitrage up -d
   ```

5. Monitor closely for first few hours

---

## Verification

### Health Checks

```bash
# Check orchestrator health
curl http://localhost:8080/health

# Check system status
curl http://localhost:8080/status

# Check risk status
curl http://localhost:8080/risk
```

### Log Monitoring

```bash
# All logs
docker compose logs -f

# Specific service
docker compose logs -f kalshi-ai

# Filter for errors
docker compose logs | grep -i error

# Filter for trades
docker compose logs | grep -i "trade\|order\|fill"
```

### Dashboard Access

- **Kalshi AI Dashboard**: http://localhost:8000
- **Orchestrator API**: http://localhost:8080

---

## Troubleshooting

### Common Issues

#### Container won't start

```bash
# Check logs for errors
docker compose logs polymarket-arb

# Rebuild the image
docker compose build polymarket-arb

# Check resource usage
docker stats
```

#### API connection errors

1. Verify API keys are correct
2. Check network connectivity
3. Verify IP is not blocked/rate limited
4. Check API service status

#### "Insufficient funds" errors

1. Check wallet/account balance
2. Verify funds are on correct network (Polygon for Polymarket)
3. Ensure enough gas (MATIC) for transactions

#### High memory usage

```bash
# Check memory per container
docker stats

# Reduce limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 256m
```

### Getting Help

1. Check logs: `docker compose logs -f`
2. Review [Troubleshooting Guide](troubleshooting.md)
3. Check GitHub issues
4. Review platform-specific documentation

### Emergency Stop

```bash
# Stop all trading immediately
curl -X POST http://localhost:8080/trading/stop

# Or stop all containers
docker compose down
```

---

## Next Steps

After successful installation:

1. ✅ Run in dry mode for 24-48 hours
2. ✅ Review logs for any errors
3. ✅ Verify strategies are working correctly
4. ✅ Set conservative risk limits
5. ✅ Enable live trading with small amounts
6. ✅ Gradually increase capital as confidence grows

See [Security Best Practices](security.md) for operational guidelines.
