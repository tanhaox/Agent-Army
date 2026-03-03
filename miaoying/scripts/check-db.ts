import { getDrizzleDb } from '../src/storage/database/connection';
import { sql } from 'drizzle-orm';

async function check() {
  const db = getDrizzleDb();

  const result = await db.execute(`
    SELECT COUNT(*) as count,
           COUNT(DISTINCT flight_status) as status_count
    FROM arrival_flights
    WHERE airport_code = 'PKX'
  `);

  console.log('业务数据库 beijing_didi:');
  console.log('  PKX记录:', result.rows[0].count);
  console.log('  状态种类:', result.rows[0].status_count);

  process.exit(0);
}

check();
