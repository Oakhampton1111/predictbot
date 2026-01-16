'use client';

import { useState } from 'react';
import { cn, formatRelativeTime } from '@/lib/utils';
import {
  AlertTriangle,
  AlertCircle,
  Info,
  Bell,
  Check,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low';
export type AlertType = 'loss_limit' | 'large_trade' | 'ai_confidence' | 'error_rate' | 'system' | 'price_movement';

export interface Alert {
  id: string;
  type: AlertType;
  severity: AlertSeverity;
  title: string;
  message: string;
  timestamp: Date;
  acknowledged: boolean;
  acknowledgedBy?: string;
  acknowledgedAt?: Date;
  metadata?: Record<string, unknown>;
}

interface ActiveAlertsProps {
  alerts: Alert[];
  isLoading?: boolean;
  onAcknowledge: (alertId: string) => Promise<void>;
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

export function ActiveAlerts({ alerts, isLoading, onAcknowledge }: ActiveAlertsProps) {
  const [expandedAlerts, setExpandedAlerts] = useState<Set<string>>(new Set());
  const [acknowledging, setAcknowledging] = useState<string | null>(null);

  const toggleExpanded = (alertId: string) => {
    setExpandedAlerts((prev) => {
      const next = new Set(prev);
      if (next.has(alertId)) {
        next.delete(alertId);
      } else {
        next.add(alertId);
      }
      return next;
    });
  };

  const handleAcknowledge = async (alertId: string) => {
    setAcknowledging(alertId);
    try {
      await onAcknowledge(alertId);
    } finally {
      setAcknowledging(null);
    }
  };

  const unacknowledgedAlerts = alerts.filter((a) => !a.acknowledged);

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/4 mb-4" />
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-700 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-red-500/10">
            <AlertTriangle className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Active Alerts</h3>
            <p className="text-sm text-gray-400">
              {unacknowledgedAlerts.length} unacknowledged alert{unacknowledgedAlerts.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>

      {unacknowledgedAlerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <div className="p-3 rounded-full bg-green-500/10 mb-4">
            <Check className="w-8 h-8 text-green-500" />
          </div>
          <p className="text-white font-medium">All Clear</p>
          <p className="text-gray-400 text-sm">No active alerts at this time</p>
        </div>
      ) : (
        <div className="space-y-3">
          {unacknowledgedAlerts.map((alert) => {
            const config = severityConfig[alert.severity];
            const Icon = config.icon;
            const isExpanded = expandedAlerts.has(alert.id);

            return (
              <div
                key={alert.id}
                className={cn(
                  'rounded-lg border transition-colors',
                  alert.severity === 'critical'
                    ? 'border-red-500/50 bg-red-500/5'
                    : 'border-gray-800 bg-gray-800/50'
                )}
              >
                <div className="p-4">
                  <div className="flex items-start gap-3">
                    <div className={cn('p-2 rounded-lg', config.bgColor)}>
                      <Icon className={cn('w-4 h-4', config.color)} />
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={cn(
                          'px-2 py-0.5 text-xs font-medium rounded uppercase',
                          config.bgColor,
                          config.color
                        )}>
                          {alert.severity}
                        </span>
                        <span className="text-xs text-gray-500">
                          {typeLabels[alert.type]}
                        </span>
                      </div>
                      
                      <h4 className="text-white font-medium">{alert.title}</h4>
                      <p className="text-gray-400 text-sm mt-1">{alert.message}</p>
                      <p className="text-gray-500 text-xs mt-2">
                        {formatRelativeTime(alert.timestamp)}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleAcknowledge(alert.id)}
                        disabled={acknowledging === alert.id}
                        className={cn(
                          'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
                          'bg-gray-700 text-white hover:bg-gray-600',
                          acknowledging === alert.id && 'opacity-50 cursor-not-allowed'
                        )}
                      >
                        {acknowledging === alert.id ? 'Acknowledging...' : 'Acknowledge'}
                      </button>
                      
                      {alert.metadata && Object.keys(alert.metadata).length > 0 && (
                        <button
                          onClick={() => toggleExpanded(alert.id)}
                          className="p-1.5 text-gray-400 hover:text-white transition-colors"
                        >
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4" />
                          ) : (
                            <ChevronDown className="w-4 h-4" />
                          )}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Expanded Details */}
                  {isExpanded && alert.metadata && (
                    <div className="mt-4 pt-4 border-t border-gray-700">
                      <h5 className="text-sm font-medium text-gray-400 mb-2">Details</h5>
                      <div className="bg-gray-900 rounded-lg p-3 overflow-x-auto">
                        <pre className="text-xs text-gray-300">
                          {JSON.stringify(alert.metadata, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default ActiveAlerts;
