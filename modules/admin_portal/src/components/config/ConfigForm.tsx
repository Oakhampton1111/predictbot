'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Save, RotateCcw, Eye } from 'lucide-react';
import type { RiskConfig, StrategyConfig, LLMConfig, NotificationConfig } from '@/types';

// Validation schemas
const riskConfigSchema = z.object({
  maxPositionSize: z.number().min(0).max(100000),
  maxTotalExposure: z.number().min(0).max(1000000),
  maxDailyLoss: z.number().min(0).max(100000),
  stopLossPercent: z.number().min(0).max(100),
  takeProfitPercent: z.number().min(0).max(1000),
});

const strategyConfigSchema = z.object({
  arbitrage: z.object({
    enabled: z.boolean(),
    minSpread: z.number().min(0).max(1),
    maxPositionSize: z.number().min(0),
  }),
  marketMaking: z.object({
    enabled: z.boolean(),
    spreadTarget: z.number().min(0).max(1),
    inventoryLimit: z.number().min(0),
  }),
  spikeDetection: z.object({
    enabled: z.boolean(),
    volumeThreshold: z.number().min(0),
    priceChangeThreshold: z.number().min(0).max(1),
  }),
  aiForecasting: z.object({
    enabled: z.boolean(),
    confidenceThreshold: z.number().min(0).max(1),
    maxPositionsPerForecast: z.number().min(0).max(100),
  }),
});

const llmConfigSchema = z.object({
  provider: z.enum(['openai', 'anthropic']),
  model: z.string().min(1),
  maxTokens: z.number().min(100).max(100000),
  temperature: z.number().min(0).max(2),
  dailyBudget: z.number().min(0),
});

const notificationConfigSchema = z.object({
  email: z.object({
    enabled: z.boolean(),
    recipients: z.array(z.string().email()),
  }),
  slack: z.object({
    enabled: z.boolean(),
    webhookUrl: z.string().url().optional().or(z.literal('')),
  }),
  telegram: z.object({
    enabled: z.boolean(),
    chatId: z.string().optional(),
  }),
});

interface ConfigFormProps {
  section: 'risk' | 'strategies' | 'llm' | 'notifications';
  initialData: RiskConfig | StrategyConfig | LLMConfig | NotificationConfig;
  onSave: (data: unknown) => Promise<void>;
  onReset: () => void;
}

export function ConfigForm({ section, initialData, onSave, onReset }: ConfigFormProps) {
  const getSchema = () => {
    switch (section) {
      case 'risk':
        return riskConfigSchema;
      case 'strategies':
        return strategyConfigSchema;
      case 'llm':
        return llmConfigSchema;
      case 'notifications':
        return notificationConfigSchema;
    }
  };

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isDirty, isSubmitting },
  } = useForm({
    resolver: zodResolver(getSchema()),
    defaultValues: initialData,
  });

  const watchedValues = watch();

  const onSubmit = async (data: unknown) => {
    await onSave(data);
  };

  const handleReset = () => {
    reset(initialData);
    onReset();
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {section === 'risk' && (
        <RiskConfigFields register={register} errors={errors} />
      )}
      {section === 'strategies' && (
        <StrategyConfigFields register={register} errors={errors} watch={watch} />
      )}
      {section === 'llm' && (
        <LLMConfigFields register={register} errors={errors} />
      )}
      {section === 'notifications' && (
        <NotificationConfigFields register={register} errors={errors} watch={watch} />
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-6 border-t border-gray-800">
        <button
          type="button"
          onClick={handleReset}
          disabled={!isDirty}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RotateCcw className="w-4 h-4" />
          Reset Changes
        </button>
        <button
          type="submit"
          disabled={!isDirty || isSubmitting}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-4 h-4" />
          {isSubmitting ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
}

// Risk Configuration Fields
function RiskConfigFields({ register, errors }: { register: any; errors: any }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">Risk Parameters</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Max Position Size ($)
          </label>
          <input
            type="number"
            {...register('maxPositionSize', { valueAsNumber: true })}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {errors.maxPositionSize && (
            <p className="text-red-500 text-xs mt-1">{errors.maxPositionSize.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Max Total Exposure ($)
          </label>
          <input
            type="number"
            {...register('maxTotalExposure', { valueAsNumber: true })}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {errors.maxTotalExposure && (
            <p className="text-red-500 text-xs mt-1">{errors.maxTotalExposure.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Max Daily Loss ($)
          </label>
          <input
            type="number"
            {...register('maxDailyLoss', { valueAsNumber: true })}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {errors.maxDailyLoss && (
            <p className="text-red-500 text-xs mt-1">{errors.maxDailyLoss.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Stop Loss (%)
          </label>
          <input
            type="number"
            step="0.1"
            {...register('stopLossPercent', { valueAsNumber: true })}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {errors.stopLossPercent && (
            <p className="text-red-500 text-xs mt-1">{errors.stopLossPercent.message}</p>
          )}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Take Profit (%)
          </label>
          <input
            type="number"
            step="0.1"
            {...register('takeProfitPercent', { valueAsNumber: true })}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          />
          {errors.takeProfitPercent && (
            <p className="text-red-500 text-xs mt-1">{errors.takeProfitPercent.message}</p>
          )}
        </div>
      </div>
    </div>
  );
}

// Strategy Configuration Fields
function StrategyConfigFields({ register, errors, watch }: { register: any; errors: any; watch: any }) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-white">Strategy Parameters</h3>
      
      {/* Arbitrage */}
      <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-white">Arbitrage</h4>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              {...register('arbitrage.enabled')}
              className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
            />
            <span className="text-sm text-gray-400">Enabled</span>
          </label>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Min Spread</label>
            <input
              type="number"
              step="0.001"
              {...register('arbitrage.minSpread', { valueAsNumber: true })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Max Position Size</label>
            <input
              type="number"
              {...register('arbitrage.maxPositionSize', { valueAsNumber: true })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </div>

      {/* Market Making */}
      <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-white">Market Making</h4>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              {...register('marketMaking.enabled')}
              className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
            />
            <span className="text-sm text-gray-400">Enabled</span>
          </label>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Spread Target</label>
            <input
              type="number"
              step="0.001"
              {...register('marketMaking.spreadTarget', { valueAsNumber: true })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Inventory Limit</label>
            <input
              type="number"
              {...register('marketMaking.inventoryLimit', { valueAsNumber: true })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </div>

      {/* Spike Detection */}
      <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-white">Spike Detection</h4>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              {...register('spikeDetection.enabled')}
              className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
            />
            <span className="text-sm text-gray-400">Enabled</span>
          </label>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Volume Threshold</label>
            <input
              type="number"
              step="0.1"
              {...register('spikeDetection.volumeThreshold', { valueAsNumber: true })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Price Change Threshold</label>
            <input
              type="number"
              step="0.01"
              {...register('spikeDetection.priceChangeThreshold', { valueAsNumber: true })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </div>

      {/* AI Forecasting */}
      <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-white">AI Forecasting</h4>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              {...register('aiForecasting.enabled')}
              className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
            />
            <span className="text-sm text-gray-400">Enabled</span>
          </label>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Confidence Threshold</label>
            <input
              type="number"
              step="0.01"
              {...register('aiForecasting.confidenceThreshold', { valueAsNumber: true })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Max Positions Per Forecast</label>
            <input
              type="number"
              {...register('aiForecasting.maxPositionsPerForecast', { valueAsNumber: true })}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// LLM Configuration Fields
function LLMConfigFields({ register, errors }: { register: any; errors: any }) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">LLM Settings</h3>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Provider</label>
          <select
            {...register('provider')}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Model</label>
          <input
            type="text"
            {...register('model')}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Max Tokens</label>
          <input
            type="number"
            {...register('maxTokens', { valueAsNumber: true })}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Temperature</label>
          <input
            type="number"
            step="0.1"
            {...register('temperature', { valueAsNumber: true })}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Daily Budget ($)</label>
          <input
            type="number"
            step="0.01"
            {...register('dailyBudget', { valueAsNumber: true })}
            className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>
    </div>
  );
}

// Notification Configuration Fields
function NotificationConfigFields({ register, errors, watch }: { register: any; errors: any; watch: any }) {
  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-white">Notification Settings</h3>
      
      {/* Email */}
      <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-white">Email Notifications</h4>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              {...register('email.enabled')}
              className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
            />
            <span className="text-sm text-gray-400">Enabled</span>
          </label>
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Recipients (comma-separated)</label>
          <input
            type="text"
            placeholder="email1@example.com, email2@example.com"
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      {/* Slack */}
      <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-white">Slack Notifications</h4>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              {...register('slack.enabled')}
              className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
            />
            <span className="text-sm text-gray-400">Enabled</span>
          </label>
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Webhook URL</label>
          <input
            type="url"
            {...register('slack.webhookUrl')}
            placeholder="https://hooks.slack.com/services/..."
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>

      {/* Telegram */}
      <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-medium text-white">Telegram Notifications</h4>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              {...register('telegram.enabled')}
              className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
            />
            <span className="text-sm text-gray-400">Enabled</span>
          </label>
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1">Chat ID</label>
          <input
            type="text"
            {...register('telegram.chatId')}
            placeholder="-1001234567890"
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
      </div>
    </div>
  );
}

export default ConfigForm;
