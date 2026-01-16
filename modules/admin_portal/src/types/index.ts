// User and Authentication Types
export type Role = 'ADMIN' | 'OPERATOR' | 'VIEWER';

export interface User {
  id: string;
  username: string;
  role: Role;
  lastLogin?: Date;
}

export interface Session {
  user: User;
  expires: string;
}

// System Health Types
export type ServiceStatus = 'healthy' | 'degraded' | 'down' | 'unknown';

export interface ServiceHealth {
  name: string;
  status: ServiceStatus;
  lastHeartbeat: Date;
  latency?: number;
  details?: Record<string, unknown>;
}

export interface SystemHealth {
  overall: ServiceStatus;
  services: ServiceHealth[];
  lastUpdated: Date;
}

// Position Types
export type Platform = 'polymarket' | 'kalshi' | 'manifold';
export type PositionSide = 'YES' | 'NO' | 'LONG' | 'SHORT';
export type PositionStatus = 'open' | 'closed' | 'pending';

export interface Position {
  id: string;
  platform: Platform;
  marketId: string;
  marketTitle: string;
  side: PositionSide;
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  status: PositionStatus;
  strategy: string;
  openedAt: Date;
  closedAt?: Date;
}

export interface PositionSummary {
  totalPositions: number;
  totalValue: number;
  totalPnl: number;
  byPlatform: Record<Platform, { count: number; value: number; pnl: number }>;
}

// Strategy Types
export type StrategyType = 'arbitrage' | 'market_making' | 'spike_detection' | 'ai_forecast';
export type StrategyStatus = 'active' | 'paused' | 'stopped' | 'error';

export interface Strategy {
  id: string;
  name: string;
  type: StrategyType;
  status: StrategyStatus;
  pnl: number;
  pnlToday: number;
  positionsCount: number;
  lastActivity?: Date;
  config: Record<string, unknown>;
  metrics: StrategyMetrics;
}

export interface StrategyMetrics {
  totalTrades: number;
  winRate: number;
  avgProfit: number;
  avgLoss: number;
  sharpeRatio?: number;
  maxDrawdown?: number;
}

// Trade Types
export type TradeType = 'buy' | 'sell';
export type TradeStatus = 'pending' | 'executed' | 'failed' | 'cancelled';

export interface Trade {
  id: string;
  platform: Platform;
  marketId: string;
  marketTitle: string;
  type: TradeType;
  side: PositionSide;
  size: number;
  price: number;
  status: TradeStatus;
  strategy: string;
  executedAt?: Date;
  createdAt: Date;
  error?: string;
}

// Activity Feed Types
export type ActivityType = 
  | 'trade_executed'
  | 'trade_failed'
  | 'position_opened'
  | 'position_closed'
  | 'strategy_started'
  | 'strategy_stopped'
  | 'ai_decision'
  | 'alert_triggered'
  | 'config_changed'
  | 'emergency_action';

export interface Activity {
  id: string;
  type: ActivityType;
  title: string;
  description: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
  severity?: 'info' | 'warning' | 'error' | 'success';
}

// AI Status Types
export interface AIStatus {
  isRunning: boolean;
  currentAgent?: string;
  lastCycleTime?: number;
  forecastCount: number;
  llmUsage: {
    tokensUsed: number;
    requestsToday: number;
    costToday: number;
  };
  agents: AgentStatus[];
}

export interface AgentStatus {
  name: string;
  status: 'idle' | 'running' | 'error';
  lastRun?: Date;
  successRate: number;
}

// Configuration Types
export interface RiskConfig {
  maxPositionSize: number;
  maxTotalExposure: number;
  maxDailyLoss: number;
  stopLossPercent: number;
  takeProfitPercent: number;
}

export interface StrategyConfig {
  arbitrage: {
    enabled: boolean;
    minSpread: number;
    maxPositionSize: number;
  };
  marketMaking: {
    enabled: boolean;
    spreadTarget: number;
    inventoryLimit: number;
  };
  spikeDetection: {
    enabled: boolean;
    volumeThreshold: number;
    priceChangeThreshold: number;
  };
  aiForecasting: {
    enabled: boolean;
    confidenceThreshold: number;
    maxPositionsPerForecast: number;
  };
}

export interface LLMConfig {
  provider: 'openai' | 'anthropic';
  model: string;
  maxTokens: number;
  temperature: number;
  dailyBudget: number;
}

export interface NotificationConfig {
  email: {
    enabled: boolean;
    recipients: string[];
  };
  slack: {
    enabled: boolean;
    webhookUrl?: string;
  };
  telegram: {
    enabled: boolean;
    chatId?: string;
  };
}

export interface AppConfig {
  risk: RiskConfig;
  strategies: StrategyConfig;
  llm: LLMConfig;
  notifications: NotificationConfig;
}

// API Key Types
export interface ApiKeyStatus {
  platform: Platform | 'openai' | 'anthropic';
  isConfigured: boolean;
  isValid: boolean;
  lastValidated?: Date;
  error?: string;
}

// Dashboard Summary Types
export interface DashboardSummary {
  systemHealth: SystemHealth;
  pnl: {
    today: number;
    week: number;
    month: number;
    total: number;
    trend: 'up' | 'down' | 'flat';
  };
  positions: PositionSummary;
  strategies: Strategy[];
  recentActivity: Activity[];
  aiStatus: AIStatus;
}

// Emergency Control Types
export type EmergencyAction = 'pause_all' | 'stop_all' | 'close_all_positions';

export interface EmergencyActionResult {
  action: EmergencyAction;
  success: boolean;
  message: string;
  affectedItems?: number;
  timestamp: Date;
}

// WebSocket Event Types
export interface WSEvent<T = unknown> {
  type: string;
  data: T;
  timestamp: Date;
}

export type WSEventType =
  | 'price_update'
  | 'position_update'
  | 'trade_executed'
  | 'strategy_update'
  | 'health_update'
  | 'activity'
  | 'alert';

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}

// Filter and Sort Types
export interface PositionFilters {
  platform?: Platform;
  status?: PositionStatus;
  strategy?: string;
  search?: string;
}

export interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
}
