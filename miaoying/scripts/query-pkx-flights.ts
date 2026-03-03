/**
 * 查询数据库中的PKX航班数据
 */

import { getDrizzleDb } from '../src/storage/database/connection';
import { sql } from 'drizzle-orm';

async function queryPKXFlights() {
  const db = getDrizzleDb();

  console.log('========================================');
  console.log('PKX 航班数据查询');
  console.log('========================================');
  console.log();

  try {
    // 1. 总体统计
    console.log('1. 总体统计');
    console.log('--------------------------------------');
    const totalStats = await db.execute(sql`
      SELECT
        COUNT(*) as total,
        COUNT(DISTINCT flight_no) as unique_flights,
        MIN(scheduled_time) as first_flight,
        MAX(scheduled_time) as last_flight,
        COUNT(CASE WHEN flight_status = 'SCH' THEN 1 END) as scheduled,
        COUNT(CASE WHEN flight_status = 'DEP' THEN 1 END) as departed,
        COUNT(CASE WHEN flight_status = 'ARR' THEN 1 END) as arrived,
        COUNT(CASE WHEN flight_status = 'DLY' THEN 1 END) as delayed
      FROM arrival_flights
      WHERE airport_code = 'PKX'
      AND DATE(scheduled_time) = '2026-03-04'
    `);

    const stats = totalStats.rows[0];
    console.log(`总记录数: ${stats.total}`);
    console.log(`不重复航班: ${stats.unique_flights}`);
    console.log(`第一班: ${stats.first_flight}`);
    console.log(`最后一班: ${stats.last_flight}`);
    console.log(`已安排 (SCH): ${stats.scheduled}`);
    console.log(`已出发 (DEP): ${stats.departed}`);
    console.log(`已到达 (ARR): ${stats.arrived}`);
    console.log(`延误 (DLY): ${stats.delayed}`);
    console.log();

    // 2. 按小时统计
    console.log('2. 按小时统计');
    console.log('--------------------------------------');
    const hourlyStats = await db.execute(sql`
      SELECT
        EXTRACT(HOUR FROM scheduled_time)::INTEGER as hour,
        COUNT(*) as total,
        COUNT(CASE WHEN flight_status = 'SCH' THEN 1 END) as scheduled,
        COUNT(CASE WHEN flight_status = 'DEP' THEN 1 END) as departed,
        COUNT(CASE WHEN flight_status = 'ARR' THEN 1 END) as arrived,
        COUNT(CASE WHEN flight_status = 'DLY' THEN 1 END) as delayed
      FROM arrival_flights
      WHERE airport_code = 'PKX'
      AND DATE(scheduled_time) = '2026-03-04'
      GROUP BY EXTRACT(HOUR FROM scheduled_time)
      ORDER BY hour
    `);

    for (const row of hourlyStats.rows) {
      const hour = String(row.hour).padStart(2, '0');
      console.log(`${hour}:00 - 总计 ${row.total} (SCH:${row.scheduled}, DEP:${row.departed}, ARR:${row.arrived}, DLY:${row.delayed})`);
    }
    console.log();

    // 3. 前10条航班
    console.log('3. 前10条航班');
    console.log('--------------------------------------');
    const firstFlights = await db.execute(sql`
      SELECT flight_no, scheduled_time, flight_status
      FROM arrival_flights
      WHERE airport_code = 'PKX'
      AND DATE(scheduled_time) = '2026-03-04'
      ORDER BY scheduled_time
      LIMIT 10
    `);

    for (const flight of firstFlights.rows) {
      console.log(`${flight.flight_no} - ${flight.scheduled_time} - ${flight.flight_status}`);
    }
    console.log();

    // 4. 后10条航班
    console.log('4. 后10条航班');
    console.log('--------------------------------------');
    const lastFlights = await db.execute(sql`
      SELECT flight_no, scheduled_time, flight_status
      FROM arrival_flights
      WHERE airport_code = 'PKX'
      AND DATE(scheduled_time) = '2026-03-04'
      ORDER BY scheduled_time DESC
      LIMIT 10
    `);

    for (const flight of lastFlights.rows) {
      console.log(`${flight.flight_no} - ${flight.scheduled_time} - ${flight.flight_status}`);
    }

  } catch (error: any) {
    console.error('查询失败:', error.message);
  } finally {
    process.exit(0);
  }
}

queryPKXFlights();
