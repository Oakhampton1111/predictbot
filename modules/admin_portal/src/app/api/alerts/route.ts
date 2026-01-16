import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';

// Mock data for development
const mockAlerts = [
  {
    id: 'alert-1',
    type: 'loss_limit',
    severity: 'critical',
    title: 'Daily Loss Limit Approaching',
    message: 'Daily loss has reached 85% of the configured limit ($850 of $1000)',
    timestamp: new Date(Date.now() - 5 * 60 * 1000),
    acknowledged: false,
    metadata: { currentLoss: 850, limit: 1000, percentage: 85 },
  },
  {
    id: 'alert-2',
    type: 'large_trade',
    severity: 'high',
    title: 'Large Trade Executed',
    message: 'Trade of $5,000 executed on Polymarket - "BTC $100k by March"',
    timestamp: new Date(Date.now() - 15 * 60 * 1000),
    acknowledged: false,
    metadata: { platform: 'polymarket', market: 'BTC $100k by March', amount: 5000 },
  },
  {
    id: 'alert-3',
    type: 'ai_confidence',
    severity: 'medium',
    title: 'Low AI Confidence Trade',
    message: 'AI executed trade with only 52% confidence (threshold: 60%)',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    acknowledged: true,
    acknowledgedBy: 'admin',
    acknowledgedAt: new Date(Date.now() - 25 * 60 * 1000),
    metadata: { confidence: 0.52, threshold: 0.6, market: 'Fed Rate Decision' },
  },
  {
    id: 'alert-4',
    type: 'error_rate',
    severity: 'high',
    title: 'High Error Rate Detected',
    message: 'API error rate has exceeded 5% in the last hour (current: 8.5%)',
    timestamp: new Date(Date.now() - 45 * 60 * 1000),
    acknowledged: true,
    acknowledgedBy: 'operator',
    acknowledgedAt: new Date(Date.now() - 40 * 60 * 1000),
    metadata: { errorRate: 0.085, threshold: 0.05, service: 'polymarket-api' },
  },
  {
    id: 'alert-5',
    type: 'system',
    severity: 'low',
    title: 'Service Restarted',
    message: 'AI Orchestrator service was automatically restarted due to memory pressure',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
    acknowledged: true,
    acknowledgedBy: 'system',
    acknowledgedAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
    metadata: { service: 'ai-orchestrator', reason: 'memory_pressure', memoryUsage: 0.95 },
  },
];

const mockAlertRules = [
  {
    id: 'rule-1',
    name: 'Daily Loss Limit',
    description: 'Alert when daily losses approach or exceed the configured limit',
    type: 'loss_limit',
    enabled: true,
    threshold: 1000,
    thresholdUnit: 'USD',
    severity: 'critical',
  },
  {
    id: 'rule-2',
    name: 'Large Trade Alert',
    description: 'Alert when a single trade exceeds the specified amount',
    type: 'large_trade',
    enabled: true,
    threshold: 2500,
    thresholdUnit: 'USD',
    severity: 'high',
  },
  {
    id: 'rule-3',
    name: 'AI Confidence Threshold',
    description: 'Alert when AI executes trades below the confidence threshold',
    type: 'ai_confidence',
    enabled: true,
    threshold: 60,
    thresholdUnit: '%',
    severity: 'medium',
  },
  {
    id: 'rule-4',
    name: 'API Error Rate',
    description: 'Alert when API error rate exceeds the threshold',
    type: 'error_rate',
    enabled: true,
    threshold: 5,
    thresholdUnit: '%',
    severity: 'high',
  },
];

const mockNotificationChannels = [
  {
    id: 'channel-1',
    type: 'email',
    name: 'Email Notifications',
    enabled: true,
    config: {
      smtpHost: 'smtp.gmail.com',
      smtpPort: 587,
      smtpUser: 'alerts@predictbot.com',
      smtpPassword: '',
      recipients: ['admin@predictbot.com'],
    },
  },
  {
    id: 'channel-2',
    type: 'slack',
    name: 'Slack Alerts',
    enabled: true,
    config: {
      webhookUrl: '',
      channel: '#trading-alerts',
    },
  },
  {
    id: 'channel-3',
    type: 'discord',
    name: 'Discord Notifications',
    enabled: false,
    config: {
      webhookUrl: '',
    },
  },
];

export async function GET(request: NextRequest) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type') || 'list';
  const page = parseInt(searchParams.get('page') || '1');
  const limit = parseInt(searchParams.get('limit') || '20');

  try {
    switch (type) {
      case 'list':
        const startIndex = (page - 1) * limit;
        const paginatedAlerts = mockAlerts.slice(startIndex, startIndex + limit);
        return NextResponse.json({
          success: true,
          data: {
            alerts: paginatedAlerts,
            total: mockAlerts.length,
            page,
            pageSize: limit,
            hasMore: startIndex + limit < mockAlerts.length,
          },
        });

      case 'rules':
        return NextResponse.json({
          success: true,
          data: mockAlertRules,
        });

      case 'channels':
        return NextResponse.json({
          success: true,
          data: mockNotificationChannels,
        });

      default:
        return NextResponse.json({ error: 'Invalid type parameter' }, { status: 400 });
    }
  } catch (error) {
    console.error('Alerts API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch alerts data' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action');

  try {
    const body = await request.json();

    switch (action) {
      case 'acknowledge':
        const { alertId } = body;
        // In production, this would update the database
        return NextResponse.json({
          success: true,
          message: `Alert ${alertId} acknowledged`,
        });

      case 'test':
        const { channelId } = body;
        // In production, this would send a test notification
        await new Promise((resolve) => setTimeout(resolve, 1000)); // Simulate delay
        return NextResponse.json({
          success: true,
          message: `Test notification sent to channel ${channelId}`,
        });

      case 'test-rule':
        const { ruleId } = body;
        // In production, this would test the rule
        await new Promise((resolve) => setTimeout(resolve, 500));
        return NextResponse.json({
          success: true,
          message: `Rule ${ruleId} test passed - would trigger alert`,
        });

      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
    }
  } catch (error) {
    console.error('Alerts POST error:', error);
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const type = searchParams.get('type');

  try {
    const body = await request.json();

    switch (type) {
      case 'rules':
        // In production, this would update the database
        return NextResponse.json({
          success: true,
          message: 'Alert rules updated successfully',
          data: body,
        });

      case 'channels':
        // In production, this would update the database
        return NextResponse.json({
          success: true,
          message: 'Notification channels updated successfully',
          data: body,
        });

      default:
        return NextResponse.json({ error: 'Invalid type parameter' }, { status: 400 });
    }
  } catch (error) {
    console.error('Alerts PUT error:', error);
    return NextResponse.json(
      { error: 'Failed to update configuration' },
      { status: 500 }
    );
  }
}
