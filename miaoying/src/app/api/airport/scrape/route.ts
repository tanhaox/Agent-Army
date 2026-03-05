/**
 * 手动触发航班抓取API
 */

import { scrapeTodayOnly } from '@/lib/airport/flightScraper';

export async function POST() {
  try {
    console.log('[手动抓取] 开始抓取今天航班数据...');

    const result = await scrapeTodayOnly();

    return Response.json({
      success: true,
      message: '抓取完成',
      data: {
        pek: result.pek,
        pkx: result.pkx,
        total: result.pek + result.pkx
      }
    });
  } catch (error) {
    console.error('[手动抓取] 失败:', error);
    return Response.json({
      success: false,
      error: error instanceof Error ? error.message : '抓取失败'
    }, { status: 500 });
  }
}
