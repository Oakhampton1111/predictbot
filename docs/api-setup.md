# API Setup Guide

This guide explains how to obtain API keys and credentials for each platform supported by PredictBot.

---

## Table of Contents

1. [Polymarket Setup](#polymarket-setup)
2. [Kalshi Setup](#kalshi-setup)
3. [Manifold Markets Setup](#manifold-markets-setup)
4. [PredictIt Setup](#predictit-setup)
5. [AI Services Setup](#ai-services-setup)
6. [Polyseer Setup](#polyseer-setup)

---

## Polymarket Setup

Polymarket is a decentralized prediction market on the Polygon blockchain. You'll need an Ethereum wallet and a Polygon RPC endpoint.

### 1. Create a Trading Wallet

**⚠️ IMPORTANT: Create a dedicated wallet for trading. Never use your main wallet!**

#### Option A: MetaMask (Recommended for beginners)
1. Install [MetaMask](https://metamask.io/) browser extension
2. Create a new wallet or import an existing one
3. **Create a new account** specifically for trading
4. Export the private key:
   - Click the three dots menu → Account Details
   - Click "Export Private Key"
   - Enter your password
   - Copy the private key (starts with `0x`)

#### Option B: Generate a new wallet programmatically
```python
from eth_account import Account
account = Account.create()
print(f"Address: {account.address}")
print(f"Private Key: {account.key.hex()}")
```

### 2. Fund Your Wallet

1. **Get USDC on Polygon**:
   - Bridge USDC from Ethereum to Polygon using [Polygon Bridge](https://wallet.polygon.technology/bridge)
   - Or buy USDC directly on Polygon via exchanges that support Polygon withdrawals

2. **Get MATIC for gas**:
   - You need a small amount of MATIC (1-5 MATIC is plenty) for transaction fees
   - Buy from exchanges or use a [faucet](https://faucet.polygon.technology/) for small amounts

### 3. Get a Polygon RPC URL

You need an RPC endpoint to interact with the Polygon blockchain.

#### Option A: Infura (Recommended)
1. Go to [Infura](https://infura.io/)
2. Create a free account
3. Create a new project
4. Select "Polygon" network
5. Copy the HTTPS endpoint URL

#### Option B: Alchemy
1. Go to [Alchemy](https://www.alchemy.com/)
2. Create a free account
3. Create a new app for Polygon Mainnet
4. Copy the HTTPS URL

#### Option C: Public RPC (Not recommended for production)
```
https://polygon-rpc.com
```

### 4. Set Environment Variables

```bash
POLY_PRIVATE_KEY=0x... # Your wallet private key
POLY_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_PROJECT_ID
```

---

## Kalshi Setup

Kalshi is a CFTC-regulated prediction market exchange.

### 1. Create a Kalshi Account

1. Go to [Kalshi](https://kalshi.com/)
2. Click "Sign Up"
3. Complete identity verification (required for trading)
4. Fund your account via bank transfer or wire

### 2. Generate API Keys

1. Log in to your Kalshi account
2. Go to **Settings** → **API Access**
3. Click "Generate API Key"
4. Save both the **API Key ID** and **API Secret**
   - ⚠️ The secret is only shown once!

### 3. Set Environment Variables

```bash
KALSHI_API_KEY=your_api_key_id
KALSHI_API_SECRET=your_api_secret
```

### API Documentation

- [Kalshi API Docs](https://trading-api.readme.io/reference/getting-started)
- Rate limits: 60 requests/minute for most endpoints

---

## Manifold Markets Setup

Manifold is a play-money prediction market platform.

### 1. Create a Manifold Account

1. Go to [Manifold Markets](https://manifold.markets/)
2. Sign up with Google or email
3. You'll receive starting Mana (play money)

### 2. Generate API Key

1. Log in to Manifold
2. Go to your **Profile** → **Edit Profile**
3. Scroll down to **API Key**
4. Click "Generate" or copy existing key

### 3. Set Environment Variables

```bash
MANIFOLD_API_KEY=your_api_key
MANIFOLD_USERNAME=your_username
```

### API Documentation

- [Manifold API Docs](https://docs.manifold.markets/api)
- Rate limits: Generally permissive, ~100 requests/minute

---

## PredictIt Setup

PredictIt is a real-money political prediction market. API access is limited.

### 1. Create a PredictIt Account

1. Go to [PredictIt](https://www.predictit.org/)
2. Create an account
3. Complete identity verification
4. Fund your account (max $850 per market)

### 2. API Access

**Note**: PredictIt has limited official API support. Options include:

#### Option A: Public Market Data API (Read-only)
```
https://www.predictit.org/api/marketdata/all/
```
This endpoint provides market data but not trading capabilities.

#### Option B: Session Token (Advanced)
1. Log in to PredictIt in your browser
2. Open Developer Tools (F12)
3. Go to Application → Cookies
4. Find and copy the session cookie value

**⚠️ Warning**: Session tokens expire and may violate ToS. Use at your own risk.

### 3. Set Environment Variables

```bash
PREDICTIT_API_TOKEN=your_session_token  # If available
# OR
PREDICTIT_USERNAME=your_username
PREDICTIT_PASSWORD=your_password  # Less secure
```

### Limitations

- No official trading API
- $850 maximum investment per market
- 10% fee on profits
- Limited automation support

---

## AI Services Setup

### OpenAI (GPT-4 / GPT-3.5)

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Go to **API Keys** section
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

**Pricing**: Pay-per-use. GPT-4 is ~$0.03/1K input tokens, $0.06/1K output tokens.

```bash
OPENAI_API_KEY=sk-...
```

### Anthropic (Claude)

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create an account
3. Go to **API Keys**
4. Generate a new key

**Pricing**: Similar to OpenAI. Claude 3 Opus is premium tier.

```bash
ANTHROPIC_API_KEY=sk-ant-...
```

### xAI (Grok)

1. Go to [xAI](https://x.ai/)
2. Request API access (may have waitlist)
3. Generate API key when available

```bash
XAI_API_KEY=your_xai_key
```

### Recommended Configuration

For cost-effective operation:
```bash
# Use GPT-4 for primary analysis
OPENAI_API_KEY=sk-...
AI_MODEL=openai:gpt-4

# Set monthly budget limit
AI_MONTHLY_BUDGET=50.0
```

---

## Polyseer Setup

Polyseer is an AI research assistant that requires a Valyu API key.

### 1. Get Valyu API Key

1. Go to [Valyu.ai](https://valyu.ai/)
2. Create an account
3. Navigate to API settings
4. Generate an API key

### 2. Set Environment Variables

```bash
VALYU_API_KEY=your_valyu_key
POLYSEER_ENABLED=true
```

---

## Security Best Practices

### DO:
- ✅ Use dedicated wallets for trading
- ✅ Store secrets in `.env` file (never commit to git)
- ✅ Use environment variables, not hardcoded values
- ✅ Rotate API keys periodically
- ✅ Set spending limits where available
- ✅ Start with DRY_RUN=1 for testing

### DON'T:
- ❌ Share API keys or private keys
- ❌ Commit `.env` files to version control
- ❌ Use your main crypto wallet
- ❌ Store large amounts in trading wallets
- ❌ Disable DRY_RUN without thorough testing

---

## Troubleshooting

### "Invalid API Key" Errors
- Verify the key is copied correctly (no extra spaces)
- Check if the key has expired
- Ensure you're using the correct environment (prod vs sandbox)

### "Rate Limited" Errors
- Reduce request frequency
- Implement exponential backoff
- Check platform-specific rate limits

### "Insufficient Funds" Errors
- Verify wallet/account balance
- Check for pending transactions
- Ensure you have gas (for Polymarket)

### Connection Errors
- Verify RPC URL is correct
- Check internet connectivity
- Try alternative RPC endpoints

---

## Quick Reference

| Platform | Key Variables | Where to Get |
|----------|--------------|--------------|
| Polymarket | `POLY_PRIVATE_KEY`, `POLY_RPC_URL` | MetaMask + Infura |
| Kalshi | `KALSHI_API_KEY`, `KALSHI_API_SECRET` | Kalshi Dashboard |
| Manifold | `MANIFOLD_API_KEY`, `MANIFOLD_USERNAME` | Manifold Profile |
| PredictIt | `PREDICTIT_API_TOKEN` | Browser DevTools |
| OpenAI | `OPENAI_API_KEY` | platform.openai.com |
| Anthropic | `ANTHROPIC_API_KEY` | console.anthropic.com |
| Polyseer | `VALYU_API_KEY` | valyu.ai |
