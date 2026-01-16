'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MainLayout } from '@/components/layout/MainLayout';
import { ConfigForm } from '@/components/config/ConfigForm';
import { ApiKeysSection } from '@/components/config/ApiKeysSection';
import { orchestratorApi } from '@/lib/api';
import { Settings, Shield, Zap, Bot, Bell, Key } from 'lucide-react';
import type { AppConfig, ApiKeyStatus } from '@/types';

// Mock data for development
const mockConfig: AppConfig = {
  risk: {
    maxPositionSize: 5000,
    maxTotalExposure: 50000,
    maxDailyLoss: 2000,
    stopLossPercent: 10,
    takeProfitPercent: 25,
  },
  strategies: {
    arbitrage: {
      enabled: true,
      minSpread: 0.02,
      maxPositionSize: 1000,
    },
    marketMaking: {
      enabled: true,
      spreadTarget: 0.03,
      inventoryLimit: 5000,
    },
    spikeDetection: {
      enabled: false,
      volumeThreshold: 2.0,
      priceChangeThreshold: 0.15,
    },
    aiForecasting: {
      enabled: true,
      confidenceThreshold: 0.7,
      maxPositionsPerForecast: 3,
    },
  },
  llm: {
    provider: 'openai',
    model: 'gpt-4-turbo-preview',
    maxTokens: 4096,
    temperature: 0.7,
    dailyBudget: 50,
  },
  notifications: {
    email: {
      enabled: true,
      recipients: ['admin@example.com'],
    },
    slack: {
      enabled: false,
      webhookUrl: '',
    },
    telegram: {
      enabled: false,
      chatId: '',
    },
  },
};

const mockApiKeys: ApiKeyStatus[] = [
  { platform: 'polymarket', isConfigured: true, isValid: true, lastValidated: new Date() },
  { platform: 'kalshi', isConfigured: true, isValid: true, lastValidated: new Date() },
  { platform: 'manifold', isConfigured: false, isValid: false },
  { platform: 'openai', isConfigured: true, isValid: true, lastValidated: new Date() },
  { platform: 'anthropic', isConfigured: false, isValid: false },
];

type ConfigSection = 'risk' | 'strategies' | 'llm' | 'notifications' | 'apikeys';

const tabs: { id: ConfigSection; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'risk', label: 'Risk Management', icon: Shield },
  { id: 'strategies', label: 'Strategies', icon: Zap },
  { id: 'llm', label: 'LLM Settings', icon: Bot },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'apikeys', label: 'API Keys', icon: Key },
];

export default function ConfigPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<ConfigSection>('risk');

  // Fetch configuration
  const { data: config = mockConfig, isLoading } = useQuery({
    queryKey: ['config'],
    queryFn: async () => {
      // In production, call real API
      // const result = await orchestratorApi.getConfig();
      // return result.data;
      return mockConfig;
    },
  });

  // Fetch API keys
  const { data: apiKeys = mockApiKeys } = useQuery({
    queryKey: ['apiKeys'],
    queryFn: async () => {
      // In production, call real API
      return mockApiKeys;
    },
  });

  // Save configuration mutation
  const saveMutation = useMutation({
    mutationFn: async (data: { section: string; config: unknown }) => {
      await orchestratorApi.updateConfig({ [data.section]: data.config });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
    },
  });

  const handleSaveConfig = async (section: string, data: unknown) => {
    await saveMutation.mutateAsync({ section, config: data });
  };

  const handleTestConnection = async (platform: string): Promise<boolean> => {
    // In production, call real API to test connection
    await new Promise((resolve) => setTimeout(resolve, 1000));
    return true;
  };

  const handleUpdateApiKey = async (platform: string, key: string) => {
    // In production, call real API to update key
    await new Promise((resolve) => setTimeout(resolve, 500));
    queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
  };

  const getConfigData = () => {
    switch (activeTab) {
      case 'risk':
        return config.risk;
      case 'strategies':
        return config.strategies;
      case 'llm':
        return config.llm;
      case 'notifications':
        return config.notifications;
      default:
        return {};
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold text-white">Configuration</h1>
          <p className="text-gray-400">
            Manage your trading bot settings and preferences
          </p>
        </div>

        {/* Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-gray-800 pb-4">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-white'
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
            </div>
          ) : activeTab === 'apikeys' ? (
            <ApiKeysSection
              apiKeys={apiKeys}
              onTestConnection={handleTestConnection}
              onUpdateKey={handleUpdateApiKey}
            />
          ) : (
            <ConfigForm
              section={activeTab}
              initialData={getConfigData()}
              onSave={(data) => handleSaveConfig(activeTab, data)}
              onReset={() => queryClient.invalidateQueries({ queryKey: ['config'] })}
            />
          )}
        </div>

        {/* Info Box */}
        <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/30">
          <div className="flex items-start gap-3">
            <Settings className="w-5 h-5 text-blue-500 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-blue-400">
                Configuration Changes
              </h4>
              <p className="text-sm text-gray-400 mt-1">
                Changes to configuration are applied immediately. Some settings may
                require a strategy restart to take effect. All changes are logged
                for audit purposes.
              </p>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
