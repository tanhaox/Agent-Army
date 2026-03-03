/**
 * 航班信息服务 - 按需获取航班预订单
 *
 * 类似天气服务的逻辑：
 * 1. 先从数据库查询今天的航班预订单
 * 2. 如果没有，调用机场官方API获取并保存
 * 3. 返回航班信息
 *
 * 数据源：
 * - PEK（首都机场）：使用官方API bcia.com.cn
 * - PKX（大兴机场）：使用Trip.com + Puppeteer
 */

import { getPool, getAuxiliaryPool, getDrizzleDb } from '@/storage/database/connection';
import { sql } from 'drizzle-orm';
import { pekFlightScraper } from '@/services/flight-scrapers/pek-flight-scraper';
import { fetchTodayPKXArrivals } from '@/lib/airport/pkxScraper';

/**
 * 检查今天是否有航班预订单
 */
async function checkTodayFlights(): Promise<boolean> {
  const db = getDrizzleDb();

  // 使用本地日期（避免时区转换问题）
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  const todayStr = `${year}-${month}-${day}`; // YYYY-MM-DD

  console.log(`[航班服务] 查询今天航班数据: ${todayStr}`);

  const result = await db.execute(sql`
    SELECT COUNT(*) as count
    FROM orders
    WHERE order_id LIKE 'FLT-%'
      AND DATE(time_pickup) = ${todayStr}::date
  `);

  const count = Number(result.rows[0]?.count || 0);
  console.log(`[航班服务] 查询结果: ${count} 条`);

  return count > 0;
}

/**
 * 从首都机场官方API获取PEK航班数据
 */
async function fetchPEKArrivals(): Promise<any[]> {
  try {
    console.log('[航班服务] 从首都机场官方API获取PEK航班数据');
    const flights = await pekFlightScraper.fetchArrivalFlights(0); // 0=今天
    console.log(`[航班服务] PEK航班获取成功: ${flights.length} 条`);
    return flights;
  } catch (error) {
    console.error('[航班服务] PEK航班获取失败:', error);
    return [];
  }
}

/**
 * 从大兴机场获取PKX航班数据
 * 数据源: Trip.com (hk.trip.com) + Puppeteer
 */
async function fetchPKXArrivals(): Promise<any[]> {
  try {
    console.log('[航班服务] 从Trip.com获取PKX航班数据');
    const flights = await fetchTodayPKXArrivals();
    console.log(`[航班服务] PKX航班获取成功: ${flights.length} 条`);

    // FlightRecord 格式转换为 StandardFlightData 格式（字段映射）
    // FlightRecord: flightNo, scheduledTime
    // StandardFlightData: flight_no, scheduled_time
    return flights.map(flight => ({
      flight_no: flight.flightNo,
      flight_number: flight.flightNo, // 兼容旧格式
      airport_code: flight.airportCode,
      arrival_terminal: flight.arrivalTerminal,
      scheduled_time: flight.scheduledTime,
      arrival_time: flight.scheduledTime, // 兼容旧格式
      estimated_time: flight.estimatedTime,
      actual_time: flight.actualTime,
      flight_status: flight.flightStatus,
      fetched_at: new Date()
    }));
  } catch (error) {
    console.error('[航班服务] PKX航班获取失败:', error);
    return [];
  }
}

/**
 * 生成航班预订单
 *
 * @param flights - 标准格式的航班数据数组（StandardFlightData[]）
 * @param airportCode - 机场代码（'PEK' 或 'PKX'）
 */
async function generateFlightPreorders(flights: any[], airportCode: string) {
  const db = getDrizzleDb();
  const today = new Date();
  const todayStr = today.toISOString().split('T')[0]; // YYYY-MM-DD

  // 按24小时时段统计
  const timeSlotCounts: Record<string, number> = {};

  flights.forEach((flight: any) => {
    // 兼容两种格式：
    // 1. StandardFlightData: flight_no, scheduled_time
    // 2. AviationStack: flight_number, arrival_time
    const flightNo = flight.flight_no || flight.flight_number;
    const arrivalTime = flight.scheduled_time || flight.arrival_time;

    if (!flightNo || !arrivalTime) return;

    // 解析到达时间
    const time = new Date(arrivalTime);
    const hour = time.getHours();
    const timeSlotKey = `${hour}-${hour + 1}`;

    timeSlotCounts[timeSlotKey] = (timeSlotCounts[timeSlotKey] || 0) + 1;
  });

  // 找出TOP2高峰时段
  const topSlots = Object.entries(timeSlotCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2);

  // 为每个高峰时段生成预订单
  for (const [timeSlot, count] of topSlots) {
    const [startHour, endHour] = timeSlot.split('-').map(Number);

    // 生成时间字符串（HH:MM格式）
    const timeString = `${String(startHour).padStart(2, '0')}:00`;
    const timePickup = new Date(todayStr + 'T' + timeString + ':00+08:00');

    // 机场坐标
    const coords = airportCode === 'PEK'
      ? { lat: 40.0799, lng: 116.5843 }
      : { lat: 39.8099, lng: 116.4107 };

    // 生成订单ID
    const orderId = `FLT-${airportCode}-${todayStr.replace(/-/g, '')}-${timeSlot.replace(/:/g, '')}`;

    // 插入预订单
    try {
      await db.execute(sql`
        INSERT INTO orders (
          order_id, user_id, driver_id,
          start_point, end_point,
          start_loc_name, end_loc_name,
          city, car_type, platform, district,
          price_total, is_big_order, is_reservation,
          order_category, trip_type,
          time_pickup, date_tag, special_weather,
          order_type, order_status,
          efficiency_score
        ) VALUES (
          ${orderId}, NULL, 'SYSTEM',
          POINT(${coords.lng}, ${coords.lat}), POINT(${coords.lng + 0.01}, ${coords.lat + 0.01}),
          ${airportCode === 'PEK' ? '首都机场' : '大兴机场'}, ${airportCode === 'PEK' ? '首都机场' : '大兴机场'},
          '北京', 'economy', '航班', '朝阳区',
          ${count * 50}, ${count > 5}, true,
          'scheduled', 'airport_pickup',
          ${timePickup}, ${getTomorrowDateTag()}, false,
          'airport_pickup', 'pending',
          ${count * 50}
        )
        ON CONFLICT (order_id) DO NOTHING
      `);

      console.log(`[航班服务] 生成预订单: ${orderId} (${count}架次)`);
    } catch (error) {
      // 忽略重复插入错误
      const errorMsg = error instanceof Error ? error.message : String(error);
      if (!errorMsg.includes('duplicate key')) {
        console.error(`[航班服务] 插入预订单失败:`, error);
      }
    }
  }

  return topSlots.length;
}

/**
 * 获取今天的航班预订单数量
 * 优先使用新调度系统的数据（arrival_flights 表）
 */
export async function getTodayFlights(): Promise<number> {
  // 查询 arrival_flights（在 beijing_auxiliary 辅助数据库）
  const auxiliaryPool = getAuxiliaryPool('beijing');

  // 查询 orders（在 beijing_didi 业务数据库）
  const businessPool = getPool();

  // 使用本地日期（避免时区转换问题）
  const today = new Date();
  const year = today.getFullYear();
  const month = String(today.getMonth() + 1).padStart(2, '0');
  const day = String(today.getDate()).padStart(2, '0');
  const todayStr = `${year}-${month}-${day}`; // YYYY-MM-DD

  console.log(`[航班服务] 查询今天航班数据: ${todayStr}`);

  // 优先查询新调度系统的数据（arrival_flights 表，在 miaoying 全局数据库）
  try {
    // 计算北京时间的日期（UTC+8）
    const now = new Date();
    const beijingTime = new Date(now.getTime() + 8 * 60 * 60 * 1000);
    const beijingDateStr = beijingTime.toISOString().split('T')[0]; // 北京时间YYYY-MM-DD

    // 调试：检查数据库连接信息
    const client = await auxiliaryPool.connect();
    try {
      const connInfo = await client.query('SELECT current_database(), current_schema(), current_user');
      console.log('[航班服务] 全局数据库连接信息:', connInfo.rows[0]);
    } finally {
      client.release();
    }

    const newSystemResult = await auxiliaryPool.query(`
      SELECT COUNT(*) FILTER (WHERE flight_status IN ('SCH', 'ARV', 'DLY')) as count
      FROM arrival_flights
      WHERE DATE(scheduled_time) = $1::date
        AND airport_code IN ('PEK', 'PKX')
    `, [beijingDateStr]);

    const newSystemCount = Number(newSystemResult.rows[0]?.count || 0);
    console.log(`[航班服务] 新调度系统数据: ${newSystemCount} 条`);

    if (newSystemCount > 0) {
      return newSystemCount;
    }
  } catch (error: any) {
    console.log('[航班服务] 新系统查询失败，尝试旧系统:', error.message);
  }

  // 如果新系统没有数据，使用旧系统（预订单，在 didi 业务数据库）
  console.log('[航班服务] 新系统无数据，使用旧系统预订单');

  const oldSystemResult = await businessPool.query(`
    SELECT COUNT(*) as count
    FROM orders
    WHERE order_id LIKE 'FLT-%'
      AND DATE(time_pickup) = $1::date
  `, [todayStr]);

  const oldSystemCount = Number(oldSystemResult.rows[0]?.count || 0);
  console.log(`[航班服务] 旧系统预订单: ${oldSystemCount} 条`);

  // 如果旧系统也没有数据，尝试从 API 获取
  if (oldSystemCount === 0) {
    console.log('[航班服务] 旧系统也无数据，尝试从机场官方API获取...');

    // 并行获取PEK和PKX航班数据
    const [pekFlights, pkxFlights] = await Promise.all([
      fetchPEKArrivals(),
      fetchPKXArrivals()
    ]);

    // 生成预订单
    await generateFlightPreorders(pekFlights, 'PEK');
    await generateFlightPreorders(pkxFlights, 'PKX');

    // 重新查询
    const retryResult = await businessPool.query(`
      SELECT COUNT(*) as count
      FROM orders
      WHERE order_id LIKE 'FLT-%'
        AND DATE(time_pickup) = $1::date
    `, [todayStr]);
    return Number(retryResult.rows[0]?.count || 0);
  }

  return oldSystemCount;
}

/**
 * 辅助函数：获取明天的日期标签
 */
function getTomorrowDateTag(): string {
  const now = new Date();
  const hour = now.getHours();

  // 如果当前时间早于8点，明天的标签可能是今天
  if (hour < 8) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return '今天';
  }

  return '明天';
}
