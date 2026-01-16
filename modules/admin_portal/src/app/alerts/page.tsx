'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import {
  ActiveAlerts,
  AlertHistory,
  AlertRulesConfig,
  NotificationChannels,
  Alert,
  AlertRule,
  NotificationChannel,
} from '@/components/alerts';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Bell, History, Settings, Send } from 'lucide-react';

async function fetchAlerts(type: string, params: Record<string, string | number> = {}) {
  const searchParams = new URLSearchParams(
    Object.entries({ type, ...params }).map(([k, v]) => [k, String(v)])
  );
  const response = await fetch(`/api/alerts?${searchParams}`);
  if (!response.ok) throw new Error('Failed to fetch alerts data');
  const data = await response.json();
  return data.data;
}

async function acknowledgeAlert(alertId: string) {
  const response = await fetch('/api/alerts?action=acknowledge', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ alertId }),
  });
  if (!response.ok) throw new Error('Failed to acknowledge alert');
  return response.json();
}

async function updateAlertRules(rules: AlertRule[]) {
  const response = await fetch('/api/alerts?type=rules', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rules),
  });
  if (!response.ok) throw new Error('Failed to update rules');
  return response.json();
}

async function updateNotificationChannels(channels: NotificationChannel[]) {
  const response = await fetch('/api/alerts?type=channels', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(channels),
  });
  if (!response.ok) throw new Error('Failed to update channels');
  return response.json();
}

async function testNotificationChannel(channelId: string) {
  const response = await fetch('/api/alerts?action=test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ channelId }),
  });
  if (!response.ok) throw new Error('Failed to test channel');
  return response.json();
}

async function testAlertRule(ruleId: string) {
  const response = await fetch('/api/alerts?action=test-rule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ruleId }),
  });
  if (!response.ok) throw new Error('Failed to test rule');
  return response.json();
}

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [historyPage, setHistoryPage] = useState(1);

  // Fetch active alerts
  const { data: alertsData, isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts', 'list'],
    queryFn: () => fetchAlerts('list'),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch alert history
  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['alerts', 'history', historyPage],
    queryFn: () => fetchAlerts('list', { page: historyPage, limit: 20 }),
  });

  // Fetch alert rules
  const { data: rulesData, isLoading: rulesLoading } = useQuery({
    queryKey: ['alerts', 'rules'],
    queryFn: () => fetchAlerts('rules'),
  });

  // Fetch notification channels
  const { data: channelsData, isLoading: channelsLoading } = useQuery({
    queryKey: ['alerts', 'channels'],
    queryFn: () => fetchAlerts('channels'),
  });

  // Mutations
  const acknowledgeMutation = useMutation({
    mutationFn: acknowledgeAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  const updateRulesMutation = useMutation({
    mutationFn: updateAlertRules,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'rules'] });
    },
  });

  const updateChannelsMutation = useMutation({
    mutationFn: updateNotificationChannels,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts', 'channels'] });
    },
  });

  const handleAcknowledge = async (alertId: string) => {
    await acknowledgeMutation.mutateAsync(alertId);
  };

  const handleSaveRules = async (rules: AlertRule[]) => {
    await updateRulesMutation.mutateAsync(rules);
  };

  const handleTestRule = async (ruleId: string) => {
    const result = await testAlertRule(ruleId);
    return { success: result.success, message: result.message };
  };

  const handleSaveChannels = async (channels: NotificationChannel[]) => {
    await updateChannelsMutation.mutateAsync(channels);
  };

  const handleTestChannel = async (channelId: string) => {
    const result = await testNotificationChannel(channelId);
    return { success: result.success, message: result.message };
  };

  const activeAlerts = (alertsData?.alerts || []).filter((a: Alert) => !a.acknowledged);

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold text-white">Alerts</h1>
          <p className="text-gray-400">Monitor and manage system alerts and notifications</p>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="active" className="space-y-6">
          <TabsList className="bg-gray-800 border border-gray-700">
            <TabsTrigger value="active" className="data-[state=active]:bg-primary">
              <Bell className="w-4 h-4 mr-2" />
              Active ({activeAlerts.length})
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:bg-primary">
              <History className="w-4 h-4 mr-2" />
              History
            </TabsTrigger>
            <TabsTrigger value="rules" className="data-[state=active]:bg-primary">
              <Settings className="w-4 h-4 mr-2" />
              Rules
            </TabsTrigger>
            <TabsTrigger value="channels" className="data-[state=active]:bg-primary">
              <Send className="w-4 h-4 mr-2" />
              Channels
            </TabsTrigger>
          </TabsList>

          {/* Active Alerts Tab */}
          <TabsContent value="active">
            <ActiveAlerts
              alerts={alertsData?.alerts || []}
              isLoading={alertsLoading}
              onAcknowledge={handleAcknowledge}
            />
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <AlertHistory
              alerts={historyData?.alerts || []}
              totalCount={historyData?.total || 0}
              page={historyPage}
              pageSize={20}
              isLoading={historyLoading}
              onPageChange={setHistoryPage}
            />
          </TabsContent>

          {/* Rules Tab */}
          <TabsContent value="rules">
            <AlertRulesConfig
              rules={rulesData || []}
              isLoading={rulesLoading}
              isSaving={updateRulesMutation.isPending}
              onSave={handleSaveRules}
              onTestRule={handleTestRule}
            />
          </TabsContent>

          {/* Channels Tab */}
          <TabsContent value="channels">
            <NotificationChannels
              channels={channelsData || []}
              isLoading={channelsLoading}
              isSaving={updateChannelsMutation.isPending}
              onSave={handleSaveChannels}
              onTestChannel={handleTestChannel}
            />
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  );
}
