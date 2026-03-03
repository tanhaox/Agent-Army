/**
 * 检查今天的航班数据
 */

import { getDrizzleDb } from '../src/storage/database/connection';
import { arrivalFlights } from '../src/storage/database/shared/schema';
import { sql } from 'drizzle-orm';

async function checkTodayFlights() {
  const db = getDrizzleDb();

  // 获取今天的日期范围
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  console.log('========================================');
  console.log('检查今天的航班数据');
  console.log('========================================');
  console.log(`查询时间范围: ${today.toISOString()} - ${tomorrow.toISOString()}`);
  console.log();

  try {
    // 查询今天的航班总数
    const totalCount = await db
      .select({ count: sql<number>`count(*)` })
      .from(arrivalFlights)
      .where(sql`arrival_flights.scheduled_time >= ${today} AND arrival_flights.scheduled_time < ${tomorrow}`);

    console.log(`✓ 今天航班总数: ${totalCount[0].count}`);
    console.log();

    // 按机场统计
    const byAirport = await db
      .select({
        airport: arrivalFlights.airportCode,
        count: sql<number>`count(*)`,
      })
      .from(arrivalFlights)
      .where(sql`arrival_flights.scheduled_time >= ${today} AND arrival_flights.scheduled_time < ${tomorrow}`)
      .groupBy(arrivalFlights.airportCode);

    console.log('按机场统计:');
    byAirport.forEach(item => {
      console.log(`  ${item.airport}: ${item.count} 个航班`);
    });
    console.log();

    // 按状态统计
    const byStatus = await db
      .select({
        status: arrivalFlights.flightStatus,
        count: sql<number>`count(*)`,
      })
      .from(arrivalFlights)
      .where(sql`arrival_flights.scheduled_time >= ${today} AND arrival_flights.scheduled_time < ${tomorrow}`)
      .groupBy(arrivalFlights.flightStatus);

    console.log('按状态统计:');
    byStatus.forEach(item => {
      console.log(`  ${item.status}: ${item.count} 个航班`);
    });
    console.log();

    // 查看最近更新的航班
    const recentFlights = await db
      .select()
      .from(arrivalFlights)
      .where(sql`arrival_flights.scheduled_time >= ${today} AND arrival_flights.scheduled_time < ${tomorrow}`)
      .orderBy(sql`arrival_flights.fetched_at DESC`)
      .limit(5);

    console.log('最近更新的5个航班:');
    recentFlights.forEach((flight, index) => {
      console.log(`  ${index + 1}. ${flight.flightNo} - ${flight.airportCode}`);
      console.log(`     计划到达: ${flight.scheduledTime.toISOString()}`);
      console.log(`     状态: ${flight.flightStatus}`);
      console.log(`     抓取时间: ${flight.fetchedAt.toISOString()}`);
      console.log();
    });

    // 检查最早和最晚的抓取时间
    const fetchTimes = await db
      .select({
        min: sql<string>`min(arrival_flights.fetched_at)`,
        max: sql<string>`max(arrival_flights.fetched_at)`,
      })
      .from(arrivalFlights)
      .where(sql`arrival_flights.scheduled_time >= ${today} AND arrival_flights.scheduled_time < ${tomorrow}`);

    if (fetchTimes[0].min && fetchTimes[0].max) {
      console.log('抓取时间范围:');
      console.log(`  最早: ${new Date(fetchTimes[0].min).toLocaleString('zh-CN')}`);
      console.log(`  最晚: ${new Date(fetchTimes[0].max).toLocaleString('zh-CN')}`);
    }

  } catch (error) {
    console.error('查询失败:', error);
  } finally {
    process.exit(0);
  }
}

checkTodayFlights();
