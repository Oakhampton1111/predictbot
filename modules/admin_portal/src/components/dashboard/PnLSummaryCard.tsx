'use client';

import { cn, formatCurrency, formatPercent, getPnlClass } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus, DollarSign } from 'lucide-react';

interface PnLSummaryCardProps {
  today: number;
  week: number;
  month: number;
  total: number;
  trend: 'up' | 'down' | 'flat';
}

export function PnLSummaryCard({
  today,
  week,
  month,
  total,
  trend,
}: PnLSummaryCardProps) {
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
  const trendColor = trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-gray-500';

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-green-500/10">
            <DollarSign className="w-5 h-5 text-green-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">P&L Summary</h3>
            <p className="text-sm text-gray-400">Profit & Loss Overview</p>
          </div>
        </div>
        <TrendIcon className={cn('w-6 h-6', trendColor)} />
      </div>

      {/* Today's P&L - Large Display */}
      <div className="mb-6">
        <p className="text-sm text-gray-400 mb-1">Today</p>
        <div className="flex items-baseline gap-2">
          <span className={cn('text-4xl font-bold', getPnlClass(today))}>
            {formatCurrency(today)}
          </span>
          {today !== 0 && (
            <span className={cn('text-sm', getPnlClass(today))}>
              {formatPercent((today / Math.abs(total || 1)) * 100)}
            </span>
          )}
        </div>
      </div>

      {/* Period Breakdown */}
      <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-800">
        <div>
          <p className="text-xs text-gray-500 mb-1">This Week</p>
          <p className={cn('text-lg font-semibold', getPnlClass(week))}>
            {formatCurrency(week)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">This Month</p>
          <p className={cn('text-lg font-semibold', getPnlClass(month))}>
            {formatCurrency(month)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">All Time</p>
          <p className={cn('text-lg font-semibold', getPnlClass(total))}>
            {formatCurrency(total)}
          </p>
        </div>
      </div>
    </div>
  );
}

export default PnLSummaryCard;
