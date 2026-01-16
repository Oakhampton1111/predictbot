# Security Best Practices

This document outlines security best practices for operating the PredictBot trading stack safely.

---

## Table of Contents

1. [Wallet Security](#wallet-security)
2. [API Key Management](#api-key-management)
3. [Environment Configuration](#environment-configuration)
4. [Server Security](#server-security)
5. [Operational Security](#operational-security)
6. [Incident Response](#incident-response)

---

## Wallet Security

### Use a Dedicated Trading Wallet

**⚠️ CRITICAL: Never use your main wallet for automated trading!**

1. **Create a separate wallet** specifically for PredictBot
2. **Only fund it** with the amount you're willing to risk
3. **Never store** more than your intended trading capital

### Wallet Setup Checklist

- [ ] Created new wallet specifically for trading
- [ ] Backed up seed phrase securely (offline, encrypted)
- [ ] Funded with limited capital only
- [ ] Verified wallet address before depositing
- [ ] Tested with small transaction first

### Private Key Protection

```bash
# NEVER do this:
POLY_PRIVATE_KEY=0x123...  # In code or public files

# ALWAYS do this:
# Store in .env file with restricted permissions
chmod 600 .env
```

### Recommended Wallet Funding

| Risk Level | Funding Amount | Use Case |
|------------|----------------|----------|
| Testing | $50-100 | Initial testing, dry runs |
| Conservative | $200-500 | Low-risk strategies only |
| Moderate | $500-1000 | Full stack operation |
| Aggressive | $1000+ | Experienced users only |

---

## API Key Management

### Key Generation Best Practices

1. **Generate unique keys** for each application
2. **Use descriptive names** (e.g., "PredictBot-Production")
3. **Set minimum permissions** required
4. **Enable IP restrictions** where available
5. **Set spending limits** on AI APIs

### Key Rotation Schedule

| Key Type | Rotation Frequency | Notes |
|----------|-------------------|-------|
| Exchange API Keys | Every 90 days | Or immediately if compromised |
| AI Service Keys | Every 90 days | Monitor usage for anomalies |
| RPC Endpoints | As needed | Rotate if rate limited |

### Secure Storage

```bash
# .env file permissions (Linux/Mac)
chmod 600 .env
chown $USER:$USER .env

# Verify permissions
ls -la .env
# Should show: -rw------- 1 user user ... .env
```

### What to Do If Keys Are Compromised

1. **Immediately revoke** the compromised key
2. **Generate new keys** from the platform dashboard
3. **Update .env** with new keys
4. **Restart services** to load new keys
5. **Review logs** for unauthorized activity
6. **Check account balances** for unexpected changes

---

## Environment Configuration

### .env File Security

```bash
# Create .env from template
cp .env.template .env

# Set restrictive permissions
chmod 600 .env

# Verify it's in .gitignore
grep ".env" .gitignore
```

### Never Commit Secrets

Add to `.gitignore`:
```
.env
.env.*
*.pem
*.key
secrets/
```

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Prevent committing secrets

# Check for private keys
if git diff --cached | grep -E "PRIVATE_KEY|API_KEY|API_SECRET" | grep -v "template\|example"; then
    echo "ERROR: Potential secret detected in commit!"
    echo "Please remove secrets before committing."
    exit 1
fi
```

### Environment Variable Validation

Always run validation before starting:
```bash
python scripts/validate_secrets.py --strict
```

---

## Server Security

### VPS Hardening

1. **Update system packages**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Configure firewall**
   ```bash
   # Allow SSH
   sudo ufw allow 22/tcp
   
   # Allow only necessary ports
   sudo ufw allow 8000/tcp  # Kalshi AI dashboard (if needed)
   sudo ufw allow 8080/tcp  # Orchestrator health check
   
   # Enable firewall
   sudo ufw enable
   ```

3. **Disable root login**
   ```bash
   # Edit /etc/ssh/sshd_config
   PermitRootLogin no
   PasswordAuthentication no  # Use SSH keys only
   ```

4. **Use SSH keys**
   ```bash
   # Generate key pair (on local machine)
   ssh-keygen -t ed25519 -C "predictbot-server"
   
   # Copy to server
   ssh-copy-id user@server
   ```

### Docker Security

1. **Don't run as root**
   ```dockerfile
   # In Dockerfiles
   USER nonroot
   ```

2. **Use read-only mounts where possible**
   ```yaml
   volumes:
     - ./config:/app/config:ro  # Read-only
   ```

3. **Limit container resources**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 512m
   ```

4. **Use specific image tags**
   ```dockerfile
   FROM python:3.12-slim  # Not python:latest
   ```

### Network Security

1. **Use internal Docker network** for inter-service communication
2. **Expose only necessary ports** to host
3. **Use HTTPS** for any external dashboards
4. **Consider VPN** for remote access

---

## Operational Security

### Dry Run First

**ALWAYS start with DRY_RUN=1**

```bash
# In .env
DRY_RUN=1

# Verify in logs
docker-compose logs | grep -i "dry.run"
```

### Gradual Deployment

1. **Phase 1**: Run with DRY_RUN=1 for 24-48 hours
2. **Phase 2**: Enable one strategy with minimal capital
3. **Phase 3**: Gradually increase capital and enable more strategies
4. **Phase 4**: Full deployment with monitoring

### Monitoring Checklist

- [ ] Check logs daily for errors
- [ ] Monitor wallet/account balances
- [ ] Review trade history for anomalies
- [ ] Check API usage and costs
- [ ] Verify circuit breakers are working

### Risk Limits

Set conservative limits initially:

```yaml
# config.yml
risk_management:
  global:
    max_daily_loss: 50.0      # Start low
    max_total_position: 500.0  # Half of bankroll
```

### Backup Strategy

1. **Configuration backups**
   ```bash
   # Backup config (without secrets)
   cp config/config.yml config/config.yml.backup
   ```

2. **Database backups**
   ```bash
   # Backup SQLite databases
   docker cp predictbot-kalshi-ai:/app/data/kalshi_ai.db ./backups/
   ```

3. **Log retention**
   - Keep logs for at least 30 days
   - Archive important logs monthly

---

## Incident Response

### Signs of Compromise

- Unexpected trades or positions
- API rate limit errors (someone else using keys)
- Unusual login notifications from platforms
- Wallet balance changes you didn't make
- High AI API costs

### Immediate Response Steps

1. **Stop all trading**
   ```bash
   docker-compose down
   ```

2. **Revoke all API keys** from platform dashboards

3. **Check account balances** on all platforms

4. **Review logs** for unauthorized activity
   ```bash
   docker-compose logs > incident_logs.txt
   ```

5. **Transfer funds** from trading wallet if needed

6. **Generate new keys** and update configuration

7. **Investigate** how compromise occurred

8. **Document** the incident

### Emergency Contacts

Keep these handy:
- Kalshi support: support@kalshi.com
- Polymarket Discord: [link]
- Your exchange's emergency contact

### Post-Incident Checklist

- [ ] All old keys revoked
- [ ] New keys generated and tested
- [ ] Logs reviewed and archived
- [ ] Root cause identified
- [ ] Security improvements implemented
- [ ] Incident documented

---

## Security Checklist Summary

### Before First Run

- [ ] Created dedicated trading wallet
- [ ] Funded wallet with limited capital
- [ ] Generated all API keys
- [ ] Created .env file with correct permissions
- [ ] Verified .env is in .gitignore
- [ ] Ran secrets validation script
- [ ] Set DRY_RUN=1
- [ ] Configured conservative risk limits

### Regular Maintenance

- [ ] Review logs weekly
- [ ] Check API key expiration
- [ ] Monitor account balances
- [ ] Update system packages monthly
- [ ] Rotate keys quarterly
- [ ] Backup configurations

### Before Going Live

- [ ] Tested thoroughly in dry-run mode
- [ ] Verified all circuit breakers work
- [ ] Set appropriate position limits
- [ ] Configured alerts/notifications
- [ ] Documented emergency procedures
- [ ] Have incident response plan ready

---

## Additional Resources

- [OWASP Security Guidelines](https://owasp.org/)
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Ethereum Wallet Security](https://ethereum.org/en/security/)
