import Redis from 'ioredis';

const globalForRedis = globalThis as unknown as {
  redis: Redis | undefined;
};

function createRedisClient(): Redis {
  const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
  
  const client = new Redis(redisUrl, {
    maxRetriesPerRequest: 3,
    retryStrategy: (times: number) => Math.min(times * 100, 3000),
    lazyConnect: true,
  } as any);

  client.on('error', (err) => {
    console.error('Redis connection error:', err);
  });

  client.on('connect', () => {
    console.log('Redis connected successfully');
  });

  return client;
}

export const redis = globalForRedis.redis ?? createRedisClient();

if (process.env.NODE_ENV !== 'production') globalForRedis.redis = redis;

// Helper functions for common Redis operations
export async function getJSON<T>(key: string): Promise<T | null> {
  try {
    const data = await redis.get(key);
    return data ? JSON.parse(data) : null;
  } catch (error) {
    console.error(`Error getting JSON from Redis key ${key}:`, error);
    return null;
  }
}

export async function setJSON<T>(key: string, value: T, ttlSeconds?: number): Promise<void> {
  try {
    const data = JSON.stringify(value);
    if (ttlSeconds) {
      await redis.setex(key, ttlSeconds, data);
    } else {
      await redis.set(key, data);
    }
  } catch (error) {
    console.error(`Error setting JSON to Redis key ${key}:`, error);
  }
}

export async function publishEvent(channel: string, event: unknown): Promise<void> {
  try {
    await redis.publish(channel, JSON.stringify(event));
  } catch (error) {
    console.error(`Error publishing to channel ${channel}:`, error);
  }
}

// Cache keys
export const CACHE_KEYS = {
  SYSTEM_HEALTH: 'admin:system_health',
  POSITIONS: 'admin:positions',
  STRATEGIES: 'admin:strategies',
  CONFIG: 'admin:config',
  ACTIVITY_FEED: 'admin:activity_feed',
  AI_STATUS: 'admin:ai_status',
  PNL_SUMMARY: 'admin:pnl_summary',
} as const;

// Pub/Sub channels
export const CHANNELS = {
  PRICE_UPDATES: 'predictbot:prices',
  TRADE_UPDATES: 'predictbot:trades',
  POSITION_UPDATES: 'predictbot:positions',
  STRATEGY_UPDATES: 'predictbot:strategies',
  HEALTH_UPDATES: 'predictbot:health',
  ALERTS: 'predictbot:alerts',
  EMERGENCY: 'predictbot:emergency',
} as const;

export default redis;
