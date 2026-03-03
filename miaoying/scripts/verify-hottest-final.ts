import { getAuxiliaryPool } from '../src/storage/database/connection';

async function verifyHottestPeriods() {
  const pool = getAuxiliaryPool('beijing');

  console.log('========================================');
  console.log('最火爆时段验证（全天）');
  console.log('========================================');
  console.log();

  try {
    // 1. PKX全天数据统计
    console.log('1. PKX (大兴机场) 全天统计');
    console.log('--------------------------------------');
    const pkxStats = await pool.query(`
      SELECT
        EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')::INTEGER as hour,
        COUNT(*) FILTER (WHERE flight_status IN ('SCH', 'ARV', 'DLY')) as total
      FROM arrival_flights
      WHERE airport_code = 'PKX'
        AND DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai') = '2026-03-04'
      GROUP BY EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')
      ORDER BY hour
    `);

    console.log(`时段统计 (${pkxStats.rows.length} 个时段):`);
    pkxStats.rows.forEach((row: any) => {
      const hour = String(row.hour).padStart(2, '0');
      console.log(`  ${hour}:00: ${row.total}架`);
    });
    console.log();

    // 2. PEK全天数据统计
    console.log('2. PEK (首都机场) 全天统计 (TOP 10)');
    console.log('--------------------------------------');
    const pekStats = await pool.query(`
      SELECT
        COALESCE(arrival_terminal, 'ALL') as terminal,
        EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')::INTEGER as hour,
        COUNT(*) FILTER (WHERE flight_status IN ('SCH', 'ARV', 'DLY')) as total
      FROM arrival_flights
      WHERE airport_code = 'PEK'
        AND DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai') = '2026-03-04'
      GROUP BY arrival_terminal, EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')
      ORDER BY total DESC
      LIMIT 10
    `);

    pekStats.rows.forEach((row: any, index: number) => {
      const hour = String(row.hour).padStart(2, '0');
      const terminal = row.terminal === 'ALL' ? '全部' : row.terminal;
      console.log(`  ${index + 1}. ${terminal} ${hour}:00: ${row.total}架`);
    });
    console.log();

    // 3. 全局最火爆时段 TOP 10
    console.log('3. 全局最火爆时段 TOP 10');
    console.log('--------------------------------------');
    const topPeriods = await pool.query(`
      SELECT
        airport_code,
        COALESCE(arrival_terminal, 'ALL') as terminal,
        EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')::INTEGER as hour,
        COUNT(*) FILTER (WHERE flight_status IN ('SCH', 'ARV', 'DLY')) as total
      FROM arrival_flights
      WHERE airport_code IN ('PEK', 'PKX')
        AND DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai') = '2026-03-04'
      GROUP BY airport_code, arrival_terminal, EXTRACT(HOUR FROM scheduled_time AT TIME ZONE 'Asia/Shanghai')
      ORDER BY total DESC
      LIMIT 10
    `);

    topPeriods.rows.forEach((row: any, index: number) => {
      const airport = row.airport_code;
      const terminal = row.terminal === 'ALL' ? '全部' : row.terminal;
      const hour = String(row.hour).padStart(2, '0');
      const count = row.total;
      console.log(`  ${index + 1}. ${airport} ${terminal} ${hour}:00: ${count}架`);
    });
    console.log();

  } catch (error: any) {
    console.error('验证失败:', error.message);
  } finally {
    process.exit(0);
  }
}

verifyHottestPeriods();
