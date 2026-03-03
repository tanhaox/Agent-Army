import { getDrizzleDb } from '../src/storage/database/connection';

async function check() {
  const db = getDrizzleDb();

  const result = await db.execute(`
    SELECT
      flight_no,
      scheduled_time,
      flight_status
    FROM arrival_flights
    WHERE airport_code = 'PKX'
    ORDER BY scheduled_time
    LIMIT 10
  `);

  console.log('业务数据库 beijing_didi 中的PKX数据 (前10条):');
  result.rows.forEach((row: any) => {
    console.log(`  ${row.flight_no} - ${row.scheduled_time} - ${row.flight_status}`);
  });

  // 统计总数
  const countResult = await db.execute(`
    SELECT
      COUNT(*) as total,
      MIN(scheduled_time) as first,
      MAX(scheduled_time) as last
    FROM arrival_flights
    WHERE airport_code = 'PKX'
  `);

  console.log('\n统计:');
  console.log(`  总记录: ${countResult.rows[0].total}`);
  console.log(`  第一班: ${countResult.rows[0].first}`);
  console.log(`  最后一班: ${countResult.rows[0].last}`);

  process.exit(0);
}

check();
