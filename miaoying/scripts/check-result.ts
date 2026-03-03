import { config } from 'dotenv';
config({ path: '.env.local' });

import { getDrizzleDb } from '../src/storage/database/connection';
import { orders } from '../src/storage/database/shared/schema';
import { sql } from 'drizzle-orm';

(async () => {
  const db = getDrizzleDb();

  const result = await db
    .select({ count: sql`count(*)::int` })
    .from(orders)
    .where(sql`order_id LIKE 'REAL-%'`);

  console.log('REAL-订单数量:', result[0]?.count || 0);

  // 查看前5条
  const samples = await db
    .select({ orderId: orders.orderId, startLocName: orders.startLocName })
    .from(orders)
    .where(sql`order_id LIKE 'REAL-%'`)
    .limit(5);

  console.log('示例订单:', samples);

  process.exit(0);
})();
