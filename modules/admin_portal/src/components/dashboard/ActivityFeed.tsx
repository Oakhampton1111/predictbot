'use client';

import { useEffect, useRef } from 'react';
import { cn, formatRelativeTime } from '@/lib/utils';
import {
  Activity,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Zap,
  Bot,
  Settings,
  AlertOctagon,
} from 'lucide-react';
import type { Activity as ActivityType, ActivityType as ActivityTypeEnum } from '@/types';

interface ActivityFeedProps {
  activities: ActivityType[];
  maxItems?: number;
  autoScroll?: boolean;
}

const activityIcons: Record<ActivityTypeEnum, React.ComponentType<{ className?: string }>> = {
  trade_executed: TrendingUp,
  trade_failed: XCircle,
  position_opened: TrendingUp,
  position_closed: TrendingDown,
  strategy_started: Zap,
  strategy_stopped: Zap,
  ai_decision: Bot,
  alert_triggered: AlertTriangle,
  config_changed: Settings,
  emergency_action: AlertOctagon,
};

const activityColors: Record<ActivityTypeEnum, string> = {
  trade_executed: 'text-green-500 bg-green-500/10',
  trade_failed: 'text-red-500 bg-red-500/10',
  position_opened: 'text-blue-500 bg-blue-500/10',
  position_closed: 'text-yellow-500 bg-yellow-500/10',
  strategy_started: 'text-green-500 bg-green-500/10',
  strategy_stopped: 'text-red-500 bg-red-500/10',
  ai_decision: 'text-purple-500 bg-purple-500/10',
  alert_triggered: 'text-yellow-500 bg-yellow-500/10',
  config_changed: 'text-gray-500 bg-gray-500/10',
  emergency_action: 'text-red-500 bg-red-500/10',
};

const severityColors = {
  info: 'border-l-blue-500',
  warning: 'border-l-yellow-500',
  error: 'border-l-red-500',
  success: 'border-l-green-500',
};

export function ActivityFeed({
  activities,
  maxItems = 20,
  autoScroll = true,
}: ActivityFeedProps) {
  const feedRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to top when new activities arrive
  useEffect(() => {
    if (autoScroll && feedRef.current) {
      feedRef.current.scrollTop = 0;
    }
  }, [activities, autoScroll]);

  const displayedActivities = activities.slice(0, maxItems);

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-purple-500/10">
            <Activity className="w-5 h-5 text-purple-500" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Activity Feed</h3>
            <p className="text-sm text-gray-400">Recent events and actions</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-gray-500">Live</span>
        </div>
      </div>

      {/* Activity List */}
      <div
        ref={feedRef}
        className="space-y-2 max-h-[400px] overflow-y-auto pr-2"
      >
        {displayedActivities.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500">No recent activity</p>
          </div>
        ) : (
          displayedActivities.map((activity) => (
            <ActivityItem key={activity.id} activity={activity} />
          ))
        )}
      </div>
    </div>
  );
}

interface ActivityItemProps {
  activity: ActivityType;
}

function ActivityItem({ activity }: ActivityItemProps) {
  const Icon = activityIcons[activity.type] || Activity;
  const colorClass = activityColors[activity.type] || 'text-gray-500 bg-gray-500/10';
  const severityClass = activity.severity ? severityColors[activity.severity] : 'border-l-transparent';

  return (
    <div
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg bg-gray-800/30 border-l-2 activity-enter',
        severityClass
      )}
    >
      <div className={cn('p-2 rounded-lg flex-shrink-0', colorClass)}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-white truncate">{activity.title}</p>
        <p className="text-xs text-gray-400 line-clamp-2">{activity.description}</p>
        <p className="text-xs text-gray-500 mt-1">
          {formatRelativeTime(activity.timestamp)}
        </p>
      </div>
    </div>
  );
}

export default ActivityFeed;
