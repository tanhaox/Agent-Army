/**
 * PKX 航班数据抓取服务（Node.js 包装器）
 *
 * ⚠️⚠️⚠️ 临时方案警告 ⚠️⚠️⚠️
 *
 * 当前实现：使用 Python + undetected-chromedriver 爬取 Trip.com 网站
 *
 * 【重要说明】：
 * 1. 这是**临时方案**，仅用于开发和测试阶段
 * 2. 生产环境**必须**替换为官方 API 或其他稳定数据源
 * 3. 爬取方案存在以下风险：
 *    - 不稳定：网站结构变化会导致爬取失败
 *    - 性能差：单次抓取耗时 ~30 秒（API 仅需 ~3 秒）
 *    - 维护成本高：需要持续更新爬取逻辑
 *    - 法律风险：可能违反网站服务条款
 *    - 资源占用高：需要运行 Chrome 浏览器（~1GB 内存）
 *
 * 【后续行动】：
 * - 寻找大兴机场官方 API（类似 PEK 的 bcia.com.cn）
 * - 或联系 Trip.com 获取官方 API 接口
 * - 或使用第三方航班数据服务（如 FlightAware、VariFlight）
 *
 * 【降级策略】：
 * - 如果爬取失败，返回空数组（不影响 PEK 数据）
 * - 错误信息会记录到日志，便于监控
 *
 * 调用 Python 脚本进行抓取
 */

import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface FlightRecord {
  flightNo: string;
  airportCode: 'PKX';
  arrivalTerminal: string | null;
  scheduledTime: Date;
  estimatedTime: Date | null;
  actualTime: Date | null;
  flightStatus: 'ARV' | 'EST' | 'SCH' | 'CNL' | 'DLY';
}

interface PythonResult {
  success: boolean;
  data?: {
    airport_code: string;
    airport_name: string;
    flight_type: string;
    date: string;
    fetched_at: string;
    flights: Array<{
      flight_no: string;
      airport_code: string;
      arrival_terminal: null;
      scheduled_time: string;
      estimated_time: string;
      actual_time: null;
      flight_status: string;
    }>;
  };
  error?: string;
}

/**
 * 调用 Python 脚本抓取 PKX 航班
 */
async function fetchPKXFlightsFromPython(targetDate?: Date): Promise<FlightRecord[]> {
  // 格式化目标日期
  const dateStr = targetDate
    ? targetDate.toISOString().split('T')[0]
    : undefined;

  const dateDesc = dateStr ? `${dateStr} 的` : '今天';
  console.log(`[PKX抓取] 调用 Python 脚本抓取${dateDesc}航班...`);

  try {
    // 构建命令
    const cmd = dateStr
      ? `python scripts/fetch-pkx-flights-final.py --date ${dateStr}`
      : 'python scripts/fetch-pkx-flights-final.py';

    console.log(`[PKX抓取] 执行命令: ${cmd}`);

    // 调用 Python 脚本
    const { stdout, stderr } = await execAsync(cmd, {
      cwd: process.cwd(),
      timeout: 120000, // 120秒超时（2分钟，足够 Python 脚本完成）
      maxBuffer: 1024 * 1024 * 10, // 10MB 缓冲区
    });

    if (stderr) {
      console.error('[PKX抓取] Python stderr:', stderr);
    }

    // 解析 JSON 输出
    const result: PythonResult = JSON.parse(stdout);

    if (!result.success) {
      throw new Error(result.error || '未知错误');
    }

    if (!result.data) {
      throw new Error('Python 脚本返回数据为空');
    }

    // 转换为标准格式
    const flights: FlightRecord[] = result.data.flights.map(f => ({
      flightNo: f.flight_no,
      airportCode: 'PKX' as const,
      arrivalTerminal: f.arrival_terminal,
      scheduledTime: new Date(f.scheduled_time),
      estimatedTime: new Date(f.estimated_time),
      actualTime: f.actual_time ? new Date(f.actual_time) : null,
      flightStatus: f.flight_status as FlightRecord['flightStatus']
    }));

    console.log(`[PKX抓取] 成功！获取 ${flights.length} 个航班`);

    return flights;

  } catch (error) {
    console.error('[PKX抓取] 调用失败:', error);

    // 如果 Python 脚本失败，返回空数组
    console.log('[PKX抓取] ⚠️  返回空数组');
    return [];
  }
}

/**
 * 获取今天所有到达航班（通过 Python）
 */
export async function fetchTodayPKXArrivals(): Promise<FlightRecord[]> {
  return fetchPKXFlightsFromPython();
}

/**
 * 获取明天所有到达航班（通过 Python）
 */
export async function fetchTomorrowPKXArrivals(): Promise<FlightRecord[]> {
  const tomorrow = new Date();
  tomorrow.setDate(tomorrow.getDate() + 1);
  return fetchPKXFlightsFromPython(tomorrow);
}
