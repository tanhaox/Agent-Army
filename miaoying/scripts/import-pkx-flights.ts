/**
 * 导入PKX航班数据到数据库
 *
 * 用法: npx tsx scripts/import-pkx-flights.ts <data-file>
 * 示例: npx tsx scripts/import-pkx-flights.ts data/pkx-flights-2026-03-04-full.json
 */

import { getDrizzleDb } from '../src/storage/database/connection';
import { sql } from 'drizzle-orm';
import * as fs from 'fs';
import * as path from 'path';

interface FlightData {
  flight_no: string;
  airport_code: string;
  arrival_terminal: string | null;
  scheduled_time: string;
  estimated_time: string;
  actual_time: string | null;
  flight_status: string;
}

interface PKXResponse {
  success: boolean;
  data: {
    airport_code: string;
    airport_name: string;
    flight_type: string;
    date: string;
    fetched_at: string;
    total_flights: number;
    flights: FlightData[];
  };
}

async function importPKXFlights(dataFilePath: string) {
  const db = getDrizzleDb();

  console.log('========================================');
  console.log('PKX 航班数据导入');
  console.log('========================================');
  console.log(`数据文件: ${dataFilePath}`);
  console.log();

  try {
    // 1. 读取数据文件
    console.log('1. 读取数据文件...');
    const fullPath = path.resolve(process.cwd(), dataFilePath);
    const fileContent = fs.readFileSync(fullPath, 'utf-8');
    const jsonData: PKXResponse = JSON.parse(fileContent);

    if (!jsonData.success || !jsonData.data) {
      throw new Error('无效的数据格式');
    }

    const { flights, fetched_at, date } = jsonData.data;
    console.log(`  ✓ 读取成功: ${flights.length} 条航班记录`);
    console.log(`  ✓ 抓取时间: ${fetched_at}`);
    console.log(`  ✓ 航班日期: ${date}`);
    console.log();

    // 2. 检查表是否存在
    console.log('2. 检查数据库表...');
    const tableExists = await db.execute(sql`
      SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'arrival_flights'
      )
    `);

    if (!tableExists.rows[0]?.exists) {
      console.log('  ✗ 表 arrival_flights 不存在，请先运行迁移脚本');
      console.log('    命令: npx tsx scripts/create-flight-tables.ts');
      process.exit(1);
    }
    console.log('  ✓ 表存在');
    console.log();

    // 3. 清理当天的旧数据（可选）
    console.log('3. 清理旧数据...');
    const deleteResult = await db.execute(sql`
      DELETE FROM arrival_flights
      WHERE airport_code = 'PKX'
      AND DATE(scheduled_time) = ${date}
    `);
    console.log(`  ✓ 删除旧数据: ${deleteResult.rowCount ?? 0} 条`);
    console.log();

    // 4. 批量插入数据
    console.log('4. 插入航班数据...');
    let successCount = 0;
    let errorCount = 0;
    const batchSize = 50;

    for (let i = 0; i < flights.length; i += batchSize) {
      const batch = flights.slice(i, i + batchSize);

      try {
        for (const flight of batch) {
          await db.execute(sql`
            INSERT INTO arrival_flights (
              flight_no,
              airport_code,
              arrival_terminal,
              scheduled_time,
              estimated_time,
              actual_time,
              flight_status,
              fetched_at
            ) VALUES (
              ${flight.flight_no},
              ${flight.airport_code},
              ${flight.arrival_terminal},
              ${flight.scheduled_time},
              ${flight.estimated_time},
              ${flight.actual_time},
              ${flight.flight_status},
              ${fetched_at}
            )
            ON CONFLICT DO NOTHING
          `);
          successCount++;
        }

        // 显示进度
        const progress = Math.min(i + batchSize, flights.length);
        console.log(`  进度: ${progress}/${flights.length} (${Math.round(progress / flights.length * 100)}%)`);

      } catch (error: any) {
        console.error(`  ✗ 批次插入失败 (offset ${i}):`, error.message);
        errorCount += batch.length;
      }
    }

    console.log();
    console.log('========================================');
    console.log('✓ 导入完成！');
    console.log('========================================');
    console.log(`成功: ${successCount} 条`);
    console.log(`失败: ${errorCount} 条`);
    console.log();

    // 5. 验证数据
    console.log('5. 验证导入数据...');
    const verifyResult = await db.execute(sql`
      SELECT
        COUNT(*) as total,
        COUNT(DISTINCT flight_no) as unique_flights,
        COUNT(CASE WHEN flight_status = 'SCH' THEN 1 END) as scheduled,
        COUNT(CASE WHEN flight_status = 'DEP' THEN 1 END) as departed,
        COUNT(CASE WHEN flight_status = 'ARR' THEN 1 END) as arrived,
        COUNT(CASE WHEN flight_status = 'DLY' THEN 1 END) as delayed
      FROM arrival_flights
      WHERE airport_code = 'PKX'
      AND DATE(scheduled_time) = ${date}
    `);

    const stats = verifyResult.rows[0];
    console.log(`  总记录数: ${stats.total}`);
    console.log(`  不重复航班: ${stats.unique_flights}`);
    console.log(`  已安排 (SCH): ${stats.scheduled}`);
    console.log(`  已出发 (DEP): ${stats.departed}`);
    console.log(`  已到达 (ARR): ${stats.arrived}`);
    console.log(`  延误 (DLY): ${stats.delayed}`);
    console.log();

  } catch (error: any) {
    console.error('❌ 导入失败:', error.message);
    if (error.code) {
      console.error(`  错误代码: ${error.code}`);
    }
    process.exit(1);
  } finally {
    process.exit(0);
  }
}

// 获取命令行参数
const dataFile = process.argv[2];
if (!dataFile) {
  console.log('用法: npx tsx scripts/import-pkx-flights.ts <data-file>');
  console.log('示例: npx tsx scripts/import-pkx-flights.ts data/pkx-flights-2026-03-04-full.json');
  process.exit(1);
}

importPKXFlights(dataFile);
