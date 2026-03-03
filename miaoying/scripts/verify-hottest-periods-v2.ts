/**
 * 验证最火爆时段统计（使用辅助数据库）
 */

import { getAuxiliaryPool } from '../src/storage/database/connection';

async function verifyHottestPeriods() {
  const pool = getAuxiliaryPool('beijing');

  console.log('========================================');
  console.log('最火爆时段验证');
  console.log('========================================');
  console.log();

  try {
    // 1. 检查数据在哪个数据库
    console.log('1. 检查PKX数据位置');
    console.log('--------------------------------------');
    const pkxCount = await pool.query(`
      SELECT COUNT(*) as count
      FROM arrival_flights
      WHERE airport_code = 'PKX'
        AND DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai') = '2026-03-04'
    `);
    console.log(`辅助数据库 beijing_auxiliary PKX记录: ${pkxCount.rows[0].count}`);
    console.log();

    // 2. 查询所有机场按小时统计
    console.log('2. 所有机场按小时统计（今天）');
    console.log('--------------------------------------');
    const allStats = await pool.query(`
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

    console.log(`查询结果: ${allStats.rows.length} 条记录`);

    // 按机场分组显示TOP时段
    const byAirport: { [key: string]: any[] } = { PEK: [], PKX: [] };

    for (const row of allStats.rows) {
      const airport = row.airport_code;
      const terminal = row.terminal || 'ALL';
      const hour = String(row.hour).padStart(2, '0');
      const count = Number(row.total);

      byAirport[airport].push({
        terminal,
        time: `${hour}:00`,
        count
      });
    }

    // PEK统计
    if (byAirport.PEK.length > 0) {
      console.log('PEK (首都机场) TOP 5:');
      byAirport.PEK.sort((a, b) => b.count - a.count);
      byAirport.PEK.slice(0, 5).forEach((item, index) => {
        console.log(`  ${index + 1}. ${item.terminal} ${item.time}: ${item.count}架`);
      });
      console.log();
    } else {
      console.log('PEK: 无数据');
      console.log();
    }

    // PKX统计
    if (byAirport.PKX.length > 0) {
      console.log('PKX (大兴机场) TOP 5:');
      byAirport.PKX.sort((a, b) => b.count - a.count);
      byAirport.PKX.slice(0, 5).forEach((item, index) => {
        console.log(`  ${index + 1}. ${item.terminal} ${item.time}: ${item.count}架`);
      });
      console.log();
    } else {
      console.log('PKX: 无数据');
      console.log();
    }

    // 3. 找出最火爆时段（全局）
    console.log('3. 全局最火爆时段 TOP 10');
    console.log('--------------------------------------');
    const topPeriods = await pool.query(`
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

    for (let i = 0; i < topPeriods.rows.length; i++) {
      const row = topPeriods.rows[i];
      const airport = row.airport_code;
      const terminal = row.terminal === 'ALL' ? '全部' : row.terminal;
      const hour = String(row.hour).padStart(2, '0');
      const count = Number(row.total);
      console.log(`${i + 1}. ${airport} ${terminal} ${hour}:00 - ${count}架`);
    }

    console.log();

    // 4. 验证API返回的最火爆时段
    console.log('4. API返回数据验证');
    console.log('--------------------------------------');

    const response = await fetch('http://localhost:6001/api/airport/prediction');
    const apiData = await response.json();

    if (apiData.success && apiData.data.summary) {
      const summary = apiData.data.summary;

      console.log(`API最热机场: ${summary.hottestAirport || '(空)'}`);
      console.log(`API最热航站楼: ${summary.hottestTerminal}`);
      console.log(`API最热时段: ${summary.hottestHour}`);
      console.log();

      // 验证TOP Periods
      if (summary.topPeriods && summary.topPeriods.length > 0) {
        console.log('API TOP Periods:');
        summary.topPeriods.slice(0, 5).forEach((period: any, index: number) => {
          console.log(`  ${index + 1}. ${period.timeRange} ${period.terminal}: ${period.count}架`);
        });
        console.log();

        // 对比数据库
        console.log('数据库实际数据（对应时段）:');
        for (const period of summary.topPeriods.slice(0, 3)) {
          const hourMatch = period.timeRange.match(/(\d{2}):(\d{2})-(\d{2}):(\d{2})/);
          if (hourMatch) {
            const hour = parseInt(hourMatch[1]);
            const terminal = period.terminal === '全部' ? 'ALL' : period.terminal;

            const verifyResult = await pool.query(`
              SELECT
                airport_code,
                COALESCE(arrival_terminal, 'ALL') as terminal,
                COUNT(*) FILTER (WHERE flight_status IN ('SCH', 'ARR', 'DLY')) as total
              FROM arrival_flights
              WHERE DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai') = CURRENT_DATE
                AND EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai') = ${hour}
                AND COALESCE(arrival_terminal, 'ALL') = ${terminal}
              GROUP BY airport_code, arrival_terminal
            `);

            console.log(`  ${period.timeRange} ${period.terminal}:`);
            for (const row of verifyResult.rows) {
              console.log(`    ${row.airport_code} ${row.terminal === 'ALL' ? '全部' : row.terminal}: ${Number(row.total)}架`);
            }
          }
        }
      }
    }

  } catch (error: any) {
    console.error('验证失败:', error.message);
    console.error(error.stack);
  } finally {
    process.exit(0);
  }
}

verifyHottestPeriods();
