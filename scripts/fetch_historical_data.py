#!/usr/bin/env python3
"""
Historical Data Fetcher for PredictBot Backtesting

Fetches real historical market data from:
- Kalshi (via API)
- Polymarket (via Gamma API)
- Manifold Markets (via public API)

This data is used for comprehensive backtesting of all trading strategies.
"""

import os
import sys
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class HistoricalMarket:
    """Represents a historical market with price history."""
    market_id: str
    platform: str  # kalshi, polymarket, manifold
    title: str
    description: str
    category: str
    created_at: datetime
    close_time: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution: Optional[str]  # YES, NO, or probability for manifold
    volume: float
    liquidity: float
    price_history: List[Dict]  # [{timestamp, yes_price, no_price, volume}]
    final_price: Optional[float]
    

class KalshiDataFetcher:
    """Fetches historical data from Kalshi."""
    
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def fetch_markets(self, limit: int = 200, status: str = "closed") -> List[Dict]:
        """Fetch markets from Kalshi API."""
        try:
            url = f"{self.BASE_URL}/markets"
            params = {
                "limit": limit,
                "status": status,
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("markets", [])
                else:
                    print(f"Kalshi API error: {response.status}")
                    return []
        except Exception as e:
            print(f"Error fetching Kalshi markets: {e}")
            return []
    
    async def fetch_market_history(self, ticker: str) -> List[Dict]:
        """Fetch price history for a specific market."""
        try:
            url = f"{self.BASE_URL}/markets/{ticker}/history"
            params = {"limit": 1000}
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("history", [])
                else:
                    return []
        except Exception as e:
            print(f"Error fetching Kalshi history for {ticker}: {e}")
            return []
    
    async def get_historical_markets(self, max_markets: int = 100) -> List[HistoricalMarket]:
        """Get historical markets with price data."""
        markets = await self.fetch_markets(limit=max_markets, status="closed")
        historical = []
        
        for market in markets[:max_markets]:
            try:
                ticker = market.get("ticker", "")
                history = await self.fetch_market_history(ticker)
                
                # Parse price history
                price_history = []
                for h in history:
                    price_history.append({
                        "timestamp": h.get("ts", ""),
                        "yes_price": h.get("yes_price", 50) / 100,
                        "no_price": h.get("no_price", 50) / 100,
                        "volume": h.get("volume", 0),
                    })
                
                # Determine resolution
                result = market.get("result", "")
                resolution = "YES" if result == "yes" else "NO" if result == "no" else None
                
                hist_market = HistoricalMarket(
                    market_id=ticker,
                    platform="kalshi",
                    title=market.get("title", ""),
                    description=market.get("subtitle", ""),
                    category=market.get("category", ""),
                    created_at=datetime.fromisoformat(market.get("open_time", "2024-01-01T00:00:00Z").replace("Z", "+00:00")),
                    close_time=datetime.fromisoformat(market.get("close_time", "2024-12-31T00:00:00Z").replace("Z", "+00:00")) if market.get("close_time") else None,
                    resolved_at=datetime.fromisoformat(market.get("expiration_time", "2024-12-31T00:00:00Z").replace("Z", "+00:00")) if market.get("expiration_time") else None,
                    resolution=resolution,
                    volume=market.get("volume", 0),
                    liquidity=market.get("open_interest", 0),
                    price_history=price_history,
                    final_price=market.get("last_price", 50) / 100 if market.get("last_price") else None,
                )
                historical.append(hist_market)
                
            except Exception as e:
                print(f"Error processing Kalshi market {market.get('ticker', 'unknown')}: {e}")
                continue
        
        return historical


class PolymarketDataFetcher:
    """Fetches historical data from Polymarket via Gamma API."""
    
    GAMMA_URL = "https://gamma-api.polymarket.com"
    CLOB_URL = "https://clob.polymarket.com"
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def fetch_markets(self, limit: int = 100, closed: bool = True) -> List[Dict]:
        """Fetch markets from Polymarket Gamma API."""
        try:
            url = f"{self.GAMMA_URL}/markets"
            params = {
                "limit": limit,
                "closed": str(closed).lower(),
                "order": "volume",
                "ascending": "false",
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Polymarket API error: {response.status}")
                    return []
        except Exception as e:
            print(f"Error fetching Polymarket markets: {e}")
            return []
    
    async def fetch_price_history(self, condition_id: str) -> List[Dict]:
        """Fetch price history for a market condition."""
        try:
            url = f"{self.GAMMA_URL}/prices"
            params = {
                "market": condition_id,
                "interval": "1h",
                "fidelity": 100,
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("history", []) if isinstance(data, dict) else data
                else:
                    return []
        except Exception as e:
            print(f"Error fetching Polymarket history: {e}")
            return []
    
    async def get_historical_markets(self, max_markets: int = 100) -> List[HistoricalMarket]:
        """Get historical markets with price data."""
        markets = await self.fetch_markets(limit=max_markets, closed=True)
        historical = []
        
        for market in markets[:max_markets]:
            try:
                condition_id = market.get("conditionId", market.get("id", ""))
                history = await self.fetch_price_history(condition_id)
                
                # Parse price history
                price_history = []
                for h in history if isinstance(history, list) else []:
                    price_history.append({
                        "timestamp": h.get("t", h.get("timestamp", "")),
                        "yes_price": float(h.get("p", h.get("price", 0.5))),
                        "no_price": 1 - float(h.get("p", h.get("price", 0.5))),
                        "volume": float(h.get("v", h.get("volume", 0))),
                    })
                
                # Determine resolution
                outcome = market.get("outcome", market.get("resolutionSource", ""))
                resolution = "YES" if outcome in ["Yes", "yes", "1"] else "NO" if outcome in ["No", "no", "0"] else None
                
                hist_market = HistoricalMarket(
                    market_id=condition_id,
                    platform="polymarket",
                    title=market.get("question", market.get("title", "")),
                    description=market.get("description", ""),
                    category=market.get("category", market.get("groupItemTitle", "")),
                    created_at=datetime.fromisoformat(market.get("createdAt", "2024-01-01T00:00:00Z").replace("Z", "+00:00")) if market.get("createdAt") else datetime.now(),
                    close_time=datetime.fromisoformat(market.get("endDate", "2024-12-31T00:00:00Z").replace("Z", "+00:00")) if market.get("endDate") else None,
                    resolved_at=datetime.fromisoformat(market.get("resolutionDate", "2024-12-31T00:00:00Z").replace("Z", "+00:00")) if market.get("resolutionDate") else None,
                    resolution=resolution,
                    volume=float(market.get("volume", market.get("volumeNum", 0))),
                    liquidity=float(market.get("liquidity", market.get("liquidityNum", 0))),
                    price_history=price_history,
                    final_price=float(market.get("outcomePrices", [0.5])[0]) if market.get("outcomePrices") else None,
                )
                historical.append(hist_market)
                
            except Exception as e:
                print(f"Error processing Polymarket market: {e}")
                continue
        
        return historical


class ManifoldDataFetcher:
    """Fetches historical data from Manifold Markets."""
    
    BASE_URL = "https://api.manifold.markets/v0"
    
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def fetch_markets(self, limit: int = 100) -> List[Dict]:
        """Fetch resolved markets from Manifold."""
        try:
            url = f"{self.BASE_URL}/markets"
            params = {
                "limit": limit,
                "sort": "most-popular",
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    markets = await response.json()
                    # Filter to resolved binary markets
                    return [m for m in markets if m.get("isResolved") and m.get("outcomeType") == "BINARY"]
                else:
                    print(f"Manifold API error: {response.status}")
                    return []
        except Exception as e:
            print(f"Error fetching Manifold markets: {e}")
            return []
    
    async def fetch_market_bets(self, market_id: str) -> List[Dict]:
        """Fetch bet history for a market."""
        try:
            url = f"{self.BASE_URL}/bets"
            params = {
                "contractId": market_id,
                "limit": 1000,
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return []
        except Exception as e:
            print(f"Error fetching Manifold bets: {e}")
            return []
    
    async def get_historical_markets(self, max_markets: int = 100) -> List[HistoricalMarket]:
        """Get historical markets with price data."""
        markets = await self.fetch_markets(limit=max_markets * 2)  # Fetch more to filter
        historical = []
        
        for market in markets[:max_markets]:
            try:
                market_id = market.get("id", "")
                bets = await self.fetch_market_bets(market_id)
                
                # Build price history from bets
                price_history = []
                for bet in sorted(bets, key=lambda x: x.get("createdTime", 0)):
                    price_history.append({
                        "timestamp": datetime.fromtimestamp(bet.get("createdTime", 0) / 1000).isoformat(),
                        "yes_price": bet.get("probAfter", 0.5),
                        "no_price": 1 - bet.get("probAfter", 0.5),
                        "volume": abs(bet.get("amount", 0)),
                    })
                
                # Determine resolution
                resolution_prob = market.get("resolutionProbability", market.get("resolution"))
                if resolution_prob == "YES" or resolution_prob == 1:
                    resolution = "YES"
                elif resolution_prob == "NO" or resolution_prob == 0:
                    resolution = "NO"
                else:
                    resolution = None
                
                hist_market = HistoricalMarket(
                    market_id=market_id,
                    platform="manifold",
                    title=market.get("question", ""),
                    description=market.get("description", "")[:500] if market.get("description") else "",
                    category=market.get("groupSlugs", ["general"])[0] if market.get("groupSlugs") else "general",
                    created_at=datetime.fromtimestamp(market.get("createdTime", 0) / 1000),
                    close_time=datetime.fromtimestamp(market.get("closeTime", 0) / 1000) if market.get("closeTime") else None,
                    resolved_at=datetime.fromtimestamp(market.get("resolutionTime", 0) / 1000) if market.get("resolutionTime") else None,
                    resolution=resolution,
                    volume=market.get("volume", 0),
                    liquidity=market.get("totalLiquidity", 0),
                    price_history=price_history,
                    final_price=market.get("probability", 0.5),
                )
                historical.append(hist_market)
                
            except Exception as e:
                print(f"Error processing Manifold market {market.get('id', 'unknown')}: {e}")
                continue
        
        return historical


class HistoricalDataManager:
    """Manages historical data collection and storage."""
    
    def __init__(self, data_dir: str = "data/historical"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def fetch_all_platforms(self, markets_per_platform: int = 50) -> Dict[str, List[HistoricalMarket]]:
        """Fetch historical data from all platforms."""
        all_data = {}
        
        print("\n" + "="*60)
        print("📊 FETCHING HISTORICAL DATA FROM ALL PLATFORMS")
        print("="*60)
        
        # Fetch from Kalshi
        print("\n🔵 Fetching Kalshi data...")
        try:
            async with KalshiDataFetcher() as fetcher:
                kalshi_markets = await fetcher.get_historical_markets(markets_per_platform)
                all_data["kalshi"] = kalshi_markets
                print(f"   ✅ Fetched {len(kalshi_markets)} Kalshi markets")
        except Exception as e:
            print(f"   ❌ Kalshi fetch failed: {e}")
            all_data["kalshi"] = []
        
        # Fetch from Polymarket
        print("\n🟣 Fetching Polymarket data...")
        try:
            async with PolymarketDataFetcher() as fetcher:
                poly_markets = await fetcher.get_historical_markets(markets_per_platform)
                all_data["polymarket"] = poly_markets
                print(f"   ✅ Fetched {len(poly_markets)} Polymarket markets")
        except Exception as e:
            print(f"   ❌ Polymarket fetch failed: {e}")
            all_data["polymarket"] = []
        
        # Fetch from Manifold
        print("\n🟢 Fetching Manifold data...")
        try:
            async with ManifoldDataFetcher() as fetcher:
                manifold_markets = await fetcher.get_historical_markets(markets_per_platform)
                all_data["manifold"] = manifold_markets
                print(f"   ✅ Fetched {len(manifold_markets)} Manifold markets")
        except Exception as e:
            print(f"   ❌ Manifold fetch failed: {e}")
            all_data["manifold"] = []
        
        return all_data
    
    def save_data(self, data: Dict[str, List[HistoricalMarket]], filename: str = "historical_markets.json"):
        """Save historical data to JSON file."""
        filepath = self.data_dir / filename
        
        # Convert to serializable format
        serializable = {}
        for platform, markets in data.items():
            serializable[platform] = []
            for market in markets:
                market_dict = asdict(market)
                # Convert datetime objects to strings
                for key in ["created_at", "close_time", "resolved_at"]:
                    if market_dict[key]:
                        market_dict[key] = market_dict[key].isoformat()
                serializable[platform].append(market_dict)
        
        with open(filepath, "w") as f:
            json.dump(serializable, f, indent=2)
        
        print(f"\n💾 Saved historical data to {filepath}")
        return filepath
    
    def load_data(self, filename: str = "historical_markets.json") -> Dict[str, List[HistoricalMarket]]:
        """Load historical data from JSON file."""
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            print(f"❌ Data file not found: {filepath}")
            return {}
        
        with open(filepath, "r") as f:
            data = json.load(f)
        
        # Convert back to HistoricalMarket objects
        result = {}
        for platform, markets in data.items():
            result[platform] = []
            for market_dict in markets:
                # Convert datetime strings back to datetime objects
                for key in ["created_at", "close_time", "resolved_at"]:
                    if market_dict[key]:
                        market_dict[key] = datetime.fromisoformat(market_dict[key])
                result[platform].append(HistoricalMarket(**market_dict))
        
        return result
    
    def get_summary(self, data: Dict[str, List[HistoricalMarket]]) -> Dict:
        """Get summary statistics of historical data."""
        summary = {
            "total_markets": 0,
            "platforms": {},
            "categories": {},
            "resolutions": {"YES": 0, "NO": 0, "UNKNOWN": 0},
            "total_volume": 0,
            "avg_price_points": 0,
        }
        
        total_price_points = 0
        
        for platform, markets in data.items():
            summary["platforms"][platform] = {
                "count": len(markets),
                "volume": sum(m.volume for m in markets),
                "resolved": sum(1 for m in markets if m.resolution),
            }
            summary["total_markets"] += len(markets)
            summary["total_volume"] += sum(m.volume for m in markets)
            
            for market in markets:
                # Count resolutions
                if market.resolution == "YES":
                    summary["resolutions"]["YES"] += 1
                elif market.resolution == "NO":
                    summary["resolutions"]["NO"] += 1
                else:
                    summary["resolutions"]["UNKNOWN"] += 1
                
                # Count categories
                cat = market.category or "unknown"
                summary["categories"][cat] = summary["categories"].get(cat, 0) + 1
                
                # Count price points
                total_price_points += len(market.price_history)
        
        if summary["total_markets"] > 0:
            summary["avg_price_points"] = total_price_points / summary["total_markets"]
        
        return summary


async def main():
    """Main function to fetch and save historical data."""
    print("\n" + "="*70)
    print("🚀 PREDICTBOT HISTORICAL DATA FETCHER")
    print("="*70)
    
    manager = HistoricalDataManager()
    
    # Fetch data from all platforms
    data = await manager.fetch_all_platforms(markets_per_platform=50)
    
    # Save data
    manager.save_data(data)
    
    # Print summary
    summary = manager.get_summary(data)
    
    print("\n" + "="*60)
    print("📈 DATA SUMMARY")
    print("="*60)
    print(f"\nTotal Markets: {summary['total_markets']}")
    print(f"Total Volume: ${summary['total_volume']:,.2f}")
    print(f"Avg Price Points per Market: {summary['avg_price_points']:.1f}")
    
    print("\n📊 By Platform:")
    for platform, stats in summary["platforms"].items():
        print(f"   {platform.capitalize()}: {stats['count']} markets, ${stats['volume']:,.2f} volume, {stats['resolved']} resolved")
    
    print("\n🎯 Resolutions:")
    for res, count in summary["resolutions"].items():
        print(f"   {res}: {count}")
    
    print("\n📁 Top Categories:")
    sorted_cats = sorted(summary["categories"].items(), key=lambda x: x[1], reverse=True)[:10]
    for cat, count in sorted_cats:
        print(f"   {cat}: {count}")
    
    print("\n✅ Historical data fetch complete!")
    return data


if __name__ == "__main__":
    asyncio.run(main())
