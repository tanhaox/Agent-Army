/**
 * 验证最火爆时段统计
 */

import { getAuxiliaryPool } from '../src/storage/database/connection';
import { sql } from 'drizzle-orm';

async function verifyHottestPeriods() {
  const pool = getAuxiliaryPool('beijing');

  console.log('========================================');
  console.log('最火爆时段验证');
  console.log('========================================');
  console.log();

  try {
    // 1. 查询所有机场按小时统计
    console.log('1. 所有机场按小时统计（全部航站楼）');
    console.log('--------------------------------------');
    const allStats = await db.execute(sql`
      SELECT
        airport_code,
        COALESCE(arrival_terminal, 'ALL') as terminal,
        EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')::INTEGER as hour,
        COUNT(*) FILTER (WHERE flight_status IN ('SCH', 'ARR', 'DLY')) as total
      FROM arrival_flights
      WHERE DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai') = CURRENT_DATE
        AND airport_code IN ('PEK', 'PKX')
      GROUP BY airport_code, arrival_terminal, EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')
      ORDER BY airport_code, terminal, hour
    `);

    // 按机场分组显示
    const byAirport: { [key: string]: { [terminal: string]: { [hour: string]: number } } } = {};

    for (const row of allStats.rows) {
      const airport = row.airport_code;
      const terminal = row.terminal || 'ALL';
      const hour = String(row.hour).padStart(2, '0');
      const count = Number(row.total);

      if (!byAirport[airport]) byAirport[airport] = {};
      if (!byAirport[airport][terminal]) byAirport[airport][terminal] = {};
      byAirport[airport][terminal][`${hour}:00`] = count;
    }

    // PEK统计
    if (byAirport.PEK) {
      console.log('PEK (首都机场):');
      for (const [terminal, hours] of Object.entries(byAirport.PEK)) {
        console.log(`  ${terminal}:`);
        const sorted = Object.entries(hours).sort((a, b) => b[1] - a[1]);
        sorted.slice(0, 5).forEach(([time, count]) => {
          console.log(`    ${time}: ${count}架`);
        });
      }
      console.log();
    }

    // PKX统计
    if (byAirport.PKX) {
      console.log('PKX (大兴机场):');
      for (const [terminal, hours] of Object.entries(byAirport.PKX)) {
        console.log(`  ${terminal}:`);
        const sorted = Object.entries(hours).sort((a, b) => b[1] - a[1]);
        sorted.slice(0, 5).forEach(([time, count]) => {
          console.log(`    ${time}: ${count}架`);
        });
      }
      console.log();
    }

    // 2. 找出最火爆时段
    console.log('2. 全局最火爆时段 TOP 10');
    console.log('--------------------------------------');
    const topPeriods = await db.execute(sql`
      SELECT
        airport_code,
        COALESCE(arrival_terminal, 'ALL') as terminal,
        EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')::INTEGER as hour,
        COUNT(*) FILTER (WHERE flight_status IN ('SCH', 'ARR', 'DLY')) as total
      FROM arrival_flights
      WHERE DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai') = CURRENT_DATE
        AND airport_code IN ('PEK', 'PKX')
      GROUP BY airport_code, arrival_terminal, EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')
      ORDER BY total DESC
      LIMIT 10
    `);

    for (const row of topPeriods.rows) {
      const airport = row.airport_code;
      const terminal = row.terminal === 'ALL' ? '全部' : row.terminal;
      const hour = String(row.hour).padStart(2, '0');
      const count = Number(row.total);
      console.log(`${airport} ${terminal} ${hour}:00 - ${count}架`);
    }

    console.log();

    // 3. 验证API返回的最火爆时段
    console.log('3. API返回数据验证');
    console.log('--------------------------------------');

    const response = await fetch('http://localhost:6001/api/airport/prediction');
    const apiData = await response.json();

    if (apiData.success && apiData.data.summary) {
      const summary = apiData.data.summary;

      console.log(`API最热机场: ${summary.hottestAirport || '(空)'}`);
      console.log(`API最热航站楼: ${summary.hottestTerminal}`);
      console.log(`API最热时段: ${summary.hottestHour}`);
      console.log();

      // 查询数据库中该时段的数据
      if (summary.hottestHour && summary.hottestTerminal) {
        const hourMatch = summary.hottestHour.match(/(\d{2}):(\d{2})-(\d{2}):(\d{2})/);
        if (hourMatch) {
          const hour = parseInt(hourMatch[1]);
          const terminal = summary.hottestTerminal === '全部' ? 'ALL' : summary.hottestTerminal;

          const verifyResult = await db.execute(sql`
            SELECT
              airport_code,
              COALESCE(arrival_terminal, 'ALL') as terminal,
              EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')::INTEGER as hour,
              COUNT(*) FILTER (WHERE flight_status IN ('SCH', 'ARR', 'DLY')) as total
            FROM arrival_flights
            WHERE DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai') = CURRENT_DATE
              AND EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai') = ${hour}
              AND COALESCE(arrival_terminal, 'ALL') = ${terminal}
            GROUP BY airport_code, arrival_terminal, EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')
          `);

          console.log(`数据库验证 ${summary.hottestHour} ${summary.hottestTerminal}:`);
          for (const row of verifyResult.rows) {
            console.log(`  ${row.airport_code} ${row.terminal === 'ALL' ? '全部' : row.terminal}: ${Number(row.total)}架`);
          }
        }
      }
    }

  } catch (error: any) {
    console.error('验证失败:', error.message);
  } finally {
    process.exit(0);
  }
}

verifyHottestPeriods();
