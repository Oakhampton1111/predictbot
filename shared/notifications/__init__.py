"""
Notification handlers for PredictBot Stack.

Provides email, Slack, Discord, and webhook notification capabilities.
"""

from .email import EmailNotifier
from .slack import SlackNotifier
from .discord import DiscordNotifier

__all__ = ["EmailNotifier", "SlackNotifier", "DiscordNotifier"]
