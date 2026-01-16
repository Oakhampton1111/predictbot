#!/usr/bin/env python3
"""
PredictBot - Market Data Collection Script
==========================================

Collects historical and real-time market data from prediction market platforms.

Usage:
    # Collect data from all platforms
    python scripts/collect_market_data.py --platforms all --duration 24h
    
    # Collect from specific platform
    python scripts/collect_market_data.py --platforms polymarket --duration 7d
    
    # Continuous collection mode
    python scripts/collect_market_data.py --continuous --interval 60
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation.data import (
    CollectorConfig,
    PolymarketCollector,
    KalshiCollector,
    FileDataStore,
    SQLiteDataStore,
)
from simulation.models import Platform


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string like '24h', '7d', '30m'."""
    unit = duration_str[-1].lower()
    value = int(duration_str[:-1])
    
    if unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    else:
        raise ValueError(f"Unknown duration unit: {unit}")


async def collect_once(
    collectors: list,
    store,
    include_orderbooks: bool = True,
    include_trades: bool = True,
):
    """Run a single collection cycle."""
    total_snapshots = 0
    total_orderbooks = 0
    total_trades = 0
    total_resolutions = 0
    
    for collector in collectors:
        try:
            logger.info(f"Collecting from {collector.platform.value}...")
            
            # Collect snapshots
            snapshots = await collector.collect_all_snapshots()
            if snapshots:
                saved = store.save_snapshots(snapshots)
                total_snapshots += saved
                logger.info(f"  Saved {saved} snapshots")
            
            # Collect order books
            if include_orderbooks:
                orderbooks = await collector.collect_all_orderbooks()
                if orderbooks:
                    saved = store.save_orderbooks(orderbooks)
                    total_orderbooks += saved
                    logger.info(f"  Saved {saved} orderbooks")
            
            # Collect trades
            if include_trades:
                trades = await collector.collect_all_trades()
                if trades:
                    saved = store.save_trades(trades)
                    total_trades += saved
                    logger.info(f"  Saved {saved} trades")
            
            # Collect resolutions
            resolutions = await collector.fetch_resolutions()
            if resolutions:
                saved = store.save_resolutions(resolutions)
                total_resolutions += saved
                logger.info(f"  Saved {saved} resolutions")
                
        except Exception as e:
            logger.error(f"Error collecting from {collector.platform.value}: {e}")
    
    return {
        "snapshots": total_snapshots,
        "orderbooks": total_orderbooks,
        "trades": total_trades,
        "resolutions": total_resolutions,
    }


async def run_continuous_collection(
    collectors: list,
    store,
    interval_seconds: int = 60,
    include_orderbooks: bool = True,
    include_trades: bool = True,
):
    """Run continuous data collection."""
    logger.info(f"Starting continuous collection (interval: {interval_seconds}s)")
    
    try:
        while True:
            start_time = datetime.utcnow()
            
            results = await collect_once(
                collectors, store, include_orderbooks, include_trades
            )
            
            logger.info(
                f"Collection complete: {results['snapshots']} snapshots, "
                f"{results['orderbooks']} orderbooks, {results['trades']} trades"
            )
            
            # Wait for next interval
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            sleep_time = max(0, interval_seconds - elapsed)
            
            if sleep_time > 0:
                logger.debug(f"Sleeping for {sleep_time:.1f}s")
                await asyncio.sleep(sleep_time)
                
    except asyncio.CancelledError:
        logger.info("Collection stopped")
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")


async def main():
    parser = argparse.ArgumentParser(
        description="Collect market data from prediction market platforms"
    )
    
    parser.add_argument(
        "--platforms",
        type=str,
        default="all",
        help="Platforms to collect from (all, polymarket, kalshi)"
    )
    
    parser.add_argument(
        "--duration",
        type=str,
        default="24h",
        help="Duration to collect (e.g., 24h, 7d, 30m)"
    )
    
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuous collection"
    )
    
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Collection interval in seconds (for continuous mode)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="./data/market_data",
        help="Output directory or database path"
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "sqlite"],
        default="sqlite",
        help="Storage format"
    )
    
    parser.add_argument(
        "--max-markets",
        type=int,
        default=100,
        help="Maximum markets to track per platform"
    )
    
    parser.add_argument(
        "--min-volume",
        type=float,
        default=1000.0,
        help="Minimum 24h volume to include"
    )
    
    parser.add_argument(
        "--no-orderbooks",
        action="store_true",
        help="Skip order book collection"
    )
    
    parser.add_argument(
        "--no-trades",
        action="store_true",
        help="Skip trade collection"
    )
    
    parser.add_argument(
        "--polymarket-api-key",
        type=str,
        default=os.environ.get("POLYMARKET_API_KEY"),
        help="Polymarket API key"
    )
    
    parser.add_argument(
        "--kalshi-email",
        type=str,
        default=os.environ.get("KALSHI_EMAIL"),
        help="Kalshi email"
    )
    
    parser.add_argument(
        "--kalshi-password",
        type=str,
        default=os.environ.get("KALSHI_PASSWORD"),
        help="Kalshi password"
    )
    
    parser.add_argument(
        "--kalshi-demo",
        action="store_true",
        help="Use Kalshi demo environment"
    )
    
    args = parser.parse_args()
    
    # Create collector config
    config = CollectorConfig(
        max_markets=args.max_markets,
        min_volume_24h=args.min_volume,
        collection_interval_seconds=args.interval,
    )
    
    # Create collectors
    collectors = []
    platforms = args.platforms.lower().split(",")
    
    if "all" in platforms or "polymarket" in platforms:
        poly_config = CollectorConfig(
            api_key=args.polymarket_api_key,
            max_markets=args.max_markets,
            min_volume_24h=args.min_volume,
        )
        collectors.append(PolymarketCollector(poly_config))
        logger.info("Added Polymarket collector")
    
    if "all" in platforms or "kalshi" in platforms:
        kalshi_config = CollectorConfig(
            api_key=args.kalshi_email,
            api_secret=args.kalshi_password,
            max_markets=args.max_markets,
            min_volume_24h=args.min_volume,
        )
        collectors.append(KalshiCollector(kalshi_config, use_demo=args.kalshi_demo))
        logger.info("Added Kalshi collector")
    
    if not collectors:
        logger.error("No collectors configured")
        return 1
    
    # Create data store
    if args.format == "sqlite":
        db_path = args.output if args.output.endswith(".db") else f"{args.output}.db"
        store = SQLiteDataStore(db_path)
        logger.info(f"Using SQLite storage: {db_path}")
    else:
        store = FileDataStore(args.output)
        logger.info(f"Using file storage: {args.output}")
    
    # Initialize collectors
    for collector in collectors:
        if not await collector.initialize():
            logger.error(f"Failed to initialize {collector.platform.value} collector")
            return 1
    
    try:
        if args.continuous:
            # Run continuous collection
            await run_continuous_collection(
                collectors,
                store,
                interval_seconds=args.interval,
                include_orderbooks=not args.no_orderbooks,
                include_trades=not args.no_trades,
            )
        else:
            # Run single collection
            duration = parse_duration(args.duration)
            end_time = datetime.utcnow()
            start_time = end_time - duration
            
            logger.info(f"Collecting data from {start_time} to {end_time}")
            
            results = await collect_once(
                collectors,
                store,
                include_orderbooks=not args.no_orderbooks,
                include_trades=not args.no_trades,
            )
            
            logger.info("Collection complete!")
            logger.info(f"  Snapshots: {results['snapshots']}")
            logger.info(f"  Order books: {results['orderbooks']}")
            logger.info(f"  Trades: {results['trades']}")
            logger.info(f"  Resolutions: {results['resolutions']}")
            
    finally:
        # Cleanup
        for collector in collectors:
            await collector.disconnect()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
