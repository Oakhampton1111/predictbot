"""
Alert Service for PredictBot Stack

Provides multi-channel alert notifications including email, Slack, and Discord.
Integrates with the event bus for real-time alert distribution.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from .event_bus import AsyncEventBus, EventType, EventPriority
from .event_schemas import AlertSeverity, AlertTriggeredData

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Available notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class Alert:
    """Alert data structure."""
    alert_id: str
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[str] = None
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() + "Z",
            "related_entity_type": self.related_entity_type,
            "related_entity_id": self.related_entity_id,
            "notification_channels": [c.value for c in self.notification_channels],
            "metadata": self.metadata,
            "acknowledged": self.acknowledged,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() + "Z" if self.acknowledged_at else None,
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() + "Z" if self.resolved_at else None,
        }


@dataclass
class RateLimitConfig:
    """Rate limiting configuration for notifications."""
    max_alerts_per_minute: int = 10
    max_alerts_per_hour: int = 100
    cooldown_seconds: int = 60
    dedupe_window_seconds: int = 300


class AlertRateLimiter:
    """Rate limiter to prevent notification spam."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._minute_counts: Dict[str, int] = defaultdict(int)
        self._hour_counts: Dict[str, int] = defaultdict(int)
        self._last_reset_minute: datetime = datetime.utcnow()
        self._last_reset_hour: datetime = datetime.utcnow()
        self._recent_alerts: Dict[str, datetime] = {}
        self._cooldowns: Dict[str, datetime] = {}
    
    def _reset_counters_if_needed(self):
        """Reset counters if time windows have passed."""
        now = datetime.utcnow()
        
        if (now - self._last_reset_minute).total_seconds() >= 60:
            self._minute_counts.clear()
            self._last_reset_minute = now
        
        if (now - self._last_reset_hour).total_seconds() >= 3600:
            self._hour_counts.clear()
            self._last_reset_hour = now
        
        # Clean up old entries
        cutoff = now - timedelta(seconds=self.config.dedupe_window_seconds)
        self._recent_alerts = {
            k: v for k, v in self._recent_alerts.items() if v > cutoff
        }
        self._cooldowns = {
            k: v for k, v in self._cooldowns.items() if v > now
        }
    
    def _get_alert_key(self, alert: Alert) -> str:
        """Generate a key for deduplication."""
        return f"{alert.alert_type}:{alert.source}:{alert.related_entity_id or 'none'}"
    
    def should_send(self, alert: Alert, channel: NotificationChannel) -> bool:
        """
        Check if an alert should be sent based on rate limits.
        
        Args:
            alert: The alert to check
            channel: The notification channel
            
        Returns:
            True if alert should be sent, False if rate limited
        """
        self._reset_counters_if_needed()
        
        channel_key = channel.value
        alert_key = self._get_alert_key(alert)
        now = datetime.utcnow()
        
        # Check cooldown
        if channel_key in self._cooldowns:
            logger.debug(f"Channel {channel_key} is in cooldown")
            return False
        
        # Check deduplication
        if alert_key in self._recent_alerts:
            logger.debug(f"Alert {alert_key} was recently sent")
            return False
        
        # Check minute limit
        if self._minute_counts[channel_key] >= self.config.max_alerts_per_minute:
            logger.warning(f"Minute rate limit reached for {channel_key}")
            self._cooldowns[channel_key] = now + timedelta(seconds=self.config.cooldown_seconds)
            return False
        
        # Check hour limit
        if self._hour_counts[channel_key] >= self.config.max_alerts_per_hour:
            logger.warning(f"Hour rate limit reached for {channel_key}")
            return False
        
        return True
    
    def record_sent(self, alert: Alert, channel: NotificationChannel):
        """Record that an alert was sent."""
        channel_key = channel.value
        alert_key = self._get_alert_key(alert)
        
        self._minute_counts[channel_key] += 1
        self._hour_counts[channel_key] += 1
        self._recent_alerts[alert_key] = datetime.utcnow()


class AlertService:
    """
    Main alert service for managing and sending notifications.
    
    Supports multiple notification channels with rate limiting,
    deduplication, and integration with the event bus.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the alert service.
        
        Args:
            config: Configuration dictionary containing:
                - redis_url: Redis connection URL
                - email_enabled: Whether email notifications are enabled
                - slack_enabled: Whether Slack notifications are enabled
                - discord_enabled: Whether Discord notifications are enabled
                - email_config: Email configuration (smtp_host, smtp_port, etc.)
                - slack_config: Slack configuration (webhook_url)
                - discord_config: Discord configuration (webhook_url)
                - rate_limit: Rate limiting configuration
        """
        self.config = config
        self.redis_url = config.get("redis_url", "redis://localhost:6379")
        
        # Channel enablement
        self.email_enabled = config.get("email_enabled", False)
        self.slack_enabled = config.get("slack_enabled", False)
        self.discord_enabled = config.get("discord_enabled", False)
        self.webhook_enabled = config.get("webhook_enabled", False)
        
        # Channel configurations
        self.email_config = config.get("email_config", {})
        self.slack_config = config.get("slack_config", {})
        self.discord_config = config.get("discord_config", {})
        self.webhook_config = config.get("webhook_config", {})
        
        # Rate limiting
        rate_limit_config = config.get("rate_limit", {})
        self.rate_limiter = AlertRateLimiter(RateLimitConfig(**rate_limit_config))
        
        # Event bus
        self.event_bus: Optional[AsyncEventBus] = None
        
        # Alert storage (in-memory, could be backed by Redis/DB)
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        
        # Notification handlers (lazy loaded)
        self._email_handler = None
        self._slack_handler = None
        self._discord_handler = None
        
        # Severity to channel mapping
        self.severity_channels: Dict[AlertSeverity, List[NotificationChannel]] = {
            AlertSeverity.CRITICAL: [
                NotificationChannel.EMAIL,
                NotificationChannel.SLACK,
                NotificationChannel.DISCORD,
            ],
            AlertSeverity.HIGH: [
                NotificationChannel.SLACK,
                NotificationChannel.DISCORD,
            ],
            AlertSeverity.MEDIUM: [
                NotificationChannel.SLACK,
            ],
            AlertSeverity.LOW: [],
            AlertSeverity.INFO: [],
        }
    
    async def initialize(self):
        """Initialize the alert service and connect to event bus."""
        self.event_bus = AsyncEventBus(self.redis_url, "alert-service")
        await self.event_bus.connect()
        
        # Subscribe to alert events
        await self.event_bus.subscribe(
            EventType.ALERT_TRIGGERED,
            self._handle_alert_triggered
        )
        await self.event_bus.subscribe(
            EventType.ALERT_ACKNOWLEDGED,
            self._handle_alert_acknowledged
        )
        await self.event_bus.subscribe(
            EventType.ALERT_RESOLVED,
            self._handle_alert_resolved
        )
        
        # Subscribe to events that should trigger alerts
        await self.event_bus.subscribe(
            EventType.CIRCUIT_BREAKER_TRIGGERED,
            self._handle_circuit_breaker
        )
        await self.event_bus.subscribe(
            EventType.DAILY_LOSS_LIMIT_REACHED,
            self._handle_daily_loss_limit
        )
        await self.event_bus.subscribe(
            EventType.SERVICE_ERROR,
            self._handle_service_error
        )
        await self.event_bus.subscribe(
            EventType.AI_CONFIDENCE_LOW,
            self._handle_ai_low_confidence
        )
        
        await self.event_bus.start_listening()
        logger.info("Alert service initialized")
    
    async def shutdown(self):
        """Shutdown the alert service."""
        if self.event_bus:
            await self.event_bus.stop_listening()
            await self.event_bus.disconnect()
        logger.info("Alert service shutdown")
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert through all configured channels.
        
        Args:
            alert: The alert to send
            
        Returns:
            True if at least one notification was sent successfully
        """
        # Store alert
        self._active_alerts[alert.alert_id] = alert
        self._alert_history.append(alert)
        
        # Determine channels based on severity if not specified
        channels = alert.notification_channels
        if not channels:
            channels = self.severity_channels.get(alert.severity, [])
        
        # Publish to event bus
        if self.event_bus:
            await self.event_bus.publish(
                EventType.ALERT_TRIGGERED,
                AlertTriggeredData(
                    alert_id=alert.alert_id,
                    alert_type=alert.alert_type,
                    severity=alert.severity,
                    title=alert.title,
                    message=alert.message,
                    source=alert.source,
                    related_entity_type=alert.related_entity_type,
                    related_entity_id=alert.related_entity_id,
                    notification_channels=[c.value for c in channels],
                ).model_dump(),
                priority=self._severity_to_priority(alert.severity)
            )
        
        # Send to each channel
        success = False
        for channel in channels:
            if self.rate_limiter.should_send(alert, channel):
                try:
                    sent = await self._send_to_channel(alert, channel)
                    if sent:
                        self.rate_limiter.record_sent(alert, channel)
                        success = True
                except Exception as e:
                    logger.error(f"Failed to send alert to {channel.value}: {e}")
        
        return success
    
    async def _send_to_channel(self, alert: Alert, channel: NotificationChannel) -> bool:
        """Send alert to a specific channel."""
        if channel == NotificationChannel.EMAIL and self.email_enabled:
            return await self._send_email(alert)
        elif channel == NotificationChannel.SLACK and self.slack_enabled:
            return await self._send_slack(alert)
        elif channel == NotificationChannel.DISCORD and self.discord_enabled:
            return await self._send_discord(alert)
        elif channel == NotificationChannel.WEBHOOK and self.webhook_enabled:
            return await self._send_webhook(alert)
        return False
    
    async def _send_email(self, alert: Alert) -> bool:
        """Send alert via email."""
        try:
            from .notifications.email import EmailNotifier
            
            if self._email_handler is None:
                self._email_handler = EmailNotifier(self.email_config)
            
            return await self._email_handler.send_alert(alert)
        except ImportError:
            logger.error("Email notifier not available")
            return False
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False
    
    async def _send_slack(self, alert: Alert) -> bool:
        """Send alert via Slack."""
        try:
            from .notifications.slack import SlackNotifier
            
            if self._slack_handler is None:
                self._slack_handler = SlackNotifier(self.slack_config)
            
            return await self._slack_handler.send_alert(alert)
        except ImportError:
            logger.error("Slack notifier not available")
            return False
        except Exception as e:
            logger.error(f"Slack notification failed: {e}")
            return False
    
    async def _send_discord(self, alert: Alert) -> bool:
        """Send alert via Discord."""
        try:
            from .notifications.discord import DiscordNotifier
            
            if self._discord_handler is None:
                self._discord_handler = DiscordNotifier(self.discord_config)
            
            return await self._discord_handler.send_alert(alert)
        except ImportError:
            logger.error("Discord notifier not available")
            return False
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
            return False
    
    async def _send_webhook(self, alert: Alert) -> bool:
        """Send alert via generic webhook."""
        try:
            import aiohttp
            
            webhook_url = self.webhook_config.get("url")
            if not webhook_url:
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=alert.to_dict(),
                    headers={"Content-Type": "application/json"}
                ) as response:
                    return response.status < 400
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return False
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        note: Optional[str] = None
    ) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: The alert ID to acknowledge
            acknowledged_by: Who is acknowledging the alert
            note: Optional acknowledgment note
            
        Returns:
            True if alert was acknowledged successfully
        """
        if alert_id not in self._active_alerts:
            logger.warning(f"Alert {alert_id} not found")
            return False
        
        alert = self._active_alerts[alert_id]
        alert.acknowledged = True
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        
        # Publish acknowledgment event
        if self.event_bus:
            await self.event_bus.publish(
                EventType.ALERT_ACKNOWLEDGED,
                {
                    "alert_id": alert_id,
                    "acknowledged_by": acknowledged_by,
                    "acknowledgment_note": note,
                }
            )
        
        logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        return True
    
    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_type: str = "manual",
        note: Optional[str] = None
    ) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: The alert ID to resolve
            resolved_by: Who is resolving the alert
            resolution_type: Type of resolution (manual, auto, timeout)
            note: Optional resolution note
            
        Returns:
            True if alert was resolved successfully
        """
        if alert_id not in self._active_alerts:
            logger.warning(f"Alert {alert_id} not found")
            return False
        
        alert = self._active_alerts[alert_id]
        alert.resolved = True
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.utcnow()
        
        # Calculate duration
        duration = int((alert.resolved_at - alert.timestamp).total_seconds())
        
        # Publish resolution event
        if self.event_bus:
            await self.event_bus.publish(
                EventType.ALERT_RESOLVED,
                {
                    "alert_id": alert_id,
                    "resolved_by": resolved_by,
                    "resolution_type": resolution_type,
                    "resolution_note": note,
                    "duration_seconds": duration,
                }
            )
        
        # Remove from active alerts
        del self._active_alerts[alert_id]
        
        logger.info(f"Alert {alert_id} resolved by {resolved_by}")
        return True
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[str] = None
    ) -> List[Alert]:
        """
        Get list of active (unresolved) alerts.
        
        Args:
            severity: Filter by severity
            alert_type: Filter by alert type
            
        Returns:
            List of active alerts
        """
        alerts = list(self._active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_alert_history(
        self,
        limit: int = 100,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get alert history.
        
        Args:
            limit: Maximum number of alerts to return
            severity: Filter by severity
            
        Returns:
            List of historical alerts
        """
        alerts = self._alert_history
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)[:limit]
    
    def _severity_to_priority(self, severity: AlertSeverity) -> EventPriority:
        """Convert alert severity to event priority."""
        mapping = {
            AlertSeverity.CRITICAL: EventPriority.CRITICAL,
            AlertSeverity.HIGH: EventPriority.HIGH,
            AlertSeverity.MEDIUM: EventPriority.NORMAL,
            AlertSeverity.LOW: EventPriority.LOW,
            AlertSeverity.INFO: EventPriority.LOW,
        }
        return mapping.get(severity, EventPriority.NORMAL)
    
    # Event handlers
    async def _handle_alert_triggered(self, event):
        """Handle incoming alert triggered events."""
        # This is called when other services publish alerts
        logger.debug(f"Alert triggered event received: {event.data}")
    
    async def _handle_alert_acknowledged(self, event):
        """Handle alert acknowledged events."""
        logger.debug(f"Alert acknowledged event received: {event.data}")
    
    async def _handle_alert_resolved(self, event):
        """Handle alert resolved events."""
        logger.debug(f"Alert resolved event received: {event.data}")
    
    async def _handle_circuit_breaker(self, event):
        """Handle circuit breaker triggered events."""
        data = event.data
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            alert_type="circuit_breaker",
            severity=AlertSeverity.CRITICAL,
            title="Circuit Breaker Triggered",
            message=f"Circuit breaker triggered: {data.get('trigger_reason', 'Unknown reason')}",
            source=event.source_service,
            related_entity_type="circuit_breaker",
            related_entity_id=data.get("trigger_id"),
            metadata=data,
        )
        await self.send_alert(alert)
    
    async def _handle_daily_loss_limit(self, event):
        """Handle daily loss limit reached events."""
        data = event.data
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            alert_type="daily_loss_limit",
            severity=AlertSeverity.CRITICAL,
            title="Daily Loss Limit Reached",
            message=f"Daily loss of ${data.get('daily_loss', 0):.2f} has exceeded the limit of ${data.get('daily_limit', 0):.2f}",
            source=event.source_service,
            related_entity_type="risk",
            metadata=data,
        )
        await self.send_alert(alert)
    
    async def _handle_service_error(self, event):
        """Handle service error events."""
        data = event.data
        severity = AlertSeverity.CRITICAL if data.get("is_fatal") else AlertSeverity.HIGH
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            alert_type="service_error",
            severity=severity,
            title=f"Service Error: {data.get('service_name', 'Unknown')}",
            message=data.get("error_message", "Unknown error"),
            source=event.source_service,
            related_entity_type="service",
            related_entity_id=data.get("instance_id"),
            metadata=data,
        )
        await self.send_alert(alert)
    
    async def _handle_ai_low_confidence(self, event):
        """Handle AI low confidence events."""
        data = event.data
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            alert_type="ai_low_confidence",
            severity=AlertSeverity.MEDIUM,
            title="AI Low Confidence Warning",
            message=f"AI confidence ({data.get('confidence', 0):.2%}) below threshold ({data.get('threshold', 0):.2%}): {data.get('reason', 'Unknown')}",
            source=event.source_service,
            related_entity_type="forecast",
            related_entity_id=data.get("forecast_id"),
            metadata=data,
        )
        await self.send_alert(alert)


# Factory function
def create_alert_service(config: Dict[str, Any]) -> AlertService:
    """
    Create an alert service instance.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        AlertService instance
    """
    return AlertService(config)
