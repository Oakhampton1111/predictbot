-- =============================================================================
-- PredictBot Stack - Database Initialization Script
-- =============================================================================
-- This script initializes the PostgreSQL database with TimescaleDB extension
-- and creates all required tables for the prediction market trading bot.
--
-- Tables:
--   - positions: Active and historical trading positions
--   - trades: Individual trade executions
--   - pnl_snapshots: Time-series P&L data (TimescaleDB hypertable)
--   - ai_forecasts: AI-generated probability forecasts
--   - alerts: System alerts and notifications
--   - config_history: Configuration change audit log
-- =============================================================================

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Positions Table
-- =============================================================================
-- Tracks all trading positions across platforms
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    platform VARCHAR(20) NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    market_question TEXT,
    side VARCHAR(10) NOT NULL CHECK (side IN ('yes', 'no', 'buy', 'sell')),
    size DECIMAL(18,8) NOT NULL CHECK (size > 0),
    entry_price DECIMAL(18,8) NOT NULL CHECK (entry_price >= 0 AND entry_price <= 1),
    current_price DECIMAL(18,8) CHECK (current_price >= 0 AND current_price <= 1),
    unrealized_pnl DECIMAL(18,8),
    realized_pnl DECIMAL(18,8) DEFAULT 0,
    strategy VARCHAR(20) NOT NULL,
    opened_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    closed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'closed', 'liquidated', 'expired')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for positions table
CREATE INDEX IF NOT EXISTS idx_positions_platform ON positions(platform);
CREATE INDEX IF NOT EXISTS idx_positions_market_id ON positions(market_id);
CREATE INDEX IF NOT EXISTS idx_positions_strategy ON positions(strategy);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status);
CREATE INDEX IF NOT EXISTS idx_positions_opened_at ON positions(opened_at);
CREATE INDEX IF NOT EXISTS idx_positions_platform_status ON positions(platform, status);

-- =============================================================================
-- Trades Table
-- =============================================================================
-- Records individual trade executions
CREATE TABLE IF NOT EXISTS trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    position_id UUID REFERENCES positions(id) ON DELETE SET NULL,
    platform VARCHAR(20) NOT NULL,
    market_id VARCHAR(100) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy_yes', 'buy_no', 'sell_yes', 'sell_no', 'buy', 'sell')),
    size DECIMAL(18,8) NOT NULL CHECK (size > 0),
    price DECIMAL(18,8) NOT NULL CHECK (price >= 0 AND price <= 1),
    fees DECIMAL(18,8) DEFAULT 0,
    strategy VARCHAR(20) NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    order_id VARCHAR(100),
    tx_hash VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for trades table
CREATE INDEX IF NOT EXISTS idx_trades_position_id ON trades(position_id);
CREATE INDEX IF NOT EXISTS idx_trades_platform ON trades(platform);
CREATE INDEX IF NOT EXISTS idx_trades_market_id ON trades(market_id);
CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy);
CREATE INDEX IF NOT EXISTS idx_trades_executed_at ON trades(executed_at);
CREATE INDEX IF NOT EXISTS idx_trades_platform_executed ON trades(platform, executed_at);

-- =============================================================================
-- P&L Snapshots Table (TimescaleDB Hypertable)
-- =============================================================================
-- Time-series data for P&L tracking
CREATE TABLE IF NOT EXISTS pnl_snapshots (
    id SERIAL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    total_pnl DECIMAL(18,8) NOT NULL,
    realized_pnl DECIMAL(18,8) NOT NULL,
    unrealized_pnl DECIMAL(18,8) NOT NULL,
    daily_pnl DECIMAL(18,8) DEFAULT 0,
    by_strategy JSONB DEFAULT '{}',
    by_platform JSONB DEFAULT '{}',
    position_count INTEGER DEFAULT 0,
    trade_count INTEGER DEFAULT 0,
    PRIMARY KEY (id, timestamp)
);

-- Convert to TimescaleDB hypertable for efficient time-series queries
SELECT create_hypertable('pnl_snapshots', 'timestamp', if_not_exists => TRUE);

-- Create continuous aggregate for hourly P&L summaries
CREATE MATERIALIZED VIEW IF NOT EXISTS pnl_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    AVG(total_pnl) AS avg_total_pnl,
    MAX(total_pnl) AS max_total_pnl,
    MIN(total_pnl) AS min_total_pnl,
    LAST(total_pnl, timestamp) AS last_total_pnl,
    AVG(daily_pnl) AS avg_daily_pnl,
    SUM(trade_count) AS total_trades
FROM pnl_snapshots
GROUP BY bucket
WITH NO DATA;

-- Create continuous aggregate for daily P&L summaries
CREATE MATERIALIZED VIEW IF NOT EXISTS pnl_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    AVG(total_pnl) AS avg_total_pnl,
    MAX(total_pnl) AS max_total_pnl,
    MIN(total_pnl) AS min_total_pnl,
    LAST(total_pnl, timestamp) AS last_total_pnl,
    LAST(daily_pnl, timestamp) AS daily_pnl,
    SUM(trade_count) AS total_trades
FROM pnl_snapshots
GROUP BY bucket
WITH NO DATA;

-- =============================================================================
-- AI Forecasts Table
-- =============================================================================
-- Stores AI-generated probability forecasts for tracking accuracy
CREATE TABLE IF NOT EXISTS ai_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    market_id VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,
    market_question TEXT,
    predicted_probability DECIMAL(5,4) NOT NULL CHECK (predicted_probability >= 0 AND predicted_probability <= 1),
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    reasoning TEXT,
    sources JSONB DEFAULT '[]',
    model_used VARCHAR(50),
    agent_name VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    resolution_date TIMESTAMP WITH TIME ZONE,
    outcome BOOLEAN,
    accuracy_score DECIMAL(5,4),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for ai_forecasts table
CREATE INDEX IF NOT EXISTS idx_ai_forecasts_market_id ON ai_forecasts(market_id);
CREATE INDEX IF NOT EXISTS idx_ai_forecasts_platform ON ai_forecasts(platform);
CREATE INDEX IF NOT EXISTS idx_ai_forecasts_created_at ON ai_forecasts(created_at);
CREATE INDEX IF NOT EXISTS idx_ai_forecasts_model ON ai_forecasts(model_used);
CREATE INDEX IF NOT EXISTS idx_ai_forecasts_outcome ON ai_forecasts(outcome) WHERE outcome IS NOT NULL;

-- =============================================================================
-- Alerts Table
-- =============================================================================
-- System alerts and notifications
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(100),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(100),
    resolution_notes TEXT
);

-- Indexes for alerts table
CREATE INDEX IF NOT EXISTS idx_alerts_type ON alerts(type);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_acknowledged ON alerts(acknowledged_at) WHERE acknowledged_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_alerts_severity_unack ON alerts(severity, created_at) WHERE acknowledged_at IS NULL;

-- =============================================================================
-- Config History Table
-- =============================================================================
-- Audit log for configuration changes
CREATE TABLE IF NOT EXISTS config_history (
    id SERIAL PRIMARY KEY,
    config JSONB NOT NULL,
    previous_config JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    change_summary TEXT,
    change_type VARCHAR(20) CHECK (change_type IN ('create', 'update', 'rollback')),
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Indexes for config_history table
CREATE INDEX IF NOT EXISTS idx_config_history_changed_at ON config_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_config_history_changed_by ON config_history(changed_by);

-- =============================================================================
-- Helper Functions
-- =============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on positions
DROP TRIGGER IF EXISTS update_positions_updated_at ON positions;
CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate position P&L
CREATE OR REPLACE FUNCTION calculate_position_pnl(
    p_side VARCHAR,
    p_size DECIMAL,
    p_entry_price DECIMAL,
    p_current_price DECIMAL
) RETURNS DECIMAL AS $$
BEGIN
    IF p_side IN ('yes', 'buy') THEN
        RETURN p_size * (p_current_price - p_entry_price);
    ELSE
        RETURN p_size * (p_entry_price - p_current_price);
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================================================
-- Views
-- =============================================================================

-- View for open positions with calculated P&L
CREATE OR REPLACE VIEW open_positions_view AS
SELECT
    p.*,
    calculate_position_pnl(p.side, p.size, p.entry_price, p.current_price) AS calculated_pnl
FROM positions p
WHERE p.status = 'open';

-- View for strategy performance summary
CREATE OR REPLACE VIEW strategy_performance_view AS
SELECT
    strategy,
    COUNT(*) FILTER (WHERE status = 'open') AS open_positions,
    COUNT(*) FILTER (WHERE status = 'closed') AS closed_positions,
    SUM(realized_pnl) FILTER (WHERE status = 'closed') AS total_realized_pnl,
    SUM(unrealized_pnl) FILTER (WHERE status = 'open') AS total_unrealized_pnl,
    AVG(realized_pnl) FILTER (WHERE status = 'closed' AND realized_pnl > 0) AS avg_win,
    AVG(realized_pnl) FILTER (WHERE status = 'closed' AND realized_pnl < 0) AS avg_loss,
    COUNT(*) FILTER (WHERE status = 'closed' AND realized_pnl > 0) AS win_count,
    COUNT(*) FILTER (WHERE status = 'closed' AND realized_pnl < 0) AS loss_count
FROM positions
GROUP BY strategy;

-- View for platform performance summary
CREATE OR REPLACE VIEW platform_performance_view AS
SELECT
    platform,
    COUNT(*) FILTER (WHERE status = 'open') AS open_positions,
    COUNT(*) FILTER (WHERE status = 'closed') AS closed_positions,
    SUM(realized_pnl) FILTER (WHERE status = 'closed') AS total_realized_pnl,
    SUM(unrealized_pnl) FILTER (WHERE status = 'open') AS total_unrealized_pnl,
    COUNT(DISTINCT market_id) AS unique_markets
FROM positions
GROUP BY platform;

-- View for AI forecast accuracy
CREATE OR REPLACE VIEW ai_forecast_accuracy_view AS
SELECT
    model_used,
    platform,
    COUNT(*) AS total_forecasts,
    COUNT(*) FILTER (WHERE outcome IS NOT NULL) AS resolved_forecasts,
    AVG(accuracy_score) FILTER (WHERE accuracy_score IS NOT NULL) AS avg_accuracy,
    AVG(confidence) AS avg_confidence,
    COUNT(*) FILTER (WHERE outcome = TRUE AND predicted_probability > 0.5) +
    COUNT(*) FILTER (WHERE outcome = FALSE AND predicted_probability < 0.5) AS correct_predictions
FROM ai_forecasts
GROUP BY model_used, platform;

-- =============================================================================
-- Data Retention Policies (TimescaleDB)
-- =============================================================================

-- Automatically drop P&L snapshots older than 1 year
SELECT add_retention_policy('pnl_snapshots', INTERVAL '1 year', if_not_exists => TRUE);

-- Compress P&L snapshots older than 7 days
SELECT add_compression_policy('pnl_snapshots', INTERVAL '7 days', if_not_exists => TRUE);

-- =============================================================================
-- Initial Data
-- =============================================================================

-- Insert initial config record
INSERT INTO config_history (config, change_summary, change_type, changed_by)
VALUES (
    '{"version": "1.0.0", "initialized": true}'::jsonb,
    'Initial database setup',
    'create',
    'system'
);

-- =============================================================================
-- Grants (for application user)
-- =============================================================================

-- Grant all privileges on all tables to predictbot user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO predictbot;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO predictbot;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO predictbot;

-- =============================================================================
-- Completion Message
-- =============================================================================
DO $$
BEGIN
    RAISE NOTICE 'PredictBot database initialization completed successfully!';
    RAISE NOTICE 'TimescaleDB extension enabled';
    RAISE NOTICE 'Tables created: positions, trades, pnl_snapshots, ai_forecasts, alerts, config_history';
    RAISE NOTICE 'Hypertable created: pnl_snapshots';
    RAISE NOTICE 'Views created: open_positions_view, strategy_performance_view, platform_performance_view, ai_forecast_accuracy_view';
END $$;
