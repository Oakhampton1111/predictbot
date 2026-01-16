import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import { redis, CACHE_KEYS } from '@/lib/redis';
import { orchestratorApi, aiApi } from '@/lib/api';

export async function GET() {
  try {
    // Check authentication
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Try to get cached data first
    const cachedData = await redis.get(CACHE_KEYS.SYSTEM_HEALTH);
    if (cachedData) {
      return NextResponse.json(JSON.parse(cachedData));
    }

    // Fetch fresh data from services
    const [healthResult, positionsResult, strategiesResult, aiStatusResult] = await Promise.allSettled([
      orchestratorApi.getHealth(),
      orchestratorApi.getPositions(),
      orchestratorApi.getStrategies(),
      aiApi.getStatus(),
    ]);

    const dashboardData = {
      systemHealth: healthResult.status === 'fulfilled' ? healthResult.value.data : null,
      positions: positionsResult.status === 'fulfilled' ? positionsResult.value.data : null,
      strategies: strategiesResult.status === 'fulfilled' ? strategiesResult.value.data : null,
      aiStatus: aiStatusResult.status === 'fulfilled' ? aiStatusResult.value.data : null,
      timestamp: new Date().toISOString(),
    };

    // Cache for 10 seconds
    await redis.setex(CACHE_KEYS.SYSTEM_HEALTH, 10, JSON.stringify(dashboardData));

    return NextResponse.json(dashboardData);
  } catch (error) {
    console.error('Dashboard API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch dashboard data' },
      { status: 500 }
    );
  }
}
