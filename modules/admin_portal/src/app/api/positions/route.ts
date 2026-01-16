import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions, canManagePositions, logAuditAction } from '@/lib/auth';
import { orchestratorApi } from '@/lib/api';

export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const searchParams = request.nextUrl.searchParams;
    const platform = searchParams.get('platform') || undefined;
    const status = searchParams.get('status') || undefined;

    const result = await orchestratorApi.getPositions({ platform, status });

    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    return NextResponse.json(result.data);
  } catch (error) {
    console.error('Positions API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch positions' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (!canManagePositions(session.user.role)) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const body = await request.json();
    const { action, positionId, positionIds } = body;

    if (action === 'close' && positionId) {
      const result = await orchestratorApi.closePosition(positionId);

      await logAuditAction(
        session.user.id,
        'close_position',
        'position',
        { positionId },
        { ip: request.headers.get('x-forwarded-for') || undefined }
      );

      if (!result.success) {
        return NextResponse.json({ error: result.error }, { status: 500 });
      }

      return NextResponse.json({ success: true });
    }

    if (action === 'close_multiple' && positionIds?.length) {
      const results = await Promise.allSettled(
        positionIds.map((id: string) => orchestratorApi.closePosition(id))
      );

      await logAuditAction(
        session.user.id,
        'close_multiple_positions',
        'position',
        { positionIds, count: positionIds.length },
        { ip: request.headers.get('x-forwarded-for') || undefined }
      );

      const successful = results.filter((r) => r.status === 'fulfilled').length;
      const failed = results.filter((r) => r.status === 'rejected').length;

      return NextResponse.json({ success: true, closed: successful, failed });
    }

    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
  } catch (error) {
    console.error('Positions API error:', error);
    return NextResponse.json(
      { error: 'Failed to process position action' },
      { status: 500 }
    );
  }
}
