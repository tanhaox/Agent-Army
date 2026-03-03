/**
 * 测试首都机场API
 *
 * 访问: /api/test/pek-flights
 */

import { pekFlightScraper } from '@/services/flight-scrapers/pek-flight-scraper';
import { NextResponse } from 'next/server';

export async function GET() {
  try {
    console.log('=== 开始测试首都机场API ===');

    // 测试抓取今天的航班数据
    const flights = await pekFlightScraper.fetchArrivalFlights(0); // 0=今天

    return NextResponse.json({
      success: true,
      data: {
        count: flights.length,
        flights: flights.slice(0, 10), // 只返回前10条作为示例
        message: flights.length > 0
          ? '✅ 首都机场API工作正常'
          : '⚠️ 今日暂无航班数据',
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
