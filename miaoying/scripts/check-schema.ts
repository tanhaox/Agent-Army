import { getAuxiliaryPool } from '../src/storage/database/connection';

async function checkSchema() {
  const pool = getAuxiliaryPool('beijing');

  const result = await pool.query(`
    SELECT
      column_name,
      data_type,
      is_nullable,
      column_default
    FROM information_schema.columns
    WHERE table_name = 'arrival_flights'
      AND column_name = 'flight_status'
  `);

  console.log('flight_status 字段信息:');
  console.log(result.rows);

  // 检查约束
  const constraints = await pool.query(`
    SELECT
      conname as constraint_name,
      pg_get_constraintdef(oid) as constraint_definition
    FROM pg_constraint
    WHERE conrelid = 'arrival_flights'::regclass
  `);

  console.log('\n所有约束:');
  constraints.rows.forEach((row: any) => {
    console.log(`  ${row.constraint_name}: ${row.constraint_definition}`);
  });

  process.exit(0);
}

checkSchema();
