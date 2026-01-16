#!/usr/bin/env python3
"""
Integration Test Script for PredictBot Stack

Tests the integration between all services including:
- Event bus connectivity
- Alert notifications
- WebSocket updates
- Audit logging
"""

import os
import sys
import asyncio
import json
import time
import uuid
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")


def print_test(name: str, passed: bool, message: str = ""):
    """Print test result."""
    status = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if passed else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    print(f"  {status} {name}")
    if message:
        print(f"         {Colors.YELLOW}{message}{Colors.RESET}")


def print_info(message: str):
    """Print info message."""
    print(f"  {Colors.BLUE}ℹ{Colors.RESET} {message}")


class IntegrationTester:
    """Integration test runner."""
    
    def __init__(self, redis_url: str, db_url: str):
        self.redis_url = redis_url
        self.db_url = db_url
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []
    
    async def run_all_tests(self) -> bool:
        """Run all integration tests."""
        print_header("PredictBot Integration Tests")
        print(f"Redis URL: {self.redis_url}")
        print(f"Database URL: {self.db_url[:50]}...")
        print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
        
        # Test categories
        await self.test_redis_connectivity()
        await self.test_event_bus()
        await self.test_event_publishing()
        await self.test_event_subscription()
        await self.test_alert_service()
        await self.test_audit_logger()
        await self.test_websocket_manager()
        
        # Print summary
        self.print_summary()
        
        return all(self.results.values())
    
    async def test_redis_connectivity(self):
        """Test Redis connectivity."""
        print_header("Redis Connectivity")
        
        try:
            import redis.asyncio as aioredis
            
            client = await aioredis.from_url(self.redis_url)
            
            # Test ping
            pong = await client.ping()
            self.results['redis_ping'] = pong
            print_test("Redis PING", pong)
            
            # Test set/get
            test_key = f"test:integration:{uuid.uuid4()}"
            test_value = "test_value"
            await client.set(test_key, test_value, ex=60)
            result = await client.get(test_key)
            success = result.decode() == test_value if result else False
            self.results['redis_set_get'] = success
            print_test("Redis SET/GET", success)
            
            # Cleanup
            await client.delete(test_key)
            await client.close()
            
        except Exception as e:
            self.results['redis_connectivity'] = False
            print_test("Redis connectivity", False, str(e))
            self.errors.append(f"Redis: {e}")
    
    async def test_event_bus(self):
        """Test event bus initialization."""
        print_header("Event Bus")
        
        try:
            from shared.event_bus import AsyncEventBus, EventType, EventPriority
            
            # Test async event bus creation
            event_bus = AsyncEventBus(self.redis_url, "test-service")
            connected = await event_bus.connect()
            self.results['event_bus_connect'] = connected
            print_test("Event bus connection", connected)
            
            if connected:
                await event_bus.disconnect()
            
            # Test event types exist
            event_types_exist = hasattr(EventType, 'TRADE_EXECUTED')
            self.results['event_types'] = event_types_exist
            print_test("Event types defined", event_types_exist)
            
            # Test priority levels
            priorities_exist = hasattr(EventPriority, 'CRITICAL')
            self.results['event_priorities'] = priorities_exist
            print_test("Event priorities defined", priorities_exist)
            
        except ImportError as e:
            self.results['event_bus_import'] = False
            print_test("Event bus import", False, str(e))
            self.errors.append(f"Event bus import: {e}")
        except Exception as e:
            self.results['event_bus'] = False
            print_test("Event bus", False, str(e))
            self.errors.append(f"Event bus: {e}")
    
    async def test_event_publishing(self):
        """Test event publishing."""
        print_header("Event Publishing")
        
        try:
            from shared.event_bus import AsyncEventBus, EventType, EventPriority
            
            event_bus = AsyncEventBus(self.redis_url, "test-publisher")
            await event_bus.connect()
            
            # Test publishing different event types
            test_events = [
                (EventType.SERVICE_STARTED, {"service_name": "test", "service_version": "1.0.0", "instance_id": "test-1", "host": "localhost", "port": 8080}),
                (EventType.TRADE_EXECUTED, {"trade_id": "test-trade", "strategy_id": "test-strat", "market_id": "test-market", "platform": "test", "side": "buy", "quantity": 1.0, "price": 0.5, "total_value": 0.5}),
                (EventType.AI_CYCLE_STARTED, {"cycle_id": "test-cycle", "cycle_number": 1, "agents_active": ["test"], "markets_analyzed": 0}),
            ]
            
            for event_type, data in test_events:
                success = await event_bus.publish(event_type, data, priority=EventPriority.NORMAL)
                self.results[f'publish_{event_type.value}'] = success
                print_test(f"Publish {event_type.value}", success)
            
            await event_bus.disconnect()
            
        except Exception as e:
            self.results['event_publishing'] = False
            print_test("Event publishing", False, str(e))
            self.errors.append(f"Event publishing: {e}")
    
    async def test_event_subscription(self):
        """Test event subscription."""
        print_header("Event Subscription")
        
        try:
            from shared.event_bus import AsyncEventBus, EventType, EventPriority
            
            received_events = []
            
            async def handler(event):
                received_events.append(event)
            
            # Create subscriber
            subscriber = AsyncEventBus(self.redis_url, "test-subscriber")
            await subscriber.connect()
            await subscriber.subscribe(EventType.SERVICE_HEALTH_CHECK, handler)
            await subscriber.start_listening()
            
            # Create publisher
            publisher = AsyncEventBus(self.redis_url, "test-publisher-2")
            await publisher.connect()
            
            # Publish test event
            test_data = {
                "service_name": "test",
                "instance_id": "test-1",
                "status": "healthy",
                "checks": {},
                "metrics": {},
                "uptime_seconds": 100
            }
            await publisher.publish(EventType.SERVICE_HEALTH_CHECK, test_data)
            
            # Wait for event to be received
            await asyncio.sleep(1)
            
            success = len(received_events) > 0
            self.results['event_subscription'] = success
            print_test("Event subscription", success, f"Received {len(received_events)} events")
            
            await subscriber.stop_listening()
            await subscriber.disconnect()
            await publisher.disconnect()
            
        except Exception as e:
            self.results['event_subscription'] = False
            print_test("Event subscription", False, str(e))
            self.errors.append(f"Event subscription: {e}")
    
    async def test_alert_service(self):
        """Test alert service."""
        print_header("Alert Service")
        
        try:
            from shared.alert_service import AlertService, Alert, NotificationChannel
            from shared.event_schemas import AlertSeverity
            
            # Create alert service (without actual notification channels)
            config = {
                "redis_url": self.redis_url,
                "email_enabled": False,
                "slack_enabled": False,
                "discord_enabled": False,
            }
            
            alert_service = AlertService(config)
            self.results['alert_service_create'] = True
            print_test("Alert service creation", True)
            
            # Test alert creation
            alert = Alert(
                alert_id=str(uuid.uuid4()),
                alert_type="test",
                severity=AlertSeverity.INFO,
                title="Test Alert",
                message="This is a test alert",
                source="integration-test"
            )
            
            alert_dict = alert.to_dict()
            self.results['alert_creation'] = 'alert_id' in alert_dict
            print_test("Alert creation", 'alert_id' in alert_dict)
            
            # Test rate limiter
            from shared.alert_service import AlertRateLimiter, RateLimitConfig
            
            rate_limiter = AlertRateLimiter(RateLimitConfig())
            should_send = rate_limiter.should_send(alert, NotificationChannel.SLACK)
            self.results['rate_limiter'] = should_send
            print_test("Rate limiter", should_send)
            
        except ImportError as e:
            self.results['alert_service_import'] = False
            print_test("Alert service import", False, str(e))
            self.errors.append(f"Alert service import: {e}")
        except Exception as e:
            self.results['alert_service'] = False
            print_test("Alert service", False, str(e))
            self.errors.append(f"Alert service: {e}")
    
    async def test_audit_logger(self):
        """Test audit logger."""
        print_header("Audit Logger")
        
        try:
            from shared.audit_logger import AuditLogger, AuditAction, AuditLog
            
            # Test audit action enum
            actions_exist = hasattr(AuditAction, 'USER_LOGIN')
            self.results['audit_actions'] = actions_exist
            print_test("Audit actions defined", actions_exist)
            
            # Test audit log dataclass
            log = AuditLog(
                action=AuditAction.USER_LOGIN.value,
                user_id="test-user",
                username="testuser",
                ip_address="127.0.0.1"
            )
            log_dict = log.to_dict()
            self.results['audit_log_creation'] = 'action' in log_dict
            print_test("Audit log creation", 'action' in log_dict)
            
            # Note: Full database test would require PostgreSQL
            print_info("Database tests skipped (requires PostgreSQL)")
            
        except ImportError as e:
            self.results['audit_logger_import'] = False
            print_test("Audit logger import", False, str(e))
            self.errors.append(f"Audit logger import: {e}")
        except Exception as e:
            self.results['audit_logger'] = False
            print_test("Audit logger", False, str(e))
            self.errors.append(f"Audit logger: {e}")
    
    async def test_websocket_manager(self):
        """Test WebSocket manager."""
        print_header("WebSocket Manager")
        
        try:
            from shared.websocket_server import (
                WebSocketManager, WebSocketClient, MessageType,
                SubscriptionChannel, EventBusWebSocketBridge
            )
            
            # Test manager creation
            manager = WebSocketManager(require_auth=False)
            self.results['ws_manager_create'] = True
            print_test("WebSocket manager creation", True)
            
            # Test message types
            msg_types_exist = hasattr(MessageType, 'SUBSCRIBE')
            self.results['ws_message_types'] = msg_types_exist
            print_test("Message types defined", msg_types_exist)
            
            # Test subscription channels
            channels_exist = hasattr(SubscriptionChannel, 'TRADES')
            self.results['ws_channels'] = channels_exist
            print_test("Subscription channels defined", channels_exist)
            
            # Test bridge creation
            bridge = EventBusWebSocketBridge(manager)
            self.results['ws_bridge_create'] = True
            print_test("Event bus bridge creation", True)
            
            # Test stats
            stats = manager.get_stats()
            self.results['ws_stats'] = 'total_connections' in stats
            print_test("WebSocket stats", 'total_connections' in stats)
            
        except ImportError as e:
            self.results['websocket_import'] = False
            print_test("WebSocket import", False, str(e))
            self.errors.append(f"WebSocket import: {e}")
        except Exception as e:
            self.results['websocket'] = False
            print_test("WebSocket", False, str(e))
            self.errors.append(f"WebSocket: {e}")
    
    def print_summary(self):
        """Print test summary."""
        print_header("Test Summary")
        
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        failed = total - passed
        
        print(f"  Total tests: {total}")
        print(f"  {Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"  {Colors.RED}Failed: {failed}{Colors.RESET}")
        
        if self.errors:
            print(f"\n  {Colors.RED}Errors:{Colors.RESET}")
            for error in self.errors:
                print(f"    - {error}")
        
        if failed == 0:
            print(f"\n  {Colors.GREEN}{Colors.BOLD}All tests passed!{Colors.RESET}")
        else:
            print(f"\n  {Colors.RED}{Colors.BOLD}Some tests failed.{Colors.RESET}")


async def test_notification_channels(config: Dict[str, Any]):
    """Test notification channels (optional)."""
    print_header("Notification Channels (Optional)")
    
    # Test Slack
    if config.get('slack_webhook_url'):
        try:
            from shared.notifications.slack import SlackNotifier
            
            notifier = SlackNotifier({
                "webhook_url": config['slack_webhook_url']
            })
            
            success = await notifier.send_simple_message(
                "Integration test message from PredictBot",
                severity="info",
                title="Integration Test"
            )
            print_test("Slack notification", success)
        except Exception as e:
            print_test("Slack notification", False, str(e))
    else:
        print_info("Slack webhook not configured, skipping")
    
    # Test Discord
    if config.get('discord_webhook_url'):
        try:
            from shared.notifications.discord import DiscordNotifier
            
            notifier = DiscordNotifier({
                "webhook_url": config['discord_webhook_url']
            })
            
            success = await notifier.send_simple_message(
                "Integration test message from PredictBot",
                severity="info",
                title="Integration Test"
            )
            print_test("Discord notification", success)
        except Exception as e:
            print_test("Discord notification", False, str(e))
    else:
        print_info("Discord webhook not configured, skipping")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="PredictBot Integration Tests")
    parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL", "redis://localhost:6379"),
        help="Redis connection URL"
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", "postgresql://predictbot:predictbot@localhost:5432/predictbot"),
        help="Database connection URL"
    )
    parser.add_argument(
        "--slack-webhook",
        default=os.getenv("SLACK_WEBHOOK_URL"),
        help="Slack webhook URL for notification test"
    )
    parser.add_argument(
        "--discord-webhook",
        default=os.getenv("DISCORD_WEBHOOK_URL"),
        help="Discord webhook URL for notification test"
    )
    parser.add_argument(
        "--test-notifications",
        action="store_true",
        help="Test notification channels"
    )
    
    args = parser.parse_args()
    
    # Run tests
    tester = IntegrationTester(args.redis_url, args.db_url)
    
    async def run():
        success = await tester.run_all_tests()
        
        if args.test_notifications:
            await test_notification_channels({
                "slack_webhook_url": args.slack_webhook,
                "discord_webhook_url": args.discord_webhook,
            })
        
        return success
    
    success = asyncio.run(run())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
