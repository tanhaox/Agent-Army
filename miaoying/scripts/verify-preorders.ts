import { getPool } from '../src/storage/database/connection';

async function verifyPreOrders(): Promise<void> {
  const pool = getPool();

  const sql = `
    SELECT
      "order_id",
      "start_loc_name",
      "time_pickup",
      "is_big_order",
      "special_tags"
    FROM "orders"
    WHERE "order_id" LIKE 'PRE-%'
    ORDER BY "created_at" DESC
    LIMIT 10
  `;

  try {
    const result = await pool.query(sql);
    console.log('✅ 查询成功！');
    console.log(`找到 ${result.rows.length} 条预订单\n`);

    result.rows.forEach((row, index) => {
      const tags = JSON.parse(row.special_tags || '{}');
      console.log(`${index + 1}. ${row.order_id}`);
      console.log(`   📍 地点: ${row.start_loc_name}`);
      console.log(`   ⏰ 时间: ${new Date(row.time_pickup).toLocaleString('zh-CN')}`);
      console.log(`   💰 大单: ${row.is_big_order ? '是' : '否'}`);
      console.log(`   🎭 场馆: ${tags.venueName}`);
      console.log(`   🎤 活动: ${tags.eventName}`);
      console.log(`   🎵 艺人: ${tags.artist}`);
      console.log(`   📅 日期: ${tags.eventDate} ${tags.eventWeekday} ${tags.startTime}-${tags.estimatedEndTime}`);
      console.log(`   ⭐ 重要性: ${tags.importance}/5`);
      console.log(`   🏢 容量: ${tags.venueCapacity}人`);
      console.log('');
    });
  } catch (error: any) {
    console.error('❌ 查询失败:', error.message);
  } finally {
    await pool.end();
  }
}

verifyPreOrders().catch(console.error);
