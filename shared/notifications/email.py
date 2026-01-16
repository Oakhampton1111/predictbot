"""
Email Notification Handler for PredictBot Stack

Provides SMTP-based email notifications with HTML templates.
Supports rate limiting and multiple recipients.
"""

import asyncio
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from string import Template

logger = logging.getLogger(__name__)

# Import Alert type for type hints
try:
    from ..alert_service import Alert
    from ..event_schemas import AlertSeverity
except ImportError:
    Alert = Any
    AlertSeverity = Any


class EmailNotifier:
    """
    Email notification handler using SMTP.
    
    Supports HTML templates, multiple recipients, and TLS/SSL.
    """
    
    # Severity to color mapping for email styling
    SEVERITY_COLORS = {
        "critical": "#dc3545",  # Red
        "high": "#fd7e14",      # Orange
        "medium": "#ffc107",    # Yellow
        "low": "#17a2b8",       # Cyan
        "info": "#6c757d",      # Gray
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the email notifier.
        
        Args:
            config: Configuration dictionary containing:
                - smtp_host: SMTP server hostname
                - smtp_port: SMTP server port (default: 587)
                - smtp_user: SMTP username
                - smtp_password: SMTP password
                - use_tls: Whether to use TLS (default: True)
                - use_ssl: Whether to use SSL (default: False)
                - from_email: Sender email address
                - from_name: Sender display name
                - to_emails: List of recipient email addresses
                - cc_emails: List of CC email addresses
                - template_dir: Directory containing email templates
        """
        self.smtp_host = config.get("smtp_host", "localhost")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_user = config.get("smtp_user")
        self.smtp_password = config.get("smtp_password")
        self.use_tls = config.get("use_tls", True)
        self.use_ssl = config.get("use_ssl", False)
        self.from_email = config.get("from_email", "alerts@predictbot.local")
        self.from_name = config.get("from_name", "PredictBot Alerts")
        self.to_emails = config.get("to_emails", [])
        self.cc_emails = config.get("cc_emails", [])
        self.template_dir = Path(config.get("template_dir", "templates"))
        
        # Cache for loaded templates
        self._template_cache: Dict[str, str] = {}
    
    async def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert via email.
        
        Args:
            alert: The alert to send
            
        Returns:
            True if email was sent successfully
        """
        if not self.to_emails:
            logger.warning("No recipient emails configured")
            return False
        
        try:
            # Build email content
            subject = self._build_subject(alert)
            html_body = self._build_html_body(alert)
            text_body = self._build_text_body(alert)
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = ", ".join(self.to_emails)
            if self.cc_emails:
                message["Cc"] = ", ".join(self.cc_emails)
            
            # Attach both plain text and HTML versions
            message.attach(MIMEText(text_body, "plain"))
            message.attach(MIMEText(html_body, "html"))
            
            # Send email in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email, message)
            
            logger.info(f"Email alert sent: {alert.alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
    
    def _send_email(self, message: MIMEMultipart):
        """Send email via SMTP (blocking operation)."""
        all_recipients = self.to_emails + self.cc_emails
        
        if self.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context) as server:
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, all_recipients, message.as_string())
        else:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, all_recipients, message.as_string())
    
    def _build_subject(self, alert: Alert) -> str:
        """Build email subject line."""
        severity = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
        return f"[{severity.upper()}] PredictBot Alert: {alert.title}"
    
    def _build_text_body(self, alert: Alert) -> str:
        """Build plain text email body."""
        severity = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
        timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(alert.timestamp, datetime) else str(alert.timestamp)
        
        lines = [
            f"PredictBot Alert",
            f"=" * 50,
            f"",
            f"Alert ID: {alert.alert_id}",
            f"Severity: {severity.upper()}",
            f"Type: {alert.alert_type}",
            f"Time: {timestamp}",
            f"Source: {alert.source}",
            f"",
            f"Title: {alert.title}",
            f"",
            f"Message:",
            f"{alert.message}",
            f"",
        ]
        
        if alert.related_entity_type:
            lines.append(f"Related Entity: {alert.related_entity_type}")
        if alert.related_entity_id:
            lines.append(f"Entity ID: {alert.related_entity_id}")
        
        if alert.metadata:
            lines.append("")
            lines.append("Additional Details:")
            for key, value in alert.metadata.items():
                lines.append(f"  {key}: {value}")
        
        lines.extend([
            "",
            "-" * 50,
            "This is an automated alert from PredictBot.",
            "Do not reply to this email.",
        ])
        
        return "\n".join(lines)
    
    def _build_html_body(self, alert: Alert) -> str:
        """Build HTML email body."""
        severity = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
        color = self.SEVERITY_COLORS.get(severity, "#6c757d")
        timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(alert.timestamp, datetime) else str(alert.timestamp)
        
        # Try to load template for specific alert type
        template = self._load_template(alert.alert_type)
        if template:
            return self._render_template(template, alert)
        
        # Default HTML template
        metadata_html = ""
        if alert.metadata:
            metadata_rows = "".join([
                f"<tr><td style='padding: 8px; border-bottom: 1px solid #eee;'><strong>{k}</strong></td>"
                f"<td style='padding: 8px; border-bottom: 1px solid #eee;'>{v}</td></tr>"
                for k, v in alert.metadata.items()
            ])
            metadata_html = f"""
            <h3 style="color: #333; margin-top: 20px;">Additional Details</h3>
            <table style="width: 100%; border-collapse: collapse;">
                {metadata_rows}
            </table>
            """
        
        entity_html = ""
        if alert.related_entity_type or alert.related_entity_id:
            entity_html = f"""
            <p style="color: #666; font-size: 14px;">
                Related: {alert.related_entity_type or 'N/A'} 
                {f'(ID: {alert.related_entity_id})' if alert.related_entity_id else ''}
            </p>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">⚠️ PredictBot Alert</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">{severity.upper()} - {alert.alert_type}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border: 1px solid #dee2e6; border-top: none;">
                <table style="width: 100%; font-size: 14px;">
                    <tr>
                        <td style="padding: 5px 0;"><strong>Alert ID:</strong></td>
                        <td style="padding: 5px 0;">{alert.alert_id}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>Time:</strong></td>
                        <td style="padding: 5px 0;">{timestamp}</td>
                    </tr>
                    <tr>
                        <td style="padding: 5px 0;"><strong>Source:</strong></td>
                        <td style="padding: 5px 0;">{alert.source}</td>
                    </tr>
                </table>
            </div>
            
            <div style="background: white; padding: 20px; border: 1px solid #dee2e6; border-top: none; border-radius: 0 0 8px 8px;">
                <h2 style="color: #333; margin-top: 0;">{alert.title}</h2>
                <p style="color: #555; font-size: 16px;">{alert.message}</p>
                {entity_html}
                {metadata_html}
            </div>
            
            <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
                <p>This is an automated alert from PredictBot Trading System.</p>
                <p>Do not reply to this email.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _load_template(self, alert_type: str) -> Optional[str]:
        """Load HTML template for alert type."""
        if alert_type in self._template_cache:
            return self._template_cache[alert_type]
        
        # Convert alert type to filename
        filename = f"{alert_type.replace('.', '_')}.html"
        template_path = self.template_dir / filename
        
        if template_path.exists():
            try:
                template = template_path.read_text()
                self._template_cache[alert_type] = template
                return template
            except Exception as e:
                logger.warning(f"Failed to load template {filename}: {e}")
        
        return None
    
    def _render_template(self, template: str, alert: Alert) -> str:
        """Render template with alert data."""
        severity = alert.severity.value if hasattr(alert.severity, 'value') else str(alert.severity)
        timestamp = alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(alert.timestamp, datetime) else str(alert.timestamp)
        
        # Build metadata string
        metadata_str = ""
        if alert.metadata:
            metadata_str = "<br>".join([f"<strong>{k}:</strong> {v}" for k, v in alert.metadata.items()])
        
        # Template variables
        variables = {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type,
            "severity": severity,
            "severity_upper": severity.upper(),
            "severity_color": self.SEVERITY_COLORS.get(severity, "#6c757d"),
            "title": alert.title,
            "message": alert.message,
            "source": alert.source,
            "timestamp": timestamp,
            "related_entity_type": alert.related_entity_type or "",
            "related_entity_id": alert.related_entity_id or "",
            "metadata": metadata_str,
        }
        
        # Add all metadata items as individual variables
        if alert.metadata:
            for key, value in alert.metadata.items():
                variables[f"meta_{key}"] = value
        
        try:
            return Template(template).safe_substitute(variables)
        except Exception as e:
            logger.warning(f"Template rendering failed: {e}")
            return self._build_html_body(alert)
    
    async def send_test_email(self) -> bool:
        """Send a test email to verify configuration."""
        from dataclasses import dataclass
        
        @dataclass
        class TestAlert:
            alert_id: str = "test-001"
            alert_type: str = "test"
            severity: str = "info"
            title: str = "Test Alert"
            message: str = "This is a test alert to verify email configuration."
            source: str = "email-notifier"
            timestamp: datetime = None
            related_entity_type: str = None
            related_entity_id: str = None
            metadata: dict = None
            
            def __post_init__(self):
                if self.timestamp is None:
                    self.timestamp = datetime.utcnow()
                if self.metadata is None:
                    self.metadata = {"test_key": "test_value"}
        
        test_alert = TestAlert()
        return await self.send_alert(test_alert)
