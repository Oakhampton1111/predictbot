-- Migration: Create audit_logs table
-- Version: 003
-- Description: Audit logging for compliance and security tracking

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id VARCHAR(100),
    user_role VARCHAR(50),
    username VARCHAR(100),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_id VARCHAR(100),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    duration_ms VARCHAR(20)
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp_action ON audit_logs(timestamp, action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_session ON audit_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_success ON audit_logs(success) WHERE success = false;

-- Create index for JSONB details queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_details ON audit_logs USING GIN (details);

-- Add comments for documentation
COMMENT ON TABLE audit_logs IS 'Audit trail for all user actions and system events';
COMMENT ON COLUMN audit_logs.id IS 'Unique identifier for the audit log entry';
COMMENT ON COLUMN audit_logs.timestamp IS 'When the action occurred';
COMMENT ON COLUMN audit_logs.user_id IS 'ID of the user who performed the action';
COMMENT ON COLUMN audit_logs.user_role IS 'Role of the user at the time of action';
COMMENT ON COLUMN audit_logs.username IS 'Username for display purposes';
COMMENT ON COLUMN audit_logs.action IS 'Type of action performed (e.g., user.login, strategy.started)';
COMMENT ON COLUMN audit_logs.resource_type IS 'Type of resource affected (e.g., strategy, trade, config)';
COMMENT ON COLUMN audit_logs.resource_id IS 'ID of the affected resource';
COMMENT ON COLUMN audit_logs.details IS 'Additional details about the action in JSON format';
COMMENT ON COLUMN audit_logs.ip_address IS 'IP address of the request (IPv4 or IPv6)';
COMMENT ON COLUMN audit_logs.user_agent IS 'User agent string from the request';
COMMENT ON COLUMN audit_logs.session_id IS 'Session identifier for tracking user sessions';
COMMENT ON COLUMN audit_logs.success IS 'Whether the action was successful';
COMMENT ON COLUMN audit_logs.error_message IS 'Error message if the action failed';
COMMENT ON COLUMN audit_logs.duration_ms IS 'Duration of the action in milliseconds';

-- Create a view for recent security events
CREATE OR REPLACE VIEW security_events AS
SELECT 
    id,
    timestamp,
    user_id,
    username,
    action,
    ip_address,
    success,
    error_message,
    details
FROM audit_logs
WHERE action IN (
    'user.login',
    'user.logout',
    'user.login_failed',
    'user.password_changed',
    'user.mfa_enabled',
    'user.mfa_disabled',
    'user.role_changed',
    'config.secrets_accessed',
    'risk.emergency_stop',
    'api.key_created',
    'api.key_revoked'
)
ORDER BY timestamp DESC;

COMMENT ON VIEW security_events IS 'View of security-related audit events for monitoring';

-- Create a view for failed actions
CREATE OR REPLACE VIEW failed_actions AS
SELECT 
    id,
    timestamp,
    user_id,
    username,
    action,
    resource_type,
    resource_id,
    error_message,
    details
FROM audit_logs
WHERE success = false
ORDER BY timestamp DESC;

COMMENT ON VIEW failed_actions IS 'View of all failed actions for troubleshooting';

-- Create a function to clean up old audit logs (retention policy)
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_days INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_audit_logs IS 'Remove audit logs older than specified retention period';

-- Create a function to get user activity summary
CREATE OR REPLACE FUNCTION get_user_activity_summary(
    p_user_id VARCHAR(100),
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    action VARCHAR(100),
    action_count BIGINT,
    last_occurrence TIMESTAMP,
    success_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.action,
        COUNT(*) as action_count,
        MAX(al.timestamp) as last_occurrence,
        ROUND(
            (COUNT(*) FILTER (WHERE al.success = true)::NUMERIC / COUNT(*)::NUMERIC) * 100,
            2
        ) as success_rate
    FROM audit_logs al
    WHERE al.user_id = p_user_id
      AND al.timestamp >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY al.action
    ORDER BY action_count DESC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_activity_summary IS 'Get summary of user activity over specified period';

-- Create partitioning for large-scale deployments (optional, requires PostgreSQL 10+)
-- Uncomment if you expect high volume of audit logs

-- CREATE TABLE audit_logs_partitioned (
--     LIKE audit_logs INCLUDING ALL
-- ) PARTITION BY RANGE (timestamp);

-- CREATE TABLE audit_logs_y2024m01 PARTITION OF audit_logs_partitioned
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Grant permissions (adjust roles as needed)
-- GRANT SELECT ON audit_logs TO readonly_role;
-- GRANT SELECT, INSERT ON audit_logs TO app_role;
-- GRANT ALL ON audit_logs TO admin_role;

-- Record migration
INSERT INTO schema_migrations (version, description, applied_at)
VALUES ('003', 'Create audit_logs table and supporting objects', NOW())
ON CONFLICT (version) DO NOTHING;
