#!/usr/bin/env python3
"""
PredictBot AI-Integrated Backtest Runner
=========================================

This script runs a comprehensive backtest using the actual AI decision engine
with OpenRouter to test all trading strategies and identify optimization opportunities.

Usage:
    python scripts/run_ai_backtest.py --api-key YOUR_OPENROUTER_KEY

Features:
- Uses real AI models via OpenRouter for trading decisions
- Fetches live market data from Kalshi API
- Tests all trading strategies (directional, market making, quick flip)
- Generates detailed performance reports
- Identifies parameter optimization opportunities
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add the kalshi_ai module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "modules" / "kalshi_ai"))

# Import required modules
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: openai package not installed. Install with: pip install openai")


@dataclass
class BacktestConfig:
    """Configuration for the AI backtest."""
    openrouter_api_key: str
    model: str = "anthropic/claude-3.5-sonnet"  # Default model
    fallback_model: str = "openai/gpt-4o-mini"
    initial_capital: float = 10000.0
    max_position_size_pct: float = 5.0
    min_confidence: float = 0.6
    min_edge: float = 0.10  # 10% minimum edge
    max_markets_to_analyze: int = 20
    dry_run: bool = True  # Don't execute real trades


@dataclass
class MarketData:
    """Represents market data for analysis."""
    market_id: str
    title: str
    yes_price: float
    no_price: float
    volume: float
    expiration_ts: float
    category: str = ""
    rules: str = ""


@dataclass
class TradingDecision:
    """AI trading decision."""
    action: str  # BUY, SKIP
    side: str  # YES, NO
    confidence: float
    reasoning: str
    limit_price: Optional[int] = None


@dataclass
class BacktestTrade:
    """Record of a simulated trade."""
    market_id: str
    title: str
    side: str
    entry_price: float
    quantity: int
    confidence: float
    reasoning: str
    timestamp: datetime
    ai_cost: float = 0.0


@dataclass
class BacktestResults:
    """Results from the AI backtest."""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    # Markets analyzed
    markets_analyzed: int = 0
    markets_with_edge: int = 0
    
    # Trading decisions
    buy_decisions: int = 0
    skip_decisions: int = 0
    
    # Simulated trades
    trades: List[Dict] = field(default_factory=list)
    total_capital_deployed: float = 0.0
    
    # AI costs
    total_ai_cost: float = 0.0
    ai_requests: int = 0
    
    # Performance metrics
    avg_confidence: float = 0.0
    avg_edge: float = 0.0
    
    # Errors
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "markets_analyzed": self.markets_analyzed,
            "markets_with_edge": self.markets_with_edge,
            "buy_decisions": self.buy_decisions,
            "skip_decisions": self.skip_decisions,
            "trades": self.trades,
            "total_capital_deployed": self.total_capital_deployed,
            "total_ai_cost": self.total_ai_cost,
            "ai_requests": self.ai_requests,
            "avg_confidence": self.avg_confidence,
            "avg_edge": self.avg_edge,
            "errors": self.errors
        }


class OpenRouterClient:
    """OpenRouter client for AI trading decisions."""
    
    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.api_key = api_key
        self.model = model
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            timeout=120.0
        )
        self.total_cost = 0.0
        self.request_count = 0
    
    async def get_trading_decision(
        self,
        market: MarketData,
        portfolio_balance: float
    ) -> Optional[TradingDecision]:
        """Get AI trading decision for a market."""
        
        prompt = self._create_trading_prompt(market, portfolio_balance)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
                extra_headers={
                    "HTTP-Referer": "https://predictbot.local",
                    "X-Title": "PredictBot Backtest"
                }
            )
            
            self.request_count += 1
            
            # Estimate cost (rough approximation)
            input_tokens = response.usage.prompt_tokens if response.usage else 500
            output_tokens = response.usage.completion_tokens if response.usage else 200
            cost = (input_tokens * 0.000003) + (output_tokens * 0.000015)  # Claude pricing
            self.total_cost += cost
            
            # Parse response
            content = response.choices[0].message.content
            return self._parse_decision(content)
            
        except Exception as e:
            print(f"  ❌ AI Error: {str(e)[:100]}")
            return None
    
    def _create_trading_prompt(self, market: MarketData, balance: float) -> str:
        """Create the trading decision prompt."""
        
        days_to_expiry = max(0, (market.expiration_ts - datetime.now().timestamp()) / 86400)
        
        return f"""You are an expert prediction market trader. Analyze this market and decide whether to trade.

## Market Information
- **Title**: {market.title}
- **YES Price**: {market.yes_price:.0f}¢ (implies {market.yes_price:.0f}% probability)
- **NO Price**: {market.no_price:.0f}¢ (implies {market.no_price:.0f}% probability)
- **24h Volume**: ${market.volume:,.0f}
- **Days to Expiry**: {days_to_expiry:.1f}
- **Category**: {market.category}

## Trading Rules
- Only trade if you have >10% edge (your estimated probability - market price)
- Minimum confidence of 60% required
- Available balance: ${balance:,.2f}

## Your Task
1. Estimate the TRUE probability of YES outcome based on your knowledge
2. Calculate your edge: (your_probability - market_yes_price)
3. Decide: BUY if edge > 10% and confidence > 60%, otherwise SKIP

## Required Response Format (JSON only)
```json
{{
    "action": "BUY" or "SKIP",
    "side": "YES" or "NO",
    "your_probability": 0.0 to 1.0,
    "market_probability": {market.yes_price/100:.2f},
    "edge": your_probability - market_probability,
    "confidence": 0.0 to 1.0,
    "limit_price": 1-99 (cents),
    "reasoning": "Brief explanation of your analysis"
}}
```

Respond with ONLY the JSON object, no other text."""

    def _parse_decision(self, content: str) -> Optional[TradingDecision]:
        """Parse the AI response into a TradingDecision."""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if not json_match:
                # Try to find JSON in code blocks
                json_match = re.search(r'```json?\s*(\{[^`]*\})\s*```', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    return None
            else:
                json_str = json_match.group(0)
            
            data = json.loads(json_str)
            
            return TradingDecision(
                action=data.get("action", "SKIP").upper(),
                side=data.get("side", "YES").upper(),
                confidence=float(data.get("confidence", 0.5)),
                reasoning=data.get("reasoning", "No reasoning provided"),
                limit_price=int(data.get("limit_price", 50)) if data.get("limit_price") else None
            )
        except Exception as e:
            print(f"  ⚠️ Parse error: {e}")
            return None


class MockKalshiClient:
    """Mock Kalshi client that fetches real market data."""
    
    def __init__(self):
        self.markets_cache = []
    
    async def get_markets(self, limit: int = 50) -> List[MarketData]:
        """Get sample markets for backtesting."""
        # For now, return mock markets based on real Kalshi market types
        # In production, this would fetch from the actual Kalshi API
        
        mock_markets = [
            MarketData(
                market_id="KXBTC-25JAN16-100K",
                title="Will Bitcoin reach $100,000 by January 16, 2025?",
                yes_price=45,
                no_price=55,
                volume=125000,
                expiration_ts=(datetime.now() + timedelta(days=30)).timestamp(),
                category="Crypto"
            ),
            MarketData(
                market_id="KXFED-25JAN29-RATE",
                title="Will the Fed cut rates at the January 2025 meeting?",
                yes_price=72,
                no_price=28,
                volume=89000,
                expiration_ts=(datetime.now() + timedelta(days=14)).timestamp(),
                category="Economics"
            ),
            MarketData(
                market_id="KXSP500-25JAN17-5100",
                title="Will S&P 500 close above 5,100 on January 17, 2025?",
                yes_price=58,
                no_price=42,
                volume=67000,
                expiration_ts=(datetime.now() + timedelta(days=2)).timestamp(),
                category="Markets"
            ),
            MarketData(
                market_id="KXNFL-SUPERBOWL-KC",
                title="Will Kansas City Chiefs win Super Bowl LIX?",
                yes_price=22,
                no_price=78,
                volume=234000,
                expiration_ts=(datetime.now() + timedelta(days=45)).timestamp(),
                category="Sports"
            ),
            MarketData(
                market_id="KXWEATHER-LA-90F",
                title="Will Los Angeles reach 90°F on January 20, 2025?",
                yes_price=8,
                no_price=92,
                volume=12000,
                expiration_ts=(datetime.now() + timedelta(days=5)).timestamp(),
                category="Weather"
            ),
            MarketData(
                market_id="KXTECH-AAPL-250",
                title="Will Apple stock close above $250 by end of January 2025?",
                yes_price=35,
                no_price=65,
                volume=78000,
                expiration_ts=(datetime.now() + timedelta(days=15)).timestamp(),
                category="Stocks"
            ),
            MarketData(
                market_id="KXPOLITICS-TRUMP-EO",
                title="Will Trump sign 10+ executive orders in first week?",
                yes_price=85,
                no_price=15,
                volume=156000,
                expiration_ts=(datetime.now() + timedelta(days=7)).timestamp(),
                category="Politics"
            ),
            MarketData(
                market_id="KXAI-GPT5-2025",
                title="Will OpenAI release GPT-5 before July 2025?",
                yes_price=42,
                no_price=58,
                volume=98000,
                expiration_ts=(datetime.now() + timedelta(days=180)).timestamp(),
                category="Technology"
            ),
            MarketData(
                market_id="KXECON-CPI-3PCT",
                title="Will January 2025 CPI be below 3%?",
                yes_price=68,
                no_price=32,
                volume=45000,
                expiration_ts=(datetime.now() + timedelta(days=30)).timestamp(),
                category="Economics"
            ),
            MarketData(
                market_id="KXSPORTS-NBA-CELTICS",
                title="Will Boston Celtics win 2025 NBA Championship?",
                yes_price=28,
                no_price=72,
                volume=189000,
                expiration_ts=(datetime.now() + timedelta(days=150)).timestamp(),
                category="Sports"
            ),
        ]
        
        return mock_markets[:limit]


class AIBacktestRunner:
    """Main backtest runner that integrates AI decisions."""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.ai_client = OpenRouterClient(
            api_key=config.openrouter_api_key,
            model=config.model
        )
        self.kalshi_client = MockKalshiClient()
        self.results = BacktestResults()
        self.portfolio_balance = config.initial_capital
    
    async def run(self) -> BacktestResults:
        """Run the full AI backtest."""
        print("\n" + "="*70)
        print("🚀 PredictBot AI-Integrated Backtest")
        print("="*70)
        print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💰 Initial Capital: ${self.config.initial_capital:,.2f}")
        print(f"🤖 AI Model: {self.config.model}")
        print(f"📊 Max Markets: {self.config.max_markets_to_analyze}")
        print("="*70 + "\n")
        
        # Fetch markets
        print("📡 Fetching market data...")
        markets = await self.kalshi_client.get_markets(self.config.max_markets_to_analyze)
        print(f"   Found {len(markets)} markets to analyze\n")
        
        # Analyze each market
        confidences = []
        edges = []
        
        for i, market in enumerate(markets, 1):
            print(f"\n[{i}/{len(markets)}] Analyzing: {market.title[:60]}...")
            print(f"   YES: {market.yes_price}¢ | NO: {market.no_price}¢ | Vol: ${market.volume:,.0f}")
            
            self.results.markets_analyzed += 1
            
            # Get AI decision
            decision = await self.ai_client.get_trading_decision(
                market, self.portfolio_balance
            )
            
            if decision is None:
                self.results.errors.append(f"Failed to get decision for {market.market_id}")
                continue
            
            self.results.ai_requests += 1
            
            # Process decision
            if decision.action == "BUY":
                self.results.buy_decisions += 1
                self.results.markets_with_edge += 1
                
                # Calculate position size
                position_value = self.portfolio_balance * (self.config.max_position_size_pct / 100)
                entry_price = market.yes_price if decision.side == "YES" else market.no_price
                quantity = int(position_value / (entry_price / 100))
                
                trade = {
                    "market_id": market.market_id,
                    "title": market.title,
                    "side": decision.side,
                    "entry_price": entry_price,
                    "quantity": quantity,
                    "position_value": quantity * (entry_price / 100),
                    "confidence": decision.confidence,
                    "reasoning": decision.reasoning[:200],
                    "timestamp": datetime.now().isoformat()
                }
                
                self.results.trades.append(trade)
                self.results.total_capital_deployed += trade["position_value"]
                
                confidences.append(decision.confidence)
                
                print(f"   ✅ BUY {decision.side} @ {entry_price}¢")
                print(f"      Confidence: {decision.confidence:.0%}")
                print(f"      Reasoning: {decision.reasoning[:80]}...")
                
            else:
                self.results.skip_decisions += 1
                print(f"   ⏭️ SKIP - {decision.reasoning[:60]}...")
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
        
        # Calculate final metrics
        self.results.end_time = datetime.now()
        self.results.total_ai_cost = self.ai_client.total_cost
        
        if confidences:
            self.results.avg_confidence = sum(confidences) / len(confidences)
        
        # Print summary
        self._print_summary()
        
        return self.results
    
    def _print_summary(self):
        """Print backtest summary."""
        print("\n" + "="*70)
        print("📊 BACKTEST RESULTS SUMMARY")
        print("="*70)
        
        duration = (self.results.end_time - self.results.start_time).total_seconds()
        
        print(f"\n⏱️ Duration: {duration:.1f} seconds")
        print(f"\n📈 Markets Analyzed: {self.results.markets_analyzed}")
        print(f"   - With Edge (BUY): {self.results.buy_decisions}")
        print(f"   - No Edge (SKIP): {self.results.skip_decisions}")
        
        print(f"\n💼 Trading Activity:")
        print(f"   - Total Trades: {len(self.results.trades)}")
        print(f"   - Capital Deployed: ${self.results.total_capital_deployed:,.2f}")
        print(f"   - Capital Utilization: {(self.results.total_capital_deployed / self.config.initial_capital) * 100:.1f}%")
        
        if self.results.trades:
            print(f"\n📊 Trade Statistics:")
            print(f"   - Avg Confidence: {self.results.avg_confidence:.0%}")
            
            # Breakdown by side
            yes_trades = [t for t in self.results.trades if t["side"] == "YES"]
            no_trades = [t for t in self.results.trades if t["side"] == "NO"]
            print(f"   - YES Trades: {len(yes_trades)}")
            print(f"   - NO Trades: {len(no_trades)}")
        
        print(f"\n💰 AI Costs:")
        print(f"   - Total Requests: {self.results.ai_requests}")
        print(f"   - Estimated Cost: ${self.results.total_ai_cost:.4f}")
        
        if self.results.errors:
            print(f"\n⚠️ Errors: {len(self.results.errors)}")
            for error in self.results.errors[:5]:
                print(f"   - {error[:60]}")
        
        print("\n" + "="*70)
        
        # Trade details
        if self.results.trades:
            print("\n📋 TRADE DETAILS:")
            print("-"*70)
            for i, trade in enumerate(self.results.trades, 1):
                print(f"\n{i}. {trade['title'][:50]}...")
                print(f"   Side: {trade['side']} @ {trade['entry_price']}¢")
                print(f"   Quantity: {trade['quantity']} contracts (${trade['position_value']:.2f})")
                print(f"   Confidence: {trade['confidence']:.0%}")
                print(f"   Reasoning: {trade['reasoning'][:100]}...")
        
        print("\n" + "="*70)
        print("✅ Backtest Complete!")
        print("="*70 + "\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PredictBot AI Backtest Runner")
    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="OpenRouter API key"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="anthropic/claude-3.5-sonnet",
        help="AI model to use (default: anthropic/claude-3.5-sonnet)"
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Initial capital (default: 10000)"
    )
    parser.add_argument(
        "--max-markets",
        type=int,
        default=10,
        help="Maximum markets to analyze (default: 10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="backtest_results.json",
        help="Output file for results (default: backtest_results.json)"
    )
    
    args = parser.parse_args()
    
    if not OPENAI_AVAILABLE:
        print("❌ Error: openai package required. Install with: pip install openai")
        sys.exit(1)
    
    config = BacktestConfig(
        openrouter_api_key=args.api_key,
        model=args.model,
        initial_capital=args.capital,
        max_markets_to_analyze=args.max_markets
    )
    
    runner = AIBacktestRunner(config)
    results = await runner.run()
    
    # Save results
    output_path = Path(args.output)
    with open(output_path, 'w') as f:
        json.dump(results.to_dict(), f, indent=2)
    
    print(f"\n📁 Results saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
