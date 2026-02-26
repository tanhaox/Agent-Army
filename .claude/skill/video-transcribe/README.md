# Video Transcribe

从视频链接提取完整文稿，支持多平台视频处理。

## 支持平台

- YouTube
- B站 (bilibili.com)
- 今日头条
- 抖音

## 功能特性

- 自动提取平台字幕（优先级：简体中文 > 繁体中文（转简体） > 英文）
- 无字幕时使用 Whisper 进行语音识别
- 对话视频自动区分说话人（人物A、人物B等）
- 英文内容自动翻译为简体中文（保留英文原文）
- 纯文本输出，按段落组织

## 安装

### 1. 安装 Python 依赖

```bash
cd C:\AI-Agent-Local\.claude\skill\video-transcribe
pip install -r requirements.txt
```

### 2. 安装 FFmpeg

yt-dlp 需要 FFmpeg 来处理音频。

**Windows:**
1. 下载 FFmpeg: https://www.gyan.dev/ffmpeg/builds/
2. 解压到 `C:\ffmpeg`
3. 添加到系统环境变量 PATH

**验证安装:**
```bash
ffmpeg -version
```

### 3. 配置 AI 翻译服务（可选）

需要翻译功能时，设置以下环境变量之一：

```bash
# DeepSeek（推荐，免费额度充足）
set DEEPSEEK_API_KEY=your_api_key_here

# 豆包
set DOUBAO_API_KEY=your_api_key_here

# Kimi
set KIMI_API_KEY=your_api_key_here
```

**获取 API Key:**
- DeepSeek: https://platform.deepseek.com/
- 豆包: https://console.volcengine.com/ark
- Kimi: https://platform.moonshot.cn/

## 使用方法

### 命令行使用

```bash
cd C:\AI-Agent-Local\.claude\skill\video-transcribe\scripts

# 基本用法
python main.py <视频链接>

# 指定翻译服务
python main.py <视频链接> --translate deepseek
python main.py <视频链接> --translate doubao
python main.py <视频链接> --translate kimi

# 禁用翻译
python main.py <视频链接> --no-translate
```

### 示例

```bash
# YouTube 视频
python main.py https://www.youtube.com/watch?v=xxxxxxxxx

# B站视频
python main.py https://www.bilibili.com/video/BVxxxxxxxx

# 抖音视频
python main.py https://www.douyin.com/video/xxxxxxxxx
```

## 输出位置

生成的文稿文件保存在：`C:\AI-Agent-Local\.claude\docs\`

文件命名格式：`视频标题.txt`

## 工作流程

1. **下载音频**：使用 yt-dlp 下载最低质量的音频文件
2. **提取字幕**：优先提取平台字幕
3. **语音识别**：无字幕时使用 Whisper 识别
4. **说话人分离**：对话视频区分不同说话人
5. **翻译**：英文内容翻译为简体中文
6. **保存**：生成 .txt 文件

## 目录结构

```
video-transcribe/
├── SKILL.md              # Skill 描述文件
├── requirements.txt      # Python 依赖
├── scripts/             # 脚本目录
│   ├── main.py          # 主程序入口
│   ├── download_audio.py    # 下载音频
│   ├── extract_subtitle.py  # 提取字幕
│   ├── transcribe.py        # 语音识别
│   ├── diarization.py       # 说话人分离
│   └── translate.py         # 翻译
├── references/          # 参考文档
└── temp/               # 临时文件（自动清理）
```

## 注意事项

- 音频文件为过渡文件，处理完成后自动删除
- 视频下载使用最低质量以节省带宽和空间
- 长视频处理时间可能较长，请耐心等待
- 建议使用 DeepSeek 翻译（免费额度充足且质量好）

## 常见问题

### Q: FFmpeg 未找到？
A: 确保已安装 FFmpeg 并添加到系统 PATH 环境变量。

### Q: 下载视频失败？
A: 某些视频可能有地区限制或需要登录，尝试其他视频。

### Q: 语音识别很慢？
A: 首次运行需要下载 Whisper 模型，后续会更快。可以使用更小的模型（tiny/base）。

### Q: 翻译功能不工作？
A: 确保设置了正确的 API Key 环境变量。

### Q: 说话人分离效果不好？
A: 如果没有音频文件或模型未配置，会使用简单的规则分离。对于精确分离，需要配置 pyannote.audio 模型。

## 技术栈

- **yt-dlp**: 视频下载和字幕提取
- **Whisper**: OpenAI 开源语音识别
- **pyannote.audio**: 说话人分离
- **DeepSeek/豆包/Kimi**: AI 翻译

## 许可证

MIT License
