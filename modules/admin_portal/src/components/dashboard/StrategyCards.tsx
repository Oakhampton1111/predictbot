'use client';

import { cn, formatCurrency, getPnlClass, getStatusColor } from '@/lib/utils';
import { Zap, Play, Pause, Square, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import type { Strategy, StrategyType } from '@/types';

interface StrategyCardsProps {
  strategies: Strategy[];
  onToggleStrategy?: (strategyId: string, action: 'start' | 'pause' | 'stop') => void;
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

export function StrategyCards({ strategies, onToggleStrategy }: StrategyCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {strategies.map((strategy) => (
        <StrategyCard
          key={strategy.id}
          strategy={strategy}
          onToggle={onToggleStrategy}
        />
      ))}
    </div>
  );
}

interface StrategyCardProps {
  strategy: Strategy;
  onToggle?: (strategyId: string, action: 'start' | 'pause' | 'stop') => void;
}

function StrategyCard({ strategy, onToggle }: StrategyCardProps) {
  const isActive = strategy.status === 'active';
  const isPaused = strategy.status === 'paused';
  const isStopped = strategy.status === 'stopped';
  const hasError = strategy.status === 'error';

  const handleAction = (action: 'start' | 'pause' | 'stop') => {
    if (onToggle) {
      onToggle(strategy.id, action);
    }
  };

  return (
    <div
      className={cn(
        'rounded-xl border p-4 transition-all duration-200',
        isActive && 'border-green-500/30 bg-green-500/5',
        isPaused && 'border-yellow-500/30 bg-yellow-500/5',
        isStopped && 'border-gray-700 bg-gray-900/50',
        hasError && 'border-red-500/30 bg-red-500/5'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{strategyIcons[strategy.type]}</span>
          <div>
            <h4 className="text-sm font-semibold text-white">
              {strategyLabels[strategy.type]}
            </h4>
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  'inline-flex items-center gap-1 text-xs font-medium capitalize',
                  getStatusColor(strategy.status)
                )}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-current" />
                {strategy.status}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Toggle */}
        <div className="flex items-center gap-1">
          {!isActive && !hasError && (
            <button
              onClick={() => handleAction('start')}
              className="p-1.5 rounded-lg hover:bg-green-500/20 text-green-500 transition-colors"
              title="Start"
            >
              <Play className="w-4 h-4" />
            </button>
          )}
          {isActive && (
            <button
              onClick={() => handleAction('pause')}
              className="p-1.5 rounded-lg hover:bg-yellow-500/20 text-yellow-500 transition-colors"
              title="Pause"
            >
              <Pause className="w-4 h-4" />
            </button>
          )}
          {(isActive || isPaused) && (
            <button
              onClick={() => handleAction('stop')}
              className="p-1.5 rounded-lg hover:bg-red-500/20 text-red-500 transition-colors"
              title="Stop"
            >
              <Square className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-gray-500 mb-1">Today&apos;s P&L</p>
          <div className="flex items-center gap-1">
            <span className={cn('text-lg font-semibold', getPnlClass(strategy.pnlToday))}>
              {formatCurrency(strategy.pnlToday)}
            </span>
            {strategy.pnlToday !== 0 && (
              strategy.pnlToday > 0 ? (
                <ArrowUpRight className="w-4 h-4 text-green-500" />
              ) : (
                <ArrowDownRight className="w-4 h-4 text-red-500" />
              )
            )}
          </div>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">Positions</p>
          <span className="text-lg font-semibold text-white">
            {strategy.positionsCount}
          </span>
        </div>
      </div>

      {/* Metrics */}
      {strategy.metrics && (
        <div className="mt-3 pt-3 border-t border-gray-800 grid grid-cols-3 gap-2">
          <div>
            <p className="text-xs text-gray-500">Win Rate</p>
            <p className="text-sm font-medium text-white">
              {(strategy.metrics.winRate * 100).toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Trades</p>
            <p className="text-sm font-medium text-white">
              {strategy.metrics.totalTrades}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Total P&L</p>
            <p className={cn('text-sm font-medium', getPnlClass(strategy.pnl))}>
              {formatCurrency(strategy.pnl)}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default StrategyCards;
