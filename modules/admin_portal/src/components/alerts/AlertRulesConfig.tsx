'use client';

import { useState } from 'react';
import { cn, formatCurrency } from '@/lib/utils';
import {
  Settings,
  Save,
  TestTube,
  AlertTriangle,
  DollarSign,
  TrendingDown,
  Brain,
  AlertCircle,
  ToggleLeft,
  ToggleRight,
} from 'lucide-react';

export interface AlertRule {
  id: string;
  name: string;
  description: string;
  type: 'loss_limit' | 'large_trade' | 'ai_confidence' | 'error_rate';
  enabled: boolean;
  threshold: number;
  thresholdUnit: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
}

interface AlertRulesConfigProps {
  rules: AlertRule[];
  isLoading?: boolean;
  isSaving?: boolean;
  onSave: (rules: AlertRule[]) => Promise<void>;
  onTestRule: (ruleId: string) => Promise<{ success: boolean; message: string }>;
}

const ruleIcons: Record<string, typeof AlertTriangle> = {
  loss_limit: DollarSign,
  large_trade: TrendingDown,
  ai_confidence: Brain,
  error_rate: AlertCircle,
};

const severityColors: Record<string, string> = {
  critical: 'text-red-500',
  high: 'text-orange-500',
  medium: 'text-yellow-500',
  low: 'text-blue-500',
};

export function AlertRulesConfig({
  rules: initialRules,
  isLoading,
  isSaving,
  onSave,
  onTestRule,
}: AlertRulesConfigProps) {
  const [rules, setRules] = useState<AlertRule[]>(initialRules);
  const [testingRule, setTestingRule] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ ruleId: string; success: boolean; message: string } | null>(null);
  const [hasChanges, setHasChanges] = useState(false);

  const handleToggleRule = (ruleId: string) => {
    setRules((prev) =>
      prev.map((rule) =>
        rule.id === ruleId ? { ...rule, enabled: !rule.enabled } : rule
      )
    );
    setHasChanges(true);
  };

  const handleThresholdChange = (ruleId: string, value: number) => {
    setRules((prev) =>
      prev.map((rule) =>
        rule.id === ruleId ? { ...rule, threshold: value } : rule
      )
    );
    setHasChanges(true);
  };

  const handleSeverityChange = (ruleId: string, severity: AlertRule['severity']) => {
    setRules((prev) =>
      prev.map((rule) =>
        rule.id === ruleId ? { ...rule, severity } : rule
      )
    );
    setHasChanges(true);
  };

  const handleSave = async () => {
    await onSave(rules);
    setHasChanges(false);
  };

  const handleTestRule = async (ruleId: string) => {
    setTestingRule(ruleId);
    setTestResult(null);
    try {
      const result = await onTestRule(ruleId);
      setTestResult({ ruleId, ...result });
    } finally {
      setTestingRule(null);
    }
  };

  if (isLoading) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-700 rounded w-1/4 mb-4" />
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-24 bg-gray-700 rounded" />
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
          <div className="p-2 rounded-lg bg-purple-500/10">
            <Settings className="w-5 h-5 text-purple-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Alert Rules</h3>
            <p className="text-sm text-gray-400">Configure alert triggers and thresholds</p>
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

      {/* Rules List */}
      <div className="space-y-4">
        {rules.map((rule) => {
          const Icon = ruleIcons[rule.type] || AlertTriangle;
          const isTestingThis = testingRule === rule.id;
          const testResultForThis = testResult?.ruleId === rule.id ? testResult : null;

          return (
            <div
              key={rule.id}
              className={cn(
                'rounded-lg border p-4 transition-colors',
                rule.enabled
                  ? 'border-gray-700 bg-gray-800/50'
                  : 'border-gray-800 bg-gray-900/50 opacity-60'
              )}
            >
              <div className="flex items-start gap-4">
                {/* Icon */}
                <div className={cn(
                  'p-2 rounded-lg',
                  rule.enabled ? 'bg-gray-700' : 'bg-gray-800'
                )}>
                  <Icon className={cn('w-5 h-5', rule.enabled ? 'text-white' : 'text-gray-500')} />
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <h4 className="text-white font-medium">{rule.name}</h4>
                    <span className={cn(
                      'px-2 py-0.5 text-xs font-medium rounded uppercase',
                      severityColors[rule.severity]
                    )}>
                      {rule.severity}
                    </span>
                  </div>
                  <p className="text-gray-400 text-sm mb-4">{rule.description}</p>

                  {/* Configuration */}
                  <div className="flex flex-wrap items-center gap-4">
                    {/* Threshold */}
                    <div className="flex items-center gap-2">
                      <label className="text-sm text-gray-400">Threshold:</label>
                      <input
                        type="number"
                        value={rule.threshold}
                        onChange={(e) => handleThresholdChange(rule.id, parseFloat(e.target.value))}
                        disabled={!rule.enabled}
                        className="w-24 px-3 py-1.5 bg-gray-700 border border-gray-600 rounded text-sm text-white focus:outline-none focus:border-primary disabled:opacity-50"
                      />
                      <span className="text-sm text-gray-500">{rule.thresholdUnit}</span>
                    </div>

                    {/* Severity */}
                    <div className="flex items-center gap-2">
                      <label className="text-sm text-gray-400">Severity:</label>
                      <select
                        value={rule.severity}
                        onChange={(e) => handleSeverityChange(rule.id, e.target.value as AlertRule['severity'])}
                        disabled={!rule.enabled}
                        className="px-3 py-1.5 bg-gray-700 border border-gray-600 rounded text-sm text-white focus:outline-none focus:border-primary disabled:opacity-50"
                      >
                        <option value="critical">Critical</option>
                        <option value="high">High</option>
                        <option value="medium">Medium</option>
                        <option value="low">Low</option>
                      </select>
                    </div>

                    {/* Test Button */}
                    <button
                      onClick={() => handleTestRule(rule.id)}
                      disabled={!rule.enabled || isTestingThis}
                      className={cn(
                        'flex items-center gap-1.5 px-3 py-1.5 text-sm rounded transition-colors',
                        rule.enabled
                          ? 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:text-white'
                          : 'bg-gray-800 text-gray-500 cursor-not-allowed'
                      )}
                    >
                      <TestTube className="w-4 h-4" />
                      {isTestingThis ? 'Testing...' : 'Test Rule'}
                    </button>
                  </div>

                  {/* Test Result */}
                  {testResultForThis && (
                    <div className={cn(
                      'mt-3 p-2 rounded text-sm',
                      testResultForThis.success
                        ? 'bg-green-500/10 text-green-500'
                        : 'bg-red-500/10 text-red-500'
                    )}>
                      {testResultForThis.message}
                    </div>
                  )}
                </div>

                {/* Toggle */}
                <button
                  onClick={() => handleToggleRule(rule.id)}
                  className="flex-shrink-0"
                >
                  {rule.enabled ? (
                    <ToggleRight className="w-8 h-8 text-green-500" />
                  ) : (
                    <ToggleLeft className="w-8 h-8 text-gray-500" />
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default AlertRulesConfig;
