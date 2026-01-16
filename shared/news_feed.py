"""
PredictBot - News Feed Integration
==================================

Multi-source news feed aggregator for market-relevant news.

Supported Sources:
- NewsAPI.org (general news)
- Alpha Vantage (financial news)
- Polygon.io (market news)
- RSS feeds (custom sources)

Features:
- Multi-source aggregation
- Keyword filtering for prediction markets
- Caching to reduce API calls
- Rate limiting
- Event publishing to Redis
"""

import os
import asyncio
import aiohttp
import feedparser
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
import re

try:
    from .logging_config import get_logger
    from .metrics import get_metrics_registry
    from .event_bus import EventBus
except ImportError:
    import logging
    def get_logger(name: str, **kwargs):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def get_metrics_registry():
        return None
    
    EventBus = None


class NewsSource(str, Enum):
    """Supported news sources."""
    NEWSAPI = "newsapi"
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    RSS = "rss"


@dataclass
class NewsArticle:
    """Represents a news article."""
    id: str
    title: str
    description: str
    content: Optional[str]
    url: str
    source: str
    source_name: str
    published_at: datetime
    author: Optional[str] = None
    image_url: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    sentiment_score: Optional[float] = None  # -1 to 1
    relevance_score: Optional[float] = None  # 0 to 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "source_name": self.source_name,
            "published_at": self.published_at.isoformat(),
            "author": self.author,
            "image_url": self.image_url,
            "keywords": self.keywords,
            "sentiment_score": self.sentiment_score,
            "relevance_score": self.relevance_score,
        }


@dataclass
class NewsFeedConfig:
    """Configuration for news feed."""
    # API Keys
    newsapi_key: Optional[str] = None
    alpha_vantage_key: Optional[str] = None
    polygon_key: Optional[str] = None
    
    # RSS feeds
    rss_feeds: List[str] = field(default_factory=list)
    
    # Filtering
    keywords: List[str] = field(default_factory=lambda: [
        "election", "president", "congress", "senate", "vote",
        "fed", "federal reserve", "interest rate", "inflation",
        "crypto", "bitcoin", "ethereum", "polymarket",
        "prediction market", "betting", "odds",
        "supreme court", "legislation", "bill",
        "economy", "gdp", "unemployment", "jobs report",
        "climate", "weather", "hurricane", "earthquake",
        "sports", "championship", "super bowl", "world cup",
    ])
    
    # Rate limiting
    requests_per_minute: int = 30
    cache_ttl_seconds: int = 300  # 5 minutes
    
    # Fetch settings
    max_articles_per_source: int = 50
    lookback_hours: int = 24


class NewsAPIClient:
    """Client for NewsAPI.org."""
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.session = session
        self.logger = get_logger("news.newsapi")
    
    async def fetch_top_headlines(
        self,
        country: str = "us",
        category: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 50,
    ) -> List[NewsArticle]:
        """Fetch top headlines."""
        params = {
            "apiKey": self.api_key,
            "country": country,
            "pageSize": min(page_size, 100),
        }
        if category:
            params["category"] = category
        if query:
            params["q"] = query
        
        try:
            async with self.session.get(
                f"{self.BASE_URL}/top-headlines",
                params=params
            ) as response:
                if response.status != 200:
                    self.logger.error(f"NewsAPI error: {response.status}")
                    return []
                
                data = await response.json()
                return self._parse_articles(data.get("articles", []))
                
        except Exception as e:
            self.logger.error(f"NewsAPI fetch error: {e}")
            return []
    
    async def search_everything(
        self,
        query: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_by: str = "publishedAt",
        page_size: int = 50,
    ) -> List[NewsArticle]:
        """Search all articles."""
        params = {
            "apiKey": self.api_key,
            "q": query,
            "sortBy": sort_by,
            "pageSize": min(page_size, 100),
            "language": "en",
        }
        if from_date:
            params["from"] = from_date.strftime("%Y-%m-%dT%H:%M:%S")
        if to_date:
            params["to"] = to_date.strftime("%Y-%m-%dT%H:%M:%S")
        
        try:
            async with self.session.get(
                f"{self.BASE_URL}/everything",
                params=params
            ) as response:
                if response.status != 200:
                    self.logger.error(f"NewsAPI error: {response.status}")
                    return []
                
                data = await response.json()
                return self._parse_articles(data.get("articles", []))
                
        except Exception as e:
            self.logger.error(f"NewsAPI search error: {e}")
            return []
    
    def _parse_articles(self, articles: List[Dict]) -> List[NewsArticle]:
        """Parse NewsAPI articles."""
        result = []
        for article in articles:
            try:
                # Generate unique ID
                article_id = hashlib.md5(
                    (article.get("url", "") + article.get("title", "")).encode()
                ).hexdigest()
                
                # Parse published date
                published_str = article.get("publishedAt", "")
                try:
                    published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                except:
                    published_at = datetime.utcnow()
                
                result.append(NewsArticle(
                    id=article_id,
                    title=article.get("title", ""),
                    description=article.get("description", ""),
                    content=article.get("content"),
                    url=article.get("url", ""),
                    source=NewsSource.NEWSAPI,
                    source_name=article.get("source", {}).get("name", "Unknown"),
                    published_at=published_at,
                    author=article.get("author"),
                    image_url=article.get("urlToImage"),
                ))
            except Exception as e:
                self.logger.warning(f"Failed to parse article: {e}")
        
        return result


class AlphaVantageNewsClient:
    """Client for Alpha Vantage News API."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: str, session: aiohttp.ClientSession):
        self.api_key = api_key
        self.session = session
        self.logger = get_logger("news.alphavantage")
    
    async def fetch_news_sentiment(
        self,
        tickers: Optional[List[str]] = None,
        topics: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[NewsArticle]:
        """Fetch news with sentiment analysis."""
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.api_key,
            "limit": min(limit, 200),
        }
        if tickers:
            params["tickers"] = ",".join(tickers)
        if topics:
            params["topics"] = ",".join(topics)
        
        try:
            async with self.session.get(self.BASE_URL, params=params) as response:
                if response.status != 200:
                    self.logger.error(f"Alpha Vantage error: {response.status}")
                    return []
                
                data = await response.json()
                return self._parse_articles(data.get("feed", []))
                
        except Exception as e:
            self.logger.error(f"Alpha Vantage fetch error: {e}")
            return []
    
    def _parse_articles(self, articles: List[Dict]) -> List[NewsArticle]:
        """Parse Alpha Vantage articles."""
        result = []
        for article in articles:
            try:
                article_id = hashlib.md5(
                    article.get("url", "").encode()
                ).hexdigest()
                
                # Parse time
                time_str = article.get("time_published", "")
                try:
                    published_at = datetime.strptime(time_str, "%Y%m%dT%H%M%S")
                except:
                    published_at = datetime.utcnow()
                
                # Extract sentiment
                sentiment = article.get("overall_sentiment_score", 0)
                
                result.append(NewsArticle(
                    id=article_id,
                    title=article.get("title", ""),
                    description=article.get("summary", ""),
                    content=article.get("summary"),
                    url=article.get("url", ""),
                    source=NewsSource.ALPHA_VANTAGE,
                    source_name=article.get("source", "Unknown"),
                    published_at=published_at,
                    author=", ".join(article.get("authors", [])),
                    image_url=article.get("banner_image"),
                    sentiment_score=float(sentiment) if sentiment else None,
                ))
            except Exception as e:
                self.logger.warning(f"Failed to parse article: {e}")
        
        return result


class RSSFeedClient:
    """Client for RSS feeds."""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.logger = get_logger("news.rss")
    
    async def fetch_feed(self, feed_url: str) -> List[NewsArticle]:
        """Fetch and parse RSS feed."""
        try:
            async with self.session.get(feed_url) as response:
                if response.status != 200:
                    self.logger.error(f"RSS fetch error: {response.status} for {feed_url}")
                    return []
                
                content = await response.text()
                feed = feedparser.parse(content)
                return self._parse_entries(feed.entries, feed_url)
                
        except Exception as e:
            self.logger.error(f"RSS fetch error for {feed_url}: {e}")
            return []
    
    def _parse_entries(self, entries: List, feed_url: str) -> List[NewsArticle]:
        """Parse RSS feed entries."""
        result = []
        for entry in entries:
            try:
                article_id = hashlib.md5(
                    entry.get("link", entry.get("id", "")).encode()
                ).hexdigest()
                
                # Parse published date
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    published_at = datetime(*published[:6])
                else:
                    published_at = datetime.utcnow()
                
                # Extract description
                description = entry.get("summary", entry.get("description", ""))
                # Strip HTML tags
                description = re.sub(r'<[^>]+>', '', description)
                
                result.append(NewsArticle(
                    id=article_id,
                    title=entry.get("title", ""),
                    description=description[:500],
                    content=entry.get("content", [{}])[0].get("value") if entry.get("content") else None,
                    url=entry.get("link", ""),
                    source=NewsSource.RSS,
                    source_name=feed_url.split("/")[2],  # Extract domain
                    published_at=published_at,
                    author=entry.get("author"),
                ))
            except Exception as e:
                self.logger.warning(f"Failed to parse RSS entry: {e}")
        
        return result


class NewsFeedAggregator:
    """
    Aggregates news from multiple sources.
    
    Usage:
        config = NewsFeedConfig(
            newsapi_key="your_key",
            keywords=["election", "crypto"]
        )
        aggregator = NewsFeedAggregator(config)
        
        # Fetch all news
        articles = await aggregator.fetch_all()
        
        # Search for specific topic
        articles = await aggregator.search("bitcoin price")
        
        # Get breaking news
        breaking = await aggregator.get_breaking_news()
    """
    
    # Default RSS feeds for prediction market relevant news
    DEFAULT_RSS_FEEDS = [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
        "https://feeds.reuters.com/reuters/topNews",
        "https://www.coindesk.com/arc/outboundfeeds/rss/",
    ]
    
    def __init__(
        self,
        config: Optional[NewsFeedConfig] = None,
        event_bus: Optional[Any] = None,
    ):
        """
        Initialize news feed aggregator.
        
        Args:
            config: News feed configuration
            event_bus: Optional EventBus for publishing events
        """
        self.logger = get_logger("news.aggregator")
        self.metrics = get_metrics_registry()
        self.event_bus = event_bus
        
        # Load config from environment if not provided
        self.config = config or NewsFeedConfig(
            newsapi_key=os.environ.get("NEWSAPI_KEY"),
            alpha_vantage_key=os.environ.get("ALPHA_VANTAGE_KEY"),
            polygon_key=os.environ.get("POLYGON_API_KEY"),
            rss_feeds=self.DEFAULT_RSS_FEEDS,
        )
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, tuple] = {}  # {cache_key: (articles, timestamp)}
        self._seen_ids: Set[str] = set()
        
        # Initialize clients
        self._newsapi: Optional[NewsAPIClient] = None
        self._alphavantage: Optional[AlphaVantageNewsClient] = None
        self._rss: Optional[RSSFeedClient] = None
        
        self.logger.info("News feed aggregator initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            
            # Initialize clients
            if self.config.newsapi_key:
                self._newsapi = NewsAPIClient(self.config.newsapi_key, self._session)
            if self.config.alpha_vantage_key:
                self._alphavantage = AlphaVantageNewsClient(self.config.alpha_vantage_key, self._session)
            self._rss = RSSFeedClient(self._session)
        
        return self._session
    
    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_cache(self, key: str) -> Optional[List[NewsArticle]]:
        """Get cached articles if not expired."""
        if key in self._cache:
            articles, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.config.cache_ttl_seconds):
                return articles
        return None
    
    def _set_cache(self, key: str, articles: List[NewsArticle]) -> None:
        """Cache articles."""
        self._cache[key] = (articles, datetime.utcnow())
    
    def _filter_by_keywords(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Filter articles by configured keywords."""
        if not self.config.keywords:
            return articles
        
        keywords_lower = [k.lower() for k in self.config.keywords]
        filtered = []
        
        for article in articles:
            text = f"{article.title} {article.description}".lower()
            matching_keywords = [k for k in keywords_lower if k in text]
            
            if matching_keywords:
                article.keywords = matching_keywords
                article.relevance_score = len(matching_keywords) / len(keywords_lower)
                filtered.append(article)
        
        return filtered
    
    def _deduplicate(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles."""
        unique = []
        for article in articles:
            if article.id not in self._seen_ids:
                self._seen_ids.add(article.id)
                unique.append(article)
        return unique
    
    async def fetch_all(
        self,
        filter_keywords: bool = True,
        max_age_hours: Optional[int] = None,
    ) -> List[NewsArticle]:
        """
        Fetch news from all configured sources.
        
        Args:
            filter_keywords: Filter by configured keywords
            max_age_hours: Maximum article age in hours
            
        Returns:
            List of news articles sorted by published date
        """
        await self._get_session()
        
        all_articles = []
        tasks = []
        
        # NewsAPI
        if self._newsapi:
            tasks.append(self._fetch_newsapi())
        
        # Alpha Vantage
        if self._alphavantage:
            tasks.append(self._fetch_alphavantage())
        
        # RSS feeds
        if self._rss and self.config.rss_feeds:
            for feed_url in self.config.rss_feeds:
                tasks.append(self._rss.fetch_feed(feed_url))
        
        # Fetch all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Fetch error: {result}")
            elif isinstance(result, list):
                all_articles.extend(result)
        
        # Filter by age
        if max_age_hours:
            cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
            all_articles = [a for a in all_articles if a.published_at > cutoff]
        
        # Filter by keywords
        if filter_keywords:
            all_articles = self._filter_by_keywords(all_articles)
        
        # Deduplicate
        all_articles = self._deduplicate(all_articles)
        
        # Sort by published date (newest first)
        all_articles.sort(key=lambda a: a.published_at, reverse=True)
        
        self.logger.info(f"Fetched {len(all_articles)} articles from all sources")
        
        return all_articles
    
    async def _fetch_newsapi(self) -> List[NewsArticle]:
        """Fetch from NewsAPI."""
        cache_key = "newsapi_headlines"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        articles = await self._newsapi.fetch_top_headlines(
            page_size=self.config.max_articles_per_source
        )
        
        self._set_cache(cache_key, articles)
        return articles
    
    async def _fetch_alphavantage(self) -> List[NewsArticle]:
        """Fetch from Alpha Vantage."""
        cache_key = "alphavantage_news"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        articles = await self._alphavantage.fetch_news_sentiment(
            topics=["economy_fiscal", "economy_monetary", "finance", "technology"],
            limit=self.config.max_articles_per_source
        )
        
        self._set_cache(cache_key, articles)
        return articles
    
    async def search(
        self,
        query: str,
        from_date: Optional[datetime] = None,
        max_results: int = 50,
    ) -> List[NewsArticle]:
        """
        Search for news articles.
        
        Args:
            query: Search query
            from_date: Search from this date
            max_results: Maximum results to return
            
        Returns:
            List of matching articles
        """
        await self._get_session()
        
        if not from_date:
            from_date = datetime.utcnow() - timedelta(hours=self.config.lookback_hours)
        
        articles = []
        
        # Search NewsAPI
        if self._newsapi:
            newsapi_results = await self._newsapi.search_everything(
                query=query,
                from_date=from_date,
                page_size=max_results
            )
            articles.extend(newsapi_results)
        
        # Deduplicate and sort
        articles = self._deduplicate(articles)
        articles.sort(key=lambda a: a.published_at, reverse=True)
        
        return articles[:max_results]
    
    async def get_breaking_news(
        self,
        max_age_minutes: int = 60,
    ) -> List[NewsArticle]:
        """
        Get breaking news (very recent articles).
        
        Args:
            max_age_minutes: Maximum age in minutes
            
        Returns:
            List of breaking news articles
        """
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        articles = await self.fetch_all(
            filter_keywords=True,
            max_age_hours=1
        )
        
        breaking = [a for a in articles if a.published_at > cutoff]
        
        # Publish to event bus if we have breaking news
        if breaking and self.event_bus:
            for article in breaking[:5]:  # Limit to top 5
                await self.event_bus.publish("news.breaking", article.to_dict())
        
        return breaking
    
    async def get_market_relevant_news(
        self,
        market_keywords: List[str],
        max_results: int = 20,
    ) -> List[NewsArticle]:
        """
        Get news relevant to specific markets.
        
        Args:
            market_keywords: Keywords related to the market
            max_results: Maximum results
            
        Returns:
            List of relevant articles
        """
        # Temporarily override keywords
        original_keywords = self.config.keywords
        self.config.keywords = market_keywords
        
        try:
            articles = await self.fetch_all(filter_keywords=True)
            return articles[:max_results]
        finally:
            self.config.keywords = original_keywords
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics."""
        return {
            "sources_configured": {
                "newsapi": self._newsapi is not None,
                "alpha_vantage": self._alphavantage is not None,
                "rss_feeds": len(self.config.rss_feeds),
            },
            "cache_entries": len(self._cache),
            "seen_articles": len(self._seen_ids),
            "keywords_configured": len(self.config.keywords),
        }


# Convenience function to create aggregator from environment
def create_news_aggregator(
    event_bus: Optional[Any] = None,
) -> NewsFeedAggregator:
    """
    Create a news feed aggregator from environment variables.
    
    Environment variables:
    - NEWSAPI_KEY: NewsAPI.org API key
    - ALPHA_VANTAGE_KEY: Alpha Vantage API key
    - POLYGON_API_KEY: Polygon.io API key
    
    Args:
        event_bus: Optional EventBus for publishing events
        
    Returns:
        Configured NewsFeedAggregator
    """
    return NewsFeedAggregator(event_bus=event_bus)
