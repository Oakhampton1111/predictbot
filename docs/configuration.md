# Configuration Reference

Complete reference for all configuration options in PredictBot Stack.

## Table of Contents

- [Environment Variables (.env)](#environment-variables-env)
- [Strategy Configuration (config.yml)](#strategy-configuration-configyml)
- [Market Mappings (markets.yml)](#market-mappings-marketsyml)
- [LLM Provider Configuration](#llm-provider-configuration)
- [Alert Configuration](#alert-configuration)
- [Docker Compose Profiles](#docker-compose-profiles)

---

## Environment Variables (.env)

### Core Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DRY_RUN` | boolean | `1` | Enable paper trading mode (1=dry run, 0=live) |
| `LOG_LEVEL` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

### Database Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `POSTGRES_PASSWORD` | string | **required** | PostgreSQL password |
| `DATABASE_URL` | string | auto-generated | Full PostgreSQL connection string |
| `REDIS_URL` | string | `redis://redis:6379` | Redis connection URL |

**Example:**
```bash
POSTGRES_PASSWORD=your_secure_password
DATABASE_URL=postgresql://predictbot:your_secure_password@postgres:5432/predictbot
```

### Platform API Keys

#### Polymarket

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `POLY_PRIVATE_KEY` | string | **required** | Ethereum wallet private key |
| `POLY_RPC_URL` | string | **required** | Polygon RPC endpoint URL |

**Example:**
```bash
POLY_PRIVATE_KEY=0x1234567890abcdef...
POLY_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/your-api-key
```

**Recommended RPC Providers:**
- Alchemy: `https://polygon-mainnet.g.alchemy.com/v2/<key>`
- Infura: `https://polygon-mainnet.infura.io/v3/<key>`
- QuickNode: `https://polygon.quicknode.com/<key>`

#### Kalshi

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `KALSHI_API_KEY` | string | **required** | Kalshi API key |
| `KALSHI_API_SECRET` | string | **required** | Kalshi API secret |

**Example:**
```bash
KALSHI_API_KEY=your_kalshi_api_key
KALSHI_API_SECRET=your_kalshi_api_secret
```

#### Manifold Markets

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MANIFOLD_API_KEY` | string | **required** | Manifold API key |
| `MANIFOLD_USERNAME` | string | optional | Manifold username for identification |

**Example:**
```bash
MANIFOLD_API_KEY=your_manifold_api_key
MANIFOLD_USERNAME=your_username
```

#### PredictIt

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `PREDICTIT_USERNAME` | string | optional | PredictIt username |
| `PREDICTIT_PASSWORD` | string | optional | PredictIt password |

### AI Configuration

#### LLM API Keys

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_API_KEY` | string | optional | OpenAI API key |
| `ANTHROPIC_API_KEY` | string | optional | Anthropic API key |
| `GROQ_API_KEY` | string | optional | Groq API key |
| `XAI_API_KEY` | string | optional | xAI (Grok) API key |

**Example:**
```bash
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
GROQ_API_KEY=gsk_your-groq-key
```

#### AI Trading Parameters

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AI_MODEL` | string | `openai:gpt-4` | Default LLM model to use |
| `AI_SCAN_INTERVAL` | integer | `300` | Seconds between market scans |
| `AI_CONFIDENCE_THRESHOLD` | float | `0.6` | Minimum confidence to execute trade |
| `AI_MAX_BET` | float | `100` | Maximum bet size for AI trades |

**Example:**
```bash
AI_MODEL=openai:gpt-4-turbo
AI_SCAN_INTERVAL=300
AI_CONFIDENCE_THRESHOLD=0.65
AI_MAX_BET=50
```

#### AI Budget Limits

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OPENAI_MONTHLY_BUDGET` | float | `50` | Monthly OpenAI spend limit ($) |
| `ANTHROPIC_MONTHLY_BUDGET` | float | `30` | Monthly Anthropic spend limit ($) |
| `GROQ_MONTHLY_BUDGET` | float | `10` | Monthly Groq spend limit ($) |

### Risk Management

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MAX_DAILY_LOSS` | float | `100.0` | Stop trading if daily loss exceeds ($) |
| `MAX_TOTAL_POSITION` | float | `1000.0` | Maximum total position exposure ($) |
| `CIRCUIT_BREAKER_THRESHOLD` | integer | `5` | Consecutive failures before halt |
| `CIRCUIT_BREAKER_COOLDOWN` | integer | `300` | Cooldown period in seconds |

**Example:**
```bash
MAX_DAILY_LOSS=50
MAX_TOTAL_POSITION=500
CIRCUIT_BREAKER_THRESHOLD=3
CIRCUIT_BREAKER_COOLDOWN=600
```

### Strategy-Specific Settings

#### Arbitrage

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ARB_MIN_PROFIT` | float | `0.02` | Minimum profit threshold (2%) |
| `ARB_MAX_TRADE_SIZE` | float | `300` | Maximum trade size ($) |
| `ENABLE_ARB` | boolean | `1` | Enable arbitrage strategy |

#### Market Making (Polymarket)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MM_POLY_SPREAD_BPS` | integer | `500` | Spread in basis points (5%) |
| `MM_POLY_ORDER_SIZE` | float | `50` | Order size ($) |
| `MM_POLY_INVENTORY_LIMIT` | float | `500` | Maximum inventory ($) |
| `ENABLE_MM_POLYMARKET` | boolean | `1` | Enable Polymarket MM |

#### Market Making (Manifold)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MM_MANIFOLD_ORDER_SIZE` | float | `100` | Order size (M$) |
| `ENABLE_MM_MANIFOLD` | boolean | `1` | Enable Manifold MM |

#### Spike Trading

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SPIKE_SENSITIVITY` | float | `0.05` | Price change threshold (5%) |
| `SPIKE_STRATEGY` | string | `mean_reversion` | Strategy type |
| `SPIKE_MAX_SIZE` | float | `100` | Maximum position size ($) |
| `SPIKE_COOLDOWN` | integer | `60` | Cooldown between trades (seconds) |
| `ENABLE_SPIKE` | boolean | `1` | Enable spike trading |

**Spike Strategy Options:**
- `mean_reversion` - Bet against the spike
- `momentum` - Bet with the spike
- `hybrid` - Adaptive based on conditions

### Notification Settings

#### Slack

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SLACK_WEBHOOK_URL` | string | optional | Slack incoming webhook URL |

#### Discord

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DISCORD_WEBHOOK_URL` | string | optional | Discord webhook URL |

#### Email

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ALERT_EMAIL_ENABLED` | boolean | `false` | Enable email alerts |
| `SMTP_HOST` | string | optional | SMTP server hostname |
| `SMTP_PORT` | integer | `587` | SMTP server port |
| `SMTP_USER` | string | optional | SMTP username |
| `SMTP_PASSWORD` | string | optional | SMTP password |
| `ALERT_EMAIL_TO` | string | optional | Alert recipient email |

**Example:**
```bash
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
ALERT_EMAIL_TO=alerts@yourdomain.com
```

### Admin Portal

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ADMIN_USERNAME` | string | `admin` | Admin portal username |
| `ADMIN_PASSWORD` | string | **required** | Admin portal password |
| `NEXTAUTH_SECRET` | string | **required** | NextAuth.js secret (32+ chars) |
| `NEXTAUTH_URL` | string | `http://localhost:3003` | Admin portal URL |

### Monitoring

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GRAFANA_USER` | string | `admin` | Grafana admin username |
| `GRAFANA_PASSWORD` | string | `admin` | Grafana admin password |
| `PROMETHEUS_RETENTION` | string | `15d` | Prometheus data retention |

### Resource Limits

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CONTAINER_CPU_LIMIT` | string | `1.0` | CPU limit per container |
| `CONTAINER_MEMORY_LIMIT` | string | `512m` | Memory limit per container |

---

## Strategy Configuration (config.yml)

The `config/config.yml` file contains detailed strategy parameters.

### Full Example

```yaml
# =============================================================================
# PredictBot Stack Configuration
# =============================================================================

# Global Settings
global:
  dry_run: true
  log_level: INFO
  timezone: UTC

# -----------------------------------------------------------------------------
# Risk Management
# -----------------------------------------------------------------------------
risk:
  max_daily_loss: 100.0
  max_total_position: 1000.0
  max_position_per_market: 200.0
  circuit_breaker:
    enabled: true
    threshold: 5
    cooldown_seconds: 300

# -----------------------------------------------------------------------------
# Arbitrage Strategy
# -----------------------------------------------------------------------------
arbitrage:
  enabled: true
  platforms:
    - polymarket
    - kalshi
  min_profit_threshold: 0.02  # 2%
  max_trade_size: 300.0
  scan_interval_seconds: 10
  execution:
    slippage_tolerance: 0.005  # 0.5%
    max_retries: 3
    retry_delay_seconds: 5

# -----------------------------------------------------------------------------
# Market Making - Polymarket
# -----------------------------------------------------------------------------
market_making:
  polymarket:
    enabled: true
    spread_bps: 500  # 5%
    order_size: 50.0
    inventory_limit: 500.0
    rebalance_threshold: 0.7  # Rebalance at 70% inventory
    min_liquidity: 1000.0  # Minimum market liquidity
    markets:
      - slug: "presidential-election-2024"
        spread_bps: 300  # Tighter spread for liquid markets
      - slug: "fed-rate-decision"
        spread_bps: 400
  
  manifold:
    enabled: true
    order_size: 100.0  # M$
    markets: []  # Empty = all eligible markets

# -----------------------------------------------------------------------------
# Spike Trading
# -----------------------------------------------------------------------------
spike_trading:
  enabled: true
  sensitivity: 0.05  # 5% price change triggers
  strategy: mean_reversion  # mean_reversion, momentum, hybrid
  max_position_size: 100.0
  cooldown_seconds: 60
  lookback_window: 300  # 5 minutes
  filters:
    min_volume: 1000.0
    min_liquidity: 5000.0
    exclude_categories:
      - "sports"
      - "entertainment"

# -----------------------------------------------------------------------------
# AI Trading
# -----------------------------------------------------------------------------
ai_trading:
  enabled: true
  scan_interval_seconds: 300
  confidence_threshold: 0.6
  max_bet_size: 100.0
  
  # Model preferences (in order of preference)
  models:
    primary: "openai:gpt-4-turbo"
    fallback: "anthropic:claude-3-sonnet"
    local: "ollama:llama2:70b"
  
  # Agent configuration
  agents:
    scanner:
      enabled: true
      max_markets: 50
    research:
      enabled: true
      max_sources: 10
    sentiment:
      enabled: true
      sources:
        - twitter
        - news
        - reddit
    risk:
      enabled: true
      max_correlation: 0.7
    execution:
      enabled: true
      slippage_tolerance: 0.01
  
  # Market filters
  filters:
    min_volume: 5000.0
    min_time_to_resolution: 86400  # 1 day
    max_time_to_resolution: 2592000  # 30 days
    categories:
      include:
        - "politics"
        - "economics"
        - "technology"
      exclude:
        - "sports"
        - "entertainment"

# -----------------------------------------------------------------------------
# Notifications
# -----------------------------------------------------------------------------
notifications:
  trade_executed:
    slack: true
    discord: true
    email: false
  circuit_breaker:
    slack: true
    discord: true
    email: true
  daily_summary:
    slack: true
    discord: false
    email: true
    time: "00:00"  # UTC
  
  # Thresholds for alerts
  thresholds:
    large_trade: 100.0  # Alert on trades > $100
    daily_loss_warning: 50.0  # Warn at 50% of limit
    position_concentration: 0.5  # Warn if >50% in one market

# -----------------------------------------------------------------------------
# Scheduling
# -----------------------------------------------------------------------------
schedule:
  # Trading hours (UTC)
  trading_hours:
    start: "00:00"
    end: "23:59"
  
  # Maintenance windows
  maintenance:
    - day: sunday
      start: "04:00"
      end: "06:00"
```

### Configuration Sections

#### Global Settings

```yaml
global:
  dry_run: true          # Override DRY_RUN env var
  log_level: INFO        # DEBUG, INFO, WARNING, ERROR
  timezone: UTC          # Timezone for scheduling
```

#### Risk Management

```yaml
risk:
  max_daily_loss: 100.0           # Stop all trading
  max_total_position: 1000.0      # Total exposure limit
  max_position_per_market: 200.0  # Per-market limit
  circuit_breaker:
    enabled: true
    threshold: 5                   # Failures before trigger
    cooldown_seconds: 300          # Recovery time
```

#### Strategy-Specific

Each strategy section follows the pattern:

```yaml
strategy_name:
  enabled: true/false
  # Strategy-specific parameters
  filters:
    # Market selection criteria
  execution:
    # Trade execution parameters
```

---

## Market Mappings (markets.yml)

The `config/markets.yml` file maps equivalent markets across platforms.

### Example

```yaml
# Market mappings for cross-platform arbitrage
mappings:
  - name: "2024 Presidential Election"
    polymarket:
      slug: "will-trump-win-2024"
      condition_id: "0x..."
    kalshi:
      ticker: "PRES-24-DEM"
    predictit:
      market_id: 7456
    
  - name: "Fed Rate Decision March"
    polymarket:
      slug: "fed-rate-march-2024"
    kalshi:
      ticker: "FED-24MAR-T25"
    
  - name: "Bitcoin Price EOY"
    polymarket:
      slug: "btc-100k-2024"
    kalshi:
      ticker: "BTC-24DEC-100K"

# Category mappings
categories:
  politics:
    - "election"
    - "congress"
    - "supreme-court"
  economics:
    - "fed"
    - "inflation"
    - "gdp"
  crypto:
    - "bitcoin"
    - "ethereum"
```

---

## LLM Provider Configuration

### Model Identifiers

Format: `provider:model-name`

| Provider | Models | Example |
|----------|--------|---------|
| OpenAI | gpt-4, gpt-4-turbo, gpt-3.5-turbo | `openai:gpt-4-turbo` |
| Anthropic | claude-3-opus, claude-3-sonnet, claude-3-haiku | `anthropic:claude-3-sonnet` |
| Groq | llama2-70b, mixtral-8x7b | `groq:llama2-70b` |
| Ollama | llama2, mistral, codellama | `ollama:llama2:70b` |

### Provider Priority

Configure fallback order in `config.yml`:

```yaml
ai_trading:
  models:
    primary: "openai:gpt-4-turbo"      # First choice
    fallback: "anthropic:claude-3-sonnet"  # If primary fails
    local: "ollama:llama2:70b"         # Offline fallback
```

### Cost Optimization

```yaml
ai_trading:
  cost_optimization:
    # Use cheaper models for initial screening
    screening_model: "groq:llama2-70b"
    # Use premium models for final decisions
    decision_model: "openai:gpt-4-turbo"
    # Cache responses to reduce API calls
    cache_ttl_seconds: 3600
```

---

## Alert Configuration

### Alert Types

| Alert Type | Description | Default Channels |
|------------|-------------|------------------|
| `trade_executed` | Trade was executed | Slack, Discord |
| `trade_failed` | Trade execution failed | Slack, Discord, Email |
| `circuit_breaker` | Circuit breaker triggered | All channels |
| `daily_loss_warning` | Approaching daily loss limit | Slack, Email |
| `daily_loss_limit` | Daily loss limit reached | All channels |
| `service_down` | Service health check failed | All channels |
| `ai_low_confidence` | AI confidence below threshold | Slack |
| `position_limit` | Position limit reached | Slack, Discord |
| `daily_summary` | End of day summary | Email |

### Channel Configuration

```yaml
notifications:
  channels:
    slack:
      webhook_url: "${SLACK_WEBHOOK_URL}"
      username: "PredictBot"
      icon_emoji: ":robot_face:"
    
    discord:
      webhook_url: "${DISCORD_WEBHOOK_URL}"
      username: "PredictBot"
    
    email:
      enabled: true
      smtp:
        host: "${SMTP_HOST}"
        port: 587
        user: "${SMTP_USER}"
        password: "${SMTP_PASSWORD}"
      from: "predictbot@yourdomain.com"
      to:
        - "alerts@yourdomain.com"
```

### Alert Rules

```yaml
notifications:
  rules:
    - name: "Large Trade Alert"
      condition: "trade.amount > 100"
      channels: [slack, discord]
      priority: high
    
    - name: "Loss Warning"
      condition: "daily_pnl < -50"
      channels: [slack, email]
      priority: critical
    
    - name: "AI Decision"
      condition: "ai.confidence > 0.8"
      channels: [slack]
      priority: low
```

---

## Docker Compose Profiles

### Available Profiles

| Profile | Services Included |
|---------|-------------------|
| `full` | All services |
| `arbitrage` | polymarket-arb |
| `market-making` | polymarket-mm, manifold-mm |
| `ai-trading` | kalshi-ai, mcp-server, polyseer |
| `spike-trading` | polymarket-spike |
| `monitoring` | prometheus, grafana, loki, promtail |
| `admin` | admin_portal |
| `ai` | ollama, ai_orchestrator |

### Usage

```bash
# Start specific profile
docker compose --profile full up -d

# Start multiple profiles
docker compose --profile arbitrage --profile monitoring up -d

# Start without a profile (core services only)
docker compose up -d
```

### Custom Profiles

Add custom profiles in `docker-compose.override.yml`:

```yaml
services:
  my-custom-service:
    profiles:
      - custom
      - full
```

---

## Environment-Specific Configuration

### Development

```bash
# .env.development
DRY_RUN=1
LOG_LEVEL=DEBUG
AI_CONFIDENCE_THRESHOLD=0.5
MAX_DAILY_LOSS=10
```

### Staging

```bash
# .env.staging
DRY_RUN=1
LOG_LEVEL=INFO
AI_CONFIDENCE_THRESHOLD=0.6
MAX_DAILY_LOSS=50
```

### Production

```bash
# .env.production
DRY_RUN=0
LOG_LEVEL=INFO
AI_CONFIDENCE_THRESHOLD=0.7
MAX_DAILY_LOSS=100
```

### Loading Environment Files

```bash
# Use specific env file
docker compose --env-file .env.production up -d
```

---

## Validation

### Validate Configuration

```bash
# Validate config.yml
python scripts/validate_config.py

# Validate with verbose output
python scripts/validate_config.py --verbose

# Validate specific file
python scripts/validate_config.py --config config/config.yml
```

### Validate Secrets

```bash
# Validate .env secrets
python scripts/validate_secrets.py

# Check specific platform
python scripts/validate_secrets.py --platform polymarket
```

---

**Related Documentation:**
- [Quick Start Guide](quickstart.md) - Getting started
- [Deployment Guide](deployment.md) - Production deployment
- [API Reference](api-reference.md) - API documentation
