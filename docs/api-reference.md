# API Reference

Complete API documentation for PredictBot Stack services.

## Table of Contents

- [Orchestrator API](#orchestrator-api)
- [AI Orchestrator API](#ai-orchestrator-api)
- [Admin Portal API](#admin-portal-api)
- [WebSocket Events](#websocket-events)
- [Event Bus Events](#event-bus-events)
- [Authentication](#authentication)

---

## Orchestrator API

**Base URL:** `http://localhost:8080`

The Orchestrator is the central coordination service that manages risk, positions, and trading operations.

### Health & Status

#### GET /health

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "dry_run": true,
  "services": {
    "postgres": "connected",
    "redis": "connected",
    "event_bus": "active"
  }
}
```

#### GET /api/status

Get detailed system status.

**Response:**
```json
{
  "status": "running",
  "strategies": {
    "arbitrage": {"enabled": true, "status": "active"},
    "market_making_poly": {"enabled": true, "status": "active"},
    "market_making_manifold": {"enabled": true, "status": "active"},
    "spike_trading": {"enabled": true, "status": "active"},
    "ai_trading": {"enabled": true, "status": "active"}
  },
  "circuit_breaker": {
    "status": "closed",
    "failures": 0,
    "threshold": 5
  },
  "last_trade": "2024-01-15T10:30:00Z"
}
```

### Risk Management

#### GET /api/risk/status

Get current risk status.

**Response:**
```json
{
  "daily_pnl": -25.50,
  "daily_loss_limit": 100.0,
  "daily_loss_remaining": 74.50,
  "total_position": 450.0,
  "max_total_position": 1000.0,
  "position_utilization": 0.45,
  "circuit_breaker": {
    "status": "closed",
    "consecutive_failures": 0,
    "cooldown_remaining": 0
  }
}
```

#### POST /api/risk/reset

Reset daily risk counters (admin only).

**Request:**
```json
{
  "confirm": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Daily risk counters reset"
}
```

#### GET /api/circuit-breaker/status

Get circuit breaker status.

**Response:**
```json
{
  "status": "closed",
  "consecutive_failures": 2,
  "threshold": 5,
  "cooldown_seconds": 300,
  "last_triggered": null
}
```

#### POST /api/circuit-breaker/reset

Manually reset circuit breaker.

**Response:**
```json
{
  "success": true,
  "status": "closed"
}
```

### Positions

#### GET /api/positions

Get all current positions.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `platform` | string | Filter by platform (polymarket, kalshi, manifold) |
| `strategy` | string | Filter by strategy |

**Response:**
```json
{
  "positions": [
    {
      "id": "pos_123",
      "market_id": "presidential-election",
      "platform": "polymarket",
      "strategy": "arbitrage",
      "side": "yes",
      "size": 100.0,
      "entry_price": 0.52,
      "current_price": 0.55,
      "unrealized_pnl": 5.77,
      "opened_at": "2024-01-15T08:00:00Z"
    }
  ],
  "total_value": 450.0,
  "total_unrealized_pnl": 25.50
}
```

#### POST /api/positions/sync

Force synchronization of positions with exchanges.

**Response:**
```json
{
  "success": true,
  "synced_positions": 5,
  "discrepancies_found": 0
}
```

### Trades

#### GET /api/trades

Get trade history.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Number of trades (default: 50) |
| `offset` | integer | Pagination offset |
| `status` | string | Filter by status (executed, failed, simulated) |
| `strategy` | string | Filter by strategy |
| `start_date` | string | Start date (ISO 8601) |
| `end_date` | string | End date (ISO 8601) |

**Response:**
```json
{
  "trades": [
    {
      "id": "trade_456",
      "market_id": "presidential-election",
      "platform": "polymarket",
      "strategy": "arbitrage",
      "side": "buy",
      "size": 50.0,
      "price": 0.52,
      "fee": 0.25,
      "status": "executed",
      "pnl": 2.50,
      "executed_at": "2024-01-15T10:30:00Z",
      "dry_run": false
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

#### GET /api/trades/{trade_id}

Get specific trade details.

**Response:**
```json
{
  "id": "trade_456",
  "market_id": "presidential-election",
  "platform": "polymarket",
  "strategy": "arbitrage",
  "side": "buy",
  "size": 50.0,
  "price": 0.52,
  "fee": 0.25,
  "status": "executed",
  "pnl": 2.50,
  "executed_at": "2024-01-15T10:30:00Z",
  "execution_details": {
    "order_id": "0x...",
    "tx_hash": "0x...",
    "slippage": 0.002,
    "latency_ms": 150
  }
}
```

### Opportunities

#### GET /api/opportunities

Get current trading opportunities.

**Response:**
```json
{
  "opportunities": [
    {
      "type": "arbitrage",
      "market": "presidential-election",
      "platforms": ["polymarket", "kalshi"],
      "spread": 0.04,
      "potential_profit": 3.85,
      "confidence": 0.95,
      "detected_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

#### GET /api/arbitrage/opportunities

Get arbitrage-specific opportunities.

**Response:**
```json
{
  "opportunities": [
    {
      "market_name": "Presidential Election 2024",
      "polymarket": {
        "slug": "presidential-election",
        "yes_price": 0.52,
        "no_price": 0.48
      },
      "kalshi": {
        "ticker": "PRES-24-DEM",
        "yes_price": 0.48,
        "no_price": 0.52
      },
      "spread": 0.04,
      "direction": "buy_poly_sell_kalshi",
      "max_size": 300.0,
      "expected_profit": 11.54
    }
  ]
}
```

### Balances

#### GET /api/balances

Get account balances across platforms.

**Response:**
```json
{
  "balances": {
    "polymarket": {
      "usdc": 1500.0,
      "available": 1200.0,
      "in_orders": 300.0
    },
    "kalshi": {
      "usd": 2000.0,
      "available": 1800.0,
      "in_positions": 200.0
    },
    "manifold": {
      "mana": 5000.0,
      "available": 4500.0
    }
  },
  "total_usd_equivalent": 3500.0
}
```

### Metrics

#### GET /api/metrics

Get Prometheus-format metrics.

**Response:**
```
# HELP predictbot_trades_total Total number of trades
# TYPE predictbot_trades_total counter
predictbot_trades_total{strategy="arbitrage",status="executed"} 150
predictbot_trades_total{strategy="market_making",status="executed"} 500

# HELP predictbot_pnl_total Total P&L in USD
# TYPE predictbot_pnl_total gauge
predictbot_pnl_total 125.50

# HELP predictbot_position_total Total position value
# TYPE predictbot_position_total gauge
predictbot_position_total 450.0
```

#### GET /api/metrics/summary

Get metrics summary in JSON.

**Response:**
```json
{
  "period": "24h",
  "trades": {
    "total": 45,
    "executed": 42,
    "failed": 3,
    "simulated": 0
  },
  "pnl": {
    "realized": 125.50,
    "unrealized": 25.00,
    "total": 150.50
  },
  "by_strategy": {
    "arbitrage": {"trades": 15, "pnl": 45.00},
    "market_making": {"trades": 20, "pnl": 60.50},
    "spike_trading": {"trades": 5, "pnl": 10.00},
    "ai_trading": {"trades": 5, "pnl": 10.00}
  }
}
```

### Alerts

#### GET /api/alerts

Get alert history.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Number of alerts (default: 50) |
| `type` | string | Filter by alert type |
| `acknowledged` | boolean | Filter by acknowledgment status |

**Response:**
```json
{
  "alerts": [
    {
      "id": "alert_789",
      "type": "trade_executed",
      "severity": "info",
      "message": "Arbitrage trade executed: $50 profit",
      "data": {"trade_id": "trade_456"},
      "channels_sent": ["slack", "discord"],
      "created_at": "2024-01-15T10:30:00Z",
      "acknowledged": false
    }
  ]
}
```

#### POST /api/alerts/test

Send test alert.

**Request:**
```json
{
  "channel": "slack",
  "message": "Test alert from PredictBot"
}
```

**Response:**
```json
{
  "success": true,
  "channel": "slack",
  "message_id": "msg_123"
}
```

#### POST /api/alerts/{alert_id}/acknowledge

Acknowledge an alert.

**Response:**
```json
{
  "success": true,
  "alert_id": "alert_789",
  "acknowledged_at": "2024-01-15T10:35:00Z"
}
```

---

## AI Orchestrator API

**Base URL:** `http://localhost:8081`

The AI Orchestrator manages the LangGraph-based multi-agent system.

### Health & Status

#### GET /health

Check AI orchestrator health.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dry_run": true,
  "agents": [
    "scanner",
    "research",
    "sentiment",
    "risk",
    "execution",
    "supervisor"
  ],
  "llm_providers": {
    "openai": "available",
    "anthropic": "available",
    "ollama": "available"
  }
}
```

#### GET /api/providers

Get LLM provider status.

**Response:**
```json
{
  "providers": {
    "openai": {
      "status": "available",
      "model": "gpt-4-turbo",
      "requests_today": 150,
      "budget_remaining": 35.50
    },
    "anthropic": {
      "status": "available",
      "model": "claude-3-sonnet",
      "requests_today": 50,
      "budget_remaining": 22.00
    },
    "ollama": {
      "status": "available",
      "model": "llama2:70b",
      "requests_today": 200
    }
  },
  "primary": "openai",
  "fallback": "anthropic"
}
```

### Market Analysis

#### POST /api/scan

Trigger manual market scan.

**Request:**
```json
{
  "platforms": ["polymarket", "kalshi"],
  "categories": ["politics", "economics"],
  "limit": 50
}
```

**Response:**
```json
{
  "scan_id": "scan_123",
  "status": "started",
  "markets_to_scan": 50
}
```

#### GET /api/scan/{scan_id}

Get scan results.

**Response:**
```json
{
  "scan_id": "scan_123",
  "status": "completed",
  "markets_scanned": 50,
  "opportunities_found": 5,
  "duration_seconds": 45,
  "results": [
    {
      "market_id": "presidential-election",
      "platform": "polymarket",
      "score": 0.85,
      "recommendation": "analyze"
    }
  ]
}
```

#### GET /api/analyze

Analyze specific market.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `market` | string | Market ID or slug |
| `platform` | string | Platform name |

**Response:**
```json
{
  "market_id": "presidential-election",
  "platform": "polymarket",
  "analysis": {
    "current_price": 0.52,
    "fair_value_estimate": 0.58,
    "confidence": 0.75,
    "edge": 0.06,
    "recommendation": "buy",
    "size_recommendation": 50.0,
    "reasoning": "Based on recent polling data and historical patterns..."
  },
  "agent_contributions": {
    "research": {"confidence": 0.80, "summary": "..."},
    "sentiment": {"confidence": 0.70, "summary": "..."},
    "risk": {"approved": true, "max_size": 100.0}
  },
  "analyzed_at": "2024-01-15T10:30:00Z"
}
```

### Agent Management

#### GET /api/agents

Get all agent statuses.

**Response:**
```json
{
  "agents": {
    "scanner": {
      "status": "idle",
      "last_run": "2024-01-15T10:25:00Z",
      "markets_processed": 50
    },
    "research": {
      "status": "running",
      "current_market": "presidential-election",
      "sources_checked": 5
    },
    "sentiment": {
      "status": "idle",
      "last_run": "2024-01-15T10:28:00Z"
    },
    "risk": {
      "status": "idle",
      "approvals_today": 10,
      "rejections_today": 3
    },
    "execution": {
      "status": "idle",
      "trades_today": 5
    },
    "supervisor": {
      "status": "active",
      "decisions_today": 15
    }
  }
}
```

#### POST /api/agents/{agent_name}/test

Test specific agent.

**Request:**
```json
{
  "market": "presidential-election",
  "platform": "polymarket"
}
```

**Response:**
```json
{
  "agent": "research",
  "test_result": {
    "success": true,
    "output": {
      "summary": "Market analysis complete",
      "confidence": 0.80,
      "sources": ["polling_data", "news_articles", "expert_opinions"]
    },
    "duration_ms": 2500
  }
}
```

### Decisions

#### GET /api/decisions

Get AI decision history.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | integer | Number of decisions (default: 50) |
| `market` | string | Filter by market |
| `outcome` | string | Filter by outcome (trade, skip, hold) |

**Response:**
```json
{
  "decisions": [
    {
      "id": "dec_123",
      "market_id": "presidential-election",
      "platform": "polymarket",
      "outcome": "trade",
      "action": "buy",
      "size": 50.0,
      "confidence": 0.78,
      "reasoning": "Strong edge detected based on...",
      "agent_votes": {
        "research": "buy",
        "sentiment": "buy",
        "risk": "approved"
      },
      "trade_id": "trade_456",
      "decided_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### GET /api/decisions/{decision_id}

Get detailed decision information.

**Response:**
```json
{
  "id": "dec_123",
  "market_id": "presidential-election",
  "platform": "polymarket",
  "outcome": "trade",
  "full_analysis": {
    "market_data": {...},
    "research_output": {...},
    "sentiment_output": {...},
    "risk_assessment": {...},
    "execution_plan": {...},
    "supervisor_decision": {...}
  },
  "trace": [
    {"agent": "scanner", "timestamp": "...", "output": "..."},
    {"agent": "research", "timestamp": "...", "output": "..."},
    ...
  ]
}
```

### Budget

#### GET /api/budget/status

Get AI budget status.

**Response:**
```json
{
  "period": "monthly",
  "budgets": {
    "openai": {
      "limit": 50.0,
      "used": 14.50,
      "remaining": 35.50
    },
    "anthropic": {
      "limit": 30.0,
      "used": 8.00,
      "remaining": 22.00
    },
    "groq": {
      "limit": 10.0,
      "used": 2.50,
      "remaining": 7.50
    }
  },
  "total_used": 25.00,
  "total_limit": 90.0,
  "reset_date": "2024-02-01"
}
```

---

## Admin Portal API

**Base URL:** `http://localhost:3003/api`

The Admin Portal provides a web interface and API for system management.

### Authentication

#### POST /api/auth/login

Login to admin portal.

**Request:**
```json
{
  "username": "admin",
  "password": "your_password"
}
```

**Response:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_at": "2024-01-16T10:30:00Z"
}
```

### System

#### GET /api/health

Check admin portal health.

**Response:**
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected",
  "orchestrator": "connected",
  "ai_orchestrator": "connected"
}
```

#### GET /api/system/status

Get full system status.

**Response:**
```json
{
  "services": {
    "orchestrator": {"status": "healthy", "url": "http://orchestrator:8080"},
    "ai_orchestrator": {"status": "healthy", "url": "http://ai_orchestrator:8081"},
    "postgres": {"status": "healthy"},
    "redis": {"status": "healthy"}
  },
  "trading": {
    "dry_run": true,
    "active_strategies": 5,
    "open_positions": 3
  },
  "metrics": {
    "daily_pnl": 125.50,
    "trades_today": 45
  }
}
```

### Dashboard

#### GET /api/dashboard/summary

Get dashboard summary data.

**Response:**
```json
{
  "pnl": {
    "today": 125.50,
    "week": 450.00,
    "month": 1250.00,
    "all_time": 5000.00
  },
  "positions": {
    "count": 3,
    "total_value": 450.0,
    "unrealized_pnl": 25.00
  },
  "trades": {
    "today": 45,
    "win_rate": 0.68,
    "avg_profit": 2.79
  },
  "risk": {
    "daily_loss_used": 0.25,
    "position_utilization": 0.45,
    "circuit_breaker": "closed"
  }
}
```

#### GET /api/dashboard/chart

Get chart data.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `metric` | string | Metric to chart (pnl, trades, positions) |
| `period` | string | Time period (1h, 24h, 7d, 30d) |
| `interval` | string | Data interval (1m, 5m, 1h, 1d) |

**Response:**
```json
{
  "metric": "pnl",
  "period": "24h",
  "interval": "1h",
  "data": [
    {"timestamp": "2024-01-14T11:00:00Z", "value": 100.00},
    {"timestamp": "2024-01-14T12:00:00Z", "value": 105.50},
    ...
  ]
}
```

### Strategies

#### GET /api/strategies

Get all strategies.

**Response:**
```json
{
  "strategies": [
    {
      "id": "arbitrage",
      "name": "Arbitrage",
      "enabled": true,
      "status": "active",
      "config": {
        "min_profit": 0.02,
        "max_trade_size": 300
      },
      "stats": {
        "trades_today": 15,
        "pnl_today": 45.00
      }
    }
  ]
}
```

#### PUT /api/strategies/{strategy_id}

Update strategy configuration.

**Request:**
```json
{
  "enabled": true,
  "config": {
    "min_profit": 0.03,
    "max_trade_size": 200
  }
}
```

**Response:**
```json
{
  "success": true,
  "strategy": {...}
}
```

### Settings

#### GET /api/settings

Get system settings.

**Response:**
```json
{
  "trading": {
    "dry_run": true,
    "max_daily_loss": 100.0,
    "max_total_position": 1000.0
  },
  "notifications": {
    "slack_enabled": true,
    "discord_enabled": true,
    "email_enabled": false
  },
  "ai": {
    "confidence_threshold": 0.6,
    "scan_interval": 300
  }
}
```

#### PUT /api/settings

Update system settings.

**Request:**
```json
{
  "trading": {
    "max_daily_loss": 150.0
  }
}
```

**Response:**
```json
{
  "success": true,
  "settings": {...}
}
```

---

## WebSocket Events

### Connection

Connect to WebSocket for real-time updates:

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onopen = () => {
  // Subscribe to events
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['trades', 'positions', 'alerts']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Event Types

#### trade.executed

```json
{
  "type": "trade.executed",
  "data": {
    "trade_id": "trade_456",
    "market_id": "presidential-election",
    "side": "buy",
    "size": 50.0,
    "price": 0.52,
    "pnl": 2.50
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### position.updated

```json
{
  "type": "position.updated",
  "data": {
    "position_id": "pos_123",
    "market_id": "presidential-election",
    "size": 100.0,
    "unrealized_pnl": 5.77
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### alert.created

```json
{
  "type": "alert.created",
  "data": {
    "alert_id": "alert_789",
    "type": "circuit_breaker",
    "severity": "critical",
    "message": "Circuit breaker triggered"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### metrics.updated

```json
{
  "type": "metrics.updated",
  "data": {
    "daily_pnl": 125.50,
    "total_position": 450.0,
    "trades_today": 45
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Event Bus Events

Internal Redis-based event bus for service communication.

### Event Format

```json
{
  "event_type": "trade.executed",
  "source": "orchestrator",
  "timestamp": "2024-01-15T10:30:00Z",
  "correlation_id": "corr_123",
  "data": {...}
}
```

### Event Types

| Event | Source | Description |
|-------|--------|-------------|
| `trade.requested` | Strategy | Trade request from strategy |
| `trade.approved` | Risk Manager | Trade approved by risk |
| `trade.rejected` | Risk Manager | Trade rejected by risk |
| `trade.executed` | Executor | Trade successfully executed |
| `trade.failed` | Executor | Trade execution failed |
| `position.opened` | Position Tracker | New position opened |
| `position.closed` | Position Tracker | Position closed |
| `position.updated` | Position Tracker | Position size changed |
| `alert.triggered` | Alert Manager | Alert condition met |
| `circuit_breaker.opened` | Risk Manager | Circuit breaker triggered |
| `circuit_breaker.closed` | Risk Manager | Circuit breaker reset |
| `ai.decision` | AI Orchestrator | AI made trading decision |
| `ai.analysis` | AI Orchestrator | AI completed analysis |

### Publishing Events

```python
from shared.event_bus import EventBus

bus = EventBus()
await bus.connect()

await bus.publish('trade.requested', {
    'market_id': 'presidential-election',
    'side': 'buy',
    'size': 50.0,
    'strategy': 'arbitrage'
})
```

### Subscribing to Events

```python
from shared.event_bus import EventBus

bus = EventBus()
await bus.connect()

async def handle_trade(event):
    print(f"Trade executed: {event['data']}")

await bus.subscribe('trade.executed', handle_trade)
```

---

## Authentication

### API Key Authentication

For programmatic access, use API key in header:

```bash
curl -H "X-API-Key: your_api_key" http://localhost:8080/api/status
```

### JWT Authentication (Admin Portal)

1. Login to get token:
```bash
curl -X POST http://localhost:3003/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

2. Use token in subsequent requests:
```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:3003/api/dashboard/summary
```

### Rate Limiting

| Endpoint | Limit |
|----------|-------|
| `/api/*` | 100 requests/minute |
| `/api/scan` | 10 requests/minute |
| `/api/analyze` | 30 requests/minute |
| `/ws` | 5 connections/IP |

---

## Error Responses

All APIs return consistent error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid market ID",
    "details": {
      "field": "market_id",
      "value": "invalid",
      "expected": "string matching pattern ^[a-z0-9-]+$"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

**Related Documentation:**
- [Configuration Reference](configuration.md) - API configuration options
- [Testing Guide](testing.md) - API testing procedures
- [Troubleshooting](troubleshooting.md) - API issues
