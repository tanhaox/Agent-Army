# AKShare 股票数据接口测试

本目录包含AKShare股票数据接口库的本地测试代码和测试报告。

## 目录结构

```
AKShare/
├── README.md           # 本文件
├── TEST_REPORT.md      # 详细测试报告
├── test_akshare.py     # 测试脚本
└── data/               # 测试数据(可选)
```

## 快速开始

### 1. 安装AKShare

```bash
# 使用阿里云镜像安装
pip install akshare -i https://mirrors.aliyun.com/pypi/simple/ --upgrade
```

### 2. 运行测试

```bash
python test_akshare.py
```

### 3. 查看报告

测试完成后查看 [TEST_REPORT.md](./TEST_REPORT.md) 了解详细的测试结果。

## 测试覆盖

AKShare提供了丰富的金融数据接口，本项目测试了以下功能：

### 股票数据
- [x] A股实时行情 (`stock_zh_a_spot_em`)
- [x] 个股历史数据 (`stock_zh_a_hist`)
- [x] 个股详细信息 (`stock_individual_info_em`)
- [ ] 港股实时行情 (`stock_hk_spot_em`)
- [ ] 美股实时行情 (`stock_us_spot_em`)

### 基金数据
- [ ] ETF基金实时行情 (`fund_etf_spot_em`)
- [ ] LOF基金实时行情 (`fund_lof_spot_em`)
- [ ] REITs实时行情 (`reits_realtime_em`)

### 期货数据
- [x] 期货实时行情 (`futures_zh_realtime`)
- [ ] 商品期货指数 (`futures_index_ccidx`)

### 宏观经济数据
- [x] CPI数据 (`macro_china_cpi`)
- [ ] PPI数据 (`macro_china_ppi`)
- [ ] GDP数据 (`macro_china_gdp`)
- [ ] 货币供应量 (`macro_china_money_supply`)

> 说明: [x] 表示测试通过，[ ] 表示测试未通过或未测试

## 测试结果(2026-03-12)

| 接口 | 状态 | 说明 |
|------|------|------|
| stock_zh_a_hist | ✅ 通过 | 获取268条平安银行历史数据 |
| stock_individual_info_em | ✅ 通过 | 获取9项基本面信息 |
| macro_china_cpi | ✅ 通过 | 获取218条CPI数据 |
| futures_zh_realtime | ✅ 通过 | 获取13条期货数据 |
| stock_zh_a_spot_em | ⚠️ 网络中断 | 需要重试机制 |
| fund_etf_spot_em | ⚠️ 网络中断 | 需要重试机制 |
| stock_hk_spot_em | ⚠️ 网络中断 | 需要重试机制 |
| stock_us_spot_em | ⚠️ 网络中断 | 需要重试机制 |

## 常见问题

### Q1: 连接被远程服务器关闭怎么办？

这是数据源的反爬虫机制。解决方案：

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
```

### Q2: 如何部署为HTTP API服务？

使用AKTools提供RESTful API接口：

```bash
# 安装AKTools
pip install aktools --upgrade

# 启动服务
python -m aktools --port 8080

# 使用Gunicorn部署(生产环境)
gunicorn -w 4 -b 0.0.0.0:8080 aktools:app
```

### Q3: 如何控制请求频率？

添加延迟避免触发限流：

```python
import time

for code in stock_list:
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily")
        time.sleep(0.5)  # 每次请求间隔0.5秒
    except Exception as e:
        print(f"获取{code}失败: {e}")
        time.sleep(2)  # 失败后增加延迟
```

## 生产环境部署

### 推荐架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   应用层    │────▶│  AKTools    │────▶│  数据源     │
│  (Next.js)  │     │  HTTP API   │     │ (东方财富等) │
└─────────────┘     └─────────────┘     └─────────────┘
                         │
                    Gunicorn
                         │
                      Nginx
```

### 部署步骤

1. **安装依赖**
   ```bash
   pip install akshare aktools gunicorn
   ```

2. **配置Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8080 aktools:app
   ```

3. **配置Nginx反向代理**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:8080;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

4. **配置进程监控**
   ```bash
   # 使用supervisor
   supervisorctl start akshare-api
   ```

## 相关资源

- [AKShare官方文档](https://akshare.akfamily.xyz)
- [AKShare GitHub](https://github.com/akfamily/akshare)
- [AKTools文档](https://github.com.comakfamily/aktools)
- [使用手册](../AKShare股票数据全面接入服务器使用手册.docx)

## 许可证

本测试代码仅用于学习和测试目的。AKShare遵循MIT许可证。

## 更新日志

- **2026-03-12**: 初始版本，完成基础接口测试
