import { getAuxiliaryPool } from '../src/storage/database/connection';

async function checkDuplicates() {
  const pool = getAuxiliaryPool('beijing');

  // 检查是否有唯一约束
  const constraints = await pool.query(`
    SELECT
      conname,
      pg_get_constraintdef(oid) as definition
    FROM pg_constraint
    WHERE conrelid = 'arrival_flights'::regclass
      AND contype = 'u'
  `);

  console.log('唯一约束:');
  constraints.rows.forEach((row: any) => {
    console.log(`  ${row.conname}: ${row.definition}`);
  });

  // 检查重复数据
  const duplicates = await pool.query(`
    SELECT flight_no, scheduled_time, COUNT(*) as count
    FROM arrival_flights
    WHERE airport_code = 'PKX'
    GROUP BY flight_no, scheduled_time
    HAVING COUNT(*) > 1
  `);

  console.log('\n重复数据:');
  console.log(`  ${duplicates.rows.length} 组重复`);

  // 统计总数据
  const total = await pool.query(`
    SELECT
      COUNT(*) as total,
      COUNT(DISTINCT CONCAT(flight_no, '|', scheduled_time)) as unique
    FROM arrival_flights
    WHERE airport_code = 'PKX'
  `);

  console.log('\n数据统计:');
  console.log(`  总记录数: ${total.rows[0].total}`);
  console.log(`  唯一记录: ${total.rows[0].unique}`);

  process.exit(0);
}

checkDuplicates();
