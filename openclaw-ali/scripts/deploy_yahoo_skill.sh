#!/bin/bash
# 雅虎财经Skill自动部署脚本

echo "=========================================="
echo "  雅虎财经Skill部署到OpenClaw服务器"
echo "=========================================="
echo ""

# 服务器信息
SERVER="root@112.126.61.223"
SOURCE_DIR="./skills/yahoo-finance"
TARGET_DIR="~/.openclaw/skills/yahoo-finance"

# 检查本地文件
echo "1. 检查本地文件..."
if [ ! -d "$SOURCE_DIR" ]; then
    echo "   ❌ 错误：本地skill目录不存在: $SOURCE_DIR"
    exit 1
fi

REQUIRED_FILES=("SKILL.md" "tool.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$SOURCE_DIR/$file" ]; then
        echo "   ❌ 错误：缺少必需文件: $file"
        exit 1
    fi
    echo "   ✅ $file"
done

echo ""
echo "2. 上传到服务器..."
# 删除服务器上的旧版本（如果存在）
ssh $SERVER "rm -rf ~/.openclaw/skills/yahoo-finance"

# 上传新版本
scp -r $SOURCE_DIR $SERVER:$TARGET_DIR

if [ $? -eq 0 ]; then
    echo "   ✅ 上传成功"
else
    echo "   ❌ 上传失败"
    exit 1
fi

echo ""
echo "3. 设置权限..."
ssh $SERVER "chmod +x ~/.openclaw/skills/yahoo-finance/tool.py"
ssh $SERVER "chmod 644 ~/.openclaw/skills/yahoo-finance/SKILL.md"
echo "   ✅ 权限设置完成"

echo ""
echo "4. 重启OpenClaw Gateway..."
ssh $SERVER "openclaw gateway restart"
echo "   ✅ Gateway已重启"

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""
echo "下一步：在OpenClaw中测试"
echo "  输入: refresh skills"
echo "  输入: 同步贵州茅台的雅虎财经数据"
echo ""

# 验证
echo "5. 验证部署..."
ssh $SERVER "ls -lh ~/.openclaw/skills/yahoo-finance/" | grep -E "SKILL.md|tool.py"

echo ""
echo "✅ Skill已成功部署到OpenClaw！"
