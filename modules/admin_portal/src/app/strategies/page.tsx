'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { StrategyCard } from '@/components/strategies/StrategyCard';
import { EmergencyControls } from '@/components/strategies/EmergencyControls';
import { orchestratorApi } from '@/lib/api';
import type { Strategy } from '@/types';

// Mock data for development
const mockStrategies: Strategy[] = [
  {
    id: '1',
    name: 'Arbitrage',
    type: 'arbitrage',
    status: 'active',
    pnl: 15000,
    pnlToday: 450,
    positionsCount: 3,
    lastActivity: new Date(),
    config: {
      minSpread: 0.02,
      maxPositionSize: 1000,
      platforms: ['polymarket', 'kalshi'],
    },
    metrics: {
      totalTrades: 150,
      winRate: 0.72,
      avgProfit: 45,
      avgLoss: 25,
      sharpeRatio: 1.8,
      maxDrawdown: 0.05,
    },
  },
  {
    id: '2',
    name: 'Market Making',
    type: 'market_making',
    status: 'active',
    pnl: 8500,
    pnlToday: 280,
    positionsCount: 5,
    lastActivity: new Date(),
    config: {
      spreadTarget: 0.03,
      inventoryLimit: 5000,
      rebalanceThreshold: 0.1,
    },
    metrics: {
      totalTrades: 320,
      winRate: 0.65,
      avgProfit: 30,
      avgLoss: 20,
      sharpeRatio: 1.5,
      maxDrawdown: 0.08,
    },
  },
  {
    id: '3',
    name: 'Spike Detection',
    type: 'spike_detection',
    status: 'paused',
    pnl: 3200,
    pnlToday: 0,
    positionsCount: 0,
    lastActivity: new Date(Date.now() - 3600000),
    config: {
      volumeThreshold: 2.0,
      priceChangeThreshold: 0.15,
      cooldownMinutes: 30,
    },
    metrics: {
      totalTrades: 45,
      winRate: 0.78,
      avgProfit: 120,
      avgLoss: 80,
      sharpeRatio: 2.1,
      maxDrawdown: 0.12,
    },
  },
  {
    id: '4',
    name: 'AI Forecast',
    type: 'ai_forecast',
    status: 'active',
    pnl: 12000,
    pnlToday: 504,
    positionsCount: 4,
    lastActivity: new Date(),
    config: {
      confidenceThreshold: 0.7,
      maxPositionsPerForecast: 3,
      llmModel: 'gpt-4',
    },
    metrics: {
      totalTrades: 89,
      winRate: 0.68,
      avgProfit: 180,
      avgLoss: 95,
      sharpeRatio: 1.9,
      maxDrawdown: 0.1,
    },
  },
];

export default function StrategiesPage() {
  const queryClient = useQueryClient();
  const [systemPaused, setSystemPaused] = useState(false);
  const [systemStopped, setSystemStopped] = useState(false);

  // Fetch strategies
  const { data: strategies = mockStrategies, isLoading } = useQuery({
    queryKey: ['strategies'],
    queryFn: async () => {
      // In production, call real API
      // const result = await orchestratorApi.getStrategies();
      // return result.data || [];
      return mockStrategies;
    },
    refetchInterval: 10000,
  });

  // Strategy control mutations
  const strategyMutation = useMutation({
    mutationFn: async ({
      strategyId,
      action,
    }: {
      strategyId: string;
      action: 'start' | 'pause' | 'stop';
    }) => {
      await orchestratorApi.updateStrategyStatus(strategyId, action);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['strategies'] });
    },
  });

  // Emergency control handlers
  const handlePauseAll = async () => {
    await orchestratorApi.pauseAllStrategies();
    setSystemPaused(true);
    queryClient.invalidateQueries({ queryKey: ['strategies'] });
  };

  const handleStopAll = async () => {
    await orchestratorApi.stopAllStrategies();
    setSystemStopped(true);
    setSystemPaused(false);
    queryClient.invalidateQueries({ queryKey: ['strategies'] });
  };

  const handleCloseAllPositions = async () => {
    await orchestratorApi.emergencyCloseAll();
    queryClient.invalidateQueries({ queryKey: ['positions'] });
  };

  const handleStrategyAction = (
    strategyId: string,
    action: 'start' | 'pause' | 'stop'
  ) => {
    strategyMutation.mutate({ strategyId, action });
  };

  const handleConfigureStrategy = (strategy: Strategy) => {
    // In production, open a configuration modal
    console.log('Configure strategy:', strategy);
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold text-white">Strategies</h1>
          <p className="text-gray-400">
            Manage and monitor your trading strategies
          </p>
        </div>

        {/* Emergency Controls */}
        <EmergencyControls
          onPauseAll={handlePauseAll}
          onStopAll={handleStopAll}
          onCloseAllPositions={handleCloseAllPositions}
          isPaused={systemPaused}
          isStopped={systemStopped}
        />

        {/* Strategy Cards */}
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">
            Active Strategies
          </h2>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {strategies.map((strategy) => (
                <StrategyCard
                  key={strategy.id}
                  strategy={strategy}
                  onStart={() => handleStrategyAction(strategy.id, 'start')}
                  onPause={() => handleStrategyAction(strategy.id, 'pause')}
                  onStop={() => handleStrategyAction(strategy.id, 'stop')}
                  onConfigure={() => handleConfigureStrategy(strategy)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Active Strategies
            </p>
            <p className="text-2xl font-bold text-white">
              {strategies.filter((s) => s.status === 'active').length}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Total Positions
            </p>
            <p className="text-2xl font-bold text-white">
              {strategies.reduce((sum, s) => sum + s.positionsCount, 0)}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Today&apos;s P&L
            </p>
            <p className="text-2xl font-bold text-green-500">
              ${strategies.reduce((sum, s) => sum + s.pnlToday, 0).toFixed(2)}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-gray-900/50 border border-gray-800">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
              Total P&L
            </p>
            <p className="text-2xl font-bold text-green-500">
              ${strategies.reduce((sum, s) => sum + s.pnl, 0).toFixed(2)}
            </p>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
