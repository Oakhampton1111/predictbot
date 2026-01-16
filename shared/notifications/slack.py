"""
Slack Notification Handler for PredictBot Stack

Provides Slack webhook-based notifications with rich message formatting.
Uses Slack Block Kit for structured, interactive messages.
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


class SlackNotifier:
    """
    Slack notification handler using webhooks.
    
    Supports rich message formatting with Block Kit,
    severity-based colors, and action buttons.
    """
    
    # Severity to color mapping (Slack uses hex colors)
    SEVERITY_COLORS = {
        "critical": "#dc3545",  # Red
        "high": "#fd7e14",      # Orange
        "medium": "#ffc107",    # Yellow
        "low": "#17a2b8",       # Cyan
        "info": "#6c757d",      # Gray
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
        Initialize the Slack notifier.
        
        Args:
            config: Configuration dictionary containing:
                - webhook_url: Slack webhook URL
                - channel: Override channel (optional)
                - username: Bot username (optional)
                - icon_emoji: Bot icon emoji (optional)
                - mention_users: List of user IDs to mention for critical alerts
                - mention_channel: Whether to @channel for critical alerts
        """
        self.webhook_url = config.get("webhook_url")
        self.channel = config.get("channel")
        self.username = config.get("username", "PredictBot Alerts")
        self.icon_emoji = config.get("icon_emoji", ":robot_face:")
        self.mention_users = config.get("mention_users", [])
        self.mention_channel = config.get("mention_channel", False)
        self.timeout = config.get("timeout", 10)
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert via Slack webhook.
        
        Args:
            alert: The alert to send
            
        Returns:
            True if message was sent successfully
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        try:
            payload = self._build_payload(alert)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack alert sent: {alert.alert_id}")
                        return True
                    else:
                        text = await response.text()
                        logger.error(f"Slack API error: {response.status} - {text}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("Slack webhook request timed out")
            return False
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def _build_payload(self, alert: Alert) -> Dict[str, Any]:
        """Build Slack message payload with Block Kit."""
        severity = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
        color = self.SEVERITY_COLORS.get(severity, "#6c757d")
        emoji = self.SEVERITY_EMOJIS.get(severity, "📢")
        timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(alert.timestamp, datetime) else str(alert.timestamp)
        
        # Build mention text for critical alerts
        mention_text = ""
        if severity == "critical":
            if self.mention_channel:
                mention_text = "<!channel> "
            elif self.mention_users:
                mentions = " ".join([f"<@{uid}>" for uid in self.mention_users])
                mention_text = f"{mentions} "
        
        # Build blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {alert.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{mention_text}{alert.message}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{severity.upper()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{alert.alert_type}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:*\n{alert.source}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{timestamp}"
                    }
                ]
            }
        ]
        
        # Add related entity info if present
        if alert.related_entity_type or alert.related_entity_id:
            entity_text = []
            if alert.related_entity_type:
                entity_text.append(f"*Entity Type:* {alert.related_entity_type}")
            if alert.related_entity_id:
                entity_text.append(f"*Entity ID:* `{alert.related_entity_id}`")
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": " | ".join(entity_text)
                }
            })
        
        # Add metadata if present
        if alert.metadata:
            metadata_lines = []
            for key, value in list(alert.metadata.items())[:10]:  # Limit to 10 items
                # Truncate long values
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."
                metadata_lines.append(f"• *{key}:* {str_value}")
            
            if metadata_lines:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Additional Details:*\n" + "\n".join(metadata_lines)
                    }
                })
        
        # Add context footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Alert ID: `{alert.alert_id}` | PredictBot Trading System"
                }
            ]
        })
        
        # Build payload
        payload = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": blocks,
            "attachments": [
                {
                    "color": color,
                    "fallback": f"[{severity.upper()}] {alert.title}: {alert.message}"
                }
            ]
        }
        
        if self.channel:
            payload["channel"] = self.channel
        
        return payload
    
    async def send_simple_message(
        self,
        text: str,
        severity: str = "info",
        title: Optional[str] = None
    ) -> bool:
        """
        Send a simple text message to Slack.
        
        Args:
            text: Message text
            severity: Message severity for color
            title: Optional title
            
        Returns:
            True if message was sent successfully
        """
        if not self.webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False
        
        color = self.SEVERITY_COLORS.get(severity, "#6c757d")
        emoji = self.SEVERITY_EMOJIS.get(severity, "📢")
        
        blocks = []
        
        if title:
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True
                }
            })
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        })
        
        payload = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": blocks,
            "attachments": [{"color": color}]
        }
        
        if self.channel:
            payload["channel"] = self.channel
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
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
                color = "#28a745" if pnl >= 0 else "#dc3545"
            else:
                emoji = "📈" if side.lower() == "buy" else "📉"
                color = "#17a2b8"
        elif trade_type == "failed":
            emoji = "❌"
            color = "#dc3545"
        else:
            emoji = "📊"
            color = "#6c757d"
        
        # Build fields
        fields = [
            {"type": "mrkdwn", "text": f"*Market:*\n{market}"},
            {"type": "mrkdwn", "text": f"*Side:*\n{side.upper()}"},
            {"type": "mrkdwn", "text": f"*Quantity:*\n{quantity:,.4f}"},
            {"type": "mrkdwn", "text": f"*Price:*\n${price:,.4f}"},
        ]
        
        if pnl is not None:
            pnl_emoji = "🟢" if pnl >= 0 else "🔴"
            fields.append({
                "type": "mrkdwn",
                "text": f"*P&L:*\n{pnl_emoji} ${pnl:+,.2f}"
            })
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Trade {trade_type.title()}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": fields
            }
        ]
        
        payload = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": blocks,
            "attachments": [{"color": color}]
        }
        
        if self.channel:
            payload["channel"] = self.channel
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status == 200
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
        color = "#28a745" if total_pnl >= 0 else "#dc3545"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Daily Trading Summary - {date}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Total Trades:*\n{total_trades}"},
                    {"type": "mrkdwn", "text": f"*Winning Trades:*\n{winning_trades}"},
                    {"type": "mrkdwn", "text": f"*Win Rate:*\n{win_rate:.1f}%"},
                    {"type": "mrkdwn", "text": f"*Total P&L:*\n{pnl_emoji} ${total_pnl:+,.2f}"},
                ]
            }
        ]
        
        if best_trade:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🏆 *Best Trade:* {best_trade.get('market', 'N/A')} - ${best_trade.get('pnl', 0):+,.2f}"
                }
            })
        
        if worst_trade:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📉 *Worst Trade:* {worst_trade.get('market', 'N/A')} - ${worst_trade.get('pnl', 0):+,.2f}"
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "PredictBot Trading System | Daily Summary"
                }
            ]
        })
        
        payload = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "blocks": blocks,
            "attachments": [{"color": color}]
        }
        
        if self.channel:
            payload["channel"] = self.channel
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send daily summary: {e}")
            return False
