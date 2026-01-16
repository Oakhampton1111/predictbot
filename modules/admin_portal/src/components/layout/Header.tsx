'use client';

import { useSession, signOut } from 'next-auth/react';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import {
  User,
  LogOut,
  AlertOctagon,
  Circle,
  ChevronDown,
} from 'lucide-react';

interface HeaderProps {
  systemStatus: 'healthy' | 'degraded' | 'down' | 'unknown';
  onEmergencyStop: () => void;
}

export function Header({ systemStatus, onEmergencyStop }: HeaderProps) {
  const { data: session } = useSession();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showEmergencyConfirm, setShowEmergencyConfirm] = useState(false);

  const handleEmergencyClick = () => {
    if (showEmergencyConfirm) {
      onEmergencyStop();
      setShowEmergencyConfirm(false);
    } else {
      setShowEmergencyConfirm(true);
      // Auto-reset after 5 seconds
      setTimeout(() => setShowEmergencyConfirm(false), 5000);
    }
  };

  const getStatusColor = () => {
    switch (systemStatus) {
      case 'healthy':
        return 'text-green-500';
      case 'degraded':
        return 'text-yellow-500';
      case 'down':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusText = () => {
    switch (systemStatus) {
      case 'healthy':
        return 'All Systems Operational';
      case 'degraded':
        return 'Degraded Performance';
      case 'down':
        return 'System Down';
      default:
        return 'Status Unknown';
    }
  };

  return (
    <header className="sticky top-0 z-30 h-16 bg-gray-900/95 backdrop-blur border-b border-gray-800">
      <div className="flex items-center justify-between h-full px-6">
        {/* System Status */}
        <div className="flex items-center gap-2">
          <Circle
            className={cn('w-3 h-3 fill-current', getStatusColor())}
          />
          <span className="text-sm text-gray-400">{getStatusText()}</span>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-4">
          {/* Emergency Stop Button */}
          <button
            onClick={handleEmergencyClick}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all duration-200',
              showEmergencyConfirm
                ? 'bg-red-600 text-white animate-pulse'
                : 'bg-red-600/20 text-red-500 hover:bg-red-600 hover:text-white'
            )}
          >
            <AlertOctagon className="w-5 h-5" />
            <span className="hidden sm:inline">
              {showEmergencyConfirm ? 'CONFIRM STOP' : 'EMERGENCY STOP'}
            </span>
          </button>

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-300 hover:bg-gray-800 transition-colors"
            >
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/20">
                <User className="w-4 h-4 text-primary" />
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-sm font-medium text-white">
                  {session?.user?.username || 'User'}
                </p>
                <p className="text-xs text-gray-500 capitalize">
                  {session?.user?.role?.toLowerCase() || 'viewer'}
                </p>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-500" />
            </button>

            {/* Dropdown Menu */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-lg shadow-xl border border-gray-700 py-1">
                <div className="px-4 py-2 border-b border-gray-700">
                  <p className="text-sm font-medium text-white">
                    {session?.user?.username}
                  </p>
                  <p className="text-xs text-gray-500 capitalize">
                    {session?.user?.role?.toLowerCase()}
                  </p>
                </div>
                <button
                  onClick={() => signOut({ callbackUrl: '/login' })}
                  className="flex items-center gap-2 w-full px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
