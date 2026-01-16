# PredictBot Digital Ocean Deployment Guide

## Executive Summary

This guide provides the optimal Digital Ocean deployment configuration for PredictBot, a prediction market trading bot. Based on our analysis, **trade execution speed is NOT the primary bottleneck** for prediction markets - the limiting factors are:

1. **API Rate Limits**: Kalshi, Polymarket, and Manifold all have rate limits (typically 10-100 requests/second)
2. **Market Liquidity**: Prediction markets have lower liquidity than traditional exchanges
3. **AI Processing Time**: OpenRouter API calls take 500ms-2s per request

Therefore, we recommend a **cost-effective, reliable setup** rather than an expensive high-performance one.

---

## Recommended Deployment Configurations

### Option 1: Production Starter (Recommended for Initial Deployment)
**Monthly Cost: ~$84/month**

| Component | Droplet Type | Specs | Monthly Cost |
|-----------|--------------|-------|--------------|
| **Main Bot** | General Purpose | 2 vCPU / 8 GB RAM | $63/month |
| **Database** | Managed PostgreSQL (Basic) | 1 GB RAM | $15/month |
| **Monitoring** | Included in Droplet | - | $0 |
| **Backups** | Weekly snapshots | - | $6/month |

**Why This Works:**
- 2 vCPUs handle all 5 strategy modules concurrently
- 8 GB RAM supports 6-agent AI system + Redis caching
- General Purpose provides dedicated CPU (no noisy neighbors)
- Sufficient for 100+ trades/day

### Option 2: Production Scale (For Higher Volume)
**Monthly Cost: ~$168/month**

| Component | Droplet Type | Specs | Monthly Cost |
|-----------|--------------|-------|--------------|
| **Main Bot** | CPU-Optimized | 4 vCPU / 8 GB RAM | $84/month |
| **Database** | Managed PostgreSQL (Standard) | 2 GB RAM | $30/month |
| **Redis Cache** | Managed Redis | 1 GB | $15/month |
| **Load Balancer** | Basic | - | $12/month |
| **Backups** | Daily snapshots | - | $12/month |
| **Monitoring** | DigitalOcean Monitoring | - | $15/month |

**Why This Works:**
- CPU-Optimized for faster AI inference
- Dedicated Redis for market data caching
- Load balancer for admin portal HA
- Better for 500+ trades/day

### Option 3: High-Performance (For Arbitrage/HFT)
**Monthly Cost: ~$400/month**

| Component | Droplet Type | Specs | Monthly Cost |
|-----------|--------------|-------|--------------|
| **Trading Engine** | CPU-Optimized Premium AMD | 8 vCPU / 16 GB RAM | $168/month |
| **AI Processing** | CPU-Optimized | 4 vCPU / 8 GB RAM | $84/month |
| **Database** | Managed PostgreSQL (HA) | 4 GB RAM | $60/month |
| **Redis Cache** | Managed Redis (HA) | 2 GB | $30/month |
| **Load Balancer** | Standard | - | $24/month |
| **Spaces (Storage)** | 250 GB | - | $5/month |
| **Monitoring** | Full stack | - | $29/month |

**Why This Works:**
- Separate trading and AI workloads
- Premium AMD CPUs with NVMe SSDs for lowest latency
- High-availability database and cache
- Best for cross-market arbitrage requiring <100ms execution

---

## Region Selection for Lowest Latency

### Prediction Market API Locations:

| Platform | API Location | Best DO Region | Latency |
|----------|--------------|----------------|---------|
| **Kalshi** | US East (NYC) | NYC1/NYC3 | <5ms |
| **Polymarket** | US East | NYC1/NYC3 | <5ms |
| **Manifold** | US West (SF) | SFO3 | <10ms |
| **OpenRouter** | US (distributed) | NYC1/SFO3 | <20ms |

**Recommendation**: Deploy in **NYC3** for optimal latency to Kalshi and Polymarket (primary trading platforms).

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DigitalOcean VPC (NYC3)                      │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │  Load Balancer  │    │   Spaces CDN    │                    │
│  │   (Optional)    │    │  (Static Files) │                    │
│  └────────┬────────┘    └─────────────────┘                    │
│           │                                                     │
│  ┌────────▼────────────────────────────────────────────┐       │
│  │              Main Droplet (Docker Host)              │       │
│  │                                                      │       │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │       │
│  │  │ Orchestrator │  │ Admin Portal │  │  Nginx    │  │       │
│  │  │   (Python)   │  │   (Next.js)  │  │  Proxy    │  │       │
│  │  └──────┬───────┘  └──────────────┘  └───────────┘  │       │
│  │         │                                            │       │
│  │  ┌──────▼───────────────────────────────────────┐   │       │
│  │  │           Strategy Modules (Docker)           │   │       │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │       │
│  │  │  │kalshi_ai│ │poly_arb │ │manifold │        │   │       │
│  │  │  └─────────┘ └─────────┘ └─────────┘        │   │       │
│  │  └──────────────────────────────────────────────┘   │       │
│  └─────────────────────────────────────────────────────┘       │
│                          │                                      │
│  ┌───────────────────────▼───────────────────────────┐         │
│  │              Managed Services                      │         │
│  │  ┌─────────────┐  ┌─────────────┐                 │         │
│  │  │ PostgreSQL  │  │    Redis    │                 │         │
│  │  │  (Trades)   │  │   (Cache)   │                 │         │
│  │  └─────────────┘  └─────────────┘                 │         │
│  └────────────────────────────────────────────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │      External APIs            │
              │  ┌─────────┐ ┌─────────────┐  │
              │  │ Kalshi  │ │ OpenRouter  │  │
              │  │Polymarket│ │   (AI)     │  │
              │  │ Manifold │ │            │  │
              │  └─────────┘ └─────────────┘  │
              └───────────────────────────────┘
```

---

## Step-by-Step Deployment

### 1. Create Droplet

```bash
# Using doctl CLI
doctl compute droplet create predictbot-prod \
  --region nyc3 \
  --size g-2vcpu-8gb \
  --image docker-20-04 \
  --ssh-keys YOUR_SSH_KEY_ID \
  --vpc-uuid YOUR_VPC_UUID \
  --enable-monitoring \
  --tag-names "predictbot,production"
```

### 2. Configure Firewall

```bash
# Create firewall
doctl compute firewall create \
  --name predictbot-firewall \
  --inbound-rules "protocol:tcp,ports:22,address:YOUR_IP/32 protocol:tcp,ports:80,address:0.0.0.0/0 protocol:tcp,ports:443,address:0.0.0.0/0 protocol:tcp,ports:3000,address:YOUR_IP/32" \
  --outbound-rules "protocol:tcp,ports:all,address:0.0.0.0/0 protocol:udp,ports:all,address:0.0.0.0/0" \
  --droplet-ids YOUR_DROPLET_ID
```

### 3. Setup Docker Environment

```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# Clone repository
git clone https://github.com/YOUR_ORG/predictbot-stack.git
cd predictbot-stack

# Copy and configure secrets
cp config/config.example.yml config/config.yml
cp .env.example .env

# Edit configuration
nano config/config.yml
nano .env

# Start services
docker-compose up -d
```

### 4. Configure Managed Database

```bash
# Create PostgreSQL cluster
doctl databases create predictbot-db \
  --engine pg \
  --region nyc3 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1

# Get connection string
doctl databases connection predictbot-db --format Host,Port,User,Password,Database
```

### 5. Setup SSL with Let's Encrypt

```bash
# Install certbot
apt install certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d predictbot.yourdomain.com

# Auto-renewal
certbot renew --dry-run
```

---

## Performance Optimization

### Docker Compose Production Config

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  orchestrator:
    build: ./orchestrator
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
    environment:
      - PYTHONUNBUFFERED=1
      - LOG_LEVEL=INFO

  kalshi_ai:
    build: ./modules/kalshi_ai
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G

  admin_portal:
    build: ./modules/admin_portal
    restart: always
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    ports:
      - "3000:3000"

  redis:
    image: redis:7-alpine
    restart: always
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Nginx Reverse Proxy Config

```nginx
# /etc/nginx/sites-available/predictbot
upstream admin_portal {
    server 127.0.0.1:3000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name predictbot.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/predictbot.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/predictbot.yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://admin_portal;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://admin_portal;
    }
}

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

---

## Monitoring & Alerts

### DigitalOcean Monitoring Setup

```bash
# Install monitoring agent (usually pre-installed on DO images)
curl -sSL https://repos.insights.digitalocean.com/install.sh | sudo bash

# Configure alerts via doctl
doctl monitoring alert create \
  --type "v1/insights/droplet/cpu" \
  --compare "GreaterThan" \
  --value 80 \
  --window "5m" \
  --entities YOUR_DROPLET_ID \
  --emails your@email.com \
  --description "High CPU usage on PredictBot"
```

### Key Metrics to Monitor

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| CPU Usage | >70% | >90% | Scale up or optimize |
| Memory Usage | >80% | >95% | Add RAM or fix leaks |
| Disk Usage | >70% | >90% | Clean logs or expand |
| API Latency | >500ms | >2s | Check network/API |
| Trade Success Rate | <90% | <80% | Review strategy params |

---

## Cost Comparison Summary

| Setup | Monthly Cost | Best For |
|-------|--------------|----------|
| **Starter** | $84/month | Paper trading, initial deployment |
| **Production** | $168/month | Live trading, 100-500 trades/day |
| **High-Performance** | $400/month | Arbitrage, 1000+ trades/day |

---

## Do You Need High Performance?

### When You DON'T Need Expensive Hardware:

1. **Prediction markets are slow** - Markets update every few seconds, not milliseconds
2. **API rate limits** - You can only make 10-100 requests/second anyway
3. **AI is the bottleneck** - OpenRouter calls take 500ms-2s regardless of your hardware
4. **Liquidity is limited** - You can't execute large orders instantly

### When You DO Need High Performance:

1. **Cross-market arbitrage** - Need to execute on 2+ platforms simultaneously
2. **High-frequency scalping** - Targeting sub-second price movements
3. **Large position sizes** - Need to split orders across multiple API calls
4. **Multiple AI agents** - Running 6+ agents in parallel

---

## Recommendation

**Start with the Production Starter ($84/month)** and monitor performance for 2-4 weeks. If you see:

- CPU consistently >70%
- Trade execution delays >1 second
- Missed arbitrage opportunities

Then upgrade to Production Scale or High-Performance.

The **bottleneck is almost always the external APIs**, not your server hardware.
