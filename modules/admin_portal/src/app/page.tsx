'use client';

import { useQuery } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { SystemHealthCard } from '@/components/dashboard/SystemHealthCard';
import { PnLSummaryCard } from '@/components/dashboard/PnLSummaryCard';
import { PositionsCard } from '@/components/dashboard/PositionsCard';
import { StrategyCards } from '@/components/dashboard/StrategyCards';
import { ActivityFeed } from '@/components/dashboard/ActivityFeed';
import { AIStatusCard } from '@/components/dashboard/AIStatusCard';
import { orchestratorApi, aiApi } from '@/lib/api';
import type { DashboardSummary, SystemHealth, PositionSummary, Strategy, Activity, AIStatus } from '@/types';

// Mock data for development - replace with real API calls
const mockDashboardData: DashboardSummary = {
  systemHealth: {
    overall: 'healthy',
    services: [
      { name: 'Orchestrator', status: 'healthy', lastHeartbeat: new Date(), latency: 45 },
      { name: 'PostgreSQL', status: 'healthy', lastHeartbeat: new Date(), latency: 12 },
      { name: 'Redis', status: 'healthy', lastHeartbeat: new Date(), latency: 3 },
      { name: 'Polymarket API', status: 'healthy', lastHeartbeat: new Date(), latency: 120 },
      { name: 'Kalshi API', status: 'healthy', lastHeartbeat: new Date(), latency: 95 },
      { name: 'AI Orchestrator', status: 'healthy', lastHeartbeat: new Date(), latency: 200 },
    ],
    lastUpdated: new Date(),
  },
  pnl: {
    today: 1234.56,
    week: 5678.90,
    month: 12345.67,
    total: 45678.90,
    trend: 'up',
  },
  positions: {
    totalPositions: 12,
    totalValue: 25000,
    totalPnl: 1500,
    byPlatform: {
      polymarket: { count: 5, value: 12000, pnl: 800 },
      kalshi: { count: 4, value: 8000, pnl: 500 },
      manifold: { count: 3, value: 5000, pnl: 200 },
    },
  },
  strategies: [
    {
      id: '1',
      name: 'Arbitrage',
      type: 'arbitrage',
      status: 'active',
      pnl: 15000,
      pnlToday: 450,
      positionsCount: 3,
      lastActivity: new Date(),
      config: {},
      metrics: { totalTrades: 150, winRate: 0.72, avgProfit: 45, avgLoss: 25 },
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
      config: {},
      metrics: { totalTrades: 320, winRate: 0.65, avgProfit: 30, avgLoss: 20 },
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
      config: {},
      metrics: { totalTrades: 45, winRate: 0.78, avgProfit: 120, avgLoss: 80 },
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
      config: {},
      metrics: { totalTrades: 89, winRate: 0.68, avgProfit: 180, avgLoss: 95 },
    },
  ],
  recentActivity: [
    {
      id: '1',
      type: 'trade_executed',
      title: 'Trade Executed',
      description: 'Bought 100 YES shares on "Will BTC reach $100k by March?" at $0.45',
      timestamp: new Date(Date.now() - 60000),
      severity: 'success',
    },
    {
      id: '2',
      type: 'ai_decision',
      title: 'AI Forecast Generated',
      description: 'High confidence prediction for market #12345 - 78% probability',
      timestamp: new Date(Date.now() - 180000),
      severity: 'info',
    },
    {
      id: '3',
      type: 'position_closed',
      title: 'Position Closed',
      description: 'Closed position on Kalshi with +$125 profit',
      timestamp: new Date(Date.now() - 300000),
      severity: 'success',
    },
    {
      id: '4',
      type: 'alert_triggered',
      title: 'Price Alert',
      description: 'Market "Fed Rate Decision" moved 15% in 5 minutes',
      timestamp: new Date(Date.now() - 600000),
      severity: 'warning',
    },
  ],
  aiStatus: {
    isRunning: true,
    currentAgent: 'Forecast Agent',
    lastCycleTime: 1250,
    forecastCount: 156,
    llmUsage: {
      tokensUsed: 45000,
      requestsToday: 89,
      costToday: 2.35,
    },
    agents: [
      { name: 'Data Collector', status: 'idle', lastRun: new Date(Date.now() - 60000), successRate: 0.98 },
      { name: 'Forecast Agent', status: 'running', lastRun: new Date(), successRate: 0.92 },
      { name: 'Risk Analyzer', status: 'idle', lastRun: new Date(Date.now() - 120000), successRate: 0.95 },
      { name: 'Trade Executor', status: 'idle', lastRun: new Date(Date.now() - 30000), successRate: 0.99 },
    ],
  },
};

export default function DashboardPage() {
  // Fetch dashboard data
  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard'],
    queryFn: async () => {
      // In production, this would call the real API
      // const [health, positions, strategies, aiStatus] = await Promise.all([
      //   orchestratorApi.getHealth(),
      //   orchestratorApi.getPositions(),
      //   orchestratorApi.getStrategies(),
      //   aiApi.getStatus(),
      // ]);
      // return { health, positions, strategies, aiStatus };
      
      // For now, return mock data
      return mockDashboardData;
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const handleToggleStrategy = async (strategyId: string, action: 'start' | 'pause' | 'stop') => {
    try {
      await orchestratorApi.updateStrategyStatus(strategyId, action);
      // Refetch data after action
    } catch (error) {
      console.error('Failed to update strategy:', error);
    }
  };

  if (isLoading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
          <div className="flex flex-col items-center gap-4">
            <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            <p className="text-gray-400">Loading dashboard...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error || !data) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center h-[calc(100vh-8rem)]">
          <div className="text-center">
            <p className="text-red-500 mb-2">Failed to load dashboard data</p>
            <p className="text-gray-500 text-sm">Please check your connection and try again</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400">Real-time overview of your trading bot</p>
        </div>

        {/* Top Row - Health and P&L */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <SystemHealthCard health={data.systemHealth} />
          <PnLSummaryCard
            today={data.pnl.today}
            week={data.pnl.week}
            month={data.pnl.month}
            total={data.pnl.total}
            trend={data.pnl.trend}
          />
        </div>

        {/* Middle Row - Positions and Strategies */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <PositionsCard summary={data.positions} />
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Strategies</h2>
            <StrategyCards
              strategies={data.strategies}
              onToggleStrategy={handleToggleStrategy}
            />
          </div>
        </div>

        {/* Bottom Row - Activity and AI Status */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ActivityFeed activities={data.recentActivity} />
          <AIStatusCard status={data.aiStatus} />
        </div>
      </div>
    </MainLayout>
  );
}
