/**
 * 检查今天的航班数据（辅助数据库）
 */

import { getAuxiliaryDrizzleDb } from '../src/storage/database/connection';
import { sql } from 'drizzle-orm';

async function checkToday() {
  const db = getAuxiliaryDrizzleDb('beijing');

  // 今天的日期范围
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  console.log('========================================');
  console.log('检查今天的航班数据');
  console.log('========================================');
  console.log(`日期: ${today.toLocaleDateString('zh-CN')}`);
  console.log();

  try {
    // 今天航班总数
    const result = await db.execute(sql`
      SELECT COUNT(*) as count
      FROM arrival_flights
      WHERE scheduled_time >= ${today} AND scheduled_time < ${tomorrow}
    `);
    console.log(`✓ 今天航班总数: ${result.rows[0].count}`);
    console.log();

    // 按机场统计
    const byAirport = await db.execute(sql`
      SELECT airport_code, COUNT(*) as count
      FROM arrival_flights
      WHERE scheduled_time >= ${today} AND scheduled_time < ${tomorrow}
      GROUP BY airport_code
    `);
    console.log('按机场统计:');
    byAirport.rows.forEach((row: any) => {
      console.log(`  ${row.airport_code}: ${row.count} 个航班`);
    });
    console.log();

    // 按状态统计
    const byStatus = await db.execute(sql`
      SELECT flight_status, COUNT(*) as count
      FROM arrival_flights
      WHERE scheduled_time >= ${today} AND scheduled_time < ${tomorrow}
      GROUP BY flight_status
    `);
    console.log('按状态统计:');
    byStatus.rows.forEach((row: any) => {
      console.log(`  ${row.flight_status}: ${row.count} 个航班`);
    });
    console.log();

    console.log('========================================');

  } catch (error) {
    console.error('错误:', error);
  } finally {
    process.exit(0);
  }
}

checkToday();
