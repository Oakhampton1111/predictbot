'use client';

import { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { cn } from '@/lib/utils';
import { Cpu, HardDrive, Wifi, MemoryStick } from 'lucide-react';

interface ResourceDataPoint {
  time: string;
  cpu: number;
  memory: number;
  disk: number;
  network: number;
}

interface SystemResourcesProps {
  data: ResourceDataPoint[];
  currentCpu: number;
  currentMemory: number;
  currentDisk: number;
  networkIn: number;
  networkOut: number;
  isLoading?: boolean;
}

interface ResourceGaugeProps {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  warning?: number;
  critical?: number;
}

function ResourceGauge({ label, value, icon, color, warning = 70, critical = 90 }: ResourceGaugeProps) {
  const status = value >= critical ? 'critical' : value >= warning ? 'warning' : 'normal';
  const statusColor = status === 'critical' ? 'text-red-500' : status === 'warning' ? 'text-yellow-500' : color;

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={cn('p-1.5 rounded', `bg-${color.replace('text-', '')}/10`)}>
            {icon}
          </div>
          <span className="text-sm text-gray-400">{label}</span>
        </div>
        <span className={cn('text-lg font-bold', statusColor)}>
          {value.toFixed(1)}%
        </span>
      </div>
      
      {/* Progress bar */}
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={cn(
            'h-full rounded-full transition-all duration-500',
            status === 'critical' ? 'bg-red-500' : status === 'warning' ? 'bg-yellow-500' : `bg-${color.replace('text-', '')}`
          )}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
    </div>
  );
}

export function SystemResources({
  data,
  currentCpu,
  currentMemory,
  currentDisk,
  networkIn,
  networkOut,
  isLoading,
}: SystemResourcesProps) {
  const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; dataKey: string; color: string }>; label?: string }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-gray-400 text-sm mb-2">{label}</p>
          {payload.map((entry, index) => (
            <div key={index} className="flex items-center gap-2 text-sm">
              <div
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-gray-300 capitalize">{entry.dataKey}:</span>
              <span className="text-white font-medium">{entry.value.toFixed(1)}%</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/4 mb-4" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-700 rounded" />
            ))}
          </div>
          <div className="h-48 bg-gray-700 rounded" />
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      <h3 className="text-lg font-semibold text-white mb-6">System Resources</h3>

      {/* Resource Gauges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <ResourceGauge
          label="CPU"
          value={currentCpu}
          icon={<Cpu className="w-4 h-4 text-blue-500" />}
          color="text-blue-500"
        />
        <ResourceGauge
          label="Memory"
          value={currentMemory}
          icon={<MemoryStick className="w-4 h-4 text-purple-500" />}
          color="text-purple-500"
        />
        <ResourceGauge
          label="Disk"
          value={currentDisk}
          icon={<HardDrive className="w-4 h-4 text-green-500" />}
          color="text-green-500"
          warning={80}
          critical={95}
        />
        <div className="rounded-lg border border-gray-800 bg-gray-800/50 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded bg-orange-500/10">
                <Wifi className="w-4 h-4 text-orange-500" />
              </div>
              <span className="text-sm text-gray-400">Network</span>
            </div>
          </div>
          <div className="flex items-center justify-between text-sm">
            <div>
              <span className="text-gray-500">↓ In:</span>
              <span className="text-green-500 ml-1">{(networkIn / 1024).toFixed(1)} KB/s</span>
            </div>
            <div>
              <span className="text-gray-500">↑ Out:</span>
              <span className="text-blue-500 ml-1">{(networkOut / 1024).toFixed(1)} KB/s</span>
            </div>
          </div>
        </div>
      </div>

      {/* Resource Chart */}
      <div className="h-48">
        {data.length > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="time"
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 10 }}
              />
              <YAxis
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 10 }}
                domain={[0, 100]}
                tickFormatter={(value) => `${value}%`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="cpu"
                stroke="#3B82F6"
                fill="#3B82F6"
                fillOpacity={0.2}
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="memory"
                stroke="#8B5CF6"
                fill="#8B5CF6"
                fillOpacity={0.2}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-500">
            No resource data available
          </div>
        )}
      </div>
    </div>
  );
}

export default SystemResources;
