'use client';

import { useState } from 'react';
import { cn, formatCurrency, formatRelativeTime, getPnlClass } from '@/lib/utils';
import {
  Play,
  Pause,
  Square,
  Settings,
  ChevronDown,
  ChevronUp,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import type { Strategy, StrategyType } from '@/types';

interface StrategyCardProps {
  strategy: Strategy;
  onStart: () => void;
  onPause: () => void;
  onStop: () => void;
  onConfigure: () => void;
}

const strategyIcons: Record<StrategyType, string> = {
  arbitrage: '⚖️',
  market_making: '📊',
  spike_detection: '📈',
  ai_forecast: '🤖',
};

const strategyLabels: Record<StrategyType, string> = {
  arbitrage: 'Arbitrage',
  market_making: 'Market Making',
  spike_detection: 'Spike Detection',
  ai_forecast: 'AI Forecast',
};

const strategyDescriptions: Record<StrategyType, string> = {
  arbitrage: 'Exploits price differences across platforms',
  market_making: 'Provides liquidity and earns spread',
  spike_detection: 'Detects and trades on sudden price movements',
  ai_forecast: 'Uses AI to predict market outcomes',
};

export function StrategyCard({
  strategy,
  onStart,
  onPause,
  onStop,
  onConfigure,
}: StrategyCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const isActive = strategy.status === 'active';
  const isPaused = strategy.status === 'paused';
  const isStopped = strategy.status === 'stopped';
  const hasError = strategy.status === 'error';

  const getStatusBadge = () => {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full';
    switch (strategy.status) {
      case 'active':
        return (
          <span className={`${baseClasses} bg-green-500/20 text-green-400`}>
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500 mr-1.5 animate-pulse" />
            Active
          </span>
        );
      case 'paused':
        return (
          <span className={`${baseClasses} bg-yellow-500/20 text-yellow-400`}>
            Paused
          </span>
        );
      case 'stopped':
        return (
          <span className={`${baseClasses} bg-gray-500/20 text-gray-400`}>
            Stopped
          </span>
        );
      case 'error':
        return (
          <span className={`${baseClasses} bg-red-500/20 text-red-400`}>
            Error
          </span>
        );
    }
  };

  return (
    <div
      className={cn(
        'rounded-xl border transition-all duration-200',
        isActive && 'border-green-500/30 bg-green-500/5',
        isPaused && 'border-yellow-500/30 bg-yellow-500/5',
        isStopped && 'border-gray-700 bg-gray-900/50',
        hasError && 'border-red-500/30 bg-red-500/5'
      )}
    >
      {/* Header */}
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <span className="text-4xl">{strategyIcons[strategy.type]}</span>
            <div>
              <h3 className="text-lg font-semibold text-white">
                {strategyLabels[strategy.type]}
              </h3>
              <p className="text-sm text-gray-400">
                {strategyDescriptions[strategy.type]}
              </p>
            </div>
          </div>
          {getStatusBadge()}
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="p-3 rounded-lg bg-gray-800/50">
            <p className="text-xs text-gray-500 mb-1">Today&apos;s P&L</p>
            <div className="flex items-center gap-1">
              <span className={cn('text-xl font-semibold', getPnlClass(strategy.pnlToday))}>
                {formatCurrency(strategy.pnlToday)}
              </span>
              {strategy.pnlToday > 0 ? (
                <TrendingUp className="w-4 h-4 text-green-500" />
              ) : strategy.pnlToday < 0 ? (
                <TrendingDown className="w-4 h-4 text-red-500" />
              ) : null}
            </div>
          </div>
          <div className="p-3 rounded-lg bg-gray-800/50">
            <p className="text-xs text-gray-500 mb-1">Total P&L</p>
            <span className={cn('text-xl font-semibold', getPnlClass(strategy.pnl))}>
              {formatCurrency(strategy.pnl)}
            </span>
          </div>
          <div className="p-3 rounded-lg bg-gray-800/50">
            <p className="text-xs text-gray-500 mb-1">Positions</p>
            <span className="text-xl font-semibold text-white">
              {strategy.positionsCount}
            </span>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex items-center gap-2">
          {!isActive && !hasError && (
            <button
              onClick={onStart}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-green-500/20 text-green-400 hover:bg-green-500/30 transition-colors"
            >
              <Play className="w-4 h-4" />
              Start
            </button>
          )}
          {isActive && (
            <button
              onClick={onPause}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition-colors"
            >
              <Pause className="w-4 h-4" />
              Pause
            </button>
          )}
          {(isActive || isPaused) && (
            <button
              onClick={onStop}
              className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
            >
              <Square className="w-4 h-4" />
              Stop
            </button>
          )}
          <button
            onClick={onConfigure}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors ml-auto"
          >
            <Settings className="w-4 h-4" />
            Configure
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-2 rounded-lg hover:bg-gray-800 text-gray-400 transition-colors"
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="px-6 pb-6 pt-0 border-t border-gray-800">
          <div className="pt-4 space-y-4">
            {/* Performance Metrics */}
            <div>
              <h4 className="text-sm font-medium text-gray-400 mb-3">
                Performance Metrics
              </h4>
              <div className="grid grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-gray-800/30">
                  <p className="text-xs text-gray-500">Total Trades</p>
                  <p className="text-lg font-semibold text-white">
                    {strategy.metrics.totalTrades}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-800/30">
                  <p className="text-xs text-gray-500">Win Rate</p>
                  <p className="text-lg font-semibold text-white">
                    {(strategy.metrics.winRate * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-800/30">
                  <p className="text-xs text-gray-500">Avg Profit</p>
                  <p className="text-lg font-semibold text-green-400">
                    {formatCurrency(strategy.metrics.avgProfit)}
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-gray-800/30">
                  <p className="text-xs text-gray-500">Avg Loss</p>
                  <p className="text-lg font-semibold text-red-400">
                    {formatCurrency(strategy.metrics.avgLoss)}
                  </p>
                </div>
              </div>
            </div>

            {/* Last Activity */}
            {strategy.lastActivity && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Last Activity</span>
                <span className="text-gray-400">
                  {formatRelativeTime(strategy.lastActivity)}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default StrategyCard;
