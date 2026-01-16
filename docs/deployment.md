# Production Deployment Guide

This guide covers deploying PredictBot Stack to a production VPS environment with SSL/TLS, security hardening, and operational best practices.

## Table of Contents

- [VPS Requirements](#vps-requirements)
- [Server Setup](#server-setup)
- [SSL/TLS Configuration](#ssltls-configuration-with-traefik)
- [Production Environment](#production-environment-setup)
- [Backup and Recovery](#backup-and-recovery)
- [Scaling Considerations](#scaling-considerations)
- [Security Hardening](#security-hardening-checklist)
- [Monitoring in Production](#monitoring-in-production)

---

## VPS Requirements

### Minimum Specifications

| Component | Minimum | Recommended | With Ollama |
|-----------|---------|-------------|-------------|
| **CPU** | 4 vCPU | 8 vCPU | 8+ vCPU |
| **RAM** | 8 GB | 16 GB | 32 GB |
| **Storage** | 50 GB SSD | 100 GB NVMe | 200 GB NVMe |
| **Network** | 1 Gbps | 1 Gbps | 1 Gbps |
| **GPU** | - | - | NVIDIA RTX 3080+ |

### Recommended VPS Providers

| Provider | Best For | Notes |
|----------|----------|-------|
| **Hetzner** | Cost-effective | Great EU locations, GPU servers available |
| **DigitalOcean** | Simplicity | Easy setup, good documentation |
| **Vultr** | GPU instances | Bare metal GPU options |
| **AWS EC2** | Enterprise | g4dn instances for GPU |
| **GCP** | AI workloads | T4/A100 GPU instances |

### GPU Requirements (for Ollama)

If running local LLMs with Ollama:

| Model Size | VRAM Required | Recommended GPU |
|------------|---------------|-----------------|
| 7B params | 8 GB | RTX 3070/4070 |
| 13B params | 16 GB | RTX 3090/4080 |
| 70B params | 48 GB | A100 40GB |

---

## Server Setup

### 1. Initial Server Configuration

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    curl \
    git \
    htop \
    ufw \
    fail2ban \
    unattended-upgrades

# Set timezone
sudo timedatectl set-timezone UTC

# Create dedicated user
sudo adduser predictbot
sudo usermod -aG sudo predictbot
sudo usermod -aG docker predictbot

# Switch to new user
su - predictbot
```

### 2. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version

# Enable Docker to start on boot
sudo systemctl enable docker
```

### 3. Install NVIDIA Drivers (for GPU servers)

```bash
# Add NVIDIA repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install NVIDIA container toolkit
sudo apt update
sudo apt install -y nvidia-container-toolkit

# Configure Docker to use NVIDIA runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### 4. Clone and Configure PredictBot

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/predictbot-stack.git
sudo chown -R predictbot:predictbot predictbot-stack
cd predictbot-stack

# Initialize submodules
git submodule update --init --recursive

# Run setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Configure environment
cp .env.template .env
nano .env  # Configure for production
```

---

## SSL/TLS Configuration with Traefik

### 1. Create Traefik Configuration

Create `config/traefik/traefik.yml`:

```yaml
# Traefik Static Configuration
api:
  dashboard: true
  insecure: false

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: your-email@example.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: predictbot-network

log:
  level: INFO
```

### 2. Create Traefik Dynamic Configuration

Create `config/traefik/dynamic.yml`:

```yaml
# Traefik Dynamic Configuration
http:
  middlewares:
    secure-headers:
      headers:
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
        forceSTSHeader: true
        contentTypeNosniff: true
        browserXssFilter: true
        referrerPolicy: "strict-origin-when-cross-origin"
        customFrameOptionsValue: "SAMEORIGIN"
    
    rate-limit:
      rateLimit:
        average: 100
        burst: 50
    
    auth:
      basicAuth:
        users:
          - "admin:$apr1$..." # Generate with: htpasswd -n admin
```

### 3. Add Traefik to Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: predictbot_traefik
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./config/traefik/traefik.yml:/traefik.yml:ro
      - ./config/traefik/dynamic.yml:/dynamic.yml:ro
      - ./data/letsencrypt:/letsencrypt
    networks:
      - predictbot-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.traefik.rule=Host(`traefik.yourdomain.com`)"
      - "traefik.http.routers.traefik.entrypoints=websecure"
      - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik.service=api@internal"
      - "traefik.http.routers.traefik.middlewares=auth"

  admin_portal:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.admin.rule=Host(`admin.yourdomain.com`)"
      - "traefik.http.routers.admin.entrypoints=websecure"
      - "traefik.http.routers.admin.tls.certresolver=letsencrypt"
      - "traefik.http.routers.admin.middlewares=secure-headers,rate-limit"
      - "traefik.http.services.admin.loadbalancer.server.port=3000"

  grafana:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.yourdomain.com`)"
      - "traefik.http.routers.grafana.entrypoints=websecure"
      - "traefik.http.routers.grafana.tls.certresolver=letsencrypt"
      - "traefik.http.routers.grafana.middlewares=secure-headers"
      - "traefik.http.services.grafana.loadbalancer.server.port=3000"

  orchestrator:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
      - "traefik.http.routers.api.middlewares=secure-headers,rate-limit,auth"
      - "traefik.http.services.api.loadbalancer.server.port=8080"

networks:
  predictbot-network:
    external: true
```

### 4. Deploy with SSL

```bash
# Create network if not exists
docker network create predictbot-network

# Start with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile full up -d
```

---

## Production Environment Setup

### 1. Production .env Configuration

```bash
# =============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# =============================================================================

# CRITICAL: Disable dry run for live trading
DRY_RUN=0

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------
POSTGRES_PASSWORD=<generate-strong-password>
DATABASE_URL=postgresql://predictbot:<password>@postgres:5432/predictbot

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------
NEXTAUTH_SECRET=<generate-32-char-random-string>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<generate-strong-password>
GRAFANA_PASSWORD=<generate-strong-password>

# -----------------------------------------------------------------------------
# Platform API Keys
# -----------------------------------------------------------------------------
POLY_PRIVATE_KEY=<your-wallet-private-key>
POLY_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/<your-key>

KALSHI_API_KEY=<your-kalshi-api-key>
KALSHI_API_SECRET=<your-kalshi-api-secret>

MANIFOLD_API_KEY=<your-manifold-api-key>

# -----------------------------------------------------------------------------
# AI Configuration
# -----------------------------------------------------------------------------
OPENAI_API_KEY=sk-<your-openai-key>
ANTHROPIC_API_KEY=sk-ant-<your-anthropic-key>
AI_MODEL=openai:gpt-4-turbo
AI_CONFIDENCE_THRESHOLD=0.7  # Higher threshold for production

# -----------------------------------------------------------------------------
# Risk Management (Conservative for production)
# -----------------------------------------------------------------------------
MAX_DAILY_LOSS=50
MAX_TOTAL_POSITION=500
CIRCUIT_BREAKER_THRESHOLD=3
CIRCUIT_BREAKER_COOLDOWN=600

# -----------------------------------------------------------------------------
# Notifications (Enable all for production)
# -----------------------------------------------------------------------------
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
ALERT_EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=<app-password>
ALERT_EMAIL_TO=alerts@yourdomain.com

# -----------------------------------------------------------------------------
# Resource Limits
# -----------------------------------------------------------------------------
CONTAINER_CPU_LIMIT=2.0
CONTAINER_MEMORY_LIMIT=1g
PROMETHEUS_RETENTION=30d

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
LOG_LEVEL=INFO
```

### 2. Create Systemd Service

Create `/etc/systemd/system/predictbot.service`:

```ini
[Unit]
Description=PredictBot Stack
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/predictbot-stack
ExecStart=/opt/predictbot-stack/scripts/start.sh --profile full
ExecStop=/opt/predictbot-stack/scripts/stop.sh
User=predictbot
Group=predictbot

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable predictbot
sudo systemctl start predictbot
```

### 3. Configure Log Rotation

Create `/etc/logrotate.d/predictbot`:

```
/opt/predictbot-stack/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 predictbot predictbot
    sharedscripts
    postrotate
        docker-compose -f /opt/predictbot-stack/docker-compose.yml kill -s USR1 promtail
    endscript
}
```

---

## Backup and Recovery

### 1. Automated Backup Script

The `scripts/backup.sh` script handles:
- PostgreSQL database dump
- Redis RDB snapshot
- Configuration files
- Logs (optional)

```bash
# Run manual backup
./scripts/backup.sh

# Backup to specific location
./scripts/backup.sh --output /backup/predictbot

# Include logs
./scripts/backup.sh --include-logs
```

### 2. Scheduled Backups with Cron

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/predictbot-stack/scripts/backup.sh --output /backup/predictbot >> /var/log/predictbot-backup.log 2>&1

# Add weekly full backup (including logs) on Sunday
0 3 * * 0 /opt/predictbot-stack/scripts/backup.sh --output /backup/predictbot-full --include-logs >> /var/log/predictbot-backup.log 2>&1
```

### 3. Offsite Backup

```bash
# Sync to S3
aws s3 sync /backup/predictbot s3://your-bucket/predictbot-backups/

# Sync to remote server
rsync -avz /backup/predictbot/ user@backup-server:/backups/predictbot/
```

### 4. Recovery Procedure

```bash
# 1. Stop services
./scripts/stop.sh

# 2. Restore PostgreSQL
docker-compose up -d postgres
docker-compose exec -T postgres psql -U predictbot < backup/predictbot.sql

# 3. Restore Redis
docker-compose stop redis
cp backup/dump.rdb data/redis/
docker-compose start redis

# 4. Restore configuration
cp backup/config/* config/
cp backup/.env .env

# 5. Start services
./scripts/start.sh --profile full
```

---

## Scaling Considerations

### Horizontal Scaling

For high-volume trading, consider:

#### 1. Database Scaling

```yaml
# docker-compose.scale.yml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8g
    command:
      - "postgres"
      - "-c"
      - "max_connections=200"
      - "-c"
      - "shared_buffers=2GB"
      - "-c"
      - "effective_cache_size=6GB"
```

#### 2. Redis Cluster

For high-throughput event bus:

```yaml
services:
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

#### 3. Multiple Trading Instances

```bash
# Scale specific services
docker-compose up -d --scale polymarket-mm=2 --scale polymarket-spike=2
```

### Vertical Scaling

Adjust resource limits in `.env`:

```bash
# For high-frequency trading
CONTAINER_CPU_LIMIT=4.0
CONTAINER_MEMORY_LIMIT=2g

# For AI-heavy workloads
AI_ORCHESTRATOR_MEMORY=4g
OLLAMA_MEMORY=16g
```

---

## Security Hardening Checklist

### Server Level

- [ ] **Firewall configured** (UFW/iptables)
  ```bash
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  sudo ufw allow ssh
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```

- [ ] **SSH hardened**
  ```bash
  # /etc/ssh/sshd_config
  PermitRootLogin no
  PasswordAuthentication no
  PubkeyAuthentication yes
  ```

- [ ] **Fail2ban configured**
  ```bash
  sudo systemctl enable fail2ban
  sudo systemctl start fail2ban
  ```

- [ ] **Automatic security updates**
  ```bash
  sudo dpkg-reconfigure -plow unattended-upgrades
  ```

### Application Level

- [ ] **Strong passwords** for all services
- [ ] **API keys rotated** regularly
- [ ] **Secrets not in version control**
- [ ] **`.env` file permissions** restricted
  ```bash
  chmod 600 .env
  ```

- [ ] **Docker socket protected**
- [ ] **Non-root containers** where possible
- [ ] **Network segmentation** (internal services not exposed)

### Monitoring Level

- [ ] **Alert on failed logins**
- [ ] **Alert on unusual trading activity**
- [ ] **Alert on service restarts**
- [ ] **Log all API access**
- [ ] **Audit trail enabled**

### Network Level

- [ ] **SSL/TLS enabled** for all public endpoints
- [ ] **Internal services** not exposed to internet
- [ ] **Rate limiting** configured
- [ ] **DDoS protection** (Cloudflare recommended)

---

## Monitoring in Production

### Key Metrics to Watch

| Metric | Warning Threshold | Critical Threshold |
|--------|-------------------|-------------------|
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 80% | > 95% |
| Disk Usage | > 70% | > 90% |
| API Latency | > 500ms | > 2000ms |
| Error Rate | > 1% | > 5% |
| Daily P&L | < -$25 | < -$50 |

### Grafana Alerts

Configure in Grafana:

1. **Service Down Alert**
   ```promql
   up{job=~"predictbot.*"} == 0
   ```

2. **High Error Rate**
   ```promql
   rate(http_requests_total{status=~"5.."}[5m]) > 0.05
   ```

3. **Circuit Breaker Triggered**
   ```promql
   predictbot_circuit_breaker_status == 1
   ```

4. **Daily Loss Limit**
   ```promql
   predictbot_daily_pnl < -50
   ```

### Health Check Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| Orchestrator | `/health` | `{"status": "healthy"}` |
| AI Orchestrator | `/health` | `{"status": "healthy"}` |
| Admin Portal | `/api/health` | `{"status": "ok"}` |
| Grafana | `/api/health` | `{"database": "ok"}` |
| Prometheus | `/-/healthy` | `Prometheus is Healthy` |

---

## Maintenance Procedures

### Rolling Updates

```bash
# Pull latest changes
git pull origin main
git submodule update --recursive

# Rebuild and restart with zero downtime
docker-compose pull
docker-compose up -d --build --no-deps <service-name>
```

### Database Maintenance

```bash
# Vacuum and analyze
docker-compose exec postgres psql -U predictbot -c "VACUUM ANALYZE;"

# Check table sizes
docker-compose exec postgres psql -U predictbot -c "
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
"
```

### Log Cleanup

```bash
# Clean old Docker logs
docker system prune -f

# Clean application logs older than 30 days
find /opt/predictbot-stack/logs -type f -mtime +30 -delete
```

---

## Disaster Recovery

### Recovery Time Objectives

| Scenario | RTO | RPO |
|----------|-----|-----|
| Service crash | 5 min | 0 |
| Server failure | 1 hour | 1 hour |
| Data corruption | 4 hours | 24 hours |
| Complete loss | 24 hours | 24 hours |

### Recovery Procedures

1. **Service Crash**: Automatic restart via Docker
2. **Server Failure**: Restore from backup to new server
3. **Data Corruption**: Restore from last known good backup
4. **Complete Loss**: Full restore from offsite backup

---

**Next Steps:**
- [Configuration Reference](configuration.md) - Detailed configuration options
- [Testing Guide](testing.md) - Validate your deployment
- [Troubleshooting](troubleshooting.md) - Common production issues
