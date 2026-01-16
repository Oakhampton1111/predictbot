import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions, canUseEmergencyControls, logAuditAction } from '@/lib/auth';
import { orchestratorApi } from '@/lib/api';
import { prisma } from '@/lib/prisma';
import { redis, CHANNELS } from '@/lib/redis';

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (!canUseEmergencyControls(session.user.role)) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const body = await request.json();
    const { action, reason } = body;

    if (!['pause', 'stop', 'close_all'].includes(action)) {
      return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
    }

    // Log emergency action to database
    const emergencyAction = await prisma.emergencyAction.create({
      data: {
        actionType: action,
        triggeredBy: session.user.id,
        reason: reason || null,
        status: 'pending',
      },
    });

    let result;
    let affectedItems = 0;

    try {
      switch (action) {
        case 'pause':
          result = await orchestratorApi.emergencyPause();
          break;
        case 'stop':
          result = await orchestratorApi.emergencyStop();
          break;
        case 'close_all':
          result = await orchestratorApi.emergencyCloseAll();
          affectedItems = result.data?.closedCount || 0;
          break;
      }

      // Update emergency action status
      await prisma.emergencyAction.update({
        where: { id: emergencyAction.id },
        data: {
          status: result?.success ? 'completed' : 'failed',
          result: result?.data || null,
          completedAt: new Date(),
        },
      });

      // Publish emergency event to Redis for real-time updates
      await redis.publish(
        CHANNELS.EMERGENCY,
        JSON.stringify({
          type: 'emergency_action',
          action,
          triggeredBy: session.user.username,
          timestamp: new Date().toISOString(),
          success: result?.success,
        })
      );

      // Log audit action
      await logAuditAction(
        session.user.id,
        `emergency_${action}`,
        'system',
        { action, reason, affectedItems, success: result?.success },
        { ip: request.headers.get('x-forwarded-for') || undefined }
      );

      if (!result?.success) {
        return NextResponse.json(
          { error: result?.error || 'Emergency action failed' },
          { status: 500 }
        );
      }

      return NextResponse.json({
        success: true,
        action,
        affectedItems,
        message: getSuccessMessage(action, affectedItems),
      });
    } catch (actionError) {
      // Update emergency action as failed
      await prisma.emergencyAction.update({
        where: { id: emergencyAction.id },
        data: {
          status: 'failed',
          result: { error: String(actionError) },
          completedAt: new Date(),
        },
      });

      throw actionError;
    }
  } catch (error) {
    console.error('Emergency API error:', error);
    return NextResponse.json(
      { error: 'Emergency action failed. Please check system status manually.' },
      { status: 500 }
    );
  }
}

function getSuccessMessage(action: string, affectedItems: number): string {
  switch (action) {
    case 'pause':
      return 'All strategies have been paused';
    case 'stop':
      return 'All trading has been stopped';
    case 'close_all':
      return `${affectedItems} positions have been closed`;
    default:
      return 'Emergency action completed';
  }
}
