'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { ServiceStatusGrid, SystemResources, ServiceInfo } from '@/components/health';
import { Activity, RefreshCw, Power } from 'lucide-react';
import { cn } from '@/lib/utils';

async function fetchHealthData() {
  const response = await fetch('/api/health/detailed');
  if (!response.ok) throw new Error('Failed to fetch health data');
  const data = await response.json();
  return data.data;
}

async function restartService(serviceId: string) {
  const response = await fetch('/api/health/detailed?action=restart', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ serviceId }),
  });
  if (!response.ok) throw new Error('Failed to restart service');
  return response.json();
}

export default function HealthPage() {
  const queryClient = useQueryClient();
  const [selectedService, setSelectedService] = useState<string | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['health', 'detailed'],
    queryFn: fetchHealthData,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const restartMutation = useMutation({
    mutationFn: restartService,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['health'] });
      setSelectedService(null);
    },
  });

  const handleServiceClick = (serviceId: string) => {
    setSelectedService(serviceId);
  };

  const handleRestart = async () => {
    if (selectedService) {
      await restartMutation.mutateAsync(selectedService);
    }
  };

  const selectedServiceData = selectedService
    ? data?.services?.find((s: ServiceInfo) => s.id === selectedService)
    : null;

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-green-500/10">
              <Activity className="w-6 h-6 text-green-500" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">System Health</h1>
              <p className="text-gray-400">Monitor service status and system resources</p>
            </div>
          </div>

          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 hover:text-white transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh All
          </button>
        </div>

        {/* Summary Cards */}
        {data?.summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="rounded-lg border border-gray-800 bg-gray-900/50 p-4">
              <p className="text-sm text-gray-400">Total Services</p>
              <p className="text-2xl font-bold text-white">{data.summary.total}</p>
            </div>
            <div className="rounded-lg border border-green-500/30 bg-green-500/5 p-4">
              <p className="text-sm text-gray-400">Running</p>
              <p className="text-2xl font-bold text-green-500">{data.summary.running}</p>
            </div>
            <div className="rounded-lg border border-yellow-500/30 bg-yellow-500/5 p-4">
              <p className="text-sm text-gray-400">Degraded</p>
              <p className="text-2xl font-bold text-yellow-500">{data.summary.degraded}</p>
            </div>
            <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4">
              <p className="text-sm text-gray-400">Down</p>
              <p className="text-2xl font-bold text-red-500">{data.summary.down}</p>
            </div>
          </div>
        )}

        {/* Service Status Grid */}
        <ServiceStatusGrid
          services={(data?.services || []).map((s: ServiceInfo) => ({
            ...s,
            lastHeartbeat: new Date(s.lastHeartbeat),
          }))}
          isLoading={isLoading}
          onServiceClick={handleServiceClick}
          onRefresh={() => refetch()}
        />

        {/* System Resources */}
        <SystemResources
          data={data?.resources?.history || []}
          currentCpu={data?.resources?.current?.cpu || 0}
          currentMemory={data?.resources?.current?.memory || 0}
          currentDisk={data?.resources?.current?.disk || 0}
          networkIn={data?.resources?.current?.networkIn || 0}
          networkOut={data?.resources?.current?.networkOut || 0}
          isLoading={isLoading}
        />

        {/* Service Details Modal */}
        {selectedService && selectedServiceData && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 max-w-lg w-full mx-4">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white">{selectedServiceData.name}</h3>
                <button
                  onClick={() => setSelectedService(null)}
                  className="text-gray-400 hover:text-white"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-400">Status</p>
                    <p className={cn(
                      'text-lg font-medium capitalize',
                      selectedServiceData.status === 'running' ? 'text-green-500' :
                      selectedServiceData.status === 'degraded' ? 'text-yellow-500' :
                      selectedServiceData.status === 'down' ? 'text-red-500' : 'text-gray-500'
                    )}>
                      {selectedServiceData.status}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Version</p>
                    <p className="text-lg font-medium text-white">{selectedServiceData.version || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">CPU Usage</p>
                    <p className="text-lg font-medium text-white">{selectedServiceData.cpu?.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Memory Usage</p>
                    <p className="text-lg font-medium text-white">{selectedServiceData.memory?.toFixed(1)}%</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Latency</p>
                    <p className="text-lg font-medium text-white">{selectedServiceData.latency}ms</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-400">Errors (24h)</p>
                    <p className={cn(
                      'text-lg font-medium',
                      selectedServiceData.errors > 10 ? 'text-red-500' : 'text-white'
                    )}>
                      {selectedServiceData.errors}
                    </p>
                  </div>
                </div>

                {selectedServiceData.details && (
                  <div className="mt-4 p-3 bg-gray-800 rounded-lg">
                    <p className="text-sm text-gray-400 mb-2">Details</p>
                    <pre className="text-xs text-gray-300 overflow-x-auto">
                      {JSON.stringify(selectedServiceData.details, null, 2)}
                    </pre>
                  </div>
                )}

                <div className="flex gap-3 mt-6">
                  <button
                    onClick={handleRestart}
                    disabled={restartMutation.isPending}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                      'bg-red-500/10 text-red-500 hover:bg-red-500/20',
                      restartMutation.isPending && 'opacity-50 cursor-not-allowed'
                    )}
                  >
                    <Power className="w-4 h-4" />
                    {restartMutation.isPending ? 'Restarting...' : 'Restart Service'}
                  </button>
                  <button
                    onClick={() => setSelectedService(null)}
                    className="px-4 py-2 text-sm font-medium bg-gray-800 text-gray-400 rounded-lg hover:bg-gray-700 hover:text-white transition-colors"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
