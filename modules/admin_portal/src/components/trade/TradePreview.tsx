'use client';

import { cn, formatCurrency } from '@/lib/utils';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  Loader2,
  Info,
} from 'lucide-react';
import type { Platform, PositionSide } from '@/types';

interface Market {
  id: string;
  title: string;
  platform: Platform;
  currentPrice: number;
}

interface TradePreviewData {
  market: Market;
  side: PositionSide;
  size: number;
  price: number;
  orderType: 'market' | 'limit';
  estimatedCost: number;
  estimatedFees: number;
  totalCost: number;
  slippage?: number;
  priceImpact?: number;
}

interface TradePreviewProps {
  preview: TradePreviewData;
  isExecuting?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  error?: string | null;
  success?: { tradeId: string } | null;
}

const platformLabels: Record<Platform, string> = {
  polymarket: 'Polymarket',
  kalshi: 'Kalshi',
  manifold: 'Manifold',
};

export function TradePreview({
  preview,
  isExecuting,
  onConfirm,
  onCancel,
  error,
  success,
}: TradePreviewProps) {
  const isLargeTrade = preview.totalCost > 1000;
  const hasHighSlippage = (preview.slippage || 0) > 2;
  const hasHighPriceImpact = (preview.priceImpact || 0) > 5;

  const warnings: string[] = [];
  if (isLargeTrade) {
    warnings.push('This is a large trade. Please review carefully.');
  }
  if (hasHighSlippage) {
    warnings.push(`High slippage expected: ${preview.slippage?.toFixed(2)}%`);
  }
  if (hasHighPriceImpact) {
    warnings.push(`High price impact: ${preview.priceImpact?.toFixed(2)}%`);
  }

  // Success state
  if (success) {
    return (
      <div className="rounded-xl border border-green-500/50 bg-green-500/5 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-full bg-green-500/10">
            <CheckCircle className="w-6 h-6 text-green-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Trade Executed Successfully</h3>
            <p className="text-gray-400 text-sm">Your order has been placed</p>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          <div className="flex justify-between">
            <span className="text-gray-400">Trade ID</span>
            <span className="text-white font-mono">{success.tradeId}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Market</span>
            <span className="text-white">{preview.market.title}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Side</span>
            <span className={cn(
              'font-medium',
              preview.side === 'YES' ? 'text-green-500' : 'text-red-500'
            )}>
              {preview.side}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Size</span>
            <span className="text-white">{preview.size} shares</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Total Cost</span>
            <span className="text-white font-medium">{formatCurrency(preview.totalCost)}</span>
          </div>
        </div>

        <button
          onClick={onCancel}
          className="w-full py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
        >
          Close
        </button>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="rounded-xl border border-red-500/50 bg-red-500/5 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 rounded-full bg-red-500/10">
            <XCircle className="w-6 h-6 text-red-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Trade Failed</h3>
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onConfirm}
            className="flex-1 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            Try Again
          </button>
          <button
            onClick={onCancel}
            className="px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-primary/50 bg-primary/5 p-6">
      <h3 className="text-lg font-semibold text-white mb-4">Trade Preview</h3>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="mb-4 space-y-2">
          {warnings.map((warning, index) => (
            <div
              key={index}
              className="flex items-center gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
            >
              <AlertTriangle className="w-4 h-4 text-yellow-500 flex-shrink-0" />
              <span className="text-yellow-500 text-sm">{warning}</span>
            </div>
          ))}
        </div>
      )}

      {/* Trade Details */}
      <div className="space-y-3">
        <div className="flex justify-between">
          <span className="text-gray-400">Market</span>
          <span className="text-white font-medium text-right max-w-[60%] truncate">
            {preview.market.title}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Platform</span>
          <span className="text-white">{platformLabels[preview.market.platform]}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Side</span>
          <span className={cn(
            'font-medium',
            preview.side === 'YES' ? 'text-green-500' : 'text-red-500'
          )}>
            {preview.side}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Size</span>
          <span className="text-white">{preview.size} shares</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Price</span>
          <span className="text-white">${preview.price.toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Order Type</span>
          <span className="text-white capitalize">{preview.orderType}</span>
        </div>

        <div className="border-t border-gray-700 my-3" />

        <div className="flex justify-between">
          <span className="text-gray-400">Estimated Cost</span>
          <span className="text-white">{formatCurrency(preview.estimatedCost)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Estimated Fees</span>
          <span className="text-white">{formatCurrency(preview.estimatedFees)}</span>
        </div>
        {preview.slippage !== undefined && (
          <div className="flex justify-between">
            <span className="text-gray-400 flex items-center gap-1">
              Slippage
              <Info className="w-3 h-3" />
            </span>
            <span className={cn(
              hasHighSlippage ? 'text-yellow-500' : 'text-white'
            )}>
              {preview.slippage.toFixed(2)}%
            </span>
          </div>
        )}
        {preview.priceImpact !== undefined && (
          <div className="flex justify-between">
            <span className="text-gray-400 flex items-center gap-1">
              Price Impact
              <Info className="w-3 h-3" />
            </span>
            <span className={cn(
              hasHighPriceImpact ? 'text-yellow-500' : 'text-white'
            )}>
              {preview.priceImpact.toFixed(2)}%
            </span>
          </div>
        )}

        <div className="border-t border-gray-700 my-3" />

        <div className="flex justify-between text-lg">
          <span className="text-white font-medium">Total</span>
          <span className="text-white font-bold">{formatCurrency(preview.totalCost)}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 mt-6">
        <button
          onClick={onConfirm}
          disabled={isExecuting}
          className={cn(
            'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors',
            'bg-primary text-white hover:bg-primary/90',
            isExecuting && 'opacity-50 cursor-not-allowed'
          )}
        >
          {isExecuting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Executing...
            </>
          ) : (
            'Confirm & Execute'
          )}
        </button>
        <button
          onClick={onCancel}
          disabled={isExecuting}
          className="px-6 py-3 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
      </div>

      {/* Disclaimer */}
      <p className="mt-4 text-xs text-gray-500 text-center">
        By clicking "Confirm & Execute", you agree to execute this trade. 
        This action cannot be undone.
      </p>
    </div>
  );
}

export default TradePreview;
