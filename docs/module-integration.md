# Module Integration Guide

This document explains how each cloned open-source module integrates into the PredictBot trading stack.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR (Risk Manager)                      │
│  - Health monitoring    - Circuit breakers    - Capital allocation       │
│  - Position tracking    - PnL aggregation     - Emergency stop           │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  ARBITRAGE    │         │ MARKET MAKING │         │  AI TRADING   │
│  MODULE       │         │   MODULES     │         │   MODULE      │
│               │         │               │         │               │
│ polymarket_arb│         │ polymarket_mm │         │  kalshi_ai    │
│ (Rust)        │         │ manifold_mm   │         │  (Python)     │
└───────────────┘         └───────────────┘         └───────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           TRADING PLATFORMS                              │
│     Polymarket (Polygon)    │    Kalshi    │    Manifold    │ PredictIt │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Module Responsibilities

### 1. Polymarket-Kalshi Arbitrage Bot (`polymarket_arb`)

**Source**: [terauss/Polymarket-Kalshi-Arbitrage-bot](https://github.com/terauss/Polymarket-Kalshi-Arbitrage-bot)

**Language**: Rust

**Purpose**: Detects and executes cross-platform arbitrage between Polymarket and Kalshi.

**Key Features**:
- Real-time WebSocket price monitoring on both platforms
- SIMD-accelerated arbitrage detection (sub-millisecond)
- Concurrent dual-leg order execution
- Built-in circuit breaker protection
- Market discovery with intelligent caching

**Environment Variables Required**:
```bash
# Polymarket
POLY_PRIVATE_KEY=0x...      # Ethereum wallet private key
POLY_FUNDER=0x...           # Wallet address (derived from private key)
POLY_RPC_URL=https://...    # Polygon RPC endpoint

# Kalshi
KALSHI_API_KEY=...
KALSHI_API_SECRET=...

# Configuration
DRY_RUN=1                   # 1=simulate, 0=live trading
ARB_THRESHOLD=0.98          # Minimum profit threshold
RUST_LOG=info               # Log level
```

**Integration Points**:
- Reads from `.clob_market_cache.json` for Polymarket market data
- Reads from `kalshi_team_cache.json` for market matching
- Outputs logs to stdout (captured by Docker)
- Self-contained execution engine

---

### 2. Polymarket Market Maker (`polymarket_mm`)

**Source**: [lorine93s/polymarket-market-maker-bot](https://github.com/lorine93s/polymarket-market-maker-bot)

**Language**: Python

**Purpose**: Provides liquidity on Polymarket by placing bid/ask orders.

**Key Features**:
- Inventory management with balanced YES/NO exposure
- Optimal quote placement for spread capture
- Auto-cancel/replace cycles for order management
- Risk controls for position limits
- Prometheus metrics support

**Environment Variables Required**:
```bash
# Polymarket
POLY_PRIVATE_KEY=0x...
POLY_RPC_URL=https://...

# Strategy
MM_SPREAD_BPS=500           # Spread in basis points
MM_ORDER_SIZE=50            # Order size in USD
MM_INVENTORY_LIMIT=500      # Max inventory per side
```

**Integration Points**:
- Uses Polymarket CLOB API for order placement
- Exposes Prometheus metrics on configurable port
- Logs to stdout

---

### 3. Polymarket Spike Bot (`polymarket_spike`)

**Source**: [Trust412/Polymarket-spike-bot-v1](https://github.com/Trust412/Polymarket-spike-bot-v1)

**Language**: Python

**Purpose**: Detects and trades on sudden price movements (spikes).

**Key Features**:
- Automated spike detection algorithms
- Smart order execution for quick entry/exit
- Multi-threaded for performance
- Configurable mean-reversion or momentum strategy

**Environment Variables Required**:
```bash
# Polymarket
POLY_PRIVATE_KEY=0x...
POLY_RPC_URL=https://...

# Strategy
SPIKE_SENSITIVITY=0.05      # 5% price move triggers
SPIKE_STRATEGY=mean_reversion
SPIKE_MAX_SIZE=100          # Max bet size
```

**Integration Points**:
- Monitors Polymarket WebSocket for price changes
- Executes trades via Polymarket CLOB
- Logs to stdout

---

### 4. Kalshi AI Trading Bot (`kalshi_ai`)

**Source**: [ryanfrigo/kalshi-ai-trading-bot](https://github.com/ryanfrigo/kalshi-ai-trading-bot)

**Language**: Python

**Purpose**: AI-driven trading using LLM analysis and portfolio optimization.

**Key Features**:
- Multi-agent AI framework (Forecaster, Critic, Trader)
- Kelly Criterion position sizing
- Market making + directional trading + arbitrage
- Real-time dashboard on port 8000
- SQLite database for performance tracking
- Daily AI cost limiting

**Environment Variables Required**:
```bash
# Kalshi
KALSHI_API_KEY=...
KALSHI_API_SECRET=...

# AI Services
XAI_API_KEY=...             # or OPENAI_API_KEY
OPENAI_API_KEY=sk-...

# Configuration
LIVE_TRADING=false          # or use --live flag
DAILY_AI_BUDGET=10.0        # Max daily AI spend
```

**Integration Points**:
- Exposes dashboard on port 8000
- SQLite database at `/app/data/kalshi_ai.db`
- Logs to stdout and file

---

### 5. Manifold Market Maker (`manifold_mm`)

**Source**: [manifoldmarkets/market-maker](https://github.com/manifoldmarkets/market-maker)

**Language**: TypeScript/Node.js

**Purpose**: Provides liquidity on Manifold Markets (play-money).

**Key Features**:
- EMA-based probability tracking
- Variance-adjusted spread calculation
- Automatic order management

**Environment Variables Required**:
```bash
MANIFOLD_API_KEY=...
MANIFOLD_USERNAME=...
```

**Integration Points**:
- Uses Manifold REST API
- Logs to stdout

---

### 6. MCP Server (`mcp_server`)

**Source**: [caiovicentino/polymarket-mcp-server](https://github.com/caiovicentino/polymarket-mcp-server)

**Language**: Python

**Purpose**: Model Context Protocol server for AI agent integration.

**Key Features**:
- Provides market data to AI agents
- Tool endpoints for market analysis
- Real-time data access

**Environment Variables Required**:
```bash
POLY_RPC_URL=https://...
MCP_SERVER_PORT=3000
```

**Integration Points**:
- Exposes MCP protocol on port 3000
- Used by AI trading module for data access

---

### 7. Polyseer (`polyseer`)

**Source**: [yorkeccak/Polyseer](https://github.com/yorkeccak/Polyseer)

**Language**: TypeScript/Next.js

**Purpose**: AI research assistant for market analysis.

**Key Features**:
- Multi-agent research on prediction market questions
- Web and academic search integration
- Bayesian probability aggregation

**Environment Variables Required**:
```bash
VALYU_API_KEY=...
DATABASE_PATH=/app/data/polyseer.db
```

**Integration Points**:
- Exposes web interface on port 3001
- SQLite database for caching
- Called by AI module for research

---

### 8. Predmarket SDK (`predmarket`)

**Source**: [ashercn97/predmarket](https://github.com/ashercn97/predmarket)

**Language**: Python

**Purpose**: Unified API library for Polymarket and Kalshi.

**Key Features**:
- Simplified API access
- Common interface for multiple platforms
- Data normalization

**Integration Points**:
- Used as a library by other Python modules
- Not run as a standalone service

---

## Data Flow

### 1. Market Data Flow

```
Polymarket WebSocket ──┐
                       ├──► Data Ingestion ──► Unified Data Store
Kalshi WebSocket ──────┤                              │
                       │                              ▼
Manifold REST API ─────┘                    ┌─────────────────┐
                                            │ Strategy Modules │
                                            │ (Arb, MM, Spike, │
                                            │  AI)             │
                                            └─────────────────┘
```

### 2. Trade Execution Flow

```
Strategy Module ──► Trade Signal ──► Execution Engine ──► Platform API
                                            │
                                            ▼
                                    Position Tracker
                                            │
                                            ▼
                                    Risk Manager (Orchestrator)
```

### 3. Risk Management Flow

```
All Modules ──► Logs/Metrics ──► Orchestrator
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              Position Check    PnL Check        Circuit Breaker
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
                              Risk Decision
                              (Continue/Pause/Stop)
```

---

## Environment Variable Mapping

All modules share a common `.env` file. Here's how variables map to each module:

| Variable | Arb | Poly MM | Spike | Kalshi AI | Manifold MM | MCP | Polyseer |
|----------|-----|---------|-------|-----------|-------------|-----|----------|
| `POLY_PRIVATE_KEY` | ✓ | ✓ | ✓ | - | - | - | - |
| `POLY_RPC_URL` | ✓ | ✓ | ✓ | - | - | ✓ | - |
| `KALSHI_API_KEY` | ✓ | - | - | ✓ | - | - | - |
| `KALSHI_API_SECRET` | ✓ | - | - | ✓ | - | - | - |
| `MANIFOLD_API_KEY` | - | - | - | - | ✓ | - | - |
| `OPENAI_API_KEY` | - | - | - | ✓ | - | - | - |
| `VALYU_API_KEY` | - | - | - | - | - | - | ✓ |
| `DRY_RUN` | ✓ | ✓ | ✓ | ✓ | - | - | - |

---

## Startup Sequence

The recommended startup sequence ensures dependencies are ready:

1. **MCP Server** - Provides data access for AI
2. **Polyseer** - Research assistant for AI
3. **Orchestrator** - Risk management and coordination
4. **Arbitrage Module** - Lowest latency requirement
5. **Market Making Modules** - Continuous operation
6. **Spike Trading Module** - Event-driven
7. **AI Trading Module** - Highest resource usage

This is handled automatically by Docker Compose `depends_on` configuration.

---

## Health Monitoring

Each module exposes health information:

| Module | Health Check Method |
|--------|---------------------|
| Orchestrator | HTTP `/health` on port 8080 |
| Kalshi AI | HTTP `/health` on port 8000 |
| MCP Server | HTTP `/health` on port 3000 |
| Polyseer | HTTP `/api/health` on port 3001 |
| Others | Process check via `pgrep` |

---

## Troubleshooting Integration Issues

### Module won't start
1. Check environment variables are set
2. Verify API keys are valid
3. Check Docker logs: `docker compose logs <service>`

### Modules not communicating
1. Verify Docker network connectivity
2. Check service names in docker-compose.yml
3. Ensure ports are correctly mapped

### Data not flowing
1. Check WebSocket connections in logs
2. Verify RPC endpoints are accessible
3. Check API rate limits

### Risk limits triggering
1. Review orchestrator logs
2. Check circuit breaker status
3. Verify position limits in config
