"""
Audit Logger for PredictBot Stack

Provides comprehensive audit logging for all user actions and system events.
Supports database persistence, querying, and compliance reporting.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import asynccontextmanager

from sqlalchemy import (
    create_engine, Column, String, DateTime, Boolean, Text, JSON,
    Index, select, and_, or_, desc
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import UUID

logger = logging.getLogger(__name__)

Base = declarative_base()


class AuditAction(str, Enum):
    """Enumeration of auditable actions."""
    
    # Authentication
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"
    PASSWORD_CHANGED = "user.password_changed"
    MFA_ENABLED = "user.mfa_enabled"
    MFA_DISABLED = "user.mfa_disabled"
    
    # User Management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ROLE_CHANGED = "user.role_changed"
    
    # Configuration
    CONFIG_VIEWED = "config.viewed"
    CONFIG_UPDATED = "config.updated"
    SECRETS_ACCESSED = "config.secrets_accessed"
    
    # Strategy Management
    STRATEGY_STARTED = "strategy.started"
    STRATEGY_PAUSED = "strategy.paused"
    STRATEGY_STOPPED = "strategy.stopped"
    STRATEGY_CONFIG_UPDATED = "strategy.config_updated"
    STRATEGY_CREATED = "strategy.created"
    STRATEGY_DELETED = "strategy.deleted"
    
    # Trading
    MANUAL_TRADE_EXECUTED = "trade.manual_executed"
    POSITION_MANUALLY_CLOSED = "trade.position_closed"
    ORDER_MANUALLY_CANCELLED = "trade.order_cancelled"
    
    # Risk Management
    RISK_LIMIT_UPDATED = "risk.limit_updated"
    CIRCUIT_BREAKER_RESET = "risk.circuit_breaker_reset"
    EMERGENCY_STOP_TRIGGERED = "risk.emergency_stop"
    EMERGENCY_STOP_CLEARED = "risk.emergency_stop_cleared"
    
    # Alerts
    ALERT_ACKNOWLEDGED = "alert.acknowledged"
    ALERT_RESOLVED = "alert.resolved"
    ALERT_CONFIG_UPDATED = "alert.config_updated"
    
    # System
    SYSTEM_RESTART = "system.restart"
    SERVICE_RESTART = "system.service_restart"
    BACKUP_CREATED = "system.backup_created"
    BACKUP_RESTORED = "system.backup_restored"
    
    # API
    API_KEY_CREATED = "api.key_created"
    API_KEY_REVOKED = "api.key_revoked"
    API_KEY_USED = "api.key_used"
    
    # Data Export
    DATA_EXPORTED = "data.exported"
    REPORT_GENERATED = "data.report_generated"


class AuditLogModel(Base):
    """SQLAlchemy model for audit logs."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(String(100), index=True)
    user_role = Column(String(50))
    username = Column(String(100))
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), index=True)
    resource_id = Column(String(100))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    session_id = Column(String(100))
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    duration_ms = Column(String(20))
    
    __table_args__ = (
        Index("idx_audit_logs_user_action", "user_id", "action"),
        Index("idx_audit_logs_timestamp_action", "timestamp", "action"),
        Index("idx_audit_logs_resource", "resource_type", "resource_id"),
    )


@dataclass
class AuditLog:
    """Audit log entry data structure."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    username: Optional[str] = None
    action: str = ""
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() + "Z" if self.timestamp else None,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "username": self.username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "success": self.success,
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
        }


class AuditLogger:
    """
    Audit logger for tracking all user actions and system events.
    
    Provides database persistence, querying capabilities, and
    compliance reporting features.
    """
    
    def __init__(self, db_url: str, async_mode: bool = True):
        """
        Initialize the audit logger.
        
        Args:
            db_url: Database connection URL
            async_mode: Whether to use async database operations
        """
        self.db_url = db_url
        self.async_mode = async_mode
        
        if async_mode:
            # Convert sync URL to async if needed
            if db_url.startswith("postgresql://"):
                async_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
            else:
                async_url = db_url
            self.engine = create_async_engine(async_url, echo=False)
            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
        else:
            self.engine = create_engine(db_url, echo=False)
            self.Session = sessionmaker(bind=self.engine)
        
        self._initialized = False
    
    async def initialize(self):
        """Initialize the database tables."""
        if self.async_mode:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            Base.metadata.create_all(self.engine)
        self._initialized = True
        logger.info("Audit logger initialized")
    
    async def log_action(
        self,
        action: AuditAction | str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> str:
        """
        Log an auditable action.
        
        Args:
            action: The action being logged
            user_id: ID of the user performing the action
            user_role: Role of the user
            username: Username of the user
            resource_type: Type of resource being acted upon
            resource_id: ID of the resource
            details: Additional details about the action
            ip_address: IP address of the request
            user_agent: User agent string
            session_id: Session identifier
            success: Whether the action was successful
            error_message: Error message if action failed
            duration_ms: Duration of the action in milliseconds
            
        Returns:
            The ID of the created audit log entry
        """
        action_str = action.value if isinstance(action, AuditAction) else action
        
        log_entry = AuditLogModel(
            id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_role=user_role,
            username=username,
            action=action_str,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            success=success,
            error_message=error_message,
            duration_ms=str(duration_ms) if duration_ms else None
        )
        
        if self.async_mode:
            async with self.async_session() as session:
                session.add(log_entry)
                await session.commit()
        else:
            with self.Session() as session:
                session.add(log_entry)
                session.commit()
        
        logger.debug(f"Audit log created: {action_str} by {user_id or 'system'}")
        return str(log_entry.id)
    
    def log_action_sync(
        self,
        action: AuditAction | str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None
    ) -> str:
        """Synchronous version of log_action."""
        action_str = action.value if isinstance(action, AuditAction) else action
        
        log_entry = AuditLogModel(
            id=uuid.uuid4(),
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_role=user_role,
            username=username,
            action=action_str,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            success=success,
            error_message=error_message,
            duration_ms=str(duration_ms) if duration_ms else None
        )
        
        if not self.async_mode:
            with self.Session() as session:
                session.add(log_entry)
                session.commit()
        
        return str(log_entry.id)
    
    async def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditLog]:
        """
        Query audit logs with filters.
        
        Args:
            user_id: Filter by user ID
            action: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_date: Filter by start date
            end_date: Filter by end date
            success_only: Filter by success status
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of matching audit log entries
        """
        conditions = []
        
        if user_id:
            conditions.append(AuditLogModel.user_id == user_id)
        if action:
            conditions.append(AuditLogModel.action == action)
        if resource_type:
            conditions.append(AuditLogModel.resource_type == resource_type)
        if resource_id:
            conditions.append(AuditLogModel.resource_id == resource_id)
        if start_date:
            conditions.append(AuditLogModel.timestamp >= start_date)
        if end_date:
            conditions.append(AuditLogModel.timestamp <= end_date)
        if success_only is not None:
            conditions.append(AuditLogModel.success == success_only)
        
        query = (
            select(AuditLogModel)
            .where(and_(*conditions) if conditions else True)
            .order_by(desc(AuditLogModel.timestamp))
            .limit(limit)
            .offset(offset)
        )
        
        results = []
        
        if self.async_mode:
            async with self.async_session() as session:
                result = await session.execute(query)
                rows = result.scalars().all()
        else:
            with self.Session() as session:
                result = session.execute(query)
                rows = result.scalars().all()
        
        for row in rows:
            results.append(AuditLog(
                id=str(row.id),
                timestamp=row.timestamp,
                user_id=row.user_id,
                user_role=row.user_role,
                username=row.username,
                action=row.action,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                details=row.details or {},
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                session_id=row.session_id,
                success=row.success,
                error_message=row.error_message,
                duration_ms=int(row.duration_ms) if row.duration_ms else None
            ))
        
        return results
    
    async def get_user_activity(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get activity summary for a user.
        
        Args:
            user_id: User ID to get activity for
            days: Number of days to look back
            
        Returns:
            Activity summary dictionary
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        logs = await self.get_audit_trail(
            user_id=user_id,
            start_date=start_date,
            limit=1000
        )
        
        # Aggregate by action
        action_counts: Dict[str, int] = {}
        failed_actions = 0
        
        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
            if not log.success:
                failed_actions += 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(logs),
            "failed_actions": failed_actions,
            "action_breakdown": action_counts,
            "first_activity": logs[-1].timestamp.isoformat() if logs else None,
            "last_activity": logs[0].timestamp.isoformat() if logs else None,
        }
    
    async def get_security_events(
        self,
        days: int = 7
    ) -> List[AuditLog]:
        """
        Get security-related events.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of security-related audit logs
        """
        security_actions = [
            AuditAction.USER_LOGIN_FAILED.value,
            AuditAction.PASSWORD_CHANGED.value,
            AuditAction.MFA_ENABLED.value,
            AuditAction.MFA_DISABLED.value,
            AuditAction.USER_ROLE_CHANGED.value,
            AuditAction.SECRETS_ACCESSED.value,
            AuditAction.EMERGENCY_STOP_TRIGGERED.value,
            AuditAction.API_KEY_CREATED.value,
            AuditAction.API_KEY_REVOKED.value,
        ]
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        conditions = [
            AuditLogModel.timestamp >= start_date,
            AuditLogModel.action.in_(security_actions)
        ]
        
        query = (
            select(AuditLogModel)
            .where(and_(*conditions))
            .order_by(desc(AuditLogModel.timestamp))
            .limit(500)
        )
        
        results = []
        
        if self.async_mode:
            async with self.async_session() as session:
                result = await session.execute(query)
                rows = result.scalars().all()
        else:
            with self.Session() as session:
                result = session.execute(query)
                rows = result.scalars().all()
        
        for row in rows:
            results.append(AuditLog(
                id=str(row.id),
                timestamp=row.timestamp,
                user_id=row.user_id,
                user_role=row.user_role,
                username=row.username,
                action=row.action,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                details=row.details or {},
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                session_id=row.session_id,
                success=row.success,
                error_message=row.error_message,
                duration_ms=int(row.duration_ms) if row.duration_ms else None
            ))
        
        return results
    
    async def export_audit_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> str:
        """
        Export audit logs for compliance reporting.
        
        Args:
            start_date: Start of export period
            end_date: End of export period
            format: Export format (json, csv)
            
        Returns:
            Exported data as string
        """
        logs = await self.get_audit_trail(
            start_date=start_date,
            end_date=end_date,
            limit=10000
        )
        
        if format == "json":
            import json
            return json.dumps([log.to_dict() for log in logs], indent=2)
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].to_dict().keys())
                writer.writeheader()
                for log in logs:
                    writer.writerow(log.to_dict())
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @asynccontextmanager
    async def audit_context(
        self,
        action: AuditAction | str,
        user_id: Optional[str] = None,
        user_role: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Context manager for auditing actions with automatic timing and error handling.
        
        Usage:
            async with audit_logger.audit_context(
                AuditAction.STRATEGY_STARTED,
                user_id="user123",
                resource_type="strategy",
                resource_id="strat456"
            ) as audit:
                # Perform action
                audit.details["result"] = "success"
        """
        start_time = datetime.utcnow()
        audit_data = {
            "details": {},
            "success": True,
            "error_message": None
        }
        
        try:
            yield audit_data
        except Exception as e:
            audit_data["success"] = False
            audit_data["error_message"] = str(e)
            raise
        finally:
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self.log_action(
                action=action,
                user_id=user_id,
                user_role=user_role,
                username=username,
                resource_type=resource_type,
                resource_id=resource_id,
                details=audit_data["details"],
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                success=audit_data["success"],
                error_message=audit_data["error_message"],
                duration_ms=duration_ms
            )


# Factory function
def create_audit_logger(db_url: str, async_mode: bool = True) -> AuditLogger:
    """
    Create an audit logger instance.
    
    Args:
        db_url: Database connection URL
        async_mode: Whether to use async operations
        
    Returns:
        AuditLogger instance
    """
    return AuditLogger(db_url, async_mode)
