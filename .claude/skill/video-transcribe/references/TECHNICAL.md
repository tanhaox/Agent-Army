# Video Transcribe 参考文档

## 1. 技术架构

### 1.1 整体流程图

```
视频链接
    ↓
获取视频信息
    ↓
检查平台字幕 → 有字幕 → 提取字幕
    ↓ 无字幕
下载音频文件
    ↓
Whisper 语音识别
    ↓
生成文本内容
    ↓
说话人分离
    ↓
检测语言
    ↓
需要翻译? ──是──→ AI 翻译
    ↓ 否
保存为 .txt 文件
```

### 1.2 模块说明

| 模块 | 功能 | 技术栈 |
|------|------|--------|
| download_audio.py | 下载音频文件 | yt-dlp |
| extract_subtitle.py | 提取平台字幕 | yt-dlp + OpenCC |
| transcribe.py | 语音识别 | Whisper |
| diarization.py | 说话人分离 | pyannote.audio |
| translate.py | AI 翻译 | DeepSeek/豆包/Kimi |
| main.py | 主程序协调 | - |

## 2. 字幕提取逻辑

### 2.1 字幕优先级

```
1. 简体中文 (zh-Hans, zh-CN)
2. 繁体中文 (zh-Hant, zh-TW) → 自动转简体
3. 英文 (en) → 保留原文 + 翻译
```

### 2.2 字幕格式

支持的字幕格式：
- SRT (SubRip)
- ASS/SSA
- VTT (WebVTT)

### 2.3 OpenCC 配置

繁简转换使用 OpenCC 库，配置：
- 转换类型：t2s (繁体转简体)
- 安装：`pip install opencc`

## 3. Whisper 模型说明

### 3.1 模型大小对比

| 模型 | 大小 | 速度 | 精度 | 推荐场景 |
|------|------|------|------|----------|
| tiny | ~39MB | 最快 | 一般 | 快速测试 |
| base | ~74MB | 快 | 较好 | 日常使用（默认）|
| small | ~244MB | 中等 | 好 | 平衡选择 |
| medium | ~769MB | 慢 | 很好 | 高精度需求 |
| large | ~1550MB | 最慢 | 最好 | 专业场景 |

### 3.2 模型下载

首次运行时，Whisper 会自动下载模型到：
```
~/.cache/whisper/  (Linux/Mac)
C:\Users\<用户名>\.cache\whisper\  (Windows)
```

## 4. 说话人分离

### 4.1 AI 分离（可选）

使用 pyannote.audio 进行精确分离：

```python
# 需要先接受模型用户协议
# 1. 访问: https://huggingface.co/pyannote/speaker-diarization-3.1
# 2. 接受用户协议
# 3. 生成 Hugging Face Token
# 4. 设置环境变量: HF_TOKEN=your_token_here
```

### 4.2 规则分离（默认）

基于启发式规则：
- 段落长度检测
- 标点符号分析（问号、句号）
- 对话模式识别

优点：无需额外配置，速度快
缺点：精度不如 AI 分离

## 5. AI 翻译服务

### 5.1 DeepSeek（推荐）

- API: https://api.deepseek.com/v1
- 模型: deepseek-chat
- 免费额度：充裕
- 翻译质量：优秀

获取 API Key:
1. 访问 https://platform.deepseek.com/
2. 注册/登录
3. 进入 API Keys 页面
4. 创建新 Key

### 5.2 豆包

- API: https://ark.cn-beijing.volces.com/api/v3
- 模型: ep-20250201135848-5r4g2（示例，使用实际模型 ID）
- 定价：按 tokens 计费

### 5.3 Kimi

- API: https://api.moonshot.cn/v1
- 模型: moonshot-v1-8k
- 定价：按 tokens 计费

## 6. 环境变量

```bash
# AI 翻译服务（三选一）
DEEPSEEK_API_KEY=sk-xxxxxxxxx
DOUBAO_API_KEY=xxxxxxxxx
KIMI_API_KEY=sk-xxxxxxxxx

# 说话人分离（可选）
HF_TOKEN=hf_xxxxxxxxx

# Claude API（备用）
CLAUDE_API_KEY=sk-ant-xxxxxxxxx
```

## 7. 故障排除

### 7.1 常见错误

#### 错误: `ffmpeg not found`
**解决**:
1. 下载 FFmpeg
2. 解压到 `C:\ffmpeg`
3. 添加到 PATH: `C:\ffmpeg\bin`

#### 错误: `HTTP Error 403`
**原因**: 视频有地区限制或需要登录
**解决**: 尝试其他视频或使用代理

#### 错误: `No module named 'whisper'`
**解决**:
```bash
pip install openai-whisper
```

#### 错误: `CUDA out of memory`
**解决**:
1. 使用更小的 Whisper 模型（tiny/base）
2. 或在 transcribe.py 中设置 `device="cpu"`

### 7.2 性能优化

1. **降低模型大小**
   ```python
   # transcribe.py
   model_size = 'tiny'  # 或 'base'
   ```

2. **跳过翻译**
   ```bash
   python main.py <url> --no-translate
   ```

3. **禁用说话人分离**
   修改 `diarization.py`，直接返回原文本

## 8. 扩展开发

### 8.1 添加新的视频平台

修改 `download_audio.py`，yt-dlp 已支持大部分平台：
```python
# yt-dlp 会自动检测平台，无需额外配置
```

### 8.2 添加新的翻译服务

在 `translate.py` 中添加新的 Translator 类：
```python
class YourTranslator(AITranslator):
    def translate(self, text, source_lang='en', target_lang='zh'):
        # 实现你的翻译逻辑
        pass
```

### 8.3 自定义输出格式

修改 `main.py` 中的 `output_path` 生成逻辑：
```python
# 修改文件扩展名
output_path = OUTPUT_DIR / f"{safe_title}.md"  # 输出 Markdown
```

## 9. API 参考

### 9.1 main.process_video()

```python
def process_video(url, translate_service='deepseek'):
    """
    处理视频，提取文稿

    Args:
        url: 视频链接
        translate_service: 翻译服务 (deepseek/doubao/kimi/None)

    Returns:
        输出文件路径 (Path) 或 None
    """
```

### 9.2 extract_subtitle.extract_subtitle()

```python
def extract_subtitle(url, output_dir):
    """
    提取视频字幕

    Args:
        url: 视频链接
        output_dir: 输出目录

    Returns:
        字幕文本内容，无字幕返回 None
    """
```

### 9.3 transcribe.transcribe_audio()

```python
def transcribe_audio(audio_path, model_size='base'):
    """
    使用 Whisper 进行语音识别

    Args:
        audio_path: 音频文件路径
        model_size: Whisper 模型大小 (tiny/base/small/medium/large)

    Returns:
        识别后的文本
    """
```

## 10. 更新日志

### v1.0.0 (2024-02-06)
- 初始版本
- 支持 YouTube、B站、今日头条、抖音
- 字幕提取和语音识别
- 说话人分离
- AI 翻译
