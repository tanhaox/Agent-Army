import { getPool } from '../src/storage/database/connection';

async function verifyAllPreOrdersDetailed(): Promise<void> {
  const pool = getPool();

  const sql = `
    SELECT
      "order_id",
      "start_loc_name",
      "time_pickup",
      "trip_type",
      "poi_type",
      "is_big_order",
      "special_tags"
    FROM "orders"
    WHERE "order_id" LIKE 'PRE-%' OR "order_id" LIKE 'FLIGHT-%' OR "order_id" LIKE 'EX-%'
    ORDER BY
      CASE
        WHEN "order_id" LIKE 'FLIGHT-%' THEN 1
        WHEN "order_id" LIKE 'EX-%' THEN 2
        ELSE 3
      END,
      "time_pickup" ASC
    LIMIT 20
  `;

  try {
    const result = await pool.query(sql);
    console.log('✅ 查询成功！');
    console.log(`找到 ${result.rows.length} 条预订单\n`);

    let flightCount = 0;
    let exhibitionCount = 0;
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
      const isExhibition = row.order_id.startsWith('EX-');

      if (isFlight) flightCount++;
      else if (isExhibition) exhibitionCount++;
      else concertCount++;

      const icon = isFlight ? '✈️' : isExhibition ? '🏢' : '🎵';
      const typeLabel = isFlight ? '航班' : isExhibition ? '展会' : '演唱会';

      const timeStr = new Date(row.time_pickup).toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });

      console.log(`${icon} ${index + 1}. ${row.order_id} [${typeLabel}]`);
      console.log(`   📍 地点: ${row.start_loc_name}`);
      console.log(`   ⏰ 时间: ${timeStr}`);
      console.log(`   🏷️  类型: ${row.trip_type} | ${row.poiType}`);
      console.log(`   💰 大单: ${row.is_big_order ? '是' : '否'}`);

      // 展会特有信息
      if (isExhibition && tags.timeSlotLabel) {
        console.log(`   📅 时间点: ${tags.timeSlotLabel} (${tags.timeDescription})`);
      }

      console.log(`   📊 理由: ${tags.reason}\n`);
    });

    console.log('========================================');
    console.log('📊 统计:');
    console.log(`  ✈️ 航班预订单: ${flightCount} 个`);
    console.log(`  🏢 展会预订单: ${exhibitionCount} 个`);
    console.log(`  🎵 演唱会预订单: ${concertCount} 个`);
    console.log(`  📋 总计: ${result.rows.length} 个`);
    console.log('========================================\n');

  } catch (error: any) {
    console.error('❌ 查询失败:', error.message);
  } finally {
    await pool.end();
  }
}

verifyAllPreOrdersDetailed().catch(console.error);
