'use client';

import Link from 'next/link';
import { cn, formatCurrency, formatNumber, getPnlClass } from '@/lib/utils';
import { Briefcase, ArrowRight } from 'lucide-react';
import type { PositionSummary, Platform } from '@/types';

interface PositionsCardProps {
  summary: PositionSummary;
}

const platformLabels: Record<Platform, string> = {
  polymarket: 'Polymarket',
  kalshi: 'Kalshi',
  manifold: 'Manifold',
};

const platformColors: Record<Platform, string> = {
  polymarket: 'bg-purple-500',
  kalshi: 'bg-blue-500',
  manifold: 'bg-green-500',
};

export function PositionsCard({ summary }: PositionsCardProps) {
  const platforms = Object.entries(summary.byPlatform) as [Platform, { count: number; value: number; pnl: number }][];

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/10">
            <Briefcase className="w-5 h-5 text-blue-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Active Positions</h3>
            <p className="text-sm text-gray-400">{formatNumber(summary.totalPositions)} open positions</p>
          </div>
        </div>
        <Link
          href="/positions"
          className="flex items-center gap-1 text-sm text-primary hover:text-primary/80 transition-colors"
        >
          View All
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 rounded-lg bg-gray-800/50">
          <p className="text-xs text-gray-500 mb-1">Total Value</p>
          <p className="text-xl font-semibold text-white">
            {formatCurrency(summary.totalValue)}
          </p>
        </div>
        <div className="p-4 rounded-lg bg-gray-800/50">
          <p className="text-xs text-gray-500 mb-1">Unrealized P&L</p>
          <p className={cn('text-xl font-semibold', getPnlClass(summary.totalPnl))}>
            {formatCurrency(summary.totalPnl)}
          </p>
        </div>
      </div>

      {/* Platform Breakdown */}
      <div className="space-y-3">
        <p className="text-xs text-gray-500 uppercase tracking-wider">By Platform</p>
        {platforms.map(([platform, data]) => (
          <div
            key={platform}
            className="flex items-center justify-between p-3 rounded-lg bg-gray-800/30"
          >
            <div className="flex items-center gap-3">
              <div className={cn('w-2 h-2 rounded-full', platformColors[platform])} />
              <span className="text-sm font-medium text-white">
                {platformLabels[platform]}
              </span>
              <span className="text-xs text-gray-500">
                {data.count} positions
              </span>
            </div>
            <div className="text-right">
              <p className="text-sm font-medium text-white">
                {formatCurrency(data.value)}
              </p>
              <p className={cn('text-xs', getPnlClass(data.pnl))}>
                {formatCurrency(data.pnl)}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PositionsCard;
