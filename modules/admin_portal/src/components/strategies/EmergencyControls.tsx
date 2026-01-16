'use client';

import { useState } from 'react';
import { AlertOctagon, Pause, Square, XCircle, Loader2 } from 'lucide-react';

interface EmergencyControlsProps {
  onPauseAll: () => Promise<void>;
  onStopAll: () => Promise<void>;
  onCloseAllPositions: () => Promise<void>;
  isPaused: boolean;
  isStopped: boolean;
}

export function EmergencyControls({
  onPauseAll,
  onStopAll,
  onCloseAllPositions,
  isPaused,
  isStopped,
}: EmergencyControlsProps) {
  const [confirmAction, setConfirmAction] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<string | null>(null);

  const handleAction = async (action: string, handler: () => Promise<void>) => {
    if (confirmAction === action) {
      setIsLoading(action);
      try {
        await handler();
      } catch (error) {
        console.error(`Emergency action ${action} failed:`, error);
      } finally {
        setIsLoading(null);
        setConfirmAction(null);
      }
    } else {
      setConfirmAction(action);
      // Auto-reset confirmation after 5 seconds
      setTimeout(() => {
        setConfirmAction((current) => (current === action ? null : current));
      }, 5000);
    }
  };

  return (
    <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-500/20">
          <AlertOctagon className="w-5 h-5 text-red-500" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Emergency Controls</h3>
          <p className="text-sm text-gray-400">
            Use these controls to immediately halt trading operations
          </p>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="flex items-center gap-4 mb-6 p-3 rounded-lg bg-gray-800/50">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              isPaused ? 'bg-yellow-500' : isStopped ? 'bg-red-500' : 'bg-green-500'
            }`}
          />
          <span className="text-sm text-gray-400">
            System Status:{' '}
            <span className="font-medium text-white">
              {isStopped ? 'Stopped' : isPaused ? 'Paused' : 'Running'}
            </span>
          </span>
        </div>
      </div>

      {/* Emergency Buttons */}
      <div className="space-y-3">
        {/* Pause All */}
        <button
          onClick={() => handleAction('pause', onPauseAll)}
          disabled={isPaused || isStopped || isLoading !== null}
          className={`w-full flex items-center justify-center gap-3 px-6 py-4 rounded-lg font-semibold transition-all duration-200 ${
            confirmAction === 'pause'
              ? 'bg-yellow-500 text-black animate-pulse'
              : 'bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isLoading === 'pause' ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Pause className="w-5 h-5" />
          )}
          <span>
            {confirmAction === 'pause'
              ? 'CLICK AGAIN TO CONFIRM PAUSE'
              : 'PAUSE ALL STRATEGIES'}
          </span>
        </button>

        {/* Stop All Trading */}
        <button
          onClick={() => handleAction('stop', onStopAll)}
          disabled={isStopped || isLoading !== null}
          className={`w-full flex items-center justify-center gap-3 px-6 py-4 rounded-lg font-semibold transition-all duration-200 ${
            confirmAction === 'stop'
              ? 'bg-red-600 text-white animate-pulse'
              : 'bg-red-500/20 text-red-500 hover:bg-red-500/30'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isLoading === 'stop' ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Square className="w-5 h-5" />
          )}
          <span>
            {confirmAction === 'stop'
              ? 'CLICK AGAIN TO CONFIRM STOP'
              : 'STOP ALL TRADING'}
          </span>
        </button>

        {/* Close All Positions */}
        <button
          onClick={() => handleAction('close', onCloseAllPositions)}
          disabled={isLoading !== null}
          className={`w-full flex items-center justify-center gap-3 px-6 py-4 rounded-lg font-semibold transition-all duration-200 ${
            confirmAction === 'close'
              ? 'bg-red-700 text-white animate-pulse'
              : 'bg-red-600/20 text-red-400 hover:bg-red-600/30'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isLoading === 'close' ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <XCircle className="w-5 h-5" />
          )}
          <span>
            {confirmAction === 'close'
              ? 'CLICK AGAIN TO CLOSE ALL POSITIONS'
              : 'CLOSE ALL POSITIONS'}
          </span>
        </button>
      </div>

      {/* Warning */}
      <div className="mt-4 p-3 rounded-lg bg-gray-800/30 border border-gray-700">
        <p className="text-xs text-gray-500">
          <strong className="text-gray-400">Warning:</strong> Emergency controls
          will immediately affect all trading operations. Use with caution.
          Actions require confirmation by clicking twice within 5 seconds.
        </p>
      </div>
    </div>
  );
}

export default EmergencyControls;
