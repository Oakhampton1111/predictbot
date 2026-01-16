'use client';

import { useState } from 'react';
import { cn, formatCurrency, formatPercent, formatDate, getPnlClass } from '@/lib/utils';
import { ChevronUp, ChevronDown, ExternalLink } from 'lucide-react';
import type { Position, Platform, SortConfig } from '@/types';

interface PositionsTableProps {
  positions: Position[];
  selectedIds: string[];
  onSelectPosition: (id: string) => void;
  onSelectAll: () => void;
  onViewDetails: (position: Position) => void;
  onClosePosition: (position: Position) => void;
}

const platformLabels: Record<Platform, string> = {
  polymarket: 'Polymarket',
  kalshi: 'Kalshi',
  manifold: 'Manifold',
};

const platformColors: Record<Platform, string> = {
  polymarket: 'bg-purple-500/20 text-purple-400',
  kalshi: 'bg-blue-500/20 text-blue-400',
  manifold: 'bg-green-500/20 text-green-400',
};

export function PositionsTable({
  positions,
  selectedIds,
  onSelectPosition,
  onSelectAll,
  onViewDetails,
  onClosePosition,
}: PositionsTableProps) {
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'openedAt',
    direction: 'desc',
  });

  const handleSort = (field: string) => {
    setSortConfig((prev) => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const sortedPositions = [...positions].sort((a, b) => {
    const aValue = a[sortConfig.field as keyof Position];
    const bValue = b[sortConfig.field as keyof Position];

    if (aValue === undefined || bValue === undefined) return 0;

    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
    }

    if (aValue instanceof Date && bValue instanceof Date) {
      return sortConfig.direction === 'asc'
        ? aValue.getTime() - bValue.getTime()
        : bValue.getTime() - aValue.getTime();
    }

    const aStr = String(aValue);
    const bStr = String(bValue);
    return sortConfig.direction === 'asc'
      ? aStr.localeCompare(bStr)
      : bStr.localeCompare(aStr);
  });

  const allSelected = positions.length > 0 && selectedIds.length === positions.length;

  const SortIcon = ({ field }: { field: string }) => {
    if (sortConfig.field !== field) return null;
    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    );
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-800">
            <th className="px-4 py-3 text-left">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={onSelectAll}
                className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
              />
            </th>
            <th
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300"
              onClick={() => handleSort('platform')}
            >
              <div className="flex items-center gap-1">
                Platform
                <SortIcon field="platform" />
              </div>
            </th>
            <th
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300"
              onClick={() => handleSort('marketTitle')}
            >
              <div className="flex items-center gap-1">
                Market
                <SortIcon field="marketTitle" />
              </div>
            </th>
            <th
              className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300"
              onClick={() => handleSort('side')}
            >
              <div className="flex items-center gap-1">
                Side
                <SortIcon field="side" />
              </div>
            </th>
            <th
              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300"
              onClick={() => handleSort('size')}
            >
              <div className="flex items-center justify-end gap-1">
                Size
                <SortIcon field="size" />
              </div>
            </th>
            <th
              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300"
              onClick={() => handleSort('entryPrice')}
            >
              <div className="flex items-center justify-end gap-1">
                Entry
                <SortIcon field="entryPrice" />
              </div>
            </th>
            <th
              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300"
              onClick={() => handleSort('currentPrice')}
            >
              <div className="flex items-center justify-end gap-1">
                Current
                <SortIcon field="currentPrice" />
              </div>
            </th>
            <th
              className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-300"
              onClick={() => handleSort('pnl')}
            >
              <div className="flex items-center justify-end gap-1">
                P&L
                <SortIcon field="pnl" />
              </div>
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-800">
          {sortedPositions.map((position) => (
            <tr
              key={position.id}
              className={cn(
                'table-row-hover',
                selectedIds.includes(position.id) && 'bg-primary/5'
              )}
            >
              <td className="px-4 py-3">
                <input
                  type="checkbox"
                  checked={selectedIds.includes(position.id)}
                  onChange={() => onSelectPosition(position.id)}
                  className="w-4 h-4 rounded border-gray-600 bg-gray-800 text-primary focus:ring-primary"
                />
              </td>
              <td className="px-4 py-3">
                <span
                  className={cn(
                    'inline-flex px-2 py-1 text-xs font-medium rounded',
                    platformColors[position.platform]
                  )}
                >
                  {platformLabels[position.platform]}
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="max-w-xs">
                  <p className="text-sm font-medium text-white truncate">
                    {position.marketTitle}
                  </p>
                  <p className="text-xs text-gray-500">{position.strategy}</p>
                </div>
              </td>
              <td className="px-4 py-3">
                <span
                  className={cn(
                    'inline-flex px-2 py-1 text-xs font-medium rounded',
                    position.side === 'YES' || position.side === 'LONG'
                      ? 'bg-green-500/20 text-green-400'
                      : 'bg-red-500/20 text-red-400'
                  )}
                >
                  {position.side}
                </span>
              </td>
              <td className="px-4 py-3 text-right text-sm text-white">
                {position.size}
              </td>
              <td className="px-4 py-3 text-right text-sm text-white">
                ${position.entryPrice.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-right text-sm text-white">
                ${position.currentPrice.toFixed(2)}
              </td>
              <td className="px-4 py-3 text-right">
                <div>
                  <p className={cn('text-sm font-medium', getPnlClass(position.pnl))}>
                    {formatCurrency(position.pnl)}
                  </p>
                  <p className={cn('text-xs', getPnlClass(position.pnlPercent))}>
                    {formatPercent(position.pnlPercent)}
                  </p>
                </div>
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onViewDetails(position)}
                    className="p-1.5 rounded hover:bg-gray-800 text-gray-400 hover:text-white transition-colors"
                    title="View Details"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onClosePosition(position)}
                    className="px-2 py-1 text-xs font-medium rounded bg-red-500/20 text-red-400 hover:bg-red-500/30 transition-colors"
                  >
                    Close
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {positions.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">No positions found</p>
        </div>
      )}
    </div>
  );
}

export default PositionsTable;
