# ===========================================
# 修复数据库连接配置
# ===========================================

# 备份当前配置
cp /var/www/miaoying/.env /var/www/miaoying/.env.backup-$(date +%Y%m%d-%H%M%S)

# 更新数据库连接字符串
# 问题：当前可能指向了错误的数据库名称
# 解决：使用正确的数据库名称 beijing_didi

cat > /var/www/miaoying/.env << 'ENVEOF'
# ===========================================
# miaoying（秒应）环境变量配置
# ===========================================

# ===========================================
# 应用配置
# ===========================================
NODE_ENV=production
PORT=6001
NEXT_PUBLIC_BASE_URL=http://112.126.61.223
LOG_LEVEL=info

# ===========================================
# 数据库配置
# ===========================================
# 主数据库 - beijing_didi（业务数据）
DATABASE_URL="postgresql://miaoying_user:Miaoying2024@localhost:5432/beijing_didi"
PGHOST=localhost
PGPORT=5432
PGDATABASE=beijing_didi
DB_NAME=beijing_didi
PGUSER=miaoying_user
PGPASSWORD=Miaoying2024

# 辅助数据库 - beijing_auxiliary（天气缓存、航班数据）
AUXILIARY_DATABASE_URL="postgresql://miaoying_user:Miaoying2024@localhost:5432/beijing_auxiliary"

# ===========================================
# Redis配置
# ===========================================
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_DISABLED=true

# ===========================================
# 地图服务配置
# ===========================================
MAP_PROVIDER=tianditu
TIANDITU_MAP_TK=2da6f7f8309317ea0e3dadf251525dd2
NEXT_PUBLIC_TIANDITU_MAP_TK=2da6f7f8309317ea0e3dadf251525dd2
BAIDU_MAP_AK=MNREoKkyPyeFh5QXmwbDK927LKNjgBW2
NEXT_PUBLIC_BAIDU_MAP_AK=MNREoKkyPyeFh5QXmwbDK927LKNjgBW2

# ===========================================
# JWT配置
# ===========================================
JWT_SECRET=72b8728f0c475c6ad89f05a3b89ad179a7f52eeaa1ee71560c6ab18b653da33f
CLEANUP_SECRET=c3566e6a9f9acf31c5fa2d83a2d2d3de1dfe520c36c415bfed01689240ade7e1

# ===========================================
# 管理员账号
# ===========================================
ADMIN_USERNAME=admin_dev
ADMIN_PASSWORD=Dev@2026#Strong

# ===========================================
# OCR 配置
# ===========================================
OCR_MODE=baidu
NEXT_PUBLIC_OCR_MODE=real
BAIDU_OCR_API_KEY=16N5PlMVU1fcBSAsCVNkFSwx
BAIDU_OCR_SECRET_KEY=WkctULy2sfpAFSzi9o5LvKsCmyrmQUPj
BAIDU_OCR_ENDPOINT=https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic

# ===========================================
# DeepSeek LLM配置
# ===========================================
DEEPSEEK_API_KEY=sk-85e501c6ac0c4818bb44503fb7b5e63b
DEEPSEEK_API_URL=https://api.deepseek.com
DEEPSEEK_MODEL_OCR=deepseek-chat
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MODEL_CORRECTION=deepseek-reasoner

# ===========================================
# 功能开关
# ===========================================
DISABLE_DATA_QUALITY_FILTER=false
DISABLE_LOGGING=false
DISABLE_PERFORMANCE_STATS=false
ENVEOF

# 重启应用
echo "✅ 配置文件已更新"
echo "🔄 重启应用..."
pm2 restart miaoying

echo ""
echo "✅ 修复完成！"
echo "📝 请尝试重新登录"
echo ""
echo "查看应用日志："
echo "  pm2 logs miaoying --lines 50"
