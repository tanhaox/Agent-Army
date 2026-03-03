import { getPool } from '../src/storage/database/connection';

async function verifyAllPreOrders(): Promise<void> {
  const pool = getPool();

  const sql = `
    SELECT
      "order_id",
      "start_loc_name",
      "time_pickup",
      "trip_type",
      "is_big_order",
      "special_tags"
    FROM "orders"
    WHERE "order_id" LIKE 'PRE-%' OR "order_id" LIKE 'FLIGHT-%'
    ORDER BY
      CASE
        WHEN "order_id" LIKE 'FLIGHT-%' THEN 1
        ELSE 2
      END,
      "created_at" DESC
    LIMIT 15
  `;

  try {
    const result = await pool.query(sql);
    console.log('✅ 查询成功！');
    console.log(`找到 ${result.rows.length} 条预订单\n`);

    let flightCount = 0;
    let concertCount = 0;

    result.rows.forEach((row, index) => {
      let tags = {};
      try {
        tags = typeof row.special_tags === 'string'
          ? JSON.parse(row.special_tags || '{}')
          : row.special_tags || {};
      } catch (e) {
        tags = { source: 'unknown' };
      }

      const isFlight = row.order_id.startsWith('FLIGHT-');

      if (isFlight) flightCount++;
      else concertCount++;

      const icon = isFlight ? '✈️' : '🎵';
      const typeLabel = isFlight ? '航班' : '演唱会';

      console.log(`${icon} ${index + 1}. ${row.order_id} [${typeLabel}]`);
      console.log(`   📍 地点: ${row.start_loc_name}`);
      console.log(`   ⏰ 时间: ${new Date(row.time_pickup).toLocaleString('zh-CN')}`);
      console.log(`   🚗 类型: ${row.trip_type}`);
      console.log(`   💰 大单: ${row.is_big_order ? '是' : '否'}`);
      console.log(`   📊 理由: ${tags.reason}`);
      console.log('');
    });

    console.log('========================================');
    console.log('📊 统计:');
    console.log(`  🎵 演唱会预订单: ${concertCount} 个`);
    console.log(`  ✈️ 航班预订单: ${flightCount} 个`);
    console.log(`  📋 总计: ${result.rows.length} 个`);
    console.log('========================================\n');

  } catch (error: any) {
    console.error('❌ 查询失败:', error.message);
  } finally {
    await pool.end();
  }
}

verifyAllPreOrders().catch(console.error);
