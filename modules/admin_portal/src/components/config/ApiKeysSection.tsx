'use client';

import { useState } from 'react';
import { Eye, EyeOff, Check, X, RefreshCw, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ApiKeyStatus, Platform } from '@/types';

interface ApiKeysSectionProps {
  apiKeys: ApiKeyStatus[];
  onTestConnection: (platform: string) => Promise<boolean>;
  onUpdateKey: (platform: string, key: string) => Promise<void>;
}

const platformLabels: Record<string, string> = {
  polymarket: 'Polymarket',
  kalshi: 'Kalshi',
  manifold: 'Manifold',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
};

export function ApiKeysSection({
  apiKeys,
  onTestConnection,
  onUpdateKey,
}: ApiKeysSectionProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-white">API Keys</h3>
      <p className="text-sm text-gray-400">
        Manage your API keys for trading platforms and AI providers
      </p>
      <div className="space-y-3">
        {apiKeys.map((apiKey) => (
          <ApiKeyItem
            key={apiKey.platform}
            apiKey={apiKey}
            onTestConnection={onTestConnection}
            onUpdateKey={onUpdateKey}
          />
        ))}
      </div>
    </div>
  );
}

interface ApiKeyItemProps {
  apiKey: ApiKeyStatus;
  onTestConnection: (platform: string) => Promise<boolean>;
  onUpdateKey: (platform: string, key: string) => Promise<void>;
}

function ApiKeyItem({ apiKey, onTestConnection, onUpdateKey }: ApiKeyItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [keyValue, setKeyValue] = useState('');
  const [isTesting, setIsTesting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [testResult, setTestResult] = useState<boolean | null>(null);

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await onTestConnection(apiKey.platform);
      setTestResult(result);
    } catch {
      setTestResult(false);
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    if (!keyValue.trim()) return;
    setIsSaving(true);
    try {
      await onUpdateKey(apiKey.platform, keyValue);
      setIsEditing(false);
      setKeyValue('');
    } catch (error) {
      console.error('Failed to save API key:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setKeyValue('');
  };

  const getMaskedKey = () => {
    if (!apiKey.isConfigured) return 'Not configured';
    return '••••••••••••••••••••••••••••••••';
  };

  return (
    <div className="p-4 rounded-lg bg-gray-800/50 border border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-white font-medium">
            {platformLabels[apiKey.platform] || apiKey.platform}
          </span>
          {apiKey.isConfigured && (
            <span
              className={cn(
                'inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded',
                apiKey.isValid
                  ? 'bg-green-500/20 text-green-400'
                  : 'bg-red-500/20 text-red-400'
              )}
            >
              {apiKey.isValid ? (
                <>
                  <Check className="w-3 h-3" />
                  Valid
                </>
              ) : (
                <>
                  <X className="w-3 h-3" />
                  Invalid
                </>
              )}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {!isEditing && (
            <>
              <button
                onClick={handleTest}
                disabled={!apiKey.isConfigured || isTesting}
                className="flex items-center gap-1 px-2 py-1 text-xs font-medium rounded bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isTesting ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <RefreshCw className="w-3 h-3" />
                )}
                Test
              </button>
              <button
                onClick={() => setIsEditing(true)}
                className="px-2 py-1 text-xs font-medium rounded bg-primary/20 text-primary hover:bg-primary/30 transition-colors"
              >
                {apiKey.isConfigured ? 'Update' : 'Configure'}
              </button>
            </>
          )}
        </div>
      </div>

      {isEditing ? (
        <div className="space-y-3">
          <div className="relative">
            <input
              type={showKey ? 'text' : 'password'}
              value={keyValue}
              onChange={(e) => setKeyValue(e.target.value)}
              placeholder="Enter API key..."
              className="w-full px-4 py-2 pr-10 bg-gray-800 border border-gray-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
            >
              {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
          <div className="flex items-center justify-end gap-2">
            <button
              onClick={handleCancel}
              className="px-3 py-1.5 text-sm font-medium rounded bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={!keyValue.trim() || isSaving}
              className="flex items-center gap-1 px-3 py-1.5 text-sm font-medium rounded bg-primary text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSaving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Check className="w-4 h-4" />
              )}
              Save
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between">
          <code className="text-sm text-gray-500 font-mono">{getMaskedKey()}</code>
          {testResult !== null && (
            <span
              className={cn(
                'text-xs',
                testResult ? 'text-green-400' : 'text-red-400'
              )}
            >
              {testResult ? 'Connection successful' : 'Connection failed'}
            </span>
          )}
        </div>
      )}

      {apiKey.error && !isEditing && (
        <p className="mt-2 text-xs text-red-400">{apiKey.error}</p>
      )}

      {apiKey.lastValidated && !isEditing && (
        <p className="mt-2 text-xs text-gray-500">
          Last validated: {new Date(apiKey.lastValidated).toLocaleString()}
        </p>
      )}
    </div>
  );
}

export default ApiKeysSection;
