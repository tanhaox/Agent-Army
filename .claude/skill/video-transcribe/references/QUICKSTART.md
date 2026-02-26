# 快速开始指南

## 5 分钟快速上手

### 第一步：安装依赖

```bash
# 双击运行安装脚本
install.bat

# 或手动安装
pip install -r requirements.txt
```

### 第二步：配置 FFmpeg

1. 下载 FFmpeg: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z
2. 解压到 `C:\ffmpeg`
3. 添加到系统 PATH：
   - 右键"此电脑" → 属性 → 高级系统设置 → 环境变量
   - 在"系统变量"中找到 Path，编辑
   - 添加 `C:\ffmpeg\bin`

验证安装：
```bash
ffmpeg -version
```

### 第三步：（推荐）配置翻译服务

获取免费 API Key（推荐 DeepSeek）：

1. 访问 https://platform.deepseek.com/
2. 注册/登录
3. 点击 API Keys → 创建新 Key
4. 设置环境变量：
   ```bash
   set DEEPSEEK_API_KEY=你的key
   ```

### 第四步：运行

```bash
cd C:\AI-Agent-Local\.claude\skill\video-transcribe\scripts
python main.py https://www.youtube.com/watch?v=视频ID
```

完成！文稿会保存在 `C:\AI-Agent-Local\.claude\docs\` 目录下。

## 常用命令

```bash
# 使用不同翻译服务
python main.py <链接> --translate deepseek
python main.py <链接> --translate doubao
python main.py <链接> --translate kimi

# 不翻译
python main.py <链接> --no-translate

# 仅下载音频
python download_audio.py <视频链接>
```

## 支持的视频链接示例

- YouTube: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- B站: `https://www.bilibili.com/video/BV1xx411c7mD`
- 抖音: `https://www.douyin.com/video/1234567890`

## 遇到问题？

查看 [README.md](../README.md) 或 [references/TECHNICAL.md](../references/TECHNICAL.md)
