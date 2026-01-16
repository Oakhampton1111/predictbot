'use client';

import { useState } from 'react';
import { cn, formatDate } from '@/lib/utils';
import {
  History,
  Filter,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  AlertCircle,
  Info,
  Bell,
  X,
} from 'lucide-react';
import type { Alert, AlertSeverity, AlertType } from './ActiveAlerts';

interface AlertHistoryProps {
  alerts: Alert[];
  totalCount: number;
  page: number;
  pageSize: number;
  isLoading?: boolean;
  onPageChange: (page: number) => void;
  onFiltersChange?: (filters: AlertHistoryFilters) => void;
}

interface AlertHistoryFilters {
  dateFrom?: string;
  dateTo?: string;
  severity?: AlertSeverity | 'all';
  type?: AlertType | 'all';
  status?: 'acknowledged' | 'unacknowledged' | 'all';
}

const severityConfig: Record<AlertSeverity, { color: string; bgColor: string; icon: typeof AlertTriangle }> = {
  critical: { color: 'text-red-500', bgColor: 'bg-red-500/10', icon: AlertCircle },
  high: { color: 'text-orange-500', bgColor: 'bg-orange-500/10', icon: AlertTriangle },
  medium: { color: 'text-yellow-500', bgColor: 'bg-yellow-500/10', icon: Bell },
  low: { color: 'text-blue-500', bgColor: 'bg-blue-500/10', icon: Info },
};

const typeLabels: Record<AlertType, string> = {
  loss_limit: 'Loss Limit',
  large_trade: 'Large Trade',
  ai_confidence: 'AI Confidence',
  error_rate: 'Error Rate',
  system: 'System',
  price_movement: 'Price Movement',
};

export function AlertHistory({
  alerts,
  totalCount,
  page,
  pageSize,
  isLoading,
  onPageChange,
  onFiltersChange,
}: AlertHistoryProps) {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<AlertHistoryFilters>({
    severity: 'all',
    type: 'all',
    status: 'all',
  });

  const totalPages = Math.ceil(totalCount / pageSize);

  const handleFilterChange = (key: keyof AlertHistoryFilters, value: string) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  const clearFilters = () => {
    const clearedFilters: AlertHistoryFilters = { severity: 'all', type: 'all', status: 'all' };
    setFilters(clearedFilters);
    onFiltersChange?.(clearedFilters);
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/4 mb-4" />
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-700 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gray-700">
            <History className="w-5 h-5 text-gray-400" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Alert History</h3>
            <p className="text-sm text-gray-400">{totalCount} total alerts</p>
          </div>
        </div>

        <button
          onClick={() => setShowFilters(!showFilters)}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg transition-colors',
            showFilters
              ? 'bg-primary text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
          )}
        >
          <Filter className="w-4 h-4" />
          Filters
        </button>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="mb-6 p-4 bg-gray-800 rounded-lg">
          <div className="flex flex-wrap gap-4">
            {/* Date Range */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">From</label>
              <input
                type="date"
                value={filters.dateFrom || ''}
                onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-white focus:outline-none focus:border-primary"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">To</label>
              <input
                type="date"
                value={filters.dateTo || ''}
                onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-white focus:outline-none focus:border-primary"
              />
            </div>

            {/* Severity */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">Severity</label>
              <select
                value={filters.severity || 'all'}
                onChange={(e) => handleFilterChange('severity', e.target.value)}
                className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-white focus:outline-none focus:border-primary"
              >
                <option value="all">All Severities</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>

            {/* Type */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">Type</label>
              <select
                value={filters.type || 'all'}
                onChange={(e) => handleFilterChange('type', e.target.value)}
                className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-white focus:outline-none focus:border-primary"
              >
                <option value="all">All Types</option>
                <option value="loss_limit">Loss Limit</option>
                <option value="large_trade">Large Trade</option>
                <option value="ai_confidence">AI Confidence</option>
                <option value="error_rate">Error Rate</option>
                <option value="system">System</option>
                <option value="price_movement">Price Movement</option>
              </select>
            </div>

            {/* Status */}
            <div>
              <label className="block text-xs text-gray-400 mb-1">Status</label>
              <select
                value={filters.status || 'all'}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-white focus:outline-none focus:border-primary"
              >
                <option value="all">All</option>
                <option value="acknowledged">Acknowledged</option>
                <option value="unacknowledged">Unacknowledged</option>
              </select>
            </div>

            {/* Clear Filters */}
            <div className="flex items-end">
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
                Clear
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Severity</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Type</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Alert</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Time</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Status</th>
              <th className="text-left py-3 px-4 text-gray-400 font-medium text-sm">Acknowledged By</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length > 0 ? (
              alerts.map((alert) => {
                const config = severityConfig[alert.severity];
                const Icon = config.icon;

                return (
                  <tr key={alert.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <div className={cn('p-1.5 rounded', config.bgColor)}>
                          <Icon className={cn('w-3 h-3', config.color)} />
                        </div>
                        <span className={cn('text-sm font-medium capitalize', config.color)}>
                          {alert.severity}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gray-300 text-sm">
                      {typeLabels[alert.type]}
                    </td>
                    <td className="py-3 px-4">
                      <div className="max-w-[300px]">
                        <p className="text-white text-sm font-medium truncate">{alert.title}</p>
                        <p className="text-gray-500 text-xs truncate">{alert.message}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-gray-300 text-sm">
                      {formatDate(alert.timestamp)}
                    </td>
                    <td className="py-3 px-4">
                      <span className={cn(
                        'px-2 py-1 text-xs font-medium rounded',
                        alert.acknowledged
                          ? 'bg-green-500/10 text-green-500'
                          : 'bg-yellow-500/10 text-yellow-500'
                      )}>
                        {alert.acknowledged ? 'Acknowledged' : 'Pending'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-gray-400 text-sm">
                      {alert.acknowledgedBy || '-'}
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={6} className="py-12 text-center text-gray-500">
                  No alerts found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-800">
          <p className="text-sm text-gray-400">
            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, totalCount)} of {totalCount}
          </p>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page === 1}
              className={cn(
                'p-2 rounded-lg transition-colors',
                page === 1
                  ? 'text-gray-600 cursor-not-allowed'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              )}
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            
            <span className="text-sm text-gray-400">
              Page {page} of {totalPages}
            </span>
            
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page === totalPages}
              className={cn(
                'p-2 rounded-lg transition-colors',
                page === totalPages
                  ? 'text-gray-600 cursor-not-allowed'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              )}
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default AlertHistory;
