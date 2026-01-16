'use client';

import { useState, useEffect, useCallback } from 'react';
import { cn, formatCurrency } from '@/lib/utils';
import {
  Search,
  Loader2,
  TrendingUp,
  TrendingDown,
  BarChart3,
  Droplets,
  X,
} from 'lucide-react';
import type { Platform } from '@/types';

interface Market {
  id: string;
  title: string;
  platform: Platform;
  currentPrice: number;
  priceChange24h: number;
  volume24h: number;
  liquidity: number;
  endDate?: string;
  category?: string;
}

interface MarketSearchProps {
  onSelect: (market: Market) => void;
  selectedMarketId?: string;
  platform?: Platform;
}

const platformColors: Record<Platform, string> = {
  polymarket: 'bg-purple-500/10 text-purple-500 border-purple-500/30',
  kalshi: 'bg-blue-500/10 text-blue-500 border-blue-500/30',
  manifold: 'bg-green-500/10 text-green-500 border-green-500/30',
};

const platformLabels: Record<Platform, string> = {
  polymarket: 'Polymarket',
  kalshi: 'Kalshi',
  manifold: 'Manifold',
};

export function MarketSearch({
  onSelect,
  selectedMarketId,
  platform,
}: MarketSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Market[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  const [popularMarkets, setPopularMarkets] = useState<Market[]>([]);

  // Load recent searches from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('recentMarketSearches');
    if (saved) {
      setRecentSearches(JSON.parse(saved));
    }
  }, []);

  // Fetch popular markets on mount
  useEffect(() => {
    const fetchPopular = async () => {
      try {
        const params = new URLSearchParams({ sort: 'volume', limit: '5' });
        if (platform) params.set('platform', platform);
        
        const response = await fetch(`/api/trade/markets?${params}`);
        if (response.ok) {
          const data = await response.json();
          setPopularMarkets(data.data?.markets || []);
        }
      } catch (error) {
        console.error('Failed to fetch popular markets:', error);
      }
    };
    fetchPopular();
  }, [platform]);

  const searchMarkets = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    try {
      const params = new URLSearchParams({ search: searchQuery });
      if (platform) params.set('platform', platform);
      
      const response = await fetch(`/api/trade/markets?${params}`);
      if (response.ok) {
        const data = await response.json();
        setResults(data.data?.markets || []);
      }
    } catch (error) {
      console.error('Failed to search markets:', error);
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, [platform]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (query) {
        searchMarkets(query);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query, searchMarkets]);

  const handleSelect = (market: Market) => {
    onSelect(market);
    setIsOpen(false);
    setQuery('');

    // Save to recent searches
    const updated = [market.title, ...recentSearches.filter(s => s !== market.title)].slice(0, 5);
    setRecentSearches(updated);
    localStorage.setItem('recentMarketSearches', JSON.stringify(updated));
  };

  const handleRecentSearch = (search: string) => {
    setQuery(search);
    searchMarkets(search);
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem('recentMarketSearches');
  };

  const displayMarkets = query ? results : popularMarkets;

  return (
    <div className="relative">
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          placeholder="Search markets by name, category, or ID..."
          className="w-full pl-11 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
        />
        {query && (
          <button
            onClick={() => setQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-gray-900 border border-gray-800 rounded-xl shadow-xl max-h-96 overflow-hidden">
          {/* Recent Searches */}
          {!query && recentSearches.length > 0 && (
            <div className="p-3 border-b border-gray-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500 uppercase tracking-wider">Recent Searches</span>
                <button
                  onClick={clearRecentSearches}
                  className="text-xs text-gray-500 hover:text-white"
                >
                  Clear
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {recentSearches.map((search, index) => (
                  <button
                    key={index}
                    onClick={() => handleRecentSearch(search)}
                    className="px-3 py-1 text-sm bg-gray-800 text-gray-400 rounded-full hover:bg-gray-700 hover:text-white transition-colors"
                  >
                    {search}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
            </div>
          )}

          {/* Results */}
          {!isLoading && (
            <div className="overflow-y-auto max-h-80">
              {displayMarkets.length > 0 ? (
                <>
                  {!query && (
                    <div className="px-3 pt-3 pb-1">
                      <span className="text-xs text-gray-500 uppercase tracking-wider">
                        Popular Markets
                      </span>
                    </div>
                  )}
                  {displayMarkets.map((market) => (
                    <button
                      key={market.id}
                      onClick={() => handleSelect(market)}
                      className={cn(
                        'w-full p-3 text-left hover:bg-gray-800/50 transition-colors',
                        selectedMarketId === market.id && 'bg-primary/10'
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <p className="text-white font-medium truncate">{market.title}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={cn(
                              'px-2 py-0.5 text-xs rounded border',
                              platformColors[market.platform]
                            )}>
                              {platformLabels[market.platform]}
                            </span>
                            {market.category && (
                              <span className="text-xs text-gray-500">{market.category}</span>
                            )}
                          </div>
                        </div>
                        <div className="text-right flex-shrink-0">
                          <p className="text-white font-medium">${market.currentPrice.toFixed(2)}</p>
                          <div className={cn(
                            'flex items-center gap-1 text-xs',
                            market.priceChange24h >= 0 ? 'text-green-500' : 'text-red-500'
                          )}>
                            {market.priceChange24h >= 0 ? (
                              <TrendingUp className="w-3 h-3" />
                            ) : (
                              <TrendingDown className="w-3 h-3" />
                            )}
                            {Math.abs(market.priceChange24h).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                      
                      {/* Market Stats */}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <div className="flex items-center gap-1">
                          <BarChart3 className="w-3 h-3" />
                          Vol: {formatCurrency(market.volume24h)}
                        </div>
                        <div className="flex items-center gap-1">
                          <Droplets className="w-3 h-3" />
                          Liq: {formatCurrency(market.liquidity)}
                        </div>
                        {market.endDate && (
                          <span>
                            Ends: {new Date(market.endDate).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </>
              ) : query ? (
                <div className="py-8 text-center text-gray-500">
                  No markets found for "{query}"
                </div>
              ) : (
                <div className="py-8 text-center text-gray-500">
                  Start typing to search markets
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}

export default MarketSearch;
