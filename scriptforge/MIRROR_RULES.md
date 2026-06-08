# ScriptForge 网络资源强制规则

> 本规则用于防止境外资源下载超时导致的阻塞问题，所有开发和测试必须遵守。

## 规则 1：禁止自动下载境外资源

- 禁止在运行时自动从 HuggingFace、GitHub、PyPI 等境外站点下载模型或大文件
- 所有模型文件必须提前下载到本地目录（如 `./models/`）
- 如需首次下载，在独立脚本中完成，不阻塞主服务

## 规则 2：模型本地化

- 模型加载必须使用本地路径：`./models/whisper/`、`./models/huggingface/`
- sentence-transformers 加载前设置 `HF_ENDPOINT=https://hf-mirror.com`
- 设置 `HF_HUB_CACHE=./models/huggingface` 避免默认缓存路径
- 模型加载失败时必须有 fallback 方案（如 jieba 替代 bge）

## 规则 3：网络超时与降级

- 所有 HTTP 请求 timeout ≤ 10 秒（包括 API 调用、模型下载）
- DeepSeek API 调用 timeout ≤ 120 秒（特殊允许）
- 网络请求失败时必须 graceful degrade，不能阻塞启动

## 规则 4：测试前预检查

- 测试脚本启动前检查：模型文件是否存在、端口是否占用、依赖包是否安装
- 缺失资源时输出明确的 WARNING 日志，不阻塞服务启动
- 使用 `logging.warning` 而非 `print`

## 规则 5：国内 PyPI 镜像

- pip 安装使用国内镜像：`pip install -i https://pypi.tuna.tsinghua.edu.cn/simple`
- 或永久配置：`pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple`
- HuggingFace 使用镜像：`HF_ENDPOINT=https://hf-mirror.com`
