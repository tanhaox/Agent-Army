import { getAuxiliaryPool } from '../src/storage/database/connection';

async function check() {
  const pool = getAuxiliaryPool('beijing');

  // 查询所有PKX数据
  const result = await pool.query(`
    SELECT
      flight_no,
      scheduled_time,
      flight_status
    FROM arrival_flights
    WHERE airport_code = 'PKX'
    ORDER BY scheduled_time
  `);

  console.log(`辅助数据库 beijing_auxiliary 中的PKX数据 (共${result.rows.length}条):`);
  result.rows.forEach((row: any, index: number) => {
    if (index < 10 || index >= result.rows.length - 5) {
      console.log(`  ${row.flight_no} - ${row.scheduled_time} - ${row.flight_status}`);
    } else if (index === 10) {
      console.log('  ...');
    }
  });

  // 统计不同日期的数据
  const dateStats = await pool.query(`
    SELECT
      DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai') as date,
      COUNT(*) as count
    FROM arrival_flights
    WHERE airport_code = 'PKX'
    GROUP BY DATE(scheduled_time AT TIME ZONE 'Asia/Shanghai')
  `);

  console.log('\n按日期统计:');
  dateStats.rows.forEach((row: any) => {
    console.log(`  ${row.date}: ${row.count}条`);
  });

  process.exit(0);
}

check();
