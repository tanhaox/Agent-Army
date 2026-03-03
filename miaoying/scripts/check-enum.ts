import { getAuxiliaryPool } from '../src/storage/database/connection';

async function checkEnum() {
  const pool = getAuxiliaryPool('beijing');

  // 查询所有自定义枚举类型
  const enums = await pool.query(`
    SELECT
      t.typname as enum_name,
      e.enumlabel as enum_value
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    WHERE t.typname LIKE '%status%'
    ORDER BY t.typname, e.enumsortorder
  `);

  console.log('自定义枚举类型:');
  const byEnum: { [key: string]: string[] } = {};
  enums.rows.forEach((row: any) => {
    if (!byEnum[row.enum_name]) byEnum[row.enum_name] = [];
    byEnum[row.enum_name].push(row.enum_value);
  });

  for (const [enumName, values] of Object.entries(byEnum)) {
    console.log(`\n${enumName}:`);
    values.forEach((v: string) => console.log(`  - ${v}`));
  }

  process.exit(0);
}

checkEnum();
