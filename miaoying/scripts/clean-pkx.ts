import { getAuxiliaryPool } from '../src/storage/database/connection';

async function clean() {
  const pool = getAuxiliaryPool('beijing');

  // 删除所有PKX数据
  const result = await pool.query(`
    DELETE FROM arrival_flights
    WHERE airport_code = 'PKX'
  `);

  console.log('已清理 PKX 数据:', result.rowCount, '条');

  process.exit(0);
}

clean();
