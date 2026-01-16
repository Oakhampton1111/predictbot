'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { cn } from '@/lib/utils';
import { orchestratorApi } from '@/lib/api';
import type { ServiceStatus } from '@/types';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [systemStatus, setSystemStatus] = useState<ServiceStatus>('unknown');

  // In development mode, skip auth check for UI testing
  // Set NEXT_PUBLIC_SKIP_AUTH=true in .env.local to bypass auth
  const skipAuth = process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_SKIP_AUTH === 'true';

  // Redirect to login if not authenticated (skip in dev mode)
  useEffect(() => {
    if (!skipAuth && status === 'unauthenticated') {
      router.push('/login');
    }
  }, [status, router, skipAuth]);

  // Fetch system health periodically
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const result = await orchestratorApi.getHealth();
        if (result.success && result.data) {
          setSystemStatus(result.data.status as ServiceStatus);
        } else {
          setSystemStatus('unknown');
        }
      } catch {
        setSystemStatus('down');
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 30000); // Every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleEmergencyStop = async () => {
    try {
      // First pause all strategies
      await orchestratorApi.emergencyPause();
      // Then stop all trading
      await orchestratorApi.emergencyStop();
      // Optionally close all positions
      // await orchestratorApi.emergencyCloseAll();
      
      // Refresh the page to show updated status
      router.refresh();
    } catch (error) {
      console.error('Emergency stop failed:', error);
      // Even if API fails, try to show alert
      alert('Emergency stop initiated. Please verify system status.');
    }
  };

  // Show loading state while checking auth (skip in dev mode)
  if (!skipAuth && status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-900">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render layout if not authenticated (skip in dev mode)
  if (!skipAuth && !session) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Sidebar */}
      <Sidebar
        isCollapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Content Area */}
      <div
        className={cn(
          'transition-all duration-300',
          sidebarCollapsed ? 'ml-16' : 'ml-64'
        )}
      >
        {/* Header */}
        <Header
          systemStatus={systemStatus}
          onEmergencyStop={handleEmergencyStop}
        />

        {/* Page Content */}
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}

export default MainLayout;
