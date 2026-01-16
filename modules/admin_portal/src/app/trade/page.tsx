'use client';

import { useState, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { TradeForm, MarketSearch, TradePreview, RecentManualTrades } from '@/components/trade';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  ArrowLeftRight, 
  History, 
  AlertTriangle,
  Shield,
} from 'lucide-react';
import type { Platform, PositionSide } from '@/types';

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

interface TradePreviewData {
  market: Market;
  side: PositionSide;
  size: number;
  price: number;
  orderType: 'market' | 'limit';
  estimatedCost: number;
  estimatedFees: number;
  totalCost: number;
  slippage?: number;
  priceImpact?: number;
}

async function searchMarkets(query: string, platform?: Platform): Promise<Market[]> {
  const params = new URLSearchParams({ endpoint: 'markets' });
  if (query) params.set('search', query);
  if (platform) params.set('platform', platform);
  
  const response = await fetch(`/api/trade?${params}`);
  if (!response.ok) throw new Error('Failed to search markets');
  const data = await response.json();
  return data.data?.markets || [];
}

async function previewTrade(trade: {
  market: Market;
  side: PositionSide;
  size: number;
  price: number;
  orderType: 'market' | 'limit';
}): Promise<TradePreviewData> {
  const response = await fetch('/api/trade', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action: 'preview',
      ...trade,
    }),
  });
  if (!response.ok) throw new Error('Failed to preview trade');
  const data = await response.json();
  return data.data;
}

async function executeTrade(preview: TradePreviewData): Promise<{ success: boolean; tradeId?: string; error?: string }> {
  const response = await fetch('/api/trade', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      action: 'execute',
      market: preview.market,
      side: preview.side,
      size: preview.size,
      price: preview.price,
      orderType: preview.orderType,
    }),
  });
  const data = await response.json();
  if (!response.ok) {
    return { success: false, error: data.error || 'Trade execution failed' };
  }
  return { success: true, tradeId: data.data?.tradeId };
}

export default function TradePage() {
  const [activeTab, setActiveTab] = useState('new-trade');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPlatform, setSelectedPlatform] = useState<Platform | undefined>();
  const [selectedMarket, setSelectedMarket] = useState<Market | null>(null);
  const [preview, setPreview] = useState<TradePreviewData | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<{ tradeId: string } | null>(null);

  // Fetch markets based on search
  const { data: markets = [], isLoading: isLoadingMarkets, refetch: refetchMarkets } = useQuery({
    queryKey: ['markets', searchQuery, selectedPlatform],
    queryFn: () => searchMarkets(searchQuery, selectedPlatform),
    enabled: searchQuery.length > 0,
  });

  const handleSearch = useCallback((query: string, platform?: Platform) => {
    setSearchQuery(query);
    setSelectedPlatform(platform);
    refetchMarkets();
  }, [refetchMarkets]);

  const handleMarketSelect = (market: Market) => {
    setSelectedMarket(market);
    setPreview(null);
    setError(null);
    setSuccess(null);
  };

  const handlePreview = async (trade: {
    market: Market;
    side: PositionSide;
    size: number;
    price: number;
    orderType: 'market' | 'limit';
  }) => {
    setError(null);
    const previewData = await previewTrade(trade);
    setPreview(previewData);
    return previewData;
  };

  const handleExecute = async (previewData: TradePreviewData) => {
    setIsExecuting(true);
    setError(null);
    try {
      const result = await executeTrade(previewData);
      if (result.success && result.tradeId) {
        setSuccess({ tradeId: result.tradeId });
        setPreview(null);
        setSelectedMarket(null);
      } else {
        setError(result.error || 'Trade execution failed');
      }
      return result;
    } finally {
      setIsExecuting(false);
    }
  };

  const handleConfirm = () => {
    if (preview) {
      handleExecute(preview);
    }
  };

  const handleCancel = () => {
    setPreview(null);
    setError(null);
    setSuccess(null);
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <ArrowLeftRight className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Manual Trade</h1>
              <p className="text-gray-400">Execute trades manually across platforms</p>
            </div>
          </div>
        </div>

        {/* Warning Banner */}
        <div className="flex items-center gap-3 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0" />
          <div>
            <p className="text-yellow-500 font-medium">Manual Trading Mode</p>
            <p className="text-yellow-500/80 text-sm">
              Trades executed here bypass automated strategies. Use with caution and ensure proper risk management.
            </p>
          </div>
        </div>

        {/* Role Requirement Notice */}
        <div className="flex items-center gap-3 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <Shield className="w-5 h-5 text-blue-500 flex-shrink-0" />
          <p className="text-blue-500 text-sm">
            Manual trading requires ADMIN or OPERATOR role. All trades are logged for audit purposes.
          </p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="new-trade">
              <ArrowLeftRight className="w-4 h-4 mr-2" />
              New Trade
            </TabsTrigger>
            <TabsTrigger value="history">
              <History className="w-4 h-4 mr-2" />
              Trade History
            </TabsTrigger>
          </TabsList>

          <TabsContent value="new-trade" className="space-y-6">
            {/* Market Search */}
            <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Search Markets</h3>
              <MarketSearch
                onSelect={handleMarketSelect}
                selectedMarketId={selectedMarket?.id}
                platform={selectedPlatform}
              />
            </div>

            {/* Trade Form or Preview */}
            {preview ? (
              <TradePreview
                preview={preview}
                isExecuting={isExecuting}
                onConfirm={handleConfirm}
                onCancel={handleCancel}
                error={error}
                success={success}
              />
            ) : (
              <TradeForm
                markets={markets}
                isLoadingMarkets={isLoadingMarkets}
                onSearch={handleSearch}
                onPreview={handlePreview}
                onExecute={handleExecute}
              />
            )}
          </TabsContent>

          <TabsContent value="history">
            <RecentManualTrades limit={20} />
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  );
}
