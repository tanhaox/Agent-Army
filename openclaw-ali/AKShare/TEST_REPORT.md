# AKShare股票数据接口测试报告

**测试日期**: 2026-03-12
**AKShare版本**: 1.18.38
**Pandas版本**: 3.0.0
**测试环境**: Windows 11, Python 3.13

---

## 测试结果摘要

| 接口类型 | 接口名称 | 测试状态 | 数据量 | 说明 |
|---------|---------|---------|--------|------|
| A股实时行情 | stock_zh_a_spot_em | ⚠️ 网络中断 | - | 连接被远程服务器关闭 |
| 个股历史数据 | stock_zh_a_hist | ✅ **通过** | 268条 | 平安银行(000001)历史数据 |
| 个股详细信息 | stock_individual_info_em | ✅ **通过** | 9项 | 平安银行基本信息 |
| ETF基金行情 | fund_etf_spot_em | ⚠️ 网络中断 | - | 连接被远程服务器关闭 |
| 港股实时行情 | stock_hk_spot_em | ⚠️ 网络中断 | - | 连接被远程服务器关闭 |
| 美股实时行情 | stock_us_spot_em | ⚠️ 网络中断 | - | 连接被远程服务器关闭 |
| 宏观经济-CPI | macro_china_cpi | ✅ **通过** | 218条 | 2008年1月至今CPI数据 |
| 期货实时行情 | futures_zh_realtime | ✅ **通过** | 13条 | PTA期货主力合约 |

**总计**: 8个测试用例，**4个通过**，4个网络中断

---

## 通过的测试详情

### 1. 个股历史数据 (stock_zh_a_hist) ✅

**功能**: 获取指定股票的历史K线数据

**测试参数**:
```python
symbol = "000001"      # 平安银行
period = "daily"       # 日线
start_date = "20250201"
end_date = "20260312"
adjust = "qfq"         # 前复权
```

**返回数据字段**:
- 日期
- 股票代码
- 开盘价、收盘价、最高价、最低价
- 成交量、成交额
- 振幅、涨跌幅、涨跌额、换手率

**最新5条数据示例**:
```
日期          股票代码   开盘价  收盘价  最高价  最低价    成交量       成交额
2026-03-06   000001    10.78   10.82   10.84   10.77   476577   5.15亿
2026-03-09   000001    10.79   10.76   10.82   10.74   835892   9.01亿
2026-03-10   000001    10.77   10.81   10.81   10.73   790112   8.51亿
2026-03-11   000001    10.79   10.89   10.90   10.77   720535   7.81亿
2026-03-12   000001    10.87   10.94   10.96   10.85   754906   8.24亿
```

---

### 2. 个股详细信息 (stock_individual_info_em) ✅

**功能**: 获取单只股票的基本面信息

**返回数据**:
```
项目           数据
最新价:         10.94
股票代码:        000001
股票名称:        平安银行
总股本:         194.06亿股
流通股:         194.06亿股
总市值:         2123.01亿
流通市值:       2122.97亿
行业:           银行
上市时间:       1991-04-03
```

---

### 3. CPI宏观数据 (macro_china_cpi) ✅

**功能**: 获取中国居民消费价格指数(CPI)数据

**数据范围**: 2008年1月至今，共218条记录

**主要字段**:
- 月份
- 全国-当月、全国-同比增长、全国-环比增长
- 城市-当月、城市-同比增长、城市-环比增长
- 农村-当月、农村-同比增长、农村-环比增长

---

### 4. 期货实时行情 (futures_zh_realtime) ✅

**功能**: 获取中国期货市场实时行情

**返回数据**: 13条期货合约数据

**示例数据(PTA期货)**:
```
合约     交易所   名称      最新价   结算价   开盘价   最高价   最低价   成交量      持仓量
TA0      czce    PTA主力   6998.0   7054.0   6812.0   7160.0   6764.0   3028359   1208275
TA2605   czce    PTA2605   6998.0   7054.0   6812.0   7160.0   6764.0   3028359   1208275
TA2609   czce    PTA2609   6606.0   6580.0   6498.0   6672.0   6318.0   290339    308785
```

---

## 网络中断问题分析

### 问题描述

以下4个接口在测试时出现连接中断：
- stock_zh_a_spot_em (A股实时行情)
- fund_etf_spot_em (ETF基金)
- stock_hk_spot_em (港股)
- stock_us_spot_em (美股)

**错误信息**:
```
('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

### 可能原因

1. **数据源服务器限制**: 东方财富等数据源可能对爬虫频率有限制
2. **网络不稳定**: 测试时网络波动导致连接中断
3. **反爬虫机制**: 数据源检测到自动化请求并主动断开连接
4. **请求频率过高**: 短时间内发送多个请求触发限流

### 解决方案(参考手册第四章)

#### 方案1: 添加重试机制
```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    print(f"尝试{attempt+1}失败，{delay}秒后重试...")
                    time.sleep(delay * (attempt + 1))
        return wrapper
    return decorator

@retry_on_failure(max_retries=3, delay=2)
def get_stock_spot():
    return ak.stock_zh_a_spot_em()
```

#### 方案2: 控制请求频率
```python
import time

# 批量获取时添加延迟
for code in stock_list:
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily")
        time.sleep(0.5)  # 每次请求间隔0.5秒
    except Exception as e:
        print(f"获取{code}失败: {e}")
        time.sleep(2)  # 失败后增加延迟
```

#### 方案3: 使用AKTools HTTP API

根据手册第1.3节，可以部署AKTools提供稳定的HTTP API服务：

```bash
# 安装AKTools
pip install aktools --upgrade

# 启动HTTP服务
python -m aktools --port 8080

# 使用Gunicorn部署(生产环境)
gunicorn -w 4 -b 0.0.0.0:8080 aktools:app
```

---

## 部署建议

### 开发环境
- 直接使用AKShare Python库
- 添加重试和频率控制
- 本地缓存不常变化的数据

### 生产环境
- 使用AKTools提供HTTP API服务
- Gunicorn + Nginx反向代理
- 配置进程监控(supervisor)
- 设置日志轮转和告警

### 监控要点
1. 数据获取成功率
2. 响应时间
3. 数据完整性检查
4. 异常告警通知

---

## 结论

AKShare (v1.18.38) 核心功能正常，可以成功获取：
- ✅ 个股历史K线数据
- ✅ 个股基本信息
- ✅ 宏观经济指标
- ✅ 期货实时行情

部分实时行情接口存在网络不稳定问题，建议：
1. 添加重试机制
2. 控制请求频率
3. 部署AKTools HTTP API服务
4. 配置监控告警

**总体评价**: ⭐⭐⭐⭐ 适合用于本地数据获取和分析，生产环境建议配合HTTP API部署方案。

---

**测试文件**: [test_akshare.py](./test_akshare.py)
**参考手册**: AKShare股票数据全面接入服务器使用手册.docx
