'use client';

import { cn, formatCurrency, formatRelativeTime, getStatusColor } from '@/lib/utils';
import { Bot, Brain, Clock, Cpu, DollarSign } from 'lucide-react';
import type { AIStatus } from '@/types';

interface AIStatusCardProps {
  status: AIStatus;
}

export function AIStatusCard({ status }: AIStatusCardProps) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-purple-500/10">
            <Bot className="w-5 h-5 text-purple-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">AI Status</h3>
            <p className="text-sm text-gray-400">
              {status.isRunning ? 'AI System Active' : 'AI System Idle'}
            </p>
          </div>
        </div>
        <div
          className={cn(
            'px-3 py-1 rounded-full text-xs font-medium',
            status.isRunning
              ? 'bg-green-500/20 text-green-500'
              : 'bg-gray-500/20 text-gray-500'
          )}
        >
          {status.isRunning ? 'Running' : 'Idle'}
        </div>
      </div>

      {/* Current Activity */}
      {status.currentAgent && (
        <div className="mb-4 p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
          <div className="flex items-center gap-2 mb-1">
            <Brain className="w-4 h-4 text-purple-500" />
            <span className="text-sm font-medium text-purple-400">
              Active Agent
            </span>
          </div>
          <p className="text-white font-medium">{status.currentAgent}</p>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 rounded-lg bg-gray-800/50">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-500">Last Cycle</span>
          </div>
          <p className="text-lg font-semibold text-white">
            {status.lastCycleTime ? `${status.lastCycleTime}ms` : 'N/A'}
          </p>
        </div>
        <div className="p-3 rounded-lg bg-gray-800/50">
          <div className="flex items-center gap-2 mb-1">
            <Cpu className="w-4 h-4 text-gray-500" />
            <span className="text-xs text-gray-500">Forecasts</span>
          </div>
          <p className="text-lg font-semibold text-white">
            {status.forecastCount}
          </p>
        </div>
      </div>

      {/* LLM Usage */}
      <div className="pt-4 border-t border-gray-800">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">
          LLM Usage Today
        </p>
        <div className="grid grid-cols-3 gap-3">
          <div>
            <p className="text-xs text-gray-500">Tokens</p>
            <p className="text-sm font-medium text-white">
              {status.llmUsage.tokensUsed.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Requests</p>
            <p className="text-sm font-medium text-white">
              {status.llmUsage.requestsToday}
            </p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Cost</p>
            <p className="text-sm font-medium text-white">
              {formatCurrency(status.llmUsage.costToday)}
            </p>
          </div>
        </div>
      </div>

      {/* Agent Status List */}
      {status.agents && status.agents.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-800">
          <p className="text-xs text-gray-500 uppercase tracking-wider mb-3">
            Agents
          </p>
          <div className="space-y-2">
            {status.agents.map((agent) => (
              <div
                key={agent.name}
                className="flex items-center justify-between p-2 rounded-lg bg-gray-800/30"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={cn(
                      'w-2 h-2 rounded-full',
                      agent.status === 'running'
                        ? 'bg-green-500 animate-pulse'
                        : agent.status === 'error'
                        ? 'bg-red-500'
                        : 'bg-gray-500'
                    )}
                  />
                  <span className="text-sm text-white">{agent.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500">
                    {(agent.successRate * 100).toFixed(0)}% success
                  </span>
                  {agent.lastRun && (
                    <span className="text-xs text-gray-600">
                      {formatRelativeTime(agent.lastRun)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default AIStatusCard;
