import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions, canEditConfig, logAuditAction } from '@/lib/auth';
import { orchestratorApi } from '@/lib/api';
import { prisma } from '@/lib/prisma';

export async function GET() {
  try {
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const result = await orchestratorApi.getConfig();

    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    return NextResponse.json(result.data);
  } catch (error) {
    console.error('Config API error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch configuration' },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (!canEditConfig(session.user.role)) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 });
    }

    const body = await request.json();

    // Save config snapshot for version control
    await prisma.configSnapshot.create({
      data: {
        configType: 'full',
        configData: body,
        createdBy: session.user.id,
        isActive: true,
      },
    });

    // Update the actual configuration
    const result = await orchestratorApi.updateConfig(body);

    await logAuditAction(
      session.user.id,
      'update_config',
      'config',
      { sections: Object.keys(body) },
      { ip: request.headers.get('x-forwarded-for') || undefined }
    );

    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Config API error:', error);
    return NextResponse.json(
      { error: 'Failed to update configuration' },
      { status: 500 }
    );
  }
}
