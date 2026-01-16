'use client';

import { useState, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { cn } from '@/lib/utils';
import {
  Play,
  Pause,
  Square,
  RefreshCw,
  Download,
  Upload,
  Settings,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  Clock,
  AlertTriangle,
  FlaskConical,
  ChevronDown,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';

// Mock data for demonstration
const mockBacktestResults = {
  totalReturn: 0.234,
  sharpeRatio: 1.85,
  maxDrawdown: -0.12,
  winRate: 0.62,
  totalTrades: 156,
  profitFactor: 2.1,
  avgTradeReturn: 0.015,
  startDate: '2025-01-01',
  endDate: '2025-12-31',
};

const mockEquityCurve = Array.from({ length: 50 }, (_, i) => ({
  date: `Day ${i + 1}`,
  equity: 10000 * Math.pow(1.003, i) + (Math.random() - 0.5) * 200,
  benchmark: 10000 * Math.pow(1.001, i),
}));

const mockTrades = [
  { id: 1, market: 'Will BTC exceed $100k?', platform: 'Polymarket', side: 'BUY_YES', entryPrice: 0.45, exitPrice: 0.72, size: 100, pnl: 27.0, timestamp: '2025-06-15 14:30' },
  { id: 2, market: 'Fed rate cut in Q2?', platform: 'Kalshi', side: 'BUY_NO', entryPrice: 0.35, exitPrice: 0.28, size: 150, pnl: -10.5, timestamp: '2025-06-14 09:15' },
  { id: 3, market: 'S&P 500 above 5000?', platform: 'Polymarket', side: 'BUY_YES', entryPrice: 0.62, exitPrice: 0.85, size: 200, pnl: 46.0, timestamp: '2025-06-13 16:45' },
];

const mockStrategies = [
  { id: 'arbitrage', name: 'Arbitrage', enabled: true },
  { id: 'spike', name: 'Spike Detector', enabled: true },
  { id: 'momentum', name: 'Momentum', enabled: false },
  { id: 'mean_reversion', name: 'Mean Reversion', enabled: true },
  { id: 'market_maker', name: 'Market Maker', enabled: false },
];

const mockDrawdownData = Array.from({ length: 50 }, (_, i) => ({
  date: `Day ${i + 1}`,
  drawdown: -Math.abs(Math.sin(i / 10) * 0.1 + Math.random() * 0.02),
}));

export default function SimulationPage() {
  const [simulationMode, setSimulationMode] = useState<'backtest' | 'paper'>('backtest');
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [selectedStrategy, setSelectedStrategy] = useState('all');
  const [initialCapital, setInitialCapital] = useState(10000);
  const [dateRange, setDateRange] = useState({ start: '2025-01-01', end: '2025-12-31' });

  useEffect(() => {
    if (isRunning && progress < 100) {
      const timer = setTimeout(() => {
        setProgress((prev) => Math.min(prev + Math.random() * 5, 100));
      }, 200);
      return () => clearTimeout(timer);
    } else if (progress >= 100) {
      setIsRunning(false);
    }
  }, [isRunning, progress]);

  const handleStartBacktest = () => {
    setIsRunning(true);
    setProgress(0);
  };

  const handleStopBacktest = () => {
    setIsRunning(false);
  };

  const formatPercent = (value: number) => `${(value * 100).toFixed(2)}%`;
  const formatCurrency = (value: number) => `$${value.toLocaleString()}`;

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/10">
              <FlaskConical className="w-6 h-6 text-purple-500" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">Simulation & Backtesting</h1>
              <p className="text-gray-400">Test strategies with historical data or paper trade</p>
            </div>
          </div>
          <div className="flex gap-2">
            <button className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 hover:text-white transition-colors">
              <Upload className="h-4 w-4" />
              Import
            </button>
            <button className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 hover:text-white transition-colors">
              <Download className="h-4 w-4" />
              Export
            </button>
          </div>
        </div>

        {/* Mode Tabs */}
        <div className="flex gap-2 p-1 bg-gray-800 rounded-lg w-fit">
          <button
            onClick={() => setSimulationMode('backtest')}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
              simulationMode === 'backtest' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'
            )}
          >
            <Clock className="h-4 w-4" />
            Backtest
          </button>
          <button
            onClick={() => setSimulationMode('paper')}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
              simulationMode === 'paper' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'
            )}
          >
            <Activity className="h-4 w-4" />
            Paper Trading
          </button>
        </div>

        {simulationMode === 'backtest' ? (
          <>
            {/* Configuration Panel */}
            <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Settings className="h-5 w-5 text-gray-400" />
                <h2 className="text-lg font-semibold text-white">Backtest Configuration</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Strategy</label>
                    <div className="relative">
                      <select
                        value={selectedStrategy}
                        onChange={(e) => setSelectedStrategy(e.target.value)}
                        className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white appearance-none cursor-pointer"
                      >
                        <option value="all">All Strategies</option>
                        {mockStrategies.map((s) => (
                          <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                      </select>
                      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">Start Date</label>
                    <input
                      type="date"
                      value={dateRange.start}
                      onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">End Date</label>
                    <input
                      type="date"
                      value={dateRange.end}
                      onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white"
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-gray-400 mb-2">
                      Initial Capital: {formatCurrency(initialCapital)}
                    </label>
                    <input
                      type="range"
                      value={initialCapital}
                      onChange={(e) => setInitialCapital(Number(e.target.value))}
                      min={1000}
                      max={100000}
                      step={1000}
                      className="w-full"
                    />
                  </div>
                  <div className="flex gap-2 pt-4">
                    {!isRunning ? (
                      <button
                        onClick={handleStartBacktest}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
                      >
                        <Play className="h-4 w-4" />
                        Run Backtest
                      </button>
                    ) : (
                      <button
                        onClick={handleStopBacktest}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
                      >
                        <Square className="h-4 w-4" />
                        Stop
                      </button>
                    )}
                    <button
                      onClick={() => setProgress(0)}
                      className="px-3 py-2 bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700"
                    >
                      <RefreshCw className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>

              {(isRunning || progress > 0) && (
                <div className="mt-6">
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-gray-400">Progress</span>
                    <span className="text-white">{progress.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2">
                    <div className="bg-primary h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
                  </div>
                </div>
              )}
            </div>

            {/* Results Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Total Return</p>
                    <p className={cn('text-2xl font-bold', mockBacktestResults.totalReturn >= 0 ? 'text-green-500' : 'text-red-500')}>
                      {formatPercent(mockBacktestResults.totalReturn)}
                    </p>
                  </div>
                  {mockBacktestResults.totalReturn >= 0 ? <TrendingUp className="h-8 w-8 text-green-500" /> : <TrendingDown className="h-8 w-8 text-red-500" />}
                </div>
              </div>
              <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Sharpe Ratio</p>
                    <p className="text-2xl font-bold text-white">{mockBacktestResults.sharpeRatio.toFixed(2)}</p>
                  </div>
                  <Target className="h-8 w-8 text-blue-500" />
                </div>
              </div>
              <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Max Drawdown</p>
                    <p className="text-2xl font-bold text-red-500">{formatPercent(mockBacktestResults.maxDrawdown)}</p>
                  </div>
                  <AlertTriangle className="h-8 w-8 text-red-500" />
                </div>
              </div>
              <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Win Rate</p>
                    <p className="text-2xl font-bold text-white">{formatPercent(mockBacktestResults.winRate)}</p>
                  </div>
                  <DollarSign className="h-8 w-8 text-green-500" />
                </div>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Equity Curve</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={mockEquityCurve}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9CA3AF' }} />
                    <YAxis tick={{ fontSize: 10, fill: '#9CA3AF' }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Legend />
                    <Line type="monotone" dataKey="equity" stroke="#22c55e" name="Strategy" dot={false} />
                    <Line type="monotone" dataKey="benchmark" stroke="#6b7280" name="Benchmark" dot={false} strokeDasharray="5 5" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Drawdown</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={mockDrawdownData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#9CA3AF' }} />
                    <YAxis tick={{ fontSize: 10, fill: '#9CA3AF' }} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
                    <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                    <Area type="monotone" dataKey="drawdown" stroke="#ef4444" fill="#ef444433" name="Drawdown" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Trade History */}
            <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Trade History</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-800">
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Time</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Market</th>
                      <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Side</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Entry</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Exit</th>
                      <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockTrades.map((trade) => (
                      <tr key={trade.id} className="border-b border-gray-800/50">
                        <td className="py-3 px-4 text-sm text-gray-300">{trade.timestamp}</td>
                        <td className="py-3 px-4 text-sm text-white">{trade.market}</td>
                        <td className="py-3 px-4">
                          <span className={cn('px-2 py-1 text-xs rounded', trade.side.includes('YES') ? 'bg-green-500/10 text-green-500' : 'bg-blue-500/10 text-blue-500')}>
                            {trade.side}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-right text-sm text-gray-300">{trade.entryPrice.toFixed(2)}</td>
                        <td className="py-3 px-4 text-right text-sm text-gray-300">{trade.exitPrice.toFixed(2)}</td>
                        <td className={cn('py-3 px-4 text-right text-sm font-medium', trade.pnl >= 0 ? 'text-green-500' : 'text-red-500')}>
                          {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <>
            {/* Paper Trading Dashboard */}
            <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="h-5 w-5 text-gray-400" />
                <h2 className="text-lg font-semibold text-white">Paper Trading Status</h2>
              </div>

              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-800 text-gray-300">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
                    Paused
                  </span>
                </div>
                <div className="flex gap-2">
                  <button className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                    <Play className="h-4 w-4" />
                    Start Trading
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-4 bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-400">Paper Balance</p>
                  <p className="text-2xl font-bold text-white">$10,000.00</p>
                </div>
                <div className="p-4 bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-400">Unrealized P&L</p>
                  <p className="text-2xl font-bold text-green-500">+$234.50</p>
                </div>
                <div className="p-4 bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-400">Open Positions</p>
                  <p className="text-2xl font-bold text-white">3</p>
                </div>
                <div className="p-4 bg-gray-800 rounded-lg">
                  <p className="text-sm text-gray-400">Today&apos;s Trades</p>
                  <p className="text-2xl font-bold text-white">12</p>
                </div>
              </div>
            </div>

            {/* Active Strategies */}
            <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Active Strategies</h3>
              <div className="space-y-3">
                {mockStrategies.map((strategy) => (
                  <div key={strategy.id} className="flex items-center justify-between p-4 border border-gray-800 rounded-lg">
                    <div className="flex items-center gap-4">
                      <div className={cn('w-3 h-3 rounded-full', strategy.enabled ? 'bg-green-500' : 'bg-gray-500')} />
                      <div>
                        <p className="font-medium text-white">{strategy.name}</p>
                        <p className="text-sm text-gray-400">{strategy.enabled ? 'Running' : 'Disabled'}</p>
                      </div>
                    </div>
                    <button className="px-3 py-1.5 text-sm bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700">
                      {strategy.enabled ? 'Disable' : 'Enable'}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </MainLayout>
  );
}
