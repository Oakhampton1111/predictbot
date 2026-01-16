import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';

// Mock service data for development
const services = [
  { id: 'orchestrator', name: 'Orchestrator', type: 'core' },
  { id: 'ai-orchestrator', name: 'AI Orchestrator', type: 'core' },
  { id: 'polymarket-arb', name: 'Polymarket Arbitrage', type: 'strategy' },
  { id: 'polymarket-mm', name: 'Polymarket Market Making', type: 'strategy' },
  { id: 'polymarket-spike', name: 'Polymarket Spike Detection', type: 'strategy' },
  { id: 'kalshi-ai', name: 'Kalshi AI', type: 'strategy' },
  { id: 'manifold-mm', name: 'Manifold Market Making', type: 'strategy' },
  { id: 'mcp-server', name: 'MCP Server', type: 'infrastructure' },
  { id: 'polyseer', name: 'Polyseer', type: 'data' },
  { id: 'postgresql', name: 'PostgreSQL', type: 'database' },
  { id: 'redis', name: 'Redis', type: 'database' },
  { id: 'ollama', name: 'Ollama', type: 'ai' },
];

function generateServiceStatus(serviceId: string) {
  // Simulate different statuses with weighted randomness
  const rand = Math.random();
  let status: 'running' | 'degraded' | 'down' | 'unknown';
  
  if (rand < 0.85) {
    status = 'running';
  } else if (rand < 0.95) {
    status = 'degraded';
  } else if (rand < 0.98) {
    status = 'down';
  } else {
    status = 'unknown';
  }

  const service = services.find((s) => s.id === serviceId);
  
  return {
    id: serviceId,
    name: service?.name || serviceId,
    status,
    lastHeartbeat: new Date(Date.now() - Math.random() * 60000),
    latency: Math.floor(Math.random() * 200) + 10,
    version: '1.0.0',
    uptime: Math.floor(Math.random() * 86400 * 7), // Up to 7 days in seconds
    cpu: Math.random() * 60 + (status === 'degraded' ? 30 : 0),
    memory: Math.random() * 50 + (status === 'degraded' ? 40 : 10),
    errors: status === 'running' ? Math.floor(Math.random() * 5) : Math.floor(Math.random() * 50),
    details: {
      type: service?.type,
      host: `${serviceId}.internal`,
      port: 8000 + Math.floor(Math.random() * 100),
      healthEndpoint: `/health`,
      lastError: status !== 'running' ? 'Connection timeout' : null,
    },
  };
}

function generateResourceHistory(points: number) {
  const data = [];
  const now = Date.now();
  
  for (let i = points; i >= 0; i--) {
    const time = new Date(now - i * 60000); // 1 minute intervals
    data.push({
      time: time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      cpu: 30 + Math.random() * 40 + Math.sin(i / 10) * 10,
      memory: 40 + Math.random() * 30 + Math.cos(i / 10) * 5,
      disk: 55 + Math.random() * 5,
      network: Math.random() * 100,
    });
  }
  
  return data;
}

export async function GET(request: NextRequest) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const serviceId = searchParams.get('service');

  try {
    if (serviceId) {
      // Return detailed info for a specific service
      const serviceStatus = generateServiceStatus(serviceId);
      return NextResponse.json({
        success: true,
        data: serviceStatus,
      });
    }

    // Return all services status
    const servicesStatus = services.map((s) => generateServiceStatus(s.id));
    const resourceHistory = generateResourceHistory(30);
    const currentResources = resourceHistory[resourceHistory.length - 1];

    return NextResponse.json({
      success: true,
      data: {
        services: servicesStatus,
        resources: {
          history: resourceHistory,
          current: {
            cpu: currentResources.cpu,
            memory: currentResources.memory,
            disk: currentResources.disk,
            networkIn: Math.random() * 50000,
            networkOut: Math.random() * 30000,
          },
        },
        summary: {
          total: services.length,
          running: servicesStatus.filter((s) => s.status === 'running').length,
          degraded: servicesStatus.filter((s) => s.status === 'degraded').length,
          down: servicesStatus.filter((s) => s.status === 'down').length,
          unknown: servicesStatus.filter((s) => s.status === 'unknown').length,
        },
      },
    });
  } catch (error) {
    console.error('Health API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch health data' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  const session = await getServerSession();
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Check for admin role (in production, verify from session)
  // if (session.user.role !== 'ADMIN') {
  //   return NextResponse.json({ error: 'Forbidden - Admin only' }, { status: 403 });
  // }

  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action');

  try {
    const body = await request.json();

    switch (action) {
      case 'restart':
        const { serviceId } = body;
        // In production, this would trigger a service restart
        await new Promise((resolve) => setTimeout(resolve, 2000)); // Simulate restart
        return NextResponse.json({
          success: true,
          message: `Service ${serviceId} restart initiated`,
        });

      default:
        return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
    }
  } catch (error) {
    console.error('Health POST error:', error);
    return NextResponse.json(
      { error: 'Failed to process request' },
      { status: 500 }
    );
  }
}
