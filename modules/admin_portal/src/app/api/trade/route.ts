import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/lib/auth';
import type { Platform, PositionSide } from '@/types';

// Types
interface Market {
  id: string;
  title: string;
  platform: Platform;
  currentPrice: number;
  priceChange24h: number;
  volume24h: number;
  liquidity: number;
  endDate?: string;
  category?: string;
}

interface TradePreview {
  market: Market;
  side: PositionSide;
  size: number;
  price: number;
  orderType: 'market' | 'limit';
  estimatedCost: number;
  estimatedFees: number;
  totalCost: number;
  slippage: number;
  priceImpact: number;
}

interface ManualTrade {
  id: string;
  marketId: string;
  marketTitle: string;
  platform: Platform;
  side: PositionSide;
  size: number;
  price: number;
  orderType: 'market' | 'limit';
  status: 'pending' | 'filled' | 'partial' | 'cancelled' | 'failed';
  filledSize?: number;
  filledPrice?: number;
  fees?: number;
  totalCost?: number;
  createdAt: string;
  updatedAt: string;
  executedBy: string;
  error?: string;
}

// Mock data generators
function generateMockMarkets(search?: string, platform?: Platform): Market[] {
  const allMarkets: Market[] = [
    {
      id: 'poly-btc-100k',
      title: 'Will Bitcoin reach $100,000 by end of 2026?',
      platform: 'polymarket',
      currentPrice: 0.65,
      priceChange24h: 2.5,
      volume24h: 125000,
      liquidity: 450000,
      endDate: '2026-12-31',
      category: 'Crypto',
    },
    {
      id: 'poly-eth-10k',
      title: 'Will Ethereum reach $10,000 by end of 2026?',
      platform: 'polymarket',
      currentPrice: 0.42,
      priceChange24h: -1.2,
      volume24h: 85000,
      liquidity: 320000,
      endDate: '2026-12-31',
      category: 'Crypto',
    },
    {
      id: 'kalshi-fed-rate',
      title: 'Fed to cut rates in Q1 2026?',
      platform: 'kalshi',
      currentPrice: 0.78,
      priceChange24h: 5.3,
      volume24h: 200000,
      liquidity: 500000,
      endDate: '2026-03-31',
      category: 'Economics',
    },
    {
      id: 'kalshi-recession',
      title: 'US recession in 2026?',
      platform: 'kalshi',
      currentPrice: 0.25,
      priceChange24h: -3.1,
      volume24h: 150000,
      liquidity: 380000,
      endDate: '2026-12-31',
      category: 'Economics',
    },
    {
      id: 'manifold-ai-agi',
      title: 'AGI achieved by 2030?',
      platform: 'manifold',
      currentPrice: 0.15,
      priceChange24h: 0.8,
      volume24h: 45000,
      liquidity: 120000,
      endDate: '2030-12-31',
      category: 'Technology',
    },
    {
      id: 'manifold-spacex-mars',
      title: 'SpaceX lands humans on Mars by 2030?',
      platform: 'manifold',
      currentPrice: 0.22,
      priceChange24h: 1.5,
      volume24h: 35000,
      liquidity: 95000,
      endDate: '2030-12-31',
      category: 'Space',
    },
    {
      id: 'poly-election-2028',
      title: 'Democratic candidate wins 2028 US Presidential Election?',
      platform: 'polymarket',
      currentPrice: 0.48,
      priceChange24h: 0.2,
      volume24h: 500000,
      liquidity: 1200000,
      endDate: '2028-11-05',
      category: 'Politics',
    },
    {
      id: 'kalshi-sp500-6000',
      title: 'S&P 500 above 6000 by end of 2026?',
      platform: 'kalshi',
      currentPrice: 0.55,
      priceChange24h: 1.8,
      volume24h: 180000,
      liquidity: 420000,
      endDate: '2026-12-31',
      category: 'Markets',
    },
  ];

  let filtered = allMarkets;

  if (platform) {
    filtered = filtered.filter(m => m.platform === platform);
  }

  if (search) {
    const searchLower = search.toLowerCase();
    filtered = filtered.filter(m =>
      m.title.toLowerCase().includes(searchLower) ||
      m.category?.toLowerCase().includes(searchLower) ||
      m.id.toLowerCase().includes(searchLower)
    );
  }

  return filtered;
}

function generateMockRecentTrades(limit: number): ManualTrade[] {
  const trades: ManualTrade[] = [
    {
      id: 'trade-001',
      marketId: 'poly-btc-100k',
      marketTitle: 'Will Bitcoin reach $100,000 by end of 2026?',
      platform: 'polymarket',
      side: 'YES',
      size: 500,
      price: 0.65,
      orderType: 'market',
      status: 'filled',
      filledSize: 500,
      filledPrice: 0.65,
      fees: 1.63,
      totalCost: 326.63,
      createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      executedBy: 'admin@predictbot.io',
    },
    {
      id: 'trade-002',
      marketId: 'kalshi-fed-rate',
      marketTitle: 'Fed to cut rates in Q1 2026?',
      platform: 'kalshi',
      side: 'NO',
      size: 200,
      price: 0.22,
      orderType: 'limit',
      status: 'pending',
      createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
      executedBy: 'admin@predictbot.io',
    },
    {
      id: 'trade-003',
      marketId: 'manifold-ai-agi',
      marketTitle: 'AGI achieved by 2030?',
      platform: 'manifold',
      side: 'YES',
      size: 1000,
      price: 0.15,
      orderType: 'market',
      status: 'filled',
      filledSize: 1000,
      filledPrice: 0.15,
      fees: 0.75,
      totalCost: 150.75,
      createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      executedBy: 'operator@predictbot.io',
    },
    {
      id: 'trade-004',
      marketId: 'poly-eth-10k',
      marketTitle: 'Will Ethereum reach $10,000 by end of 2026?',
      platform: 'polymarket',
      side: 'NO',
      size: 300,
      price: 0.58,
      orderType: 'market',
      status: 'failed',
      createdAt: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 48 * 60 * 60 * 1000).toISOString(),
      executedBy: 'admin@predictbot.io',
      error: 'Insufficient balance in Polymarket wallet',
    },
    {
      id: 'trade-005',
      marketId: 'kalshi-recession',
      marketTitle: 'US recession in 2026?',
      platform: 'kalshi',
      side: 'YES',
      size: 150,
      price: 0.25,
      orderType: 'limit',
      status: 'cancelled',
      createdAt: new Date(Date.now() - 72 * 60 * 60 * 1000).toISOString(),
      updatedAt: new Date(Date.now() - 70 * 60 * 60 * 1000).toISOString(),
      executedBy: 'admin@predictbot.io',
    },
  ];

  return trades.slice(0, limit);
}

function calculateTradePreview(
  market: Market,
  side: PositionSide,
  size: number,
  price: number,
  orderType: 'market' | 'limit'
): TradePreview {
  const estimatedCost = size * price;
  const feeRate = market.platform === 'polymarket' ? 0.005 : market.platform === 'kalshi' ? 0.01 : 0.005;
  const estimatedFees = estimatedCost * feeRate;
  const totalCost = estimatedCost + estimatedFees;
  
  // Calculate slippage based on order size vs liquidity
  const slippage = orderType === 'market' ? Math.min((size * price / market.liquidity) * 100, 5) : 0;
  
  // Calculate price impact
  const priceImpact = (size * price / market.liquidity) * 10;

  return {
    market,
    side,
    size,
    price,
    orderType,
    estimatedCost,
    estimatedFees,
    totalCost,
    slippage,
    priceImpact,
  };
}

// GET handler - fetch markets or recent trades
export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const endpoint = searchParams.get('endpoint') || 'markets';

    if (endpoint === 'markets') {
      const search = searchParams.get('search') || undefined;
      const platform = searchParams.get('platform') as Platform | undefined;
      const sort = searchParams.get('sort') || 'volume';
      const limit = parseInt(searchParams.get('limit') || '20');

      let markets = generateMockMarkets(search, platform);

      // Sort markets
      if (sort === 'volume') {
        markets.sort((a, b) => b.volume24h - a.volume24h);
      } else if (sort === 'liquidity') {
        markets.sort((a, b) => b.liquidity - a.liquidity);
      } else if (sort === 'price') {
        markets.sort((a, b) => b.currentPrice - a.currentPrice);
      }

      markets = markets.slice(0, limit);

      return NextResponse.json({
        success: true,
        data: {
          markets,
          total: markets.length,
        },
      });
    }

    if (endpoint === 'recent') {
      const limit = parseInt(searchParams.get('limit') || '10');
      const trades = generateMockRecentTrades(limit);

      return NextResponse.json({
        success: true,
        data: {
          trades,
          total: trades.length,
        },
      });
    }

    return NextResponse.json({ error: 'Invalid endpoint' }, { status: 400 });
  } catch (error) {
    console.error('Trade API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// POST handler - preview or execute trade
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check for ADMIN or OPERATOR role
    const userRole = (session.user as { role?: string })?.role;
    if (!userRole || !['ADMIN', 'OPERATOR'].includes(userRole)) {
      return NextResponse.json(
        { error: 'Insufficient permissions. ADMIN or OPERATOR role required.' },
        { status: 403 }
      );
    }

    const body = await request.json();
    const { action, market, side, size, price, orderType } = body;

    if (action === 'preview') {
      if (!market || !side || !size) {
        return NextResponse.json(
          { error: 'Missing required fields: market, side, size' },
          { status: 400 }
        );
      }

      const preview = calculateTradePreview(
        market,
        side,
        size,
        price || market.currentPrice,
        orderType || 'market'
      );

      return NextResponse.json({
        success: true,
        data: preview,
      });
    }

    if (action === 'execute') {
      if (!market || !side || !size) {
        return NextResponse.json(
          { error: 'Missing required fields: market, side, size' },
          { status: 400 }
        );
      }

      // Simulate trade execution
      // In production, this would call the actual trading APIs
      const tradeId = `trade-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      // Log the trade for audit
      console.log('Manual trade executed:', {
        tradeId,
        market: market.id,
        side,
        size,
        price: price || market.currentPrice,
        orderType: orderType || 'market',
        executedBy: session.user?.email,
        timestamp: new Date().toISOString(),
      });

      // Simulate success (90% success rate for demo)
      const isSuccess = Math.random() > 0.1;

      if (isSuccess) {
        return NextResponse.json({
          success: true,
          data: {
            tradeId,
            status: 'filled',
            filledSize: size,
            filledPrice: price || market.currentPrice,
            fees: (size * (price || market.currentPrice)) * 0.005,
            totalCost: (size * (price || market.currentPrice)) * 1.005,
          },
        });
      } else {
        return NextResponse.json({
          success: false,
          error: 'Trade execution failed: Insufficient liquidity',
        }, { status: 400 });
      }
    }

    return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
  } catch (error) {
    console.error('Trade API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
