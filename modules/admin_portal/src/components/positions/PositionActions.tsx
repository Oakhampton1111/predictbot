'use client';

import { useState } from 'react';
import { X, Download, Trash2, AlertTriangle } from 'lucide-react';
import type { Position } from '@/types';

interface PositionActionsProps {
  selectedCount: number;
  onCloseSelected: () => void;
  onExportCsv: () => void;
  onClearSelection: () => void;
}

export function PositionActions({
  selectedCount,
  onCloseSelected,
  onExportCsv,
  onClearSelection,
}: PositionActionsProps) {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleCloseClick = () => {
    if (selectedCount > 0) {
      setShowConfirm(true);
    }
  };

  const handleConfirmClose = () => {
    onCloseSelected();
    setShowConfirm(false);
  };

  if (selectedCount === 0) {
    return null;
  }

  return (
    <>
      {/* Action Bar */}
      <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-700">
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-400">
            <span className="font-semibold text-white">{selectedCount}</span> position
            {selectedCount !== 1 ? 's' : ''} selected
          </span>
          <button
            onClick={onClearSelection}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            Clear selection
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onExportCsv}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg bg-gray-700 text-gray-300 hover:bg-gray-600 transition-colors"
          >
            <Download className="w-4 h-4" />
            Export CSV
          </button>
          <button
            onClick={handleCloseClick}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
          >
            <X className="w-4 h-4" />
            Close Selected
          </button>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex items-center gap-3 mb-4">
              <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-500/20">
                <AlertTriangle className="w-5 h-5 text-red-500" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">
                  Close {selectedCount} Position{selectedCount !== 1 ? 's' : ''}?
                </h3>
                <p className="text-sm text-gray-400">This action cannot be undone</p>
              </div>
            </div>

            <p className="text-gray-300 mb-6">
              Are you sure you want to close {selectedCount} selected position
              {selectedCount !== 1 ? 's' : ''}? This will execute market orders to
              close all selected positions at current prices.
            </p>

            <div className="flex items-center justify-end gap-3">
              <button
                onClick={() => setShowConfirm(false)}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmClose}
                className="px-4 py-2 text-sm font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors"
              >
                Close Positions
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Position Details Modal Component
interface PositionDetailsModalProps {
  position: Position | null;
  onClose: () => void;
  onClosePosition: (position: Position) => void;
}

export function PositionDetailsModal({
  position,
  onClose,
  onClosePosition,
}: PositionDetailsModalProps) {
  if (!position) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-gray-900 rounded-xl border border-gray-800 p-6 max-w-lg w-full mx-4 shadow-2xl">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-white">Position Details</h3>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="space-y-4">
          {/* Market Info */}
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Market</p>
            <p className="text-white font-medium">{position.marketTitle}</p>
            <p className="text-sm text-gray-400">ID: {position.marketId}</p>
          </div>

          {/* Position Details Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Platform</p>
              <p className="text-white capitalize">{position.platform}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Strategy</p>
              <p className="text-white">{position.strategy}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Side</p>
              <p className="text-white">{position.side}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Size</p>
              <p className="text-white">{position.size} shares</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Entry Price</p>
              <p className="text-white">${position.entryPrice.toFixed(4)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Current Price</p>
              <p className="text-white">${position.currentPrice.toFixed(4)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">P&L</p>
              <p className={position.pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                ${position.pnl.toFixed(2)} ({position.pnlPercent >= 0 ? '+' : ''}
                {position.pnlPercent.toFixed(2)}%)
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Opened</p>
              <p className="text-white">
                {new Date(position.openedAt).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 mt-6 pt-4 border-t border-gray-800">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-gray-800 text-gray-300 hover:bg-gray-700 transition-colors"
          >
            Close
          </button>
          <button
            onClick={() => onClosePosition(position)}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 transition-colors"
          >
            Close Position
          </button>
        </div>
      </div>
    </div>
  );
}

export default PositionActions;
