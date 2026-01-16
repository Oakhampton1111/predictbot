'use client';

import { useState } from 'react';
import { cn, formatRelativeTime, getStatusBgColor } from '@/lib/utils';
import { Activity, ChevronDown, ChevronUp, Server } from 'lucide-react';
import type { ServiceHealth, SystemHealth } from '@/types';

interface SystemHealthCardProps {
  health: SystemHealth;
}

export function SystemHealthCard({ health }: SystemHealthCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getOverallStatusColor = () => {
    switch (health.overall) {
      case 'healthy':
        return 'border-green-500/50 bg-green-500/5';
      case 'degraded':
        return 'border-yellow-500/50 bg-yellow-500/5';
      case 'down':
        return 'border-red-500/50 bg-red-500/5';
      default:
        return 'border-gray-500/50 bg-gray-500/5';
    }
  };

  const getOverallStatusText = () => {
    switch (health.overall) {
      case 'healthy':
        return 'All Systems Operational';
      case 'degraded':
        return 'Some Services Degraded';
      case 'down':
        return 'Critical Services Down';
      default:
        return 'Status Unknown';
    }
  };

  return (
    <div
      className={cn(
        'rounded-xl border p-6 transition-all duration-200',
        getOverallStatusColor()
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gray-800">
            <Activity className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">System Health</h3>
            <p className="text-sm text-gray-400">{getOverallStatusText()}</p>
          </div>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-2 rounded-lg hover:bg-gray-800 transition-colors"
        >
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>
      </div>

      {/* Service Status Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {health.services.slice(0, isExpanded ? undefined : 6).map((service) => (
          <ServiceStatusItem key={service.name} service={service} />
        ))}
      </div>

      {/* Last Updated */}
      <div className="mt-4 pt-4 border-t border-gray-800">
        <p className="text-xs text-gray-500">
          Last updated: {formatRelativeTime(health.lastUpdated)}
        </p>
      </div>
    </div>
  );
}

interface ServiceStatusItemProps {
  service: ServiceHealth;
}

function ServiceStatusItem({ service }: ServiceStatusItemProps) {
  return (
    <div className="flex items-center gap-2 p-2 rounded-lg bg-gray-800/50">
      <div
        className={cn(
          'w-2 h-2 rounded-full',
          getStatusBgColor(service.status)
        )}
      />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{service.name}</p>
        {service.latency && (
          <p className="text-xs text-gray-500">{service.latency}ms</p>
        )}
      </div>
      <Server className="w-4 h-4 text-gray-600 flex-shrink-0" />
    </div>
  );
}

export default SystemHealthCard;
