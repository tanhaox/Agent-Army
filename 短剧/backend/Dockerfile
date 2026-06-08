FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libpq-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖（使用镜像加速）
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 复制应用代码
COPY . .

# 赋予启动脚本执行权限
RUN chmod +x start.sh

EXPOSE 8000

# 启动：先迁移，再运行
CMD ["./start.sh"]
