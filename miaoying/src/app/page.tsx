'use client';

import BottomNav from '@/components/BottomNav';
import SimpleMapAppSelector, { type MapApp } from '@/components/MapAppSelector';
import RecommendationCarousel from '@/components/RecommendationCarousel';
import DevConsole from '@/components/dev-console';
import { APP_CONFIG } from '@/config/app.config';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { getLocation } from '@/utils/geolocation';
import { openNavigationToApp, type NavigationOptions } from '@/utils/navigation';
import { getBrowserName } from '@/utils/locationUtils';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function Home() {
  // ✅ 所有Hooks必须在顶部调用，不能有条件调用
  const { user, token, isLoading } = useAuth();
  const { styles, isReady: themeReady } = useTheme();
  const router = useRouter();

  // 状态定义（必须在条件判断之前）
  const [todayStats, setTodayStats] = useState({
    totalOrders: 0,
    totalPrice: '0',
    avgPrice: '0',
  });
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [unlockedBigOrder, setUnlockedBigOrder] = useState(false);
  const [loadingRecommendations, setLoadingRecommendations] = useState(false);
  const [selectedRecommendationType, setSelectedRecommendationType] = useState<
    'big_order' | 'high_rate' | 'user_experience' | null
  >(null);
  const [locationReady, setLocationReady] = useState(false);
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [currentAddress, setCurrentAddress] = useState<string | null>('正在获取位置信息...');
  const [locationAccuracy, setLocationAccuracy] = useState<number | null>(null);
  const [locationMethod, setLocationMethod] = useState<string>('');
  const [locationBrowser, setLocationBrowser] = useState<string>('');
  const [orderStats, setOrderStats] = useState<{
    totalOrders: number;
    avgPrice: string;
    bestEfficiencyData: {
      time: string;
      mileage: string;
    } | null;
    topOrderTypes: string[];
    topDistrict: string | null;
    eventsInfo?: {
      concerts: Array<{
        id: string;
        dateLabel: string;
        time: string;
        location: string;
      }>;
      exhibitions: Array<{
        id: string;
        dateLabel: string;
        time: string;
        location: string;
      }>;
      flightCount: number;
    };
  } | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  // 航班预测数据状态
  const [flightPrediction, setFlightPrediction] = useState<{
    currentTime: string;
    predictionPeriod: string;
    airports: Array<{
      code: string;
      name: string;
      terminals: Array<{
        name: string;
        hourlyBreakdown: Array<{
          hour: number;
          timeRange: string;
          plannedCount: number;
          estimatedCount: number;
        }>;
        total3Hours: number;
        recommendation: string;
      }>;
    }>;
    summary: {
      hottestAirport: string;
      hottestTerminal: string;
      hottestHour: string;
      advice: string;
      topPeriods: Array<{
        timeRange: string;
        count: number;
        terminal: string;
      }>;
    };
  } | null>(null);
  const [loadingPrediction, setLoadingPrediction] = useState(false);

  // 天气数据状态
  const [weatherData, setWeatherData] = useState<{
    date: Date;
    year: number;
    month: number;
    day: number;
    weekDayName: string;
    isWorkday: boolean;
    weatherText: string;
    temperature: number;
    feelsLike?: number;
    humidity?: number;
    windDir?: string;
    windScale?: string;
    hourlyForecast?: Array<{
      time: string;
      temp: string;
      text: string;
    }>;
  } | null>(null);

  const [loadingWeather, setLoadingWeather] = useState(false);

  // 地图选择对话框状态
  const [showMapSelector, setShowMapSelector] = useState(false);
  const [selectedRecommendation, setSelectedRecommendation] = useState<any>(null);

  useEffect(() => {
    // ✅ 修复：等待 AuthContext 完全初始化后再判断
    if (isLoading) {
      console.log('[首页] AuthContext 正在初始化，等待...');
      return;
    }

    if (!user) {
      console.log('[首页] 未登录，跳转到登录页');
      router.push('/login');
      return;
    }

    console.log('[首页] 用户已登录，开始加载首页数据');
    getUserLocation();
    loadOrderStats();
    loadWeatherData();
    loadFlightPrediction();
  }, [user, token, isLoading, router]);

  const getUserLocation = async () => {
    // 读取缓存位置
    if (typeof window !== 'undefined') {
      const storedLocation = localStorage.getItem('user_location');
      if (storedLocation) {
        try {
          const location = JSON.parse(storedLocation);
          setCurrentLocation(location);
          getCachedAddress(location);
        } catch (error) {
          console.error('解析缓存位置失败:', error);
        }
      }
    }

    // 使用增强版定位工具
    try {
      const result = await getLocation({
        enableHighAccuracy: true,
        timeout: 30000,
        maximumAge: 0,
        retryCount: 2,
      });

      const location = { lat: result.lat, lng: result.lng };
      localStorage.setItem('user_location', JSON.stringify(location));
      setCurrentLocation(location);
      setLocationAccuracy(result.accuracy);
      setLocationMethod(result.method);
      setLocationBrowser(result.browser);

      console.log('✅ 定位成功:', {
        location,
        accuracy: result.accuracy,
        method: result.method,
        browser: result.browser,
      });

      // 标记定位准备就绪
      setLocationReady(true);

      // 根据定位方法和浏览器显示不同的提示
      let addressPrefix = '';
      const browserName = result.browser.toUpperCase();

      if (result.method === 'gps') {
        addressPrefix = 'GPS定位';
      } else if (result.method === 'network') {
        addressPrefix = '网络定位';
      } else if (result.method === 'ip') {
        addressPrefix = 'IP定位（城市级别）';
      } else {
        addressPrefix = '默认位置';
      }

      await getAddressFromLocation(location, addressPrefix, result.browser);
    } catch (error) {
      console.error('❌ 定位失败:', error);
      const defaultLocation = { lat: 39.9042, lng: 116.4074 };
      setCurrentLocation(defaultLocation);
      setCurrentAddress('北京市东城区（定位失败，使用默认位置）');
      setLocationAccuracy(null);
      setLocationMethod('default');
      setLocationReady(true); // 即使定位失败，也允许使用推荐功能
      await getAddressFromLocation(defaultLocation, '默认位置', 'unknown');
    }
  };

  const getAddressFromLocation = async (
    location: { lat: number; lng: number },
    addressPrefix?: string,
    browser?: string
  ) => {
    try {
      const response = await fetch(
        `/api/geocoding/reverse?lat=${location.lat}&lng=${location.lng}`
      );
      const result = await response.json();

      // 使用扁平化的数据结构（天地图迁移后的格式）
      if (result.success && result.formattedAddress) {
        let address = result.formattedAddress;

        // 添加定位方法前缀
        if (addressPrefix) {
          address = `${addressPrefix} - ${address}`;
        } else if (location.lat === 39.9042 && location.lng === 116.4074 && !currentLocation) {
          address += '（默认位置，点击更新获取真实位置）';
        }

        // 添加浏览器信息（如果使用IP定位或默认位置）
        if ((addressPrefix?.includes('IP定位') || addressPrefix?.includes('默认位置')) && browser) {
          const browserName = getBrowserName(browser);
          address += ` (${browserName}浏览器)`;
        }

        setCurrentAddress(address);
        localStorage.setItem('user_address', address);
      } else {
        console.error('获取地址失败:', result.error || result.data?.error);
        let fallbackAddress = `${addressPrefix ? addressPrefix + ' - ' : ''}纬度 ${location.lat.toFixed(4)}, 经度 ${location.lng.toFixed(4)}`;
        if (location.lat === 39.9042 && location.lng === 116.4074) {
          fallbackAddress += '（默认位置）';
        }
        if (browser && (addressPrefix?.includes('IP定位') || addressPrefix?.includes('默认位置'))) {
          const browserName = getBrowserName(browser);
          fallbackAddress += ` (${browserName}浏览器)`;
        }
        setCurrentAddress(fallbackAddress);
        localStorage.setItem('user_address', fallbackAddress);
      }
    } catch (error) {
      console.error('获取地址失败:', error);
      let fallbackAddress = `${addressPrefix ? addressPrefix + ' - ' : ''}纬度 ${location.lat.toFixed(4)}, 经度 ${location.lng.toFixed(4)}`;
      if (location.lat === 39.9042 && location.lng === 116.4074) {
        fallbackAddress += '（默认位置）';
      }
      if (browser && (addressPrefix?.includes('IP定位') || addressPrefix?.includes('默认位置'))) {
        const browserName = getBrowserName(browser);
        fallbackAddress += ` (${browserName}浏览器)`;
      }
      setCurrentAddress(fallbackAddress);
      localStorage.setItem('user_address', fallbackAddress);
    }
  };

  const getCachedAddress = (location: { lat: number; lng: number }) => {
    try {
      const cachedAddress = localStorage.getItem('user_address');
      if (cachedAddress) {
        setCurrentAddress(cachedAddress);
      }
    } catch (error) {
      console.error('读取缓存地址失败:', error);
    }
  };

  const loadRecommendations = async (type?: 'big_order' | 'high_rate' | 'user_experience') => {
    if (!user) return;

    let lat = 39.9042;
    let lng = 116.4074;

    if (typeof window !== 'undefined') {
      const storedLocation = localStorage.getItem('user_location');
      if (storedLocation) {
        try {
          const location = JSON.parse(storedLocation);
          lat = location.lat;
          lng = location.lng;
        } catch (error) {
          console.error('解析用户位置失败:', error);
        }
      }
    }

    setLoadingRecommendations(true);
    try {
      const response = await fetch(
        `/api/recommendations/smart?userId=${user.id}&lat=${lat}&lng=${lng}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          let allRecommendations = result.data || [];

          // 如果指定了类型，只返回该类型的推荐
          if (type) {
            allRecommendations = allRecommendations.filter((rec: any) => rec.type === type);
          }

          setRecommendations(allRecommendations);
        }
      }
    } catch (error) {
      console.error('Failed to load recommendations:', error);
    } finally {
      setLoadingRecommendations(false);
    }
  };

  const loadOrderStats = async () => {
    if (!user) return;

    setLoadingStats(true);
    try {
      const response = await fetch('/api/orders/statistics', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success) {
          setOrderStats(result.data);
        }
      }
    } catch (error) {
      console.error('加载订单统计失败:', error);
    } finally {
      setLoadingStats(false);
    }
  };

  const loadWeatherData = async () => {
    if (!user) return;

    setLoadingWeather(true);
    try {
      // 获取用户所在城市，默认使用北京
      const city = user?.city || '北京';

      const response = await fetch(`/api/weather/today?city=${encodeURIComponent(city)}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          setWeatherData(result.data);
        }
      }
    } catch (error) {
      console.error('加载天气数据失败:', error);
    } finally {
      setLoadingWeather(false);
    }
  };

  const loadFlightPrediction = async () => {
    if (!user) return;

    setLoadingPrediction(true);
    try {
      const response = await fetch('/api/airport/prediction', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();
        if (result.success && result.data) {
          setFlightPrediction(result.data);
          console.log('[航班预测] 预测数据加载成功:', result.data);
        }
      }
    } catch (error) {
      console.error('加载航班预测失败:', error);
    } finally {
      setLoadingPrediction(false);
    }
  };

  const handleUnlockBigOrder = async () => {
    if ((user?.points || 0) < 10) {
      alert('积分不足，需要10积分才能解锁');
      return;
    }

    if (confirm('确定花费10积分解锁大单推荐信息吗？')) {
      setUnlockedBigOrder(true);
      if (user) {
        user.points -= 10;
      }
      alert('解锁成功！');
    }
  };

  const handleRecommendationTypeClick = async (
    type: 'big_order' | 'high_rate' | 'user_experience'
  ) => {
    // 点击时才计算和推荐，不提前计算

    // 检查积分（除了user_experience类型）
    if (type !== 'user_experience') {
      const pointsRequired = type === 'big_order' ? 10 : 5;
      if ((user?.points || 0) < pointsRequired) {
        alert(`积分不足，需要${pointsRequired}积分才能查看此推荐`);
        return;
      }

      if (
        !confirm(
          `确定花费${pointsRequired}积分查看${type === 'big_order' ? '大单常出没' : '连单概率大'}推荐吗？`
        )
      ) {
        return;
      }

      // 扣除积分
      try {
        const response = await fetch('/api/user/deduct-points', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            pointsChange: -pointsRequired,
            reason: type === 'big_order' ? '查看大单常出没推荐' : '查看连单概率大推荐',
          }),
        });

        if (!response.ok) {
          alert('扣除积分失败');
          return;
        }

        const result = await response.json();
        if (result.success) {
          // 更新用户积分
          if (user) {
            user.points = result.data.newPoints;
          }
        } else {
          alert(result.error || '扣除积分失败');
          return;
        }
      } catch (error) {
        console.error('扣除积分失败:', error);
        alert('扣除积分失败');
        return;
      }
    }

    // 加载推荐（点击时才计算）
    setSelectedRecommendationType(type);
    await loadRecommendations(type);
  };

  const handleRecommendationClick = async (rec: any) => {
    // 检查是否有推荐等单地点的经纬度信息
    if (rec.startLat && rec.startLng) {
      // 使用 endLocation（推荐的等单地点名称）作为导航目的地
      const destinationName = rec.endLocation || rec.startLocation;

      // 保存选中的推荐信息
      setSelectedRecommendation({
        ...rec,
        destinationName,
      });

      // 显示地图选择对话框
      setShowMapSelector(true);
    } else {
      // 没有经纬度信息，提示用户
      const destinationName = rec.endLocation || rec.startLocation;
      alert(`推荐地点"${destinationName}"暂无精确位置信息，无法导航。`);
    }
  };

  // 处理地图选择
  const handleMapAppSelect = (app: MapApp) => {
    if (!selectedRecommendation) return;

    const rec = selectedRecommendation;
    const destinationName = rec.destinationName;

    // 构建导航参数
    const navigationOptions: NavigationOptions = {
      name: destinationName,
      lat: rec.startLat,
      lng: rec.startLng,
    };

    // 如果有用户当前位置，传入起点参数（确保"我的位置"可以正确显示）
    if (currentLocation && currentLocation.lat && currentLocation.lng) {
      navigationOptions.startName = '我的位置';
      navigationOptions.startLat = currentLocation.lat;
      navigationOptions.startLng = currentLocation.lng;
      console.log('📍 传入起点信息:', {
        name: '我的位置',
        lat: currentLocation.lat,
        lng: currentLocation.lng,
        mapApp: app === 'amap' ? '高德地图' : '百度地图',
      });
    } else {
      console.log('⚠️ 未获取到用户位置，地图APP将自动获取起点');
    }

    // 打开导航到选择的地图APP
    openNavigationToApp(navigationOptions, app);

    console.log(`🗺️ 使用${app === 'amap' ? '高德地图' : '百度地图'}导航到 "${destinationName}"`);
  };

  const getCarTypeName = (carType: string) => {
    const carTypeMap: Record<string, string> = {
      economy: '快车',
      comfort: '优享',
      premium: '专车',
      business: '商务',
    };
    return carTypeMap[carType] || carType;
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy < 10) {
      return 'text-green-600 dark:text-green-400';
    } else if (accuracy < 50) {
      return 'text-yellow-600 dark:text-yellow-400';
    } else if (accuracy < 200) {
      return 'text-orange-600 dark:text-orange-400';
    } else {
      return 'text-red-600 dark:text-red-400';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className={`${styles.fontSizes.textBase} ${styles.colors.text.secondary}`}>
          加载中...
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className={`min-h-screen ${styles.colors.bg.page} pb-[56px]`}>
      {/* Header */}
      <header className={`bg-gradient-to-r from-blue-600 to-blue-700 dark:from-blue-800 dark:to-blue-900 text-white ${styles.spacing.pagePadding} pt-[18px] pb-[20px]`}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className={`${styles.fontSizes.textSM} opacity-90`}>{APP_CONFIG.APP_NAME}</div>
            <h1 className={`${styles.fontSizes.titleXL} ${styles.fontWeights.bold} mt-[4px]`}>
              {APP_CONFIG.APP_SLOGAN}
            </h1>
            <div className={`${styles.fontSizes.textSM} opacity-90 mt-[4px]`}>
              亲爱的{user?.nickname || '司机师傅'}
              {user?.city ? `（${user.city}` : ''}
              {user?.carType ? `·${getCarTypeName(user.carType)}` : ''}
              {user?.city || user?.carType ? '）' : ''}
              ，您已经上传{' '}
              <Link
                href="/my-orders"
                className="text-yellow-300 hover:text-yellow-200 font-bold hover:underline"
              >
                {orderStats?.totalOrders || 0}
              </Link>{' '}
              条行程信息
            </div>
          </div>
          <div
            className={`w-[44px] h-[44px] bg-white/20 ${styles.borderRadius.avatar} flex items-center justify-center`}
          >
            <span className={`${styles.icon.size.xl}`}>用户</span>
          </div>
        </div>
      </header>

      {/* 今日天气模块 - v2.2.0 */}
      <div className={`${styles.spacing.pagePadding} mt-[12px]`}>
        {loadingWeather ? (
          <div className={`${styles.card} p-[16px]`}>
            <div
              className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary} text-center`}
            >
              加载天气数据中...
            </div>
          </div>
        ) : weatherData ? (
          <div className={`${styles.card} p-[16px]`}>
            {/* 实时天气 */}
            <div className="flex items-center justify-between mb-[12px]">
              <div className="flex items-center gap-[12px]">
                <div
                  style={{ width: '60px', height: '60px' }}
                  className={`bg-gradient-to-br from-yellow-100 to-orange-100 dark:from-yellow-900 dark:to-orange-900 ${styles.borderRadius.card} flex items-center justify-center`}
                >
                  <span className={`${styles.fontSizes.titleXL}`}>
                    {weatherData.weatherText === '晴'
                      ? '☀️'
                      : weatherData.weatherText === '多云'
                        ? '⛅'
                        : weatherData.weatherText === '阴'
                          ? '☁️'
                          : weatherData.weatherText.includes('雨')
                            ? '🌧️'
                            : weatherData.weatherText.includes('雪')
                              ? '❄️'
                              : '🌤️'}
                  </span>
                </div>
                <div>
                  <div
                    className={`${styles.fontSizes.titleXL} ${styles.fontWeights.bold} ${styles.colors.text.primary}`}
                  >
                    {weatherData.temperature}°C
                  </div>
                  <div
                    className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary} mt-[2px]`}
                  >
                    {weatherData.weatherText}
                    {weatherData.feelsLike && ` · 体感 ${weatherData.feelsLike}°C`}
                    {weatherData.windDir && ` · ${weatherData.windDir} ${weatherData.windScale || ''}`}
                  </div>
                </div>
              </div>
              <div
                className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary} text-right`}
              >
                <div className={`${styles.fontSizes.titleLG} ${styles.fontWeights.semibold}`}>
                  {weatherData.month}月{weatherData.day}日
                </div>
                <div className="mt-[2px]">
                  {weatherData.weekDayName}
                  {weatherData.isWorkday ? (
                    <span className="ml-[4px] px-[4px] py-[1px] bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400 rounded text-xs">
                      工作日
                    </span>
                  ) : (
                    <span className="ml-[4px] px-[4px] py-[1px] bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded text-xs">
                      周末
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* 24小时预报 - 动态滚动显示 */}
            {weatherData.hourlyForecast && weatherData.hourlyForecast.length > 0 && (
              <div
                style={{ paddingTop: '12px' }}
                className="border-t border-gray-100 dark:border-gray-700"
              >
                <div
                  className={`${styles.fontSizes.textSM} ${styles.fontWeights.medium} ${styles.colors.text.secondary} mb-[8px]} flex justify-between items-center`}
                >
                  <span>24小时预报</span>
                  <span>Data by 和风天气</span>
                </div>
                <div
                  style={{ gap: '8px', paddingBottom: '4px' }}
                  className="flex overflow-x-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600"
                >
                  {(() => {
                    // hourlyForecast 已经是按时间顺序排列的预报数据
                    // 按当前整点匹配：22:00-22:59 都显示22:00的天气
                    const forecast = weatherData.hourlyForecast || [];
                    const currentHour = new Date().getHours();
                    const currentHourStr = String(currentHour).padStart(2, '0') + ':00';

                    // 找到匹配当前小时的索引
                    let startIndex = 0;
                    forecast.forEach((hour, idx) => {
                      if (hour.time === currentHourStr) {
                        startIndex = idx;
                      }
                    });

                    // 从当前小时开始显示12个小时（可能跨天）
                    const displayForecast = [];
                    for (let i = 0; i < 12; i++) {
                      const idx = (startIndex + i) % forecast.length;
                      displayForecast.push(forecast[idx]);
                    }

                    return displayForecast.map((hour, idx) => (
                      <div
                        key={idx}
                        style={{
                          width: '54px',
                          padding: '8px',
                          backgroundColor: idx === 0 ? 'rgba(59, 130, 246, 0.1)' : undefined,
                          border: idx === 0 ? '2px solid rgba(59, 130, 246, 0.3)' : undefined,
                        }}
                        className={`flex-shrink-0 bg-gray-50 dark:bg-gray-800 ${styles.borderRadius.card} text-center`}
                      >
                        <div
                          className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mb-[4px]`}
                          style={{ color: idx === 0 ? '#3b82f6' : undefined }}
                        >
                          {idx === 0 ? `${hour.time}·现在` : hour.time}
                        </div>
                        <div className={`${styles.fontSizes.titleLG} mb-[4px]`}>
                          {hour.text === '晴'
                            ? '☀️'
                            : hour.text === '多云'
                              ? '⛅'
                              : hour.text === '阴'
                                ? '☁️'
                                : hour.text.includes('雨')
                                  ? '🌧️'
                                  : hour.text.includes('雪')
                                    ? '❄️'
                                    : '🌤️'}
                        </div>
                        <div
                          className={`${styles.fontSizes.textSM} ${styles.fontWeights.medium} ${styles.colors.text.primary}`}
                        >
                          {hour.temp}
                        </div>
                      </div>
                    ));
                  })()}
                </div>
              </div>
            )}
          </div>
        ) : null}
      </div>

      {/* 活动信息卡片 - 航班、演唱会、展会 */}
      {orderStats?.eventsInfo && (
        orderStats.eventsInfo.concerts.length > 0 ||
        orderStats.eventsInfo.exhibitions.length > 0 ||
        orderStats.eventsInfo.flightCount !== undefined
      ) ? (
        <div className={`${styles.spacing.pagePadding} mt-[12px]`}>
          <div className={`${styles.card} p-[16px]`}>
            {/* 航班高峰预测 - 未来3小时 */}
            {loadingPrediction ? (
              <div className="flex items-center justify-center p-[20px]">
                <span className="text-sky-500">加载航班预测中...</span>
              </div>
            ) : flightPrediction ? (
              <div>
                {/* 标题栏 */}
                <div className="flex items-center justify-between mb-[12px]">
                  <div className="flex items-center gap-[8px]">
                    <span className={`${styles.fontSizes.titleLG}`}>✈️</span>
                    <span className={`${styles.fontSizes.titleMD} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}>
                      机场航班预测
                    </span>
                  </div>
                  <span className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary}`}>
                    {flightPrediction.currentTime}
                  </span>
                </div>

                {/* 预测时段说明 */}
                <div className="mb-[8px] px-[8px] py-[4px] bg-gradient-to-r from-sky-50 to-blue-50 dark:from-sky-900/30 dark:to-blue-900/30 rounded border border-sky-200 dark:border-sky-700">
                  <span className={`${styles.fontSizes.textSM} ${styles.colors.text.primary}`}>
                    📊 {flightPrediction.predictionPeriod}
                  </span>
                </div>

                {/* 三个机场的预测 */}
                <div className="space-y-[8px] mb-[12px]">
                  {flightPrediction.airports.map((airport) =>
                    airport.terminals
                      .filter((terminal) => {
                        // 只删除首都机场的"全部"卡片（name为null或字符串"全部"）
                        if (airport.code === 'PEK' && (!terminal.name || terminal.name === '全部')) {
                          return false;
                        }
                        return true;
                      })
                      .map((terminal) => {
                      const isHottest = terminal.recommendation === 'hottest';
                      const isActive = terminal.recommendation === 'active';
                      const totalFlights = terminal.total3Hours;

                      return (
                        <div
                          key={`${airport.code}-${terminal.name}`}
                          className={`p-[10px] rounded border ${
                            isHottest
                              ? 'bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/40 dark:to-red-900/40 border-orange-300 dark:border-orange-700'
                              : isActive
                              ? 'bg-gradient-to-r from-sky-50 to-blue-50 dark:from-sky-900/30 dark:to-blue-900/30 border-sky-200 dark:border-sky-700'
                              : 'bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-700'
                          }`}
                        >
                          {/* 机场名称和说明 */}
                          <div className="flex items-center justify-between mb-[6px]">
                            <div className="flex items-center gap-[6px]">
                              <span className={`${styles.fontSizes.textBase} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}>
                                {airport.code === 'PEK' ? '首都' : '大兴'}机场 {terminal.name}
                              </span>
                              {isHottest && (
                                <span className="px-[4px] py-[1px] bg-orange-500 text-white text-xs rounded font-medium">
                                  🔥 最热
                                </span>
                              )}
                            </div>
                            <div className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary}`}>
                              高峰3小时
                            </div>
                          </div>

                          {/* 未来3小时分时段 */}
                          <div className="flex gap-[6px]">
                            {terminal.hourlyBreakdown.map((hour) => (
                              <div
                                key={hour.timeRange}
                                className="flex-1 p-[6px] bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700"
                              >
                                <div className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mb-[2px]`}>
                                  {hour.timeRange}
                                </div>
                                <div className={`${styles.fontSizes.textSM} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}>
                                  {hour.estimatedCount}架
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>

                {/* 最火时段推荐 */}
                {flightPrediction.summary.advice && (
                  <div className="p-[10px] bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/30 dark:to-emerald-900/30 rounded border border-green-200 dark:border-green-700">
                    <div className="flex items-center gap-[8px] mb-[6px]">
                      <span className="text-lg">🎯</span>
                      <span className={`${styles.fontSizes.textBase} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}>
                        最火时段推荐
                      </span>
                    </div>
                    <div className={`${styles.fontSizes.textSM} ${styles.colors.text.primary} mb-[8px]`}>
                      {flightPrediction.summary.advice}
                    </div>

                    {/* 全天最火时段排名 */}
                    {flightPrediction.summary.topPeriods && flightPrediction.summary.topPeriods.length > 0 && (
                      <div className="space-y-[4px]">
                        {flightPrediction.summary.topPeriods.map((period, index) => (
                          <div
                            key={index}
                            className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary} flex items-center gap-[8px]`}
                          >
                            <span className="w-[70px]">{period.timeRange}</span>
                            <span className="w-[40px]">{period.count}架</span>
                            <span>{period.terminal}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              /* 加载失败时的回退显示 */
              <div className="p-[16px] bg-gray-50 dark:bg-gray-900/20 rounded border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-[8px]">
                  <div className="flex items-center gap-[8px]">
                    <span className={`${styles.fontSizes.titleLG}`}>✈️</span>
                    <span className={`${styles.fontSizes.titleMD} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}>
                      机场航班预测
                    </span>
                  </div>
                </div>
                <div className="text-center py-[12px]">
                  <p className={`${styles.fontSizes.textSM} ${styles.colors.text.tertiary} mb-[4px]`}>
                    暂时无法加载预测数据
                  </p>
                  <p className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary}`}>
                    请稍后刷新页面重试
                  </p>
                </div>
              </div>
            )}

            {/* 演唱会信息 */}
            {orderStats.eventsInfo.concerts.length > 0 && (
              <div className="mb-[12px]">
                <div className="flex items-center gap-[8px] mb-[8px]">
                  <span className={`${styles.fontSizes.titleLG}`}>🎤</span>
                  <span className={`${styles.fontSizes.titleMD} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}>
                    演唱会
                  </span>
                  {orderStats.eventsInfo.concerts.length > 0 && (
                    <span className={`ml-[4px] px-[6px] py-[1px] bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-400 rounded text-xs`}>
                      {orderStats.eventsInfo.concerts.length}场
                    </span>
                  )}
                </div>
                <div className="space-y-[6px]">
                  {orderStats.eventsInfo.concerts.slice(0, 3).map((concert) => (
                    <div key={concert.id} className="flex items-center justify-between p-[8px] bg-purple-50 dark:bg-purple-900/20 rounded">
                      <div className="flex-1">
                        <div className={`${styles.fontSizes.textSM} ${styles.colors.text.primary}`}>
                          <span className="font-medium">{concert.dateLabel}</span>
                          <span className="ml-[8px]">{concert.time}</span>
                        </div>
                        <div className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mt-[2px]`}>
                          {concert.location}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 展会信息 */}
            {orderStats.eventsInfo.exhibitions.length > 0 && (
              <div className={`mb-[12px] ${orderStats.eventsInfo.concerts.length > 0 ? 'border-t border-gray-100 dark:border-gray-700 pt-[12px]' : ''}`}>
                <div className="flex items-center gap-[8px] mb-[8px]">
                  <span className={`${styles.fontSizes.titleLG}`}>🏢</span>
                  <span className={`${styles.fontSizes.titleMD} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}>
                    展会
                  </span>
                  {orderStats.eventsInfo.exhibitions.length > 0 && (
                    <span className={`ml-[4px] px-[6px] py-[1px] bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded text-xs`}>
                      {orderStats.eventsInfo.exhibitions.length}场
                    </span>
                  )}
                </div>
                <div className="space-y-[6px]">
                  {orderStats.eventsInfo.exhibitions.slice(0, 3).map((exhibition) => (
                    <div key={exhibition.id} className="flex items-center justify-between p-[8px] bg-blue-50 dark:bg-blue-900/20 rounded">
                      <div className="flex-1">
                        <div className={`${styles.fontSizes.textSM} ${styles.colors.text.primary}`}>
                          <span className="font-medium">{exhibition.dateLabel}</span>
                          <span className="ml-[8px]">{exhibition.time}</span>
                        </div>
                        <div className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mt-[2px]`}>
                          {exhibition.location}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 活动信息轮播（演唱会、展览、航班） */}
            {(orderStats.eventsInfo.concerts.length > 0 ||
              orderStats.eventsInfo.exhibitions.length > 0 ||
              (orderStats.eventsInfo.flightCount !== undefined && orderStats.eventsInfo.flightCount > 0)) && (
              <div className="relative overflow-hidden">
                <div className="animate-marquee whitespace-nowrap">
                  {/* 航班信息 */}
                  {orderStats.eventsInfo.flightCount !== undefined && orderStats.eventsInfo.flightCount > 0 && (
                    <div className="inline-flex items-center gap-[4px] mr-[16px] px-[8px] py-[4px] bg-sky-50 dark:bg-sky-900/20 rounded">
                      <span>✈️</span>
                      <span className={`${styles.fontSizes.textSM} ${styles.colors.text.primary}`}>
                        今日预计到达 {orderStats.eventsInfo.flightCount} 架航班
                      </span>
                    </div>
                  )}

                  {/* 演唱会信息 */}
                  {orderStats.eventsInfo.concerts.map((concert, idx) => (
                    <div key={`concert-${idx}`} className="inline-flex items-center gap-[4px] mr-[16px] px-[8px] py-[4px] bg-purple-50 dark:bg-purple-900/20 rounded">
                      <span>🎤</span>
                      <span className={`${styles.fontSizes.textSM} ${styles.colors.text.primary}`}>
                        {concert.location} {concert.dateLabel} {concert.time}
                      </span>
                    </div>
                  ))}

                  {/* 展览信息 */}
                  {orderStats.eventsInfo.exhibitions.map((exhibition, idx) => (
                    <div key={`exhibition-${idx}`} className="inline-flex items-center gap-[4px] mr-[16px] px-[8px] py-[4px] bg-blue-50 dark:bg-blue-900/20 rounded">
                      <span>🖼️</span>
                      <span className={`${styles.fontSizes.textSM} ${styles.colors.text.primary}`}>
                        {exhibition.location} {exhibition.dateLabel} {exhibition.time}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}

      {/* Quick Actions */}
      <div className={`${styles.spacing.pagePadding} mt-[12px]`}>
        <div className="grid grid-cols-2 gap-4">
          <Link
            href="/manual-add-order/upload"
            className={`${styles.card} active:shadow-lg active:scale-95 transition-all`}
          >
            <div className="flex flex-col items-center justify-center p-[14px]">
              <div
                className={`w-[48px] h-[48px] bg-green-100 dark:bg-green-900 ${styles.borderRadius.card} flex items-center justify-center mb-[10px]`}
              >
                <span className={`${styles.icon.size.xl}`}>上传</span>
              </div>
              <div className="text-center">
                <div
                  className={`${styles.fontWeights.semibold} ${styles.fontSizes.titleMD} ${styles.colors.text.primary}`}
                >
                  上传截图添加
                </div>
                <div
                  className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mt-[4px]`}
                >
                  AI智能识别
                </div>
              </div>
            </div>
          </Link>
          <Link
            href="/manual-add-order"
            className={`${styles.card} active:shadow-lg active:scale-95 transition-all`}
          >
            <div className="flex flex-col items-center justify-center p-[14px]">
              <div
                className={`w-[48px] h-[48px] bg-purple-100 dark:bg-purple-900 ${styles.borderRadius.card} flex items-center justify-center mb-[10px]`}
              >
                <span className={`${styles.icon.size.xl}`}>编辑</span>
              </div>
              <div className="text-center">
                <div
                  className={`${styles.fontWeights.semibold} ${styles.fontSizes.titleMD} ${styles.colors.text.primary}`}
                >
                  手动添加订单
                </div>
                <div
                  className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mt-[4px]`}
                >
                  快速录入订单
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>

      {/* Today Stats Card */}
      <div className={`${styles.spacing.pagePadding} mt-[12px]`}>
        <div className={`${styles.card} shadow-lg p-[16px]`}>
          <div className="text-center mb-[12px]">
            <div className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary} mb-[4px]`}>
              当前积分
            </div>
            <div
              className={`${styles.fontSizes.titleXXL} ${styles.fontWeights.bold} ${styles.colors.text.primary}`}
            >
              {user?.points || 0}
            </div>
          </div>
          <Link
            href="/my-orders"
            className={`${styles.button.padding.large} ${styles.button.radius.large} bg-blue-600 hover:bg-blue-700 active:scale-95 ${styles.fontSizes.buttonMD} font-medium text-white transition-all w-full text-center block`}
          >
            订单管理
          </Link>
        </div>
      </div>

      {/* Smart Recommendations */}
      <div className={`${styles.spacing.pagePadding} mt-[16px]`}>
        <div className="mb-[10px]">
          <h2
            className={`${styles.fontSizes.titleLG} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}
          >
            订单推荐
          </h2>
          <div
            className={`mt-[10px] flex items-start gap-[8px] ${styles.fontSizes.textSM} ${styles.colors.text.tertiary}`}
          >
            <span>定位</span>
            <span className="flex-1">
              <span className={`${styles.colors.text.secondary} ${styles.fontWeights.medium}`}>
                当前位置：
              </span>
              {currentAddress || '正在获取地址...'}
              {locationAccuracy !== null && (
                <span className={`ml-[6px] ${getAccuracyColor(locationAccuracy)}`}>
                  (精度: {locationAccuracy < 10 ? '高' : locationAccuracy < 50 ? '中' : '低'} ~
                  {Math.round(locationAccuracy)}m)
                </span>
              )}
            </span>
            <button
              onClick={() => {
                getUserLocation();
              }}
              className={`text-blue-600 dark:text-blue-400 ${styles.fontSizes.textSM} ${styles.fontWeights.medium} hover:underline active:text-blue-800 dark:active:text-blue-300 transition-colors`}
            >
              更新定位
            </button>
          </div>

          {/* 定位状态提示 */}
          {currentAddress &&
            locationMethod === 'gps' &&
            locationAccuracy !== null &&
            locationAccuracy < 50 && (
              <div
                className={`${styles.fontSizes.textXS} text-green-600 dark:text-green-400 mt-[6px]`}
              >
                ✅ GPS定位精准，推荐订单基于您的真实位置
              </div>
            )}

          {currentAddress && locationMethod === 'network' && (
            <div
              className={`${styles.fontSizes.textXS} text-yellow-600 dark:text-yellow-400 mt-[6px]`}
            >
              ⚡ 使用网络定位（WiFi/IP），精度约几百米，建议在室外使用GPS定位
            </div>
          )}

          {currentAddress && locationMethod === 'ip' && (
            <div
              className={`${styles.fontSizes.textXS} text-orange-600 dark:text-orange-400 mt-[6px]`}
            >
              🌐 使用IP定位（城市级别），精度约几公里
              {locationBrowser === 'alook' &&
                '，Alook浏览器不支持GPS定位，建议使用X浏览器或华为浏览器'}
              {locationBrowser === 'edge' && '，Edge浏览器GPS定位超时，建议在室外等待更长时间'}
            </div>
          )}

          {currentAddress && locationMethod === 'default' && (
            <div className={`${styles.fontSizes.textXS} ${styles.colors.text.disabled} mt-[6px]`}>
              ⚠️ 使用默认位置（北京）进行推荐，点击"更新定位"获取您的真实位置
              {locationBrowser === 'alook' && '，Alook浏览器不支持定位服务，建议更换浏览器'}
            </div>
          )}

          {!currentAddress && (
            <div className={`${styles.fontSizes.textXS} ${styles.colors.text.disabled} mt-[6px]`}>
              正在获取位置信息...
              {locationBrowser === 'edge' && '，Edge浏览器可能需要较长时间（最多90秒）'}
            </div>
          )}
        </div>

        {/* ✅ 定位状态提示 */}
        {locationReady && recommendations.length === 0 && (
          <div className={`${styles.card} p-[12px] mb-[12px]`}>
            {locationMethod === 'gps' && locationAccuracy !== null && locationAccuracy < 100 ? (
              <div className="flex items-center gap-[8px]">
                <span className="text-green-600 dark:text-green-400">✅</span>
                <span className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary}`}>
                  GPS定位精准（约{Math.round(locationAccuracy)}米），现在可以使用推荐功能
                </span>
              </div>
            ) : locationMethod === 'gps' && locationAccuracy !== null && locationAccuracy >= 100 ? (
              <div className="flex items-center gap-[8px]">
                <span className="text-yellow-600 dark:text-yellow-400">⚠️</span>
                <span className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary}`}>
                  GPS定位精度约{Math.round(locationAccuracy)}米，建议等待定位完成后使用推荐功能
                </span>
              </div>
            ) : locationMethod === 'network' ? (
              <div className="flex items-center gap-[8px]">
                <span className="text-yellow-600 dark:text-yellow-400">⚡</span>
                <span className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary}`}>
                  网络定位（精度约几百米），推荐结果可能不够准确
                </span>
              </div>
            ) : locationMethod === 'ip' ? (
              <div className="flex items-center gap-[8px]">
                <span className="text-orange-600 dark:text-orange-400">🌐</span>
                <span className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary}`}>
                  IP定位（城市级别，精度约几公里），强烈建议点击"更新定位"
                </span>
              </div>
            ) : (
              <div className="flex items-center gap-[8px]">
                <span className="text-gray-500 dark:text-gray-400">⚠️</span>
                <span className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary}`}>
                  使用默认位置，请点击"更新定位"获取您的真实位置
                </span>
              </div>
            )}
          </div>
        )}

        {/* 推荐类型选择 */}
        {locationReady && recommendations.length === 0 && (
          <div className={`${styles.spacing.gapY}`}>
            {/* 根据以往订单AI推荐 - 第一个位置 */}
            <div
              className={`${styles.card} p-[16px] transition-all cursor-pointer active:shadow-lg active:scale-95 hover:shadow-md`}
              onClick={() => {
                handleRecommendationTypeClick('user_experience');
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-[8px]">
                    <div className={`${styles.fontSizes.titleXL}`}>🤖</div>
                    <div
                      className={`${styles.fontSizes.titleLG} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}
                    >
                      根据以往订单AI推荐
                    </div>
                  </div>
                  <div
                    className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary} mt-[8px]`}
                  >
                    基于您的历史订单数据，AI智能推荐
                  </div>
                  {/* 定位状态提示 */}
                  {(locationMethod !== 'gps' ||
                    locationAccuracy === null ||
                    locationAccuracy >= 100) && (
                    <div
                      className={`${styles.fontSizes.textXS} mt-[6px] ${
                        locationMethod === 'gps' &&
                        locationAccuracy !== null &&
                        locationAccuracy >= 100
                          ? 'text-yellow-600 dark:text-yellow-400'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}
                    >
                      {locationMethod === 'gps' &&
                      locationAccuracy !== null &&
                      locationAccuracy >= 100
                        ? `⚠️ GPS精度${Math.round(locationAccuracy)}米（需要<100米）`
                        : locationMethod === 'network'
                          ? '⚡ 需要GPS定位'
                          : locationMethod === 'ip'
                            ? '🌐 需要GPS定位'
                            : '⚠️ 需要定位'}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary}`}>
                    免费
                  </div>
                  <div
                    className={`${styles.fontSizes.titleXL} ${styles.fontWeights.bold} text-green-600 dark:text-green-400`}
                  >
                    0
                  </div>
                </div>
              </div>
            </div>

            {/* 连单概率大 - 中间位置 */}
            <div
              className={`${styles.card} p-[16px] transition-all cursor-pointer active:shadow-lg active:scale-95 hover:shadow-md`}
              onClick={() => {
                handleRecommendationTypeClick('high_rate');
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-[8px]">
                    <div className={`${styles.fontSizes.titleXL}`}>📈</div>
                    <div
                      className={`${styles.fontSizes.titleLG} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}
                    >
                      连单概率大
                    </div>
                  </div>
                  <div
                    className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary} mt-[8px]`}
                  >
                    推荐订单多的地点，提高接单率
                  </div>
                  {/* 定位状态提示 */}
                  {(locationMethod !== 'gps' ||
                    locationAccuracy === null ||
                    locationAccuracy >= 100) && (
                    <div
                      className={`${styles.fontSizes.textXS} mt-[6px] ${
                        locationMethod === 'gps' &&
                        locationAccuracy !== null &&
                        locationAccuracy >= 100
                          ? 'text-yellow-600 dark:text-yellow-400'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}
                    >
                      {locationMethod === 'gps' &&
                      locationAccuracy !== null &&
                      locationAccuracy >= 100
                        ? `⚠️ GPS精度${Math.round(locationAccuracy)}米（需要<100米）`
                        : locationMethod === 'network'
                          ? '⚡ 需要GPS定位'
                          : locationMethod === 'ip'
                            ? '🌐 需要GPS定位'
                            : '⚠️ 需要定位'}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary}`}>
                    需要积分
                  </div>
                  <div
                    className={`${styles.fontSizes.titleXL} ${styles.fontWeights.bold} text-orange-600 dark:text-orange-400`}
                  >
                    5
                  </div>
                </div>
              </div>
            </div>

            {/* 大单常出没 - 最后一个位置 */}
            <div
              className={`${styles.card} p-[16px] transition-all cursor-pointer active:shadow-lg active:scale-95 hover:shadow-md`}
              onClick={() => {
                handleRecommendationTypeClick('big_order');
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-[8px]">
                    <div className={`${styles.fontSizes.titleXL}`}>💰</div>
                    <div
                      className={`${styles.fontSizes.titleLG} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}
                    >
                      大单常出没
                    </div>
                  </div>
                  <div
                    className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary} mt-[8px]`}
                  >
                    推荐高收益地点，找到大单机会
                  </div>
                  {/* 定位状态提示 */}
                  {(locationMethod !== 'gps' ||
                    locationAccuracy === null ||
                    locationAccuracy >= 100) && (
                    <div
                      className={`${styles.fontSizes.textXS} mt-[6px] ${
                        locationMethod === 'gps' &&
                        locationAccuracy !== null &&
                        locationAccuracy >= 100
                          ? 'text-yellow-600 dark:text-yellow-400'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}
                    >
                      {locationMethod === 'gps' &&
                      locationAccuracy !== null &&
                      locationAccuracy >= 100
                        ? `⚠️ GPS精度${Math.round(locationAccuracy)}米（需要<100米）`
                        : locationMethod === 'network'
                          ? '⚡ 需要GPS定位'
                          : locationMethod === 'ip'
                            ? '🌐 需要GPS定位'
                            : '⚠️ 需要定位'}
                    </div>
                  )}
                </div>
                <div className="text-right">
                  <div className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary}`}>
                    需要积分
                  </div>
                  <div
                    className={`${styles.fontSizes.titleXL} ${styles.fontWeights.bold} text-orange-600 dark:text-orange-400`}
                  >
                    10
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 推荐结果 */}
        {recommendations.length > 0 && (
          <div className="mt-[16px]">
            <div className="flex items-center justify-between mb-[10px]">
              <div
                className={`${styles.fontSizes.titleMD} ${styles.fontWeights.semibold} ${styles.colors.text.primary}`}
              >
                {selectedRecommendationType === 'big_order' && '💰 大单常出没'}
                {selectedRecommendationType === 'high_rate' && '📈 连单概率大'}
                {selectedRecommendationType === 'user_experience' && '🤖 根据以往订单AI推荐'}
              </div>
              <button
                onClick={() => {
                  setRecommendations([]);
                  setSelectedRecommendationType(null);
                }}
                className={`text-blue-600 dark:text-blue-400 ${styles.fontSizes.textSM} ${styles.fontWeights.medium} hover:underline active:text-blue-800 dark:active:text-blue-300 transition-colors`}
              >
                换一批
              </button>
            </div>

            {loadingRecommendations ? (
              <div className={`${styles.card} p-[40px] text-center`}>
                <div className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary}`}>
                  加载中...
                </div>
              </div>
            ) : recommendations.length === 0 ? (
              <div className={`${styles.card} p-[40px] text-center`}>
                <div className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary}`}>
                  暂无推荐数据
                </div>
              </div>
            ) : (
              <div className={`${styles.spacing.gapY}`}>
                {(() => {
                  // 将推荐列表按3个一组分组
                  const groupedRecommendations: any[][] = [];
                  for (let i = 0; i < recommendations.length; i += 3) {
                    groupedRecommendations.push(recommendations.slice(i, i + 3));
                  }

                  return groupedRecommendations.map((group, groupIndex) => (
                    <RecommendationCarousel
                      key={groupIndex}
                      recommendations={group}
                      onRecommendationClick={handleRecommendationClick}
                      unlockedBigOrder={unlockedBigOrder}
                      onUnlockBigOrder={handleUnlockBigOrder}
                    />
                  ));
                })()}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Order Statistics */}
      {orderStats && (
        <div className={`${styles.spacing.pagePadding} mt-[16px]`}>
          <h2
            className={`${styles.fontSizes.titleLG} ${styles.fontWeights.semibold} ${styles.colors.text.primary} mb-[10px]`}
          >
            订单统计
          </h2>
          <div className={`${styles.card}`}>
            <div className={`grid grid-cols-2 ${styles.spacing.cardGap} mb-[10px]`}>
              <div>
                <div
                  className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mb-[4px]`}
                >
                  总订单数
                </div>
                <div
                  className={`${styles.fontSizes.titleXL} ${styles.fontWeights.bold} ${styles.colors.text.primary}`}
                >
                  {orderStats.totalOrders}
                </div>
              </div>
              <div>
                <div
                  className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mb-[4px]`}
                >
                  平均金额
                </div>
                <div
                  className={`${styles.fontSizes.titleXL} ${styles.fontWeights.bold} ${styles.colors.text.primary}`}
                >
                  ¥{orderStats.avgPrice}
                </div>
              </div>
            </div>
            {orderStats.bestEfficiencyData && (
              <div className="pt-[10px] border-t border-gray-100">
                <div
                  className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mb-[4px]`}
                >
                  效率最高订单
                </div>
                <div className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary}`}>
                  时间：{orderStats.bestEfficiencyData.time} | 里程：
                  {orderStats.bestEfficiencyData.mileage}
                </div>
              </div>
            )}
            {orderStats.topOrderTypes && orderStats.topOrderTypes.length > 0 && (
              <div className="pt-[10px] border-t border-gray-100">
                <div
                  className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mb-[4px]`}
                >
                  常接订单类型
                </div>
                <div className={`flex flex-wrap gap-[6px]`}>
                  {orderStats.topOrderTypes.map((type, idx) => (
                    <span
                      key={idx}
                      className={`px-[8px] py-[4px] bg-blue-50 text-blue-600 ${styles.fontSizes.textXS} ${styles.borderRadius.card}`}
                    >
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {orderStats.topDistrict && (
              <div className="pt-[10px] border-t border-gray-100">
                <div
                  className={`${styles.fontSizes.textXS} ${styles.colors.text.tertiary} mb-[4px]`}
                >
                  常去区域
                </div>
                <div className={`${styles.fontSizes.textSM} ${styles.colors.text.secondary}`}>
                  {orderStats.topDistrict}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 地图选择对话框 */}
      {showMapSelector && selectedRecommendation && (
        <SimpleMapAppSelector
          destinationName={selectedRecommendation.destinationName}
          onClose={() => {
            setShowMapSelector(false);
            setSelectedRecommendation(null);
          }}
          onSelect={handleMapAppSelect}
        />
      )}

      {/* Bottom Navigation */}
      <BottomNav />

      {/* Developer Console */}
      <DevConsole />
    </div>
  );
}
