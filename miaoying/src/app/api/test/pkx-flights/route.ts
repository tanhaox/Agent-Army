/**
 * 测试大兴机场API
 *
 * 访问: /api/test/pkx-flights
 */

import { fetchTodayPKXArrivals } from '@/lib/airport/pkxScraperPython';
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    console.log('=== 开始测试大兴机场API ===');

    // 测试抓取今天的航班数据
    const flights = await fetchTodayPKXArrivals();

    return NextResponse.json({
      success: true,
      data: {
        count: flights.length,
        flights: flights.slice(0, 10), // 只返回前10条作为示例
        message: flights.length > 0
          ? '✅ 大兴机场API工作正常'
          : '⚠️ 今日暂无航班数据或抓取失败',
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    console.error('❌ 测试失败:', error);

    return NextResponse.json({
      success: false,
      error: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
    }, { status: 500 });
  }
}
