'use client';

import { useState } from 'react';
import { cn, formatRelativeTime } from '@/lib/utils';
import {
  Server,
  Database,
  Brain,
  Zap,
  Activity,
  RefreshCw,
  ChevronRight,
  CheckCircle,
  AlertTriangle,
  XCircle,
  HelpCircle,
} from 'lucide-react';

export type ServiceStatus = 'running' | 'degraded' | 'down' | 'unknown';

export interface ServiceInfo {
  id: string;
  name: string;
  status: ServiceStatus;
  lastHeartbeat: Date;
  latency?: number;
  version?: string;
  uptime?: number;
  cpu?: number;
  memory?: number;
  errors?: number;
  details?: Record<string, unknown>;
}

interface ServiceStatusGridProps {
  services: ServiceInfo[];
  isLoading?: boolean;
  onServiceClick?: (serviceId: string) => void;
  onRefresh?: () => void;
}

const statusConfig: Record<ServiceStatus, { color: string; bgColor: string; icon: typeof CheckCircle; label: string }> = {
  running: { color: 'text-green-500', bgColor: 'bg-green-500', icon: CheckCircle, label: 'Running' },
  degraded: { color: 'text-yellow-500', bgColor: 'bg-yellow-500', icon: AlertTriangle, label: 'Degraded' },
  down: { color: 'text-red-500', bgColor: 'bg-red-500', icon: XCircle, label: 'Down' },
  unknown: { color: 'text-gray-500', bgColor: 'bg-gray-500', icon: HelpCircle, label: 'Unknown' },
};

const serviceIcons: Record<string, typeof Server> = {
  orchestrator: Server,
  'ai-orchestrator': Brain,
  'polymarket-arb': Zap,
  'polymarket-mm': Activity,
  'polymarket-spike': Zap,
  'kalshi-ai': Brain,
  'manifold-mm': Activity,
  'mcp-server': Server,
  polyseer: Activity,
  postgresql: Database,
  redis: Database,
  ollama: Brain,
};

export function ServiceStatusGrid({
  services,
  isLoading,
  onServiceClick,
  onRefresh,
}: ServiceStatusGridProps) {
  const [hoveredService, setHoveredService] = useState<string | null>(null);

  const healthySevices = services.filter((s) => s.status === 'running').length;
  const degradedServices = services.filter((s) => s.status === 'degraded').length;
  const downServices = services.filter((s) => s.status === 'down').length;

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/4 mb-4" />
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-700 rounded" />
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
        <div>
          <h3 className="text-lg font-semibold text-white">Service Status</h3>
          <div className="flex items-center gap-4 mt-1">
            <span className="flex items-center gap-1 text-sm text-green-500">
              <CheckCircle className="w-4 h-4" />
              {healthySevices} healthy
            </span>
            {degradedServices > 0 && (
              <span className="flex items-center gap-1 text-sm text-yellow-500">
                <AlertTriangle className="w-4 h-4" />
                {degradedServices} degraded
              </span>
            )}
            {downServices > 0 && (
              <span className="flex items-center gap-1 text-sm text-red-500">
                <XCircle className="w-4 h-4" />
                {downServices} down
              </span>
            )}
          </div>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="flex items-center gap-2 px-3 py-1.5 text-sm bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 hover:text-white transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        )}
      </div>

      {/* Service Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {services.map((service) => {
          const config = statusConfig[service.status];
          const Icon = serviceIcons[service.id] || Server;
          const StatusIcon = config.icon;
          const isHovered = hoveredService === service.id;

          return (
            <button
              key={service.id}
              onClick={() => onServiceClick?.(service.id)}
              onMouseEnter={() => setHoveredService(service.id)}
              onMouseLeave={() => setHoveredService(null)}
              className={cn(
                'relative p-4 rounded-lg border text-left transition-all',
                service.status === 'down'
                  ? 'border-red-500/50 bg-red-500/5'
                  : service.status === 'degraded'
                  ? 'border-yellow-500/50 bg-yellow-500/5'
                  : 'border-gray-800 bg-gray-800/50',
                'hover:border-gray-600 hover:bg-gray-800'
              )}
            >
              {/* Status indicator */}
              <div className={cn(
                'absolute top-3 right-3 w-2 h-2 rounded-full',
                config.bgColor,
                service.status === 'running' && 'animate-pulse'
              )} />

              {/* Icon and Name */}
              <div className="flex items-center gap-3 mb-3">
                <div className={cn(
                  'p-2 rounded-lg',
                  service.status === 'running' ? 'bg-gray-700' : 'bg-gray-800'
                )}>
                  <Icon className={cn('w-5 h-5', config.color)} />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-white font-medium text-sm truncate">{service.name}</h4>
                  <p className={cn('text-xs', config.color)}>{config.label}</p>
                </div>
              </div>

              {/* Stats */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-500">Last heartbeat</span>
                  <span className="text-gray-400">{formatRelativeTime(service.lastHeartbeat)}</span>
                </div>
                {service.latency !== undefined && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Latency</span>
                    <span className={cn(
                      service.latency > 500 ? 'text-yellow-500' : 'text-gray-400'
                    )}>
                      {service.latency}ms
                    </span>
                  </div>
                )}
                {service.cpu !== undefined && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">CPU</span>
                    <span className={cn(
                      service.cpu > 80 ? 'text-red-500' : service.cpu > 60 ? 'text-yellow-500' : 'text-gray-400'
                    )}>
                      {service.cpu.toFixed(1)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Hover indicator */}
              {isHovered && onServiceClick && (
                <div className="absolute bottom-3 right-3">
                  <ChevronRight className="w-4 h-4 text-gray-500" />
                </div>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default ServiceStatusGrid;
