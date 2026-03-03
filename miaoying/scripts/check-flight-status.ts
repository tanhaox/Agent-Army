import { getAuxiliaryPool } from '../src/storage/database/connection';

async function checkStatus() {
  const pool = getAuxiliaryPool('beijing');

  // 查询辅助数据库中的状态值
  const result = await pool.query(`
    SELECT DISTINCT flight_status
    FROM arrival_flights
    WHERE airport_code = 'PEK'
    LIMIT 10
  `);

  console.log('辅助数据库 beijing_auxiliary 中的 flight_status 值:');
  result.rows.forEach((row: any) => {
    console.log(`  - ${row.flight_status}`);
  });

  process.exit(0);
}

checkStatus();
