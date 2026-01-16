'use client';

import { useState } from 'react';
import { cn, formatCurrency } from '@/lib/utils';
import {
  Search,
  AlertTriangle,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import type { Platform, PositionSide } from '@/types';

interface Market {
  id: string;
  title: string;
  platform: Platform;
  currentPrice: number;
  volume24h: number;
  liquidity: number;
}

interface TradePreview {
  market: Market;
  side: PositionSide;
  size: number;
  price: number;
  orderType: 'market' | 'limit';
  estimatedCost: number;
  estimatedFees: number;
  totalCost: number;
}

interface TradeFormProps {
  markets: Market[];
  isLoadingMarkets?: boolean;
  onSearch: (query: string, platform?: Platform) => void;
  onPreview: (trade: Omit<TradePreview, 'estimatedCost' | 'estimatedFees' | 'totalCost'>) => Promise<TradePreview>;
  onExecute: (preview: TradePreview) => Promise<{ success: boolean; tradeId?: string; error?: string }>;
}

const platforms: { value: Platform | 'all'; label: string }[] = [
  { value: 'all', label: 'All Platforms' },
  { value: 'polymarket', label: 'Polymarket' },
  { value: 'kalshi', label: 'Kalshi' },
  { value: 'manifold', label: 'Manifold' },
];

const platformColors: Record<Platform, string> = {
  polymarket: 'bg-purple-500/10 text-purple-500',
  kalshi: 'bg-blue-500/10 text-blue-500',
  manifold: 'bg-green-500/10 text-green-500',
};

export function TradeForm({
  markets,
  isLoadingMarkets,
  onSearch,
  onPreview,
  onExecute,
}: TradeFormProps) {
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | 'all'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);
  const [side, setSide] = useState<PositionSide>('YES');
  const [size, setSize] = useState<string>('100');
  const [price, setPrice] = useState<string>('');
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [preview, setPreview] = useState<TradePreview | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ tradeId: string } | null>(null);

  const handleSearch = () => {
    onSearch(searchQuery, selectedPlatform === 'all' ? undefined : selectedPlatform);
  };

  const handleMarketSelect = (market: Market) => {
    setSelectedMarket(market);
    setPrice(market.currentPrice.toFixed(2));
    setPreview(null);
    setError(null);
    setSuccess(null);
  };

  const handlePreview = async () => {
    if (!selectedMarket) return;
    
    setIsPreviewLoading(true);
    setError(null);
    
    try {
      const previewData = await onPreview({
        market: selectedMarket,
        side,
        size: parseFloat(size),
        price: orderType === 'limit' ? parseFloat(price) : selectedMarket.currentPrice,
        orderType,
      });
      setPreview(previewData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate preview');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!preview) return;
    
    setIsExecuting(true);
    setError(null);
    
    try {
      const result = await onExecute(preview);
      if (result.success && result.tradeId) {
        setSuccess({ tradeId: result.tradeId });
        setPreview(null);
        setSelectedMarket(null);
      } else {
        setError(result.error || 'Trade execution failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Trade execution failed');
    } finally {
      setIsExecuting(false);
    }
  };

  const isLargeTrade = parseFloat(size) > 1000;

  return (
    <div className="space-y-6">
      {/* Market Search */}
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Select Market</h3>
        
        <div className="flex flex-wrap gap-4 mb-4">
          {/* Platform Filter */}
          <select
            value={selectedPlatform}
            onChange={(e) => setSelectedPlatform(e.target.value as Platform | 'all')}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary"
          >
            {platforms.map((p) => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>

          {/* Search Input */}
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search markets..."
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary"
            />
          </div>

          <button
            onClick={handleSearch}
            className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            Search
          </button>
        </div>

        {/* Market Results */}
        <div className="max-h-64 overflow-y-auto space-y-2">
          {isLoadingMarkets ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
            </div>
          ) : markets.length > 0 ? (
            markets.map((market) => (
              <button
                key={market.id}
                onClick={() => handleMarketSelect(market)}
                className={cn(
                  'w-full p-3 rounded-lg border text-left transition-colors',
                  selectedMarket?.id === market.id
                    ? 'border-primary bg-primary/10'
                    : 'border-gray-800 bg-gray-800/50 hover:border-gray-700'
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">{market.title}</p>
                    <div className="flex items-center gap-3 mt-1">
                      <span className={cn(
                        'px-2 py-0.5 text-xs rounded capitalize',
                        platformColors[market.platform]
                      )}>
                        {market.platform}
                      </span>
                      <span className="text-gray-500 text-xs">
                        Vol: {formatCurrency(market.volume24h)}
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-white font-medium">${market.currentPrice.toFixed(2)}</p>
                    <p className="text-gray-500 text-xs">Current Price</p>
                  </div>
                </div>
              </button>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              Search for markets to get started
            </div>
          )}
        </div>
      </div>

      {/* Trade Configuration */}
      {selectedMarket && (
        <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Configure Trade</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Side Selection */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Side</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setSide('YES')}
                  className={cn(
                    'flex-1 py-2 rounded-lg font-medium transition-colors',
                    side === 'YES'
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  )}
                >
                  YES
                </button>
                <button
                  onClick={() => setSide('NO')}
                  className={cn(
                    'flex-1 py-2 rounded-lg font-medium transition-colors',
                    side === 'NO'
                      ? 'bg-red-500 text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  )}
                >
                  NO
                </button>
              </div>
            </div>

            {/* Order Type */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Order Type</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setOrderType('market')}
                  className={cn(
                    'flex-1 py-2 rounded-lg font-medium transition-colors',
                    orderType === 'market'
                      ? 'bg-primary text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  )}
                >
                  Market
                </button>
                <button
                  onClick={() => setOrderType('limit')}
                  className={cn(
                    'flex-1 py-2 rounded-lg font-medium transition-colors',
                    orderType === 'limit'
                      ? 'bg-primary text-white'
                      : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                  )}
                >
                  Limit
                </button>
              </div>
            </div>

            {/* Size */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">Size (shares)</label>
              <input
                type="number"
                value={size}
                onChange={(e) => setSize(e.target.value)}
                min="1"
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary"
              />
            </div>

            {/* Price (for limit orders) */}
            <div>
              <label className="block text-sm text-gray-400 mb-2">
                Price {orderType === 'market' && '(Market)'}
              </label>
              <input
                type="number"
                value={orderType === 'market' ? selectedMarket.currentPrice.toFixed(2) : price}
                onChange={(e) => setPrice(e.target.value)}
                disabled={orderType === 'market'}
                step="0.01"
                min="0.01"
                max="0.99"
                className={cn(
                  'w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-primary',
                  orderType === 'market' && 'opacity-50'
                )}
              />
            </div>
          </div>

          {/* Large Trade Warning */}
          {isLargeTrade && (
            <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0" />
              <p className="text-yellow-500 text-sm">
                This is a large trade. Please review carefully before executing.
              </p>
            </div>
          )}

          {/* Preview Button */}
          <button
            onClick={handlePreview}
            disabled={isPreviewLoading || !size || parseFloat(size) <= 0}
            className={cn(
              'mt-4 w-full flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors',
              'bg-gray-700 text-white hover:bg-gray-600',
              (isPreviewLoading || !size || parseFloat(size) <= 0) && 'opacity-50 cursor-not-allowed'
            )}
          >
            {isPreviewLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Generating Preview...
              </>
            ) : (
              <>
                Preview Trade
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      )}

      {/* Trade Preview */}
      {preview && (
        <div className="rounded-xl border border-primary/50 bg-primary/5 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Trade Preview</h3>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Market</span>
              <span className="text-white font-medium">{preview.market.title}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Side</span>
              <span className={cn(
                'font-medium',
                preview.side === 'YES' ? 'text-green-500' : 'text-red-500'
              )}>
                {preview.side}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Size</span>
              <span className="text-white">{preview.size} shares</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Price</span>
              <span className="text-white">${preview.price.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Order Type</span>
              <span className="text-white capitalize">{preview.orderType}</span>
            </div>
            <div className="border-t border-gray-700 my-3" />
            <div className="flex justify-between">
              <span className="text-gray-400">Estimated Cost</span>
              <span className="text-white">{formatCurrency(preview.estimatedCost)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Estimated Fees</span>
              <span className="text-white">{formatCurrency(preview.estimatedFees)}</span>
            </div>
            <div className="flex justify-between text-lg">
              <span className="text-white font-medium">Total</span>
              <span className="text-white font-bold">{formatCurrency(preview.totalCost)}</span>
            </div>
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={handleExecute}
              disabled={isExecuting}
              className={cn(
                'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors',
                'bg-primary text-white hover:bg-primary/90',
                isExecuting && 'opacity-50 cursor-not-allowed'
              )}
            >
              {isExecuting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Executing...
                </>
              ) : (
                'Execute Trade'
              )}
            </button>
            <button
              onClick={() => setPreview(null)}
              disabled={isExecuting}
              className="px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <p className="text-red-500">{error}</p>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
          <p className="text-green-500">
            Trade executed successfully! Trade ID: {success.tradeId}
          </p>
        </div>
      )}
    </div>
  );
}

export default TradeForm;
