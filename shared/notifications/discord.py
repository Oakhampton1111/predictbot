"""
Discord Notification Handler for PredictBot Stack

Provides Discord webhook-based notifications with rich embed formatting.
Supports severity-based colors and structured message layouts.
"""

import asyncio
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Import Alert type for type hints
try:
    from ..alert_service import Alert
    from ..event_schemas import AlertSeverity
except ImportError:
    Alert = Any
    AlertSeverity = Any


class DiscordNotifier:
    """
    Discord notification handler using webhooks.
    
    Supports rich embed formatting with colors, fields,
    and footer information.
    """
    
    # Severity to color mapping (Discord uses decimal colors)
    SEVERITY_COLORS = {
        "critical": 0xdc3545,  # Red
        "high": 0xfd7e14,      # Orange
        "medium": 0xffc107,    # Yellow
        "low": 0x17a2b8,       # Cyan
        "info": 0x6c757d,      # Gray
    }
    
    # Severity to emoji mapping
    SEVERITY_EMOJIS = {
        "critical": "🚨",
        "high": "⚠️",
        "medium": "📢",
        "low": "ℹ️",
        "info": "📝",
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Discord notifier.
        
        Args:
            config: Configuration dictionary containing:
                - webhook_url: Discord webhook URL
                - username: Bot username (optional)
                - avatar_url: Bot avatar URL (optional)
                - mention_roles: List of role IDs to mention for critical alerts
                - mention_users: List of user IDs to mention for critical alerts
                - thread_id: Thread ID to post in (optional)
        """
        self.webhook_url = config.get("webhook_url")
        self.username = config.get("username", "PredictBot Alerts")
        self.avatar_url = config.get("avatar_url")
        self.mention_roles = config.get("mention_roles", [])
        self.mention_users = config.get("mention_users", [])
        self.thread_id = config.get("thread_id")
        self.timeout = config.get("timeout", 10)
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert via Discord webhook.
        
        Args:
            alert: The alert to send
            
        Returns:
            True if message was sent successfully
        """
        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False
        
        try:
            payload = self._build_payload(alert)
            
            # Add thread_id to URL if specified
            url = self.webhook_url
            if self.thread_id:
                url = f"{url}?thread_id={self.thread_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status in (200, 204):
                        logger.info(f"Discord alert sent: {alert.alert_id}")
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"Discord API error: {response.status} - {text}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("Discord webhook request timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            return False
    
    def _build_payload(self, alert: Alert) -> Dict[str, Any]:
        """Build Discord message payload with embeds."""
        severity = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
        color = self.SEVERITY_COLORS.get(severity, 0x6c757d)
        emoji = self.SEVERITY_EMOJIS.get(severity, "📢")
        timestamp = alert.timestamp.isoformat() if isinstance(alert.timestamp, datetime) else str(alert.timestamp)
        
        # Build mention content for critical alerts
        content = ""
        if severity == "critical":
            mentions = []
            for role_id in self.mention_roles:
                mentions.append(f"<@&{role_id}>")
            for user_id in self.mention_users:
                mentions.append(f"<@{user_id}>")
            if mentions:
                content = " ".join(mentions)
        
        # Build embed fields
        fields = [
            {
                "name": "Severity",
                "value": severity.upper(),
                "inline": True
            },
            {
                "name": "Type",
                "value": alert.alert_type,
                "inline": True
            },
            {
                "name": "Source",
                "value": alert.source,
                "inline": True
            }
        ]
        
        # Add related entity info if present
        if alert.related_entity_type:
            fields.append({
                "name": "Entity Type",
                "value": alert.related_entity_type,
                "inline": True
            })
        
        if alert.related_entity_id:
            fields.append({
                "name": "Entity ID",
                "value": f"`{alert.related_entity_id}`",
                "inline": True
            })
        
        # Add metadata fields (limit to avoid hitting Discord limits)
        if alert.metadata:
            for key, value in list(alert.metadata.items())[:6]:
                str_value = str(value)
                if len(str_value) > 200:
                    str_value = str_value[:197] + "..."
                fields.append({
                    "name": key.replace("_", " ").title(),
                    "value": str_value,
                    "inline": True
                })
        
        # Build embed
        embed = {
            "title": f"{emoji} {alert.title}",
            "description": alert.message,
            "color": color,
            "fields": fields,
            "footer": {
                "text": f"Alert ID: {alert.alert_id} | PredictBot Trading System"
            },
            "timestamp": timestamp
        }
        
        # Build payload
        payload = {
            "username": self.username,
            "embeds": [embed]
        }
        
        if content:
            payload["content"] = content
        
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
        
        return payload
    
    async def send_simple_message(
        self,
        text: str,
        severity: str = "info",
        title: Optional[str] = None
    ) -> bool:
        """
        Send a simple text message to Discord.
        
        Args:
            text: Message text
            severity: Message severity for color
            title: Optional title
            
        Returns:
            True if message was sent successfully
        """
        if not self.webhook_url:
            logger.warning("Discord webhook URL not configured")
            return False
        
        color = self.SEVERITY_COLORS.get(severity, 0x6c757d)
        emoji = self.SEVERITY_EMOJIS.get(severity, "📢")
        
        embed = {
            "description": text,
            "color": color,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if title:
            embed["title"] = f"{emoji} {title}"
        
        payload = {
            "username": self.username,
            "embeds": [embed]
        }
        
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
        
        url = self.webhook_url
        if self.thread_id:
            url = f"{url}?thread_id={self.thread_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status in (200, 204)
        except Exception as e:
            logger.error(f"Failed to send Discord message: {e}")
            return False
    
    async def send_trade_notification(
        self,
        trade_type: str,
        market: str,
        side: str,
        quantity: float,
        price: float,
        pnl: Optional[float] = None
    ) -> bool:
        """
        Send a trade notification with formatted details.
        
        Args:
            trade_type: Type of trade (executed, failed, etc.)
            market: Market identifier
            side: Trade side (buy/sell)
            quantity: Trade quantity
            price: Trade price
            pnl: Optional P&L for closed positions
            
        Returns:
            True if message was sent successfully
        """
        if not self.webhook_url:
            return False
        
        # Determine emoji and color based on trade type and P&L
        if trade_type == "executed":
            if pnl is not None:
                emoji = "💰" if pnl >= 0 else "📉"
                color = 0x28a745 if pnl >= 0 else 0xdc3545
            else:
                emoji = "📈" if side.lower() == "buy" else "📉"
                color = 0x17a2b8
        elif trade_type == "failed":
            emoji = "❌"
            color = 0xdc3545
        else:
            emoji = "📊"
            color = 0x6c757d
        
        # Build fields
        fields = [
            {"name": "Market", "value": market, "inline": True},
            {"name": "Side", "value": side.upper(), "inline": True},
            {"name": "Quantity", "value": f"{quantity:,.4f}", "inline": True},
            {"name": "Price", "value": f"${price:,.4f}", "inline": True},
        ]
        
        if pnl is not None:
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"
            fields.append({
                "name": "P&L",
                "value": f"{pnl_emoji} ${pnl:+,.2f}",
                "inline": True
            })
        
        embed = {
            "title": f"{emoji} Trade {trade_type.title()}",
            "color": color,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "PredictBot Trading System"}
        }
        
        payload = {
            "username": self.username,
            "embeds": [embed]
        }
        
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
        
        url = self.webhook_url
        if self.thread_id:
            url = f"{url}?thread_id={self.thread_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status in (200, 204)
        except Exception as e:
            logger.error(f"Failed to send trade notification: {e}")
            return False
    
    async def send_daily_summary(
        self,
        date: str,
        total_trades: int,
        winning_trades: int,
        total_pnl: float,
        win_rate: float,
        best_trade: Optional[Dict[str, Any]] = None,
        worst_trade: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a daily trading summary.
        
        Args:
            date: Summary date
            total_trades: Total number of trades
            winning_trades: Number of winning trades
            total_pnl: Total P&L for the day
            win_rate: Win rate percentage
            best_trade: Best trade details
            worst_trade: Worst trade details
            
        Returns:
            True if message was sent successfully
        """
        if not self.webhook_url:
            return False
        
        pnl_emoji = "📈" if total_pnl >= 0 else "📉"
        color = 0x28a745 if total_pnl >= 0 else 0xdc3545
        
        fields = [
            {"name": "Total Trades", "value": str(total_trades), "inline": True},
            {"name": "Winning Trades", "value": str(winning_trades), "inline": True},
            {"name": "Win Rate", "value": f"{win_rate:.1f}%", "inline": True},
            {"name": "Total P&L", "value": f"{pnl_emoji} ${total_pnl:+,.2f}", "inline": True},
        ]
        
        if best_trade:
            fields.append({
                "name": "🏆 Best Trade",
                "value": f"{best_trade.get('market', 'N/A')}: ${best_trade.get('pnl', 0):+,.2f}",
                "inline": True
            })
        
        if worst_trade:
            fields.append({
                "name": "📉 Worst Trade",
                "value": f"{worst_trade.get('market', 'N/A')}: ${worst_trade.get('pnl', 0):+,.2f}",
                "inline": True
            })
        
        embed = {
            "title": f"📊 Daily Trading Summary - {date}",
            "color": color,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "PredictBot Trading System | Daily Summary"}
        }
        
        payload = {
            "username": self.username,
            "embeds": [embed]
        }
        
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
        
        url = self.webhook_url
        if self.thread_id:
            url = f"{url}?thread_id={self.thread_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status in (200, 204)
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False
    
    async def send_status_update(
        self,
        status: str,
        services: Dict[str, str],
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a system status update.
        
        Args:
            status: Overall system status (healthy, degraded, unhealthy)
            services: Dictionary of service names to their status
            metrics: Optional system metrics
            
        Returns:
            True if message was sent successfully
        """
        if not self.webhook_url:
            return False
        
        # Determine color based on status
        status_colors = {
            "healthy": 0x28a745,
            "degraded": 0xffc107,
            "unhealthy": 0xdc3545
        }
        status_emojis = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }
        
        color = status_colors.get(status.lower(), 0x6c757d)
        emoji = status_emojis.get(status.lower(), "❓")
        
        # Build service status field
        service_lines = []
        for service, svc_status in services.items():
            svc_emoji = status_emojis.get(svc_status.lower(), "❓")
            service_lines.append(f"{svc_emoji} **{service}**: {svc_status}")
        
        fields = [
            {
                "name": "Services",
                "value": "\n".join(service_lines) or "No services",
                "inline": False
            }
        ]
        
        # Add metrics if provided
        if metrics:
            metrics_lines = []
            for key, value in list(metrics.items())[:8]:
                if isinstance(value, float):
                    metrics_lines.append(f"**{key}**: {value:.2f}")
                else:
                    metrics_lines.append(f"**{key}**: {value}")
            
            if metrics_lines:
                fields.append({
                    "name": "Metrics",
                    "value": "\n".join(metrics_lines),
                    "inline": False
                })
        
        embed = {
            "title": f"{emoji} System Status: {status.title()}",
            "color": color,
            "fields": fields,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "PredictBot Trading System | Status Update"}
        }
        
        payload = {
            "username": self.username,
            "embeds": [embed]
        }
        
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
        
        url = self.webhook_url
        if self.thread_id:
            url = f"{url}?thread_id={self.thread_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status in (200, 204)
        except Exception as e:
            logger.error(f"Failed to send status update: {e}")
            return False
