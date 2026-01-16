'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { cn, formatCurrency, formatDate } from '@/lib/utils';
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ExternalLink,
} from 'lucide-react';
import type { Platform, PositionSide } from '@/types';

interface ManualTrade {
  id: string;
  marketId: string;
  marketTitle: string;
  platform: Platform;
  side: PositionSide;
  size: number;
  price: number;
  orderType: 'market' | 'limit';
  status: 'pending' | 'filled' | 'partial' | 'cancelled' | 'failed';
  filledSize?: number;
  filledPrice?: number;
  fees?: number;
  totalCost?: number;
  createdAt: string;
  updatedAt: string;
  executedBy: string;
  error?: string;
}

interface RecentManualTradesProps {
  limit?: number;
  onTradeClick?: (trade: ManualTrade) => void;
}

const statusConfig: Record<ManualTrade['status'], { icon: typeof Clock; color: string; label: string }> = {
  pending: { icon: Clock, color: 'text-yellow-500', label: 'Pending' },
  filled: { icon: CheckCircle, color: 'text-green-500', label: 'Filled' },
  partial: { icon: AlertCircle, color: 'text-blue-500', label: 'Partial' },
  cancelled: { icon: XCircle, color: 'text-gray-500', label: 'Cancelled' },
  failed: { icon: XCircle, color: 'text-red-500', label: 'Failed' },
};

const platformColors: Record<Platform, string> = {
  polymarket: 'bg-purple-500/10 text-purple-500',
  kalshi: 'bg-blue-500/10 text-blue-500',
  manifold: 'bg-green-500/10 text-green-500',
};

async function fetchRecentTrades(limit: number): Promise<ManualTrade[]> {
  const response = await fetch(`/api/trade/recent?limit=${limit}`);
  if (!response.ok) throw new Error('Failed to fetch recent trades');
  const data = await response.json();
  return data.data?.trades || [];
}

export function RecentManualTrades({
  limit = 10,
  onTradeClick,
}: RecentManualTradesProps) {
  const [expandedTrade, setExpandedTrade] = useState<string | null>(null);

  const { data: trades, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['trades', 'recent', limit],
    queryFn: () => fetchRecentTrades(limit),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const toggleExpand = (tradeId: string) => {
    setExpandedTrade(expandedTrade === tradeId ? null : tradeId);
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        <h3 className="text-lg font-semibold text-white">Recent Manual Trades</h3>
        <button
          onClick={() => refetch()}
          disabled={isRefetching}
          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 hover:text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn('w-4 h-4', isRefetching && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {/* Trades List */}
      <div className="divide-y divide-gray-800">
        {trades && trades.length > 0 ? (
          trades.map((trade) => {
            const StatusIcon = statusConfig[trade.status].icon;
            const isExpanded = expandedTrade === trade.id;

            return (
              <div key={trade.id} className="hover:bg-gray-800/30 transition-colors">
                {/* Trade Summary Row */}
                <div
                  className="p-4 cursor-pointer"
                  onClick={() => toggleExpand(trade.id)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {/* Status Icon */}
                      <div className={cn(
                        'p-2 rounded-lg',
                        trade.status === 'filled' ? 'bg-green-500/10' :
                        trade.status === 'failed' ? 'bg-red-500/10' :
                        trade.status === 'pending' ? 'bg-yellow-500/10' :
                        'bg-gray-500/10'
                      )}>
                        <StatusIcon className={cn('w-4 h-4', statusConfig[trade.status].color)} />
                      </div>

                      {/* Trade Info */}
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium truncate">{trade.marketTitle}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={cn(
                            'px-2 py-0.5 text-xs rounded',
                            platformColors[trade.platform]
                          )}>
                            {trade.platform}
                          </span>
                          <span className={cn(
                            'text-xs font-medium',
                            trade.side === 'YES' ? 'text-green-500' : 'text-red-500'
                          )}>
                            {trade.side}
                          </span>
                          <span className="text-xs text-gray-500">
                            {trade.size} @ ${trade.price.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Right Side */}
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className={cn(
                          'text-sm font-medium',
                          statusConfig[trade.status].color
                        )}>
                          {statusConfig[trade.status].label}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatDate(new Date(trade.createdAt))}
                        </p>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4 text-gray-500" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="px-4 pb-4">
                    <div className="p-4 bg-gray-800/50 rounded-lg space-y-3">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs text-gray-500">Trade ID</p>
                          <p className="text-sm text-white font-mono">{trade.id}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Order Type</p>
                          <p className="text-sm text-white capitalize">{trade.orderType}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Executed By</p>
                          <p className="text-sm text-white">{trade.executedBy}</p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500">Updated</p>
                          <p className="text-sm text-white">
                            {formatDate(new Date(trade.updatedAt))}
                          </p>
                        </div>
                      </div>

                      {/* Filled Details */}
                      {(trade.status === 'filled' || trade.status === 'partial') && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-3 border-t border-gray-700">
                          <div>
                            <p className="text-xs text-gray-500">Filled Size</p>
                            <p className="text-sm text-white">
                              {trade.filledSize || trade.size} shares
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Filled Price</p>
                            <p className="text-sm text-white">
                              ${(trade.filledPrice || trade.price).toFixed(2)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Fees</p>
                            <p className="text-sm text-white">
                              {formatCurrency(trade.fees || 0)}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Total Cost</p>
                            <p className="text-sm text-white font-medium">
                              {formatCurrency(trade.totalCost || 0)}
                            </p>
                          </div>
                        </div>
                      )}

                      {/* Error Message */}
                      {trade.status === 'failed' && trade.error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                          <p className="text-sm text-red-500">{trade.error}</p>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-2 pt-3 border-t border-gray-700">
                        {onTradeClick && (
                          <button
                            onClick={() => onTradeClick(trade)}
                            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
                          >
                            <ExternalLink className="w-3 h-3" />
                            View Details
                          </button>
                        )}
                        {trade.status === 'pending' && (
                          <button
                            className="px-3 py-1.5 text-sm bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 transition-colors"
                          >
                            Cancel Order
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="p-8 text-center text-gray-500">
            No manual trades yet
          </div>
        )}
      </div>
    </div>
  );
}

export default RecentManualTrades;
