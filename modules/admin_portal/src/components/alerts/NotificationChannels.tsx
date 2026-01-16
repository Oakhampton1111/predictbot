'use client';

import { useState } from 'react';
import { cn } from '@/lib/utils';
import {
  Bell,
  Mail,
  MessageSquare,
  Send,
  Save,
  TestTube,
  ToggleLeft,
  ToggleRight,
  Eye,
  EyeOff,
} from 'lucide-react';

export interface NotificationChannel {
  id: string;
  type: 'email' | 'slack' | 'discord';
  name: string;
  enabled: boolean;
  config: {
    // Email
    smtpHost?: string;
    smtpPort?: number;
    smtpUser?: string;
    smtpPassword?: string;
    recipients?: string[];
    // Slack/Discord
    webhookUrl?: string;
    channel?: string;
  };
}

interface NotificationChannelsProps {
  channels: NotificationChannel[];
  isLoading?: boolean;
  isSaving?: boolean;
  onSave: (channels: NotificationChannel[]) => Promise<void>;
  onTestChannel: (channelId: string) => Promise<{ success: boolean; message: string }>;
}

const channelIcons: Record<string, typeof Mail> = {
  email: Mail,
  slack: MessageSquare,
  discord: Send,
};

const channelColors: Record<string, string> = {
  email: 'bg-blue-500/10 text-blue-500',
  slack: 'bg-purple-500/10 text-purple-500',
  discord: 'bg-indigo-500/10 text-indigo-500',
};

export function NotificationChannels({
  channels: initialChannels,
  isLoading,
  isSaving,
  onSave,
  onTestChannel,
}: NotificationChannelsProps) {
  const [channels, setChannels] = useState<NotificationChannel[]>(initialChannels);
  const [testingChannel, setTestingChannel] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ channelId: string; success: boolean; message: string } | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [showPasswords, setShowPasswords] = useState<Set<string>>(new Set());

  const handleToggleChannel = (channelId: string) => {
    setChannels((prev) =>
      prev.map((channel) =>
        channel.id === channelId ? { ...channel, enabled: !channel.enabled } : channel
      )
    );
    setHasChanges(true);
  };

  const handleConfigChange = (channelId: string, key: string, value: string | number | string[]) => {
    setChannels((prev) =>
      prev.map((channel) =>
        channel.id === channelId
          ? { ...channel, config: { ...channel.config, [key]: value } }
          : channel
      )
    );
    setHasChanges(true);
  };

  const handleSave = async () => {
    await onSave(channels);
    setHasChanges(false);
  };

  const handleTestChannel = async (channelId: string) => {
    setTestingChannel(channelId);
    setTestResult(null);
    try {
      const result = await onTestChannel(channelId);
      setTestResult({ channelId, ...result });
    } finally {
      setTestingChannel(null);
    }
  };

  const togglePasswordVisibility = (channelId: string) => {
    setShowPasswords((prev) => {
      const next = new Set(prev);
      if (next.has(channelId)) {
        next.delete(channelId);
      } else {
        next.add(channelId);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/4 mb-4" />
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
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
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-green-500/10">
            <Bell className="w-5 h-5 text-green-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Notification Channels</h3>
            <p className="text-sm text-gray-400">Configure where alerts are sent</p>
          </div>
        </div>

        <button
          onClick={handleSave}
          disabled={!hasChanges || isSaving}
          className={cn(
            'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            hasChanges
              ? 'bg-primary text-white hover:bg-primary/90'
              : 'bg-gray-700 text-gray-400 cursor-not-allowed'
          )}
        >
          <Save className="w-4 h-4" />
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {/* Channels List */}
      <div className="space-y-4">
        {channels.map((channel) => {
          const Icon = channelIcons[channel.type] || Bell;
          const colorClass = channelColors[channel.type] || 'bg-gray-500/10 text-gray-500';
          const isTestingThis = testingChannel === channel.id;
          const testResultForThis = testResult?.channelId === channel.id ? testResult : null;

          return (
            <div
              key={channel.id}
              className={cn(
                'rounded-lg border p-4 transition-colors',
                channel.enabled
                  ? 'border-gray-700 bg-gray-800/50'
                  : 'border-gray-800 bg-gray-900/50 opacity-60'
              )}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={cn('p-2 rounded-lg', colorClass)}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-white font-medium">{channel.name}</h4>
                    <p className="text-gray-500 text-sm capitalize">{channel.type}</p>
                  </div>
                </div>

                <button
                  onClick={() => handleToggleChannel(channel.id)}
                  className="flex-shrink-0"
                >
                  {channel.enabled ? (
                    <ToggleRight className="w-8 h-8 text-green-500" />
                  ) : (
                    <ToggleLeft className="w-8 h-8 text-gray-500" />
                  )}
                </button>
              </div>

              {/* Configuration Fields */}
              <div className="space-y-3">
                {channel.type === 'email' && (
                  <>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">SMTP Host</label>
                        <input
                          type="text"
                          value={channel.config.smtpHost || ''}
                          onChange={(e) => handleConfigChange(channel.id, 'smtpHost', e.target.value)}
                          disabled={!channel.enabled}
                          placeholder="smtp.example.com"
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary disabled:opacity-50"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">SMTP Port</label>
                        <input
                          type="number"
                          value={channel.config.smtpPort || ''}
                          onChange={(e) => handleConfigChange(channel.id, 'smtpPort', parseInt(e.target.value))}
                          disabled={!channel.enabled}
                          placeholder="587"
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary disabled:opacity-50"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Username</label>
                        <input
                          type="text"
                          value={channel.config.smtpUser || ''}
                          onChange={(e) => handleConfigChange(channel.id, 'smtpUser', e.target.value)}
                          disabled={!channel.enabled}
                          placeholder="user@example.com"
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary disabled:opacity-50"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Password</label>
                        <div className="relative">
                          <input
                            type={showPasswords.has(channel.id) ? 'text' : 'password'}
                            value={channel.config.smtpPassword || ''}
                            onChange={(e) => handleConfigChange(channel.id, 'smtpPassword', e.target.value)}
                            disabled={!channel.enabled}
                            placeholder="••••••••"
                            className="w-full px-3 py-2 pr-10 bg-gray-700 border border-gray-600 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary disabled:opacity-50"
                          />
                          <button
                            type="button"
                            onClick={() => togglePasswordVisibility(channel.id)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                          >
                            {showPasswords.has(channel.id) ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Recipients (comma-separated)</label>
                      <input
                        type="text"
                        value={(channel.config.recipients || []).join(', ')}
                        onChange={(e) => handleConfigChange(channel.id, 'recipients', e.target.value.split(',').map((s) => s.trim()).filter(Boolean))}
                        disabled={!channel.enabled}
                        placeholder="admin@example.com, alerts@example.com"
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary disabled:opacity-50"
                      />
                    </div>
                  </>
                )}

                {(channel.type === 'slack' || channel.type === 'discord') && (
                  <>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Webhook URL</label>
                      <div className="relative">
                        <input
                          type={showPasswords.has(channel.id) ? 'text' : 'password'}
                          value={channel.config.webhookUrl || ''}
                          onChange={(e) => handleConfigChange(channel.id, 'webhookUrl', e.target.value)}
                          disabled={!channel.enabled}
                          placeholder={`https://hooks.${channel.type}.com/...`}
                          className="w-full px-3 py-2 pr-10 bg-gray-700 border border-gray-600 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary disabled:opacity-50"
                        />
                        <button
                          type="button"
                          onClick={() => togglePasswordVisibility(channel.id)}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                        >
                          {showPasswords.has(channel.id) ? (
                            <EyeOff className="w-4 h-4" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>
                    {channel.type === 'slack' && (
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Channel (optional)</label>
                        <input
                          type="text"
                          value={channel.config.channel || ''}
                          onChange={(e) => handleConfigChange(channel.id, 'channel', e.target.value)}
                          disabled={!channel.enabled}
                          placeholder="#alerts"
                          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary disabled:opacity-50"
                        />
                      </div>
                    )}
                  </>
                )}
              </div>

              {/* Test Button */}
              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={() => handleTestChannel(channel.id)}
                  disabled={!channel.enabled || isTestingThis}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded transition-colors',
                    channel.enabled
                      ? 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
                      : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                  )}
                >
                  <TestTube className="w-4 h-4" />
                  {isTestingThis ? 'Sending...' : 'Send Test'}
                </button>

                {testResultForThis && (
                  <span className={cn(
                    'text-sm',
                    testResultForThis.success ? 'text-green-500' : 'text-red-500'
                  )}>
                    {testResultForThis.message}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default NotificationChannels;
