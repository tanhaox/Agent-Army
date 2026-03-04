/**
 * 天地图 vs 百度地图 API 对比测试
 *
 * 测试目标：
 * 1. 验证天地图API功能完整性
 * 2. 对比天地图和百度地图的数据精度差异
 * 3. 评估迁移可行性
 *
 * 运行方式:
 * node scripts/test-tianditu-vs-baidu.js
 */

// ===================== 配置 =====================

const CONFIG = {
  // 天地图API Key
  tianditu: {
    apiKey: '2da6f7f8309317ea0e3dadf251525dd2',
    baseUrl: 'http://api.tianditu.gov.cn',
  },
  // 百度地图API Key（从环境变量读取）
  baidu: {
    apiKey: process.env.BAIDU_MAP_AK || '',
    baseUrl: 'https://api.map.baidu.com',
  },
};

// ===================== 测试用例 =====================

const TEST_CASES = {
  // 地址解析测试用例
  addresses: [
    { name: '天安门', city: '北京' },
    { name: '三里屯', city: '北京' },
    { name: '北京南站', city: '北京' },
    { name: '六里桥客运主枢纽', city: '北京' },
  ],
  // 驾车路线测试用例（起点坐标，终点坐标）
  routes: [
    {
      name: '天安门 → 国贸',
      start: { lon: 116.397128, lat: 39.916527 }, // 天安门
      end: { lon: 116.458762, lat: 39.909723 },   // 国贸
    },
    {
      name: '三里屯 → 北京南站',
      start: { lon: 116.455789, lat: 39.937562 }, // 三里屯
      end: { lon: 116.378176, lat: 39.865299 },   // 北京南站
    },
  ],
  // 逆地理编码测试用例
  coordinates: [
    { lon: 116.397128, lat: 39.916527, name: '天安门附近' },
    { lon: 116.458762, lat: 39.909723, name: '国贸附近' },
  ],
};

// ===================== 天地图API =====================

/**
 * 天地图地名搜索（地址 → 坐标）
 */
async function tiandituGeocode(address, city = '') {
  try {
    const params = encodeURIComponent(JSON.stringify({
      keyWord: address,
      level: '12', // 完整显示区县边界
      mapBound: `${city === '北京' ? '115.7,39.4,117.4,41.0' : '116.0,39.0,117.0,40.0'}`,
      queryType: '1', // 关键词查询
      start: '0',
      count: '1',
    }));

    const url = `${CONFIG.tianditu.baseUrl}/v2/search?postStr=${params}&type=query&tk=${CONFIG.tianditu.apiKey}`;
    const response = await fetch(url);
    const data = await response.json();

    if (data.status?.infocode === 1000 && data.pois && data.pois.length > 0) {
      const poi = data.pois[0];
      const [lon, lat] = poi.lonlat.split(',').map(Number);
      return {
        success: true,
        address: poi.name,
        lon,
        lat,
        formattedAddress: `${poi.name} (${poi.address || ''})`,
      };
    }

    return { success: false, error: '未找到结果' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * 天地图逆地理编码（坐标 → 地址）
 */
async function tiandituReverseGeocode(lon, lat) {
  try {
    const params = encodeURIComponent(JSON.stringify({
      lon,
      lat,
      ver: 1,
    }));

    const url = `${CONFIG.tianditu.baseUrl}/geocoder?postStr=${params}&type=geocode&tk=${CONFIG.tianditu.apiKey}`;
    const response = await fetch(url);
    const data = await response.json();

    if (data.status === '0' && data.result) {
      return {
        success: true,
        formattedAddress: data.result.formatted_address,
        addressComponent: data.result.addressComponent,
      };
    }

    return { success: false, error: data.msg || '查询失败' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * 天地图驾车路线规划
 */
async function tiandituDrivingRoute(startLon, startLat, endLon, endLat) {
  try {
    const params = encodeURIComponent(JSON.stringify({
      orig: `${startLon},${startLat}`,
      dest: `${endLon},${endLat}`,
      style: '0', // 最快路线
    }));

    const url = `${CONFIG.tianditu.baseUrl}/drive?postStr=${params}&type=search&tk=${CONFIG.tianditu.apiKey}`;
    const response = await fetch(url);
    const xmlText = await response.text();

    // 解析XML（简化版）
    const distanceMatch = xmlText.match(/<distance>([^<]+)<\/distance>/);
    const durationMatch = xmlText.match(/<duration>([^<]+)<\/duration>/);

    if (distanceMatch && durationMatch) {
      return {
        success: true,
        distance: parseFloat(distanceMatch[1]), // 公里
        duration: parseFloat(durationMatch[1]), // 秒
      };
    }

    return { success: false, error: '未找到有效路线' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ===================== 百度地图API =====================

/**
 * 百度地图地理编码（地址 → 坐标）
 */
async function baiduGeocode(address, city = '') {
  try {
    if (!CONFIG.baidu.apiKey) {
      return { success: false, error: '百度地图 API Key 未配置' };
    }

    const addressWithCity = city ? `${city}${address}` : address;
    const url = `${CONFIG.baidu.baseUrl}/geocoding/v3?address=${encodeURIComponent(addressWithCity)}&city=${encodeURIComponent(city)}&output=json&ak=${CONFIG.baidu.apiKey}`;

    const response = await fetch(url);
    const data = await response.json();

    if (data.status === 0 && data.result && data.result.location) {
      return {
        success: true,
        address: address,
        lon: data.result.location.lng,
        lat: data.result.location.lat,
        formattedAddress: data.result.formatted_address || address,
      };
    }

    return { success: false, error: data.message || '未找到结果' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * 百度地图逆地理编码（坐标 → 地址）
 */
async function baiduReverseGeocode(lon, lat) {
  try {
    if (!CONFIG.baidu.apiKey) {
      return { success: false, error: '百度地图 API Key 未配置' };
    }

    const url = `${CONFIG.baidu.baseUrl}/reverse_geocoding/v3?ak=${CONFIG.baidu.apiKey}&output=json&location=${lat},${lon}`;

    const response = await fetch(url);
    const data = await response.json();

    if (data.status === 0 && data.result) {
      return {
        success: true,
        formattedAddress: data.result.formatted_address,
        addressComponent: data.result.addressComponent,
      };
    }

    return { success: false, error: data.message || '查询失败' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * 百度地图驾车路线规划
 */
async function baiduDrivingRoute(startLon, startLat, endLon, endLat) {
  try {
    if (!CONFIG.baidu.apiKey) {
      return { success: false, error: '百度地图 API Key 未配置' };
    }

    const origin = `${startLat},${startLon}`;
    const destination = `${endLat},${endLon}`;
    const url = `${CONFIG.baidu.baseUrl}/directionlite/v1/driving?ak=${CONFIG.baidu.apiKey}&origin=${origin}&destination=${destination}&coord_type=bd09ll`;

    const response = await fetch(url);
    const data = await response.json();

    if (data.status === 0 && data.result && data.result.routes && data.result.routes.length > 0) {
      const route = data.result.routes[0];
      return {
        success: true,
        distance: route.distance / 1000, // 转换为公里
        duration: route.duration,         // 秒
      };
    }

    return { success: false, error: data.message || '未找到有效路线' };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// ===================== 工具函数 =====================

/**
 * 计算两个坐标点之间的距离（Haversine公式，单位：公里）
 */
function calculateDistance(lon1, lat1, lon2, lat2) {
  const R = 6371; // 地球半径（公里）
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

/**
 * 打印表格行
 */
function printTableRow(headers, rows) {
  const colWidths = headers.map((h, i) => {
    const maxWidth = Math.max(h.length, ...rows.map((r) => String(r[i]).length));
    return maxWidth + 2;
  });

  // 打印表头
  console.log('┌' + colWidths.map((w) => '─'.repeat(w)).join('┬') + '┐');
  console.log(
    '│' + headers.map((h, i) => h.padEnd(colWidths[i])).join('│') + '│'
  );
  console.log('├' + colWidths.map((w) => '─'.repeat(w)).join('┼') + '┤');

  // 打印数据行
  for (const row of rows) {
    console.log(
      '│' + row.map((c, i) => String(c).padEnd(colWidths[i])).join('│') + '│'
    );
  }

  console.log('└' + colWidths.map((w) => '─'.repeat(w)).join('┴') + '┘');
}

// ===================== 测试函数 =====================

/**
 * 测试地理编码（地址 → 坐标）
 */
async function testGeocode() {
  console.log('\n' + '='.repeat(80));
  console.log('📍 测试1：地理编码（地址 → 坐标）');
  console.log('='.repeat(80));

  const headers = ['地址', '平台', '经度', '纬度', '状态', '地址描述'];
  const rows = [];

  for (const testCase of TEST_CASES.addresses) {
    // 天地图
    const tiandituResult = await tiandituGeocode(testCase.name, testCase.city);
    rows.push([
      testCase.name,
      '天地图',
      tiandituResult.success ? tiandituResult.lon.toFixed(6) : 'N/A',
      tiandituResult.success ? tiandituResult.lat.toFixed(6) : 'N/A',
      tiandituResult.success ? '✅' : '❌',
      tiandituResult.success ? tiandituResult.formattedAddress.substring(0, 20) : tiandituResult.error,
    ]);

    // 百度地图
    const baiduResult = await baiduGeocode(testCase.name, testCase.city);
    rows.push([
      '',
      '百度',
      baiduResult.success ? baiduResult.lon.toFixed(6) : 'N/A',
      baiduResult.success ? baiduResult.lat.toFixed(6) : 'N/A',
      baiduResult.success ? '✅' : '❌',
      baiduResult.success ? baiduResult.formattedAddress.substring(0, 20) : baiduResult.error,
    ]);

    // 如果两者都成功，计算偏差
    if (tiandituResult.success && baiduResult.success) {
      const distance = calculateDistance(
        tiandituResult.lon,
        tiandituResult.lat,
        baiduResult.lon,
        baiduResult.lat
      );
      rows.push(['', '偏差', '', '', `${distance.toFixed(2)} km`, '']);
    }
  }

  printTableRow(headers, rows);
}

/**
 * 测试逆地理编码（坐标 → 地址）
 */
async function testReverseGeocode() {
  console.log('\n' + '='.repeat(80));
  console.log('📍 测试2：逆地理编码（坐标 → 地址）');
  console.log('='.repeat(80));

  const headers = ['坐标', '平台', '解析结果', '状态'];
  const rows = [];

  for (const testCase of TEST_CASES.coordinates) {
    const coordStr = `${testCase.lon}, ${testCase.lat}`;

    // 天地图
    const tiandituResult = await tiandituReverseGeocode(testCase.lon, testCase.lat);
    rows.push([
      coordStr,
      '天地图',
      tiandituResult.success ? tiandituResult.formattedAddress.substring(0, 25) : 'N/A',
      tiandituResult.success ? '✅' : '❌',
    ]);

    // 百度地图
    const baiduResult = await baiduReverseGeocode(testCase.lon, testCase.lat);
    rows.push([
      '',
      '百度',
      baiduResult.success ? baiduResult.formattedAddress.substring(0, 25) : 'N/A',
      baiduResult.success ? '✅' : '❌',
    ]);
  }

  printTableRow(headers, rows);
}

/**
 * 测试驾车路线规划
 */
async function testDrivingRoute() {
  console.log('\n' + '='.repeat(80));
  console.log('🚗 测试3：驾车路线规划');
  console.log('='.repeat(80));

  const headers = ['路线', '平台', '距离(km)', '时间(秒)', '状态'];
  const rows = [];

  for (const testCase of TEST_CASES.routes) {
    // 天地图
    const tiandituResult = await tiandituDrivingRoute(
      testCase.start.lon,
      testCase.start.lat,
      testCase.end.lon,
      testCase.end.lat
    );
    rows.push([
      testCase.name,
      '天地图',
      tiandituResult.success ? tiandituResult.distance.toFixed(2) : 'N/A',
      tiandituResult.success ? tiandituResult.duration.toFixed(0) : 'N/A',
      tiandituResult.success ? '✅' : '❌',
    ]);

    // 百度地图
    const baiduResult = await baiduDrivingRoute(
      testCase.start.lon,
      testCase.start.lat,
      testCase.end.lon,
      testCase.end.lat
    );
    rows.push([
      '',
      '百度',
      baiduResult.success ? baiduResult.distance.toFixed(2) : 'N/A',
      baiduResult.success ? baiduResult.duration.toFixed(0) : 'N/A',
      baiduResult.success ? '✅' : '❌',
    ]);

    // 如果两者都成功，计算差异
    if (tiandituResult.success && baiduResult.success) {
      const distanceDiff = Math.abs(tiandituResult.distance - baiduResult.distance);
      const durationDiff = Math.abs(tiandituResult.duration - baiduResult.duration);
      const distancePercent = (distanceDiff / baiduResult.distance * 100).toFixed(1);
      rows.push(['', '差异', `${distanceDiff.toFixed(2)} (${distancePercent}%)`, `${durationDiff.toFixed(0)}`, '']);
    }
  }

  printTableRow(headers, rows);
}

/**
 * 主测试函数
 */
async function main() {
  console.log('\n' + '🚀'.repeat(40));
  console.log('天地图 vs 百度地图 API 对比测试');
  console.log('🚀'.repeat(40));

  // 检查API Key
  if (!CONFIG.baidu.apiKey) {
    console.log('\n⚠️  警告：百度地图 API Key 未配置');
    console.log('   将只测试天地图API\n');
  }

  try {
    // 运行测试
    await testGeocode();
    await testReverseGeocode();
    await testDrivingRoute();

    console.log('\n' + '='.repeat(80));
    console.log('✅ 测试完成');
    console.log('='.repeat(80) + '\n');

  } catch (error) {
    console.error('\n❌ 测试失败:', error);
    process.exit(1);
  }
}

// 运行测试
main();
