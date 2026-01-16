# Troubleshooting Guide

Common issues and solutions for PredictBot Stack.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Startup Issues](#startup-issues)
- [Database Issues](#database-issues)
- [Network Issues](#network-issues)
- [Service-Specific Issues](#service-specific-issues)
- [Trading Issues](#trading-issues)
- [AI Issues](#ai-issues)
- [Monitoring Issues](#monitoring-issues)
- [Performance Issues](#performance-issues)
- [Log Analysis](#log-analysis)

---

## Quick Diagnostics

### Run Health Check

```bash
./scripts/health-check.sh
```

### Check All Container Status

```bash
docker compose ps -a
```

### View Recent Errors

```bash
# All services
docker compose logs --tail=100 | grep -i "error\|exception\|failed"

# Specific service
docker compose logs --tail=100 orchestrator | grep -i "error"
```

### Check Resource Usage

```bash
docker stats --no-stream
```

---

## Startup Issues

### Container Won't Start

**Symptom:** Container exits immediately or keeps restarting.

**Diagnosis:**
```bash
# Check container logs
docker compose logs <service-name>

# Check exit code
docker compose ps -a | grep <service-name>
```

**Common Causes & Solutions:**

1. **Missing environment variables**
   ```bash
   # Check which variables are missing
   docker compose config | grep -A5 <service-name>
   
   # Ensure .env file exists and is readable
   ls -la .env
   cat .env | grep -v "^#" | grep -v "^$"
   ```

2. **Port already in use**
   ```bash
   # Find what's using the port
   netstat -tulpn | grep <port>
   # or on macOS
   lsof -i :<port>
   
   # Solution: Stop the conflicting service or change port in .env
   ```

3. **Insufficient memory**
   ```bash
   # Check available memory
   free -h
   
   # Reduce memory limits in docker-compose.yml
   # Or stop unnecessary services
   ```

4. **Build failed**
   ```bash
   # Rebuild with no cache
   docker compose build --no-cache <service-name>
   ```

### Database Connection Failed on Startup

**Symptom:** Services fail with "connection refused" to PostgreSQL.

**Solution:**
```bash
# Ensure postgres starts first
docker compose up -d postgres
sleep 10
docker compose up -d
```

Or add health check dependency (already in docker-compose.yml):
```yaml
depends_on:
  postgres:
    condition: service_healthy
```

### Submodules Not Initialized

**Symptom:** Build fails with "directory not found" errors.

**Solution:**
```bash
git submodule update --init --recursive
```

---

## Database Issues

### PostgreSQL Won't Start

**Symptom:** PostgreSQL container exits or stays unhealthy.

**Diagnosis:**
```bash
docker compose logs postgres
```

**Common Causes & Solutions:**

1. **Corrupted data directory**
   ```bash
   # WARNING: This will delete all data!
   docker compose down -v
   docker volume rm predictbot-stack_postgres_data
   docker compose up -d postgres
   ```

2. **Permission issues**
   ```bash
   # Check volume permissions
   docker compose exec postgres ls -la /var/lib/postgresql/data
   ```

3. **Disk full**
   ```bash
   # Check disk space
   df -h
   
   # Clean up Docker
   docker system prune -f
   ```

### Connection Refused

**Symptom:** Services can't connect to PostgreSQL.

**Diagnosis:**
```bash
# Check if postgres is running
docker compose ps postgres

# Test connection from inside network
docker compose exec orchestrator python -c "
import psycopg2
conn = psycopg2.connect('postgresql://predictbot:password@postgres:5432/predictbot')
print('Connected!')
"
```

**Solutions:**

1. **Wrong credentials**
   ```bash
   # Verify DATABASE_URL matches POSTGRES_PASSWORD
   grep POSTGRES_PASSWORD .env
   grep DATABASE_URL .env
   ```

2. **Network issue**
   ```bash
   # Recreate network
   docker compose down
   docker network rm predictbot-stack_predictbot-network
   docker compose up -d
   ```

### Redis Connection Issues

**Symptom:** "Connection refused" to Redis.

**Diagnosis:**
```bash
# Check Redis is running
docker compose ps redis

# Test connection
docker compose exec redis redis-cli ping
```

**Solutions:**

1. **Redis not started**
   ```bash
   docker compose up -d redis
   ```

2. **Memory limit reached**
   ```bash
   # Check Redis memory
   docker compose exec redis redis-cli INFO memory
   
   # Flush cache if needed (WARNING: loses cached data)
   docker compose exec redis redis-cli FLUSHALL
   ```

---

## Network Issues

### Services Can't Communicate

**Symptom:** Services can't reach each other by hostname.

**Diagnosis:**
```bash
# Check network exists
docker network ls | grep predictbot

# Check services are on network
docker network inspect predictbot-stack_predictbot-network
```

**Solutions:**

1. **Recreate network**
   ```bash
   docker compose down
   docker compose up -d
   ```

2. **DNS resolution issue**
   ```bash
   # Test DNS from inside container
   docker compose exec orchestrator ping -c 3 postgres
   docker compose exec orchestrator ping -c 3 redis
   ```

### External API Connection Failed

**Symptom:** Can't reach Polymarket, Kalshi, or other external APIs.

**Diagnosis:**
```bash
# Test from inside container
docker compose exec orchestrator curl -I https://api.polymarket.com
docker compose exec orchestrator curl -I https://api.kalshi.com
```

**Solutions:**

1. **DNS issues**
   ```bash
   # Add DNS servers to Docker daemon
   # /etc/docker/daemon.json
   {
     "dns": ["8.8.8.8", "8.8.4.4"]
   }
   sudo systemctl restart docker
   ```

2. **Firewall blocking**
   ```bash
   # Check firewall rules
   sudo ufw status
   
   # Allow outbound HTTPS
   sudo ufw allow out 443/tcp
   ```

3. **Rate limiting**
   ```bash
   # Check logs for rate limit errors
   docker compose logs | grep -i "rate.limit\|429"
   
   # Increase scan intervals in config
   ```

### SSL/TLS Certificate Errors

**Symptom:** "SSL certificate verify failed" errors.

**Solutions:**

1. **Update CA certificates**
   ```bash
   # In Dockerfile, add:
   RUN apt-get update && apt-get install -y ca-certificates
   ```

2. **Check system time**
   ```bash
   # Ensure time is synchronized
   timedatectl status
   sudo timedatectl set-ntp true
   ```

---

## Service-Specific Issues

### Orchestrator Issues

**Symptom:** Orchestrator unhealthy or not responding.

**Diagnosis:**
```bash
docker compose logs orchestrator
curl http://localhost:8080/health
```

**Common Issues:**

1. **Config file invalid**
   ```bash
   python scripts/validate_config.py --verbose
   ```

2. **Database migration needed**
   ```bash
   docker compose exec orchestrator python -c "
   from database import init_db
   init_db()
   "
   ```

### Polymarket Arbitrage Bot Issues

**Symptom:** Arbitrage bot not detecting opportunities.

**Diagnosis:**
```bash
docker compose logs polymarket-arb
```

**Common Issues:**

1. **Invalid private key**
   ```bash
   # Verify key format (should start with 0x)
   grep POLY_PRIVATE_KEY .env
   ```

2. **RPC endpoint issues**
   ```bash
   # Test RPC endpoint
   curl -X POST ${POLY_RPC_URL} \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
   ```

3. **Insufficient gas**
   ```bash
   # Check wallet balance
   # Use a block explorer or web3 to check MATIC balance
   ```

### Kalshi AI Bot Issues

**Symptom:** Kalshi AI not making trades or analysis.

**Diagnosis:**
```bash
docker compose logs kalshi-ai
curl http://localhost:8000/health
```

**Common Issues:**

1. **Invalid API credentials**
   ```bash
   # Test Kalshi API
   curl -X GET "https://api.kalshi.com/v1/markets" \
     -H "Authorization: Bearer ${KALSHI_API_KEY}"
   ```

2. **AI provider issues**
   ```bash
   # Check AI provider status
   curl http://localhost:8081/api/providers
   ```

### Admin Portal Issues

**Symptom:** Admin portal not loading or login fails.

**Diagnosis:**
```bash
docker compose logs admin_portal
curl http://localhost:3003/api/health
```

**Common Issues:**

1. **NEXTAUTH_SECRET not set**
   ```bash
   # Generate and set secret
   openssl rand -base64 32
   # Add to .env as NEXTAUTH_SECRET
   ```

2. **Database not accessible**
   ```bash
   # Check database connection
   docker compose exec admin_portal node -e "
   const { PrismaClient } = require('@prisma/client');
   const prisma = new PrismaClient();
   prisma.\$connect().then(() => console.log('Connected'));
   "
   ```

---

## Trading Issues

### No Trades Being Executed

**Symptom:** System running but no trades happening.

**Checklist:**

1. **Dry run enabled?**
   ```bash
   grep DRY_RUN .env
   # If DRY_RUN=1, trades are simulated only
   ```

2. **Strategies enabled?**
   ```bash
   grep ENABLE_ .env
   # Check ENABLE_ARB, ENABLE_MM_POLYMARKET, etc.
   ```

3. **Risk limits reached?**
   ```bash
   curl http://localhost:8080/api/risk/status
   ```

4. **Circuit breaker triggered?**
   ```bash
   curl http://localhost:8080/api/circuit-breaker/status
   ```

5. **No opportunities?**
   ```bash
   curl http://localhost:8080/api/opportunities
   ```

### Trades Failing

**Symptom:** Trades attempted but failing.

**Diagnosis:**
```bash
# Check trade logs
docker compose logs | grep -i "trade.*fail\|execution.*error"

# Check recent failed trades
curl http://localhost:8080/api/trades?status=failed
```

**Common Causes:**

1. **Insufficient balance**
   ```bash
   curl http://localhost:8080/api/balances
   ```

2. **Slippage too high**
   ```bash
   # Increase slippage tolerance in config
   # Or reduce trade size
   ```

3. **Market closed/resolved**
   ```bash
   # Check market status
   curl http://localhost:3000/api/markets/<market-id>
   ```

### Position Tracking Incorrect

**Symptom:** Displayed positions don't match actual positions.

**Solution:**
```bash
# Force position sync
curl -X POST http://localhost:8080/api/positions/sync

# Check sync status
curl http://localhost:8080/api/positions/sync-status
```

---

## AI Issues

### AI Not Making Decisions

**Symptom:** AI orchestrator running but no decisions.

**Diagnosis:**
```bash
docker compose logs ai_orchestrator
curl http://localhost:8081/api/decisions?limit=5
```

**Common Issues:**

1. **No API keys configured**
   ```bash
   grep -E "OPENAI_API_KEY|ANTHROPIC_API_KEY" .env
   ```

2. **Confidence threshold too high**
   ```bash
   # Lower threshold in .env
   AI_CONFIDENCE_THRESHOLD=0.5
   ```

3. **Budget exhausted**
   ```bash
   curl http://localhost:8081/api/budget/status
   ```

### LLM API Errors

**Symptom:** "API error" or "rate limit" in AI logs.

**Solutions:**

1. **Rate limiting**
   ```bash
   # Increase scan interval
   AI_SCAN_INTERVAL=600
   ```

2. **Invalid API key**
   ```bash
   # Test API key directly
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer ${OPENAI_API_KEY}"
   ```

3. **Switch to fallback provider**
   ```bash
   # Configure fallback in config.yml
   ai_trading:
     models:
       primary: "anthropic:claude-3-sonnet"
       fallback: "groq:llama2-70b"
   ```

### Ollama Issues

**Symptom:** Local LLM not responding.

**Diagnosis:**
```bash
docker compose logs ollama
curl http://localhost:11434/api/tags
```

**Solutions:**

1. **Model not downloaded**
   ```bash
   # Pull model
   docker compose exec ollama ollama pull llama2:70b
   ```

2. **Insufficient GPU memory**
   ```bash
   # Check GPU status
   docker compose exec ollama nvidia-smi
   
   # Use smaller model
   docker compose exec ollama ollama pull llama2:7b
   ```

3. **GPU not detected**
   ```bash
   # Verify NVIDIA runtime
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

---

## Monitoring Issues

### Grafana Not Loading

**Symptom:** Grafana dashboard blank or errors.

**Diagnosis:**
```bash
docker compose logs grafana
curl http://localhost:3002/api/health
```

**Solutions:**

1. **Data source not configured**
   ```bash
   # Check provisioning
   docker compose exec grafana ls /etc/grafana/provisioning/datasources/
   ```

2. **Prometheus not reachable**
   ```bash
   # Test from Grafana container
   docker compose exec grafana curl http://prometheus:9090/-/healthy
   ```

### Prometheus Not Scraping

**Symptom:** No metrics in Prometheus.

**Diagnosis:**
```bash
# Check targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets'
```

**Solutions:**

1. **Targets down**
   ```bash
   # Check target health in Prometheus UI
   # http://localhost:9090/targets
   ```

2. **Wrong scrape config**
   ```bash
   # Verify prometheus.yml
   cat config/prometheus.yml
   ```

### Loki Not Receiving Logs

**Symptom:** No logs in Grafana Explore.

**Diagnosis:**
```bash
docker compose logs promtail
curl http://localhost:3100/ready
```

**Solutions:**

1. **Promtail not running**
   ```bash
   docker compose up -d promtail
   ```

2. **Wrong log path**
   ```bash
   # Check promtail config
   cat config/promtail-config.yml
   ```

---

## Performance Issues

### High CPU Usage

**Diagnosis:**
```bash
docker stats --no-stream | sort -k3 -r | head -10
```

**Solutions:**

1. **Reduce scan frequency**
   ```bash
   AI_SCAN_INTERVAL=600
   ```

2. **Limit concurrent operations**
   ```yaml
   # In docker-compose.yml
   deploy:
     resources:
       limits:
         cpus: '1.0'
   ```

### High Memory Usage

**Diagnosis:**
```bash
docker stats --no-stream | sort -k4 -r | head -10
```

**Solutions:**

1. **Reduce container memory limits**
   ```bash
   CONTAINER_MEMORY_LIMIT=256m
   ```

2. **Clear Redis cache**
   ```bash
   docker compose exec redis redis-cli FLUSHDB
   ```

3. **Vacuum PostgreSQL**
   ```bash
   docker compose exec postgres vacuumdb -U predictbot -d predictbot -f
   ```

### Slow API Responses

**Diagnosis:**
```bash
# Time API calls
time curl http://localhost:8080/health
time curl http://localhost:8081/health
```

**Solutions:**

1. **Add database indexes**
   ```bash
   docker compose exec postgres psql -U predictbot -c "
   CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
   CREATE INDEX IF NOT EXISTS idx_positions_market ON positions(market_id);
   "
   ```

2. **Enable query caching**
   ```bash
   # In Redis, increase memory for caching
   docker compose exec redis redis-cli CONFIG SET maxmemory 512mb
   ```

---

## Log Analysis

### Finding Errors

```bash
# All errors in last hour
docker compose logs --since 1h | grep -i "error\|exception\|failed\|critical"

# Errors by service
docker compose logs --since 1h orchestrator | grep -i error
docker compose logs --since 1h ai_orchestrator | grep -i error
```

### Common Error Patterns

| Error Pattern | Likely Cause | Solution |
|---------------|--------------|----------|
| `Connection refused` | Service not running | Start the service |
| `Authentication failed` | Invalid credentials | Check API keys |
| `Rate limit exceeded` | Too many API calls | Increase intervals |
| `Insufficient funds` | Low balance | Add funds or reduce size |
| `Circuit breaker open` | Too many failures | Wait for cooldown |
| `Timeout` | Slow network/service | Increase timeout |

### Exporting Logs

```bash
# Export to file
docker compose logs > logs/full-export-$(date +%Y%m%d).log

# Export specific service
docker compose logs orchestrator > logs/orchestrator-$(date +%Y%m%d).log

# Export with timestamps
docker compose logs -t > logs/timestamped-$(date +%Y%m%d).log
```

### Log Levels

Adjust log verbosity in `.env`:

```bash
# More verbose (for debugging)
LOG_LEVEL=DEBUG

# Normal operation
LOG_LEVEL=INFO

# Quiet (errors only)
LOG_LEVEL=ERROR
```

---

## Getting Help

### Collect Diagnostic Information

```bash
# Create diagnostic bundle
./scripts/diagnostics.sh > diagnostics-$(date +%Y%m%d).txt

# Or manually:
echo "=== Docker Version ===" > diagnostics.txt
docker --version >> diagnostics.txt
echo "=== Container Status ===" >> diagnostics.txt
docker compose ps -a >> diagnostics.txt
echo "=== Recent Logs ===" >> diagnostics.txt
docker compose logs --tail=100 >> diagnostics.txt
echo "=== Resource Usage ===" >> diagnostics.txt
docker stats --no-stream >> diagnostics.txt
```

### Before Asking for Help

1. Check this troubleshooting guide
2. Search existing GitHub issues
3. Collect diagnostic information
4. Note exact error messages
5. Describe what you've already tried

---

**Related Documentation:**
- [Quick Start Guide](quickstart.md) - Getting started
- [Testing Guide](testing.md) - Validation procedures
- [Configuration Reference](configuration.md) - All settings
