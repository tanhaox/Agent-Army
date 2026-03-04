/**
 * 天地图地理编码服务
 *
 * 功能：
 * 1. 地址 → 经纬度坐标转换（地理编码）
 * 2. 经纬度 → 地址转换（逆地理编码）
 *
 * 环境变量：
 * TIANDITU_API_KEY - 天地图API密钥（或 TIANDITU_TK）
 *
 * 坐标系说明：
 * - 天地图默认使用 GCJ-02 坐标系
 * - 支持多种坐标类型：WGS84、GCJ02、BD09
 */

/**
 * 天地图配置
 */
const TIANDITU_CONFIG = {
  // 地理编码API
  geocodeUrl: 'http://api.tianditu.gov.cn/geocoder',

  // 逆地理编码API（相同端点）
  reverseGeocodeUrl: 'http://api.tianditu.gov.cn/geocoder',

  // API密钥（从环境变量读取）
  get apiKey(): string {
    return process.env.TIANDITU_API_KEY || process.env.TIANDITU_TK || '';
  },
};

/**
 * 地理编码结果（地址 → 坐标）
 */
export interface GeocodeResult {
  success: boolean;
  lng?: number;
  lat?: number;
  address?: string; // 完整地址
  formattedAddress?: string; // 格式化地址
  level?: string; // 地址级别
  error?: string; // 错误信息
}

/**
 * 逆地理编码结果（坐标 → 地址）
 */
export interface ReverseGeocodeResult {
  formattedAddress: string; // 完整地址
  province: string; // 省份
  city: string; // 城市
  district: string; // 区县
  town: string; // 乡镇街道
  street: string; // 街道
}

/**
 * 地理编码选项
 */
export interface GeocodeOptions {
  city?: string; // 城市名称（限定搜索范围）
  mapBound?: string; // 地图范围（矩形区域，格式： minX,minY,maxX,maxY）
  level?: string; // 地址级别（如：省、市、区县、乡镇、村庄）
}

/**
 * 调用天地图地理编码API（地址 → 坐标）
 *
 * API文档：
 * http://api.tianditu.gov.cn/geocoder?ds={JSON数据}&tk={您的密钥}
 *
 * 示例请求：
 * {
 *   "keyWord": "北京市朝阳区",
 *   "level": "区县",
 *   "mapBound": "115.7,39.4,117.4,41.0",
 *   "city": "北京市"
 * }
 *
 * @param address 待编码的地址
 * @param options 可选配置
 * @returns Promise<GeocodeResult> 地理编码结果
 */
export async function geocode(
  address: string,
  options?: GeocodeOptions
): Promise<GeocodeResult> {
  try {
    const { apiKey } = TIANDITU_CONFIG;

    if (!apiKey) {
      console.error('【天地图地理编码】API密钥未配置，请设置环境变量 TIANDITU_API_KEY 或 TIANDITU_TK');
      return {
        success: false,
        error: '天地图API密钥未配置',
      };
    }

    // 构建请求数据
    const requestData: Record<string, any> = {
      keyWord: address,
    };

    // 可选参数
    if (options?.city) {
      requestData.city = options.city;
    }
    if (options?.mapBound) {
      requestData.mapBound = options.mapBound;
    }
    if (options?.level) {
      requestData.level = options.level;
    }

    // 构建URL
    const ds = encodeURIComponent(JSON.stringify(requestData));
    const url = `${TIANDITU_CONFIG.geocodeUrl}?ds=${ds}&tk=${apiKey}`;

    console.log(`【天地图地理编码】请求地址: ${address}`, options || '');

    // 发起请求
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error(`【天地图地理编码】HTTP错误: ${response.status} ${response.statusText}`);
      return {
        success: false,
        error: `HTTP错误: ${response.status}`,
      };
    }

    const data = await response.json();

    // 检查返回状态
    if (data.status !== '0') {
      console.error('【天地图地理编码】API返回错误', {
        status: data.status,
        message: data.msg || data.message,
      });
      return {
        success: false,
        error: data.msg || data.message || '地理编码失败',
      };
    }

    // 检查返回数据（天地图直接返回location，不是result.location）
    // 返回格式：{ status: "0", location: { lon, lat, ... } }
    if (!data.location) {
      console.error('【天地图地理编码】无返回结果', data);
      return {
        success: false,
        error: '无返回结果',
      };
    }

    const location = data.location;

    const result: GeocodeResult = {
      success: true,
      lng: parseFloat(location.lon),
      lat: parseFloat(location.lat),
      address: location.address || location.formatted_address || address,
      formattedAddress: location.formatted_address || location.keyWord || address,
      level: location.level,
    };

    console.log(`【天地图地理编码】成功: ${address} -> (${result.lng}, ${result.lat})`);

    return result;
  } catch (error) {
    console.error('【天地图地理编码】请求异常', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : '地理编码请求失败',
    };
  }
}

/**
 * 调用天地图逆地理编码API（坐标 → 地址）
 *
 * API文档：
 * http://api.tianditu.gov.cn/geocoder?postStr={JSON数据}&type=geocode&tk={您的密钥}
 *
 * 支持的坐标类型：
 * - wgs84：GPS坐标
 * - gcj02：火星坐标（默认）
 * - bd09：百度坐标
 *
 * @param lng 经度
 * @param lat 纬度
 * @param coordType 坐标类型（默认：gcj02）
 * @returns Promise<ReverseGeocodeResult | null> 逆地理编码结果
 */
export async function reverseGeocode(
  lng: number,
  lat: number,
  coordType: 'wgs84' | 'gcj02' | 'bd09' = 'gcj02'
): Promise<ReverseGeocodeResult | null> {
  try {
    const { apiKey } = TIANDITU_CONFIG;

    if (!apiKey) {
      console.error('【天地图逆地理编码】API密钥未配置');
      return null;
    }

    // 构建请求数据
    const requestData = {
      lon: lng.toString(),
      lat: lat.toString(),
      ver: 1, // 版本号
    };

    // 构建URL
    const postStr = encodeURIComponent(JSON.stringify(requestData));
    const url = `${TIANDITU_CONFIG.reverseGeocodeUrl}?type=geocode&postStr=${postStr}&tk=${apiKey}`;

    console.log(`【天地图逆地理编码】请求坐标: (${lng}, ${lat}), 坐标系: ${coordType}`);

    // 发起请求
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error(`【天地图逆地理编码】HTTP错误: ${response.status} ${response.statusText}`);
      return null;
    }

    const data = await response.json();

    // 检查返回状态
    if (data.status !== '0') {
      console.error('【天地图逆地理编码】API返回错误', {
        status: data.status,
        message: data.msg || data.message,
      });
      return null;
    }

    // 检查返回数据
    if (!data.result) {
      console.error('【天地图逆地理编码】无返回结果', data);
      return null;
    }

    const result: ReverseGeocodeResult = {
      formattedAddress: data.result.formatted_address || '',
      province: data.result.addressComponent?.province || '',
      city: data.result.addressComponent?.city || '',
      district: data.result.addressComponent?.district || '',
      town: data.result.addressComponent?.town || '',
      street: data.result.addressComponent?.street || '',
    };

    console.log(`【天地图逆地理编码】成功: (${lng}, ${lat}) -> ${result.formattedAddress}`);

    return result;
  } catch (error) {
    console.error('【天地图逆地理编码】请求异常', error);
    return null;
  }
}

/**
 * 根据坐标获取城市名称
 *
 * @param lng 经度
 * @param lat 纬度
 * @param coordType 坐标类型（默认：gcj02）
 * @returns Promise<string | null> 城市名称（如："北京市"）
 */
export async function getCityByCoords(
  lng: number,
  lat: number,
  coordType: 'wgs84' | 'gcj02' | 'bd09' = 'gcj02'
): Promise<string | null> {
  try {
    const result = await reverseGeocode(lng, lat, coordType);

    if (!result) {
      return null;
    }

    // 返回城市名称（保留"市"后缀）
    return result.city || null;
  } catch (error) {
    console.error('【天地图逆地理编码】获取城市失败', error);
    return null;
  }
}

/**
 * 格式化坐标为PostGIS POINT格式
 *
 * @param lng 经度
 * @param lat 纬度
 * @returns PostGIS POINT字符串
 */
export function formatAsPoint(lng: number, lat: number): string {
  return `POINT(${lng} ${lat})`;
}
