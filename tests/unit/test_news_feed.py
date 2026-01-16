"""
Unit Tests - News Feed
======================

Tests for the multi-source news aggregation module.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Skip import if feedparser not available
try:
    from shared.news_feed import (
        NewsFeed,
        NewsArticle,
        NewsSource,
        NewsSentiment,
        create_news_feed,
    )
    NEWS_FEED_AVAILABLE = True
except ImportError as e:
    NEWS_FEED_AVAILABLE = False
    pytest.skip(f"News feed module not available: {e}", allow_module_level=True)


@pytest.mark.skipif(not NEWS_FEED_AVAILABLE, reason="News feed module not available")
class TestNewsSource:
    """Tests for NewsSource enum."""
    
    def test_all_sources(self):
        """Test all news sources exist."""
        assert NewsSource.NEWSAPI == "newsapi"
        assert NewsSource.REDDIT == "reddit"
        assert NewsSource.TWITTER == "twitter"
        assert NewsSource.POLYMARKET == "polymarket"
        assert NewsSource.KALSHI == "kalshi"
        assert NewsSource.RSS == "rss"


@pytest.mark.skipif(not NEWS_FEED_AVAILABLE, reason="News feed module not available")
class TestNewsSentiment:
    """Tests for NewsSentiment enum."""
    
    def test_sentiment_values(self):
        """Test sentiment enum values."""
        assert NewsSentiment.BULLISH == "bullish"
        assert NewsSentiment.BEARISH == "bearish"
        assert NewsSentiment.NEUTRAL == "neutral"
        assert NewsSentiment.MIXED == "mixed"


@pytest.mark.skipif(not NEWS_FEED_AVAILABLE, reason="News feed module not available")
class TestNewsArticle:
    """Tests for NewsArticle dataclass."""
    
    def test_create_article(self):
        """Test creating a news article."""
        now = datetime.utcnow()
        article = NewsArticle(
            id="article-123",
            title="Bitcoin Reaches New High",
            content="Bitcoin has reached a new all-time high...",
            source=NewsSource.NEWSAPI,
            url="https://example.com/article",
            published_at=now,
            keywords=["bitcoin", "crypto", "markets"],
        )
        
        assert article.id == "article-123"
        assert article.title == "Bitcoin Reaches New High"
        assert article.source == NewsSource.NEWSAPI
        assert "bitcoin" in article.keywords


@pytest.mark.skipif(not NEWS_FEED_AVAILABLE, reason="News feed module not available")
class TestNewsFeed:
    """Tests for NewsFeed class."""
    
    def test_create_news_feed(self):
        """Test creating news feed."""
        feed = create_news_feed()
        assert feed is not None
        assert isinstance(feed, NewsFeed)
