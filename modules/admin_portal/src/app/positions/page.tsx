'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { PositionsTable } from '@/components/positions/PositionsTable';
import { PositionActions, PositionDetailsModal } from '@/components/positions/PositionActions';
import { orchestratorApi } from '@/lib/api';
import { Search, Filter, RefreshCw } from 'lucide-react';
import type { Position, Platform, PositionStatus, PositionFilters } from '@/types';

// Mock data for development
const mockPositions: Position[] = [
  {
    id: '1',
    platform: 'polymarket',
    marketId: 'pm-12345',
    marketTitle: 'Will BTC reach $100k by March 2024?',
    side: 'YES',
    size: 500,
    entryPrice: 0.45,
    currentPrice: 0.52,
    pnl: 35,
    pnlPercent: 15.56,
    status: 'open',
    strategy: 'AI Forecast',
    openedAt: new Date(Date.now() - 86400000),
  },
  {
    id: '2',
    platform: 'kalshi',
    marketId: 'kal-67890',
    marketTitle: 'Fed Rate Decision - January Meeting',
    side: 'NO',
    size: 200,
    entryPrice: 0.72,
    currentPrice: 0.68,
    pnl: 8,
    pnlPercent: 5.56,
    status: 'open',
    strategy: 'Arbitrage',
    openedAt: new Date(Date.now() - 172800000),
  },
  {
    id: '3',
    platform: 'manifold',
    marketId: 'mf-11111',
    marketTitle: 'Will GPT-5 be released in 2024?',
    side: 'YES',
    size: 1000,
    entryPrice: 0.35,
    currentPrice: 0.42,
    pnl: 70,
    pnlPercent: 20,
    status: 'open',
    strategy: 'Market Making',
    openedAt: new Date(Date.now() - 259200000),
  },
  {
    id: '4',
    platform: 'polymarket',
    marketId: 'pm-22222',
    marketTitle: 'US Presidential Election 2024 - Democratic Nominee',
    side: 'YES',
    size: 300,
    entryPrice: 0.88,
    currentPrice: 0.85,
    pnl: -9,
    pnlPercent: -3.41,
    status: 'open',
    strategy: 'Spike Detection',
    openedAt: new Date(Date.now() - 345600000),
  },
  {
    id: '5',
    platform: 'kalshi',
    marketId: 'kal-33333',
    marketTitle: 'S&P 500 Close Above 5000 by EOD',
    side: 'YES',
    size: 150,
    entryPrice: 0.62,
    currentPrice: 0.71,
    pnl: 13.5,
    pnlPercent: 14.52,
    status: 'open',
    strategy: 'AI Forecast',
    openedAt: new Date(Date.now() - 43200000),
  },
];

export default function PositionsPage() {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<PositionFilters>({});
  const [detailsPosition, setDetailsPosition] = useState<Position | null>(null);

  // Fetch positions
  const { data: positions = mockPositions, isLoading, refetch } = useQuery({
    queryKey: ['positions', filters],
    queryFn: async () => {
      // In production, call real API
      // const result = await orchestratorApi.getPositions(filters);
      // return result.data?.items || [];
      return mockPositions;
    },
    refetchInterval: 10000,
  });

  // Filter positions based on search and filters
  const filteredPositions = positions.filter((position) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      if (
        !position.marketTitle.toLowerCase().includes(query) &&
        !position.marketId.toLowerCase().includes(query) &&
        !position.strategy.toLowerCase().includes(query)
      ) {
        return false;
      }
    }
    if (filters.platform && position.platform !== filters.platform) {
      return false;
    }
    if (filters.status && position.status !== filters.status) {
      return false;
    }
    if (filters.strategy && position.strategy !== filters.strategy) {
      return false;
    }
    return true;
  });

  const handleSelectPosition = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedIds.length === filteredPositions.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredPositions.map((p) => p.id));
    }
  };

  const handleClosePosition = async (position: Position) => {
    try {
      await orchestratorApi.closePosition(position.id);
      refetch();
      setDetailsPosition(null);
    } catch (error) {
      console.error('Failed to close position:', error);
    }
  };

  const handleCloseSelected = async () => {
    try {
      await Promise.all(selectedIds.map((id) => orchestratorApi.closePosition(id)));
      setSelectedIds([]);
      refetch();
    } catch (error) {
      console.error('Failed to close positions:', error);
    }
  };

  const handleExportCsv = () => {
    const selectedPositions = filteredPositions.filter((p) =>
      selectedIds.includes(p.id)
    );
    const headers = [
      'Platform',
      'Market',
      'Side',
      'Size',
      'Entry Price',
      'Current Price',
      'P&L',
      'P&L %',
      'Strategy',
      'Opened At',
    ];
    const rows = selectedPositions.map((p) => [
      p.platform,
      p.marketTitle,
      p.side,
      p.size,
      p.entryPrice,
      p.currentPrice,
      p.pnl,
      p.pnlPercent,
      p.strategy,
      new Date(p.openedAt).toISOString(),
    ]);

    const csv = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `positions-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Positions</h1>
            <p className="text-gray-400">Manage your open positions across all platforms</p>
          </div>
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search markets, strategies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Platform Filter */}
          <select
            value={filters.platform || ''}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                platform: e.target.value as Platform | undefined,
              }))
            }
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Platforms</option>
            <option value="polymarket">Polymarket</option>
            <option value="kalshi">Kalshi</option>
            <option value="manifold">Manifold</option>
          </select>

          {/* Status Filter */}
          <select
            value={filters.status || ''}
            onChange={(e) =>
              setFilters((prev) => ({
                ...prev,
                status: e.target.value as PositionStatus | undefined,
              }))
            }
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="">All Status</option>
            <option value="open">Open</option>
            <option value="pending">Pending</option>
            <option value="closed">Closed</option>
          </select>
        </div>

        {/* Selected Actions */}
        <PositionActions
          selectedCount={selectedIds.length}
          onCloseSelected={handleCloseSelected}
          onExportCsv={handleExportCsv}
          onClearSelection={() => setSelectedIds([])}
        />

        {/* Positions Table */}
        <div className="bg-gray-900/50 rounded-xl border border-gray-800 overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <PositionsTable
              positions={filteredPositions}
              selectedIds={selectedIds}
              onSelectPosition={handleSelectPosition}
              onSelectAll={handleSelectAll}
              onViewDetails={setDetailsPosition}
              onClosePosition={handleClosePosition}
            />
          )}
        </div>

        {/* Summary */}
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>
            Showing {filteredPositions.length} of {positions.length} positions
          </span>
          <span>
            Total Value: $
            {filteredPositions
              .reduce((sum, p) => sum + p.size * p.currentPrice, 0)
              .toFixed(2)}
          </span>
        </div>
      </div>

      {/* Position Details Modal */}
      <PositionDetailsModal
        position={detailsPosition}
        onClose={() => setDetailsPosition(null)}
        onClosePosition={handleClosePosition}
      />
    </MainLayout>
  );
}
