# Backup Agent 增强功能 - 系统托盘和备份压缩

**创建日期**: 2026-02-26
**状态**: 待改进
**优先级**: 中
**类型**: 功能增强

---

## 一、需求描述

### 背景
Backup Agent 已经实现了自动备份和回滚功能，但缺少：
1. 用户友好的系统托盘界面（Windows）
2. 压缩备份功能（节省空间，便于归档）

### 目标
为 Backup Agent 增加两个新功能：
1. **系统托盘图标**：方便用户管理和查看 Backup Agent 状态
2. **备份压缩功能**：整点备份后自动压缩，节省存储空间

### 核心价值
- 🖥️ 更友好的用户界面（系统托盘）
- 💾 节省存储空间（ZIP 压缩）
- 📦 便于长期归档（压缩包）

---

## 二、技术方案

### 2.1 系统托盘功能

#### 技术栈
- **库**：`pystray` + `Pillow`
- **图标文件**：`C:\Users\tanha\Downloads\server.png`（PNG 格式）

#### 功能设计

**托盘图标显示**：
- 图标：使用用户提供的 server.png
- 鼠标悬停提示：显示 Backup Agent 状态
  - 运行中：`Backup Agent - 上次备份：5分钟前`
  - 已停止：`Backup Agent - 已停止`

**右键菜单**：
```
├── 📊 查看状态
├── 📋 查看备份清单
├── 📁 打开日志目录
├── 📦 打开压缩包目录
├── ─────────────
├── ▶️ 启动服务 / ⏸ 停止服务
└── ❌ 退出
```

**菜单功能说明**：

| 菜单项 | 功能 | 说明 |
|--------|------|------|
| 查看状态 | 显示仓库状态 | 弹窗显示当前分支、修改状态等 |
| 查看备份清单 | 列出最近备份 | 弹窗显示最近 12 小时的备份 |
| 打开日志目录 | 打开 logs 文件夹 | 使用系统资源管理器打开 |
| 打开压缩包目录 | 打开 backups 文件夹 | 使用系统资源管理器打开 |
| 启动/停止服务 | 切换服务状态 | 动态显示当前状态 |
| 退出 | 完全退出程序 | 停止所有服务并退出 |

#### 实现细节

**图标加载**：
```python
from PIL import Image

# 加载 PNG 图标
icon_image = Image.open("C:\\Users\\tanha\\Downloads\\server.png")
icon_image = icon_image.resize((64, 64), Image.Resampling.LANCZOS)
```

**托盘创建**：
```python
import pystray

icon = pystray.Icon(
    "backup_agent",
    icon_image,
    "Backup Agent",
    menu=pystray.Menu(
        pystray.MenuItem("查看状态", show_status),
        pystray.MenuItem("查看备份清单", show_backups),
        pystray.MenuItem("打开日志目录", open_logs_dir),
        pystray.MenuItem("打开压缩包目录", open_backups_dir),
        pystray.MenuItem("启动服务", start_service),
        pystray.MenuItem("停止服务", stop_service),
        pystray.MenuItem("退出", exit_app)
    )
)
icon.run()
```

---

### 2.2 备份压缩功能

#### 技术栈
- **库**：Python 内置 `zipfile`
- **格式**：ZIP

#### 功能设计

**压缩时机**：
- ✅ 整点备份完成后自动触发
- ❌ 改进意见触发备份时不压缩（太频繁）

**压缩范围**：
- 只压缩修改的文件（增量压缩）
- 使用 Git diff 获取修改的文件列表
- 不包含 `.git` 目录（节省空间）

**压缩包命名**：
```
backup-agent-20260226-181000.zip
backup-agent-20260226-190000.zip
```

**存储位置**：
```
projects/tools/backup-agent/backups/
```

**保留策略**：
- 保留最近 10 个压缩包
- 超过 10 个时自动删除最旧的压缩包

#### 实现细节

**获取修改文件列表**：
```python
def get_changed_files(repo, last_commit_hash):
    """获取自上次提交以来修改的文件"""
    # 获取当前 HEAD
    current_head = repo.head.commit

    # 获取上次提交
    last_commit = repo.commit(last_commit_hash)

    # 获取差异
    diff = current_head.diff(last_commit)

    # 收集修改的文件路径
    changed_files = []
    for item in diff:
        if item.a_path:
            changed_files.append(item.a_path)
        if item.b_path:
            changed_files.append(item.b_path)

    return changed_files
```

**创建压缩包**：
```python
import zipfile
import os
from datetime import datetime

def create_backup_zip(source_dir, changed_files, output_dir):
    """创建备份压缩包"""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    zip_name = f"backup-agent-{timestamp}.zip"
    zip_path = os.path.join(output_dir, zip_name)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in changed_files:
            full_path = os.path.join(source_dir, file_path)
            if os.path.exists(full_path):
                arcname = file_path  # 保持相对路径
                zipf.write(full_path, arcname)

    return zip_path
```

**自动清理旧压缩包**：
```python
def cleanup_old_backups(backup_dir, keep_count=10):
    """清理旧压缩包，保留最近的 N 个"""
    # 获取所有压缩包
    zip_files = []
    for file in os.listdir(backup_dir):
        if file.endswith('.zip'):
            file_path = os.path.join(backup_dir, file)
            mtime = os.path.getmtime(file_path)
            zip_files.append((file_path, mtime))

    # 按修改时间排序（新的在前）
    zip_files.sort(key=lambda x: x[1], reverse=True)

    # 删除超过保留数量的旧包
    if len(zip_files) > keep_count:
        for file_path, _ in zip_files[keep_count:]:
            os.remove(file_path)
```

---

## 三、预期结果

### 3.1 系统托盘

**视觉效果**：
- ✅ Windows 任务栏托盘区显示 Backup Agent 图标
- ✅ 鼠标悬停显示当前状态
- ✅ 右键菜单功能完整

**交互体验**：
- ✅ 点击菜单项即时响应
- ✅ 启动/停止服务状态实时切换
- ✅ 查看状态/清单弹窗显示

### 3.2 备份压缩

**压缩效果**：
- ✅ 整点备份后自动创建 ZIP 压缩包
- ✅ 只包含修改的文件（节省空间）
- ✅ 压缩包命名规范，便于识别

**自动清理**：
- ✅ 超过 10 个压缩包时自动删除旧包
- ✅ 不影响最新的 10 个压缩包

---

## 四、影响范围

### 4.1 新增文件

- `projects/tools/backup-agent/tray_icon.py` - 系统托盘模块
- `projects/tools/backup-agent/backup_compressor.py` - 备份压缩模块
- `projects/tools/backup-agent/backups/` - 压缩包存储目录

### 4.2 修改文件

- `backup_agent.py` - 集成系统托盘和压缩功能
- `scheduler.py` - 整点备份后触发压缩
- `requirements.txt` - 添加 `pystray` 和 `Pillow`
- `config.json` - 添加压缩相关配置

### 4.3 依赖影响

**新增依赖**：
```
pystray>=0.19.5
Pillow>=10.0.0
```

---

## 五、实施计划

### 步骤 1：创建备份压缩模块
- [ ] 实现 `backup_compressor.py`
- [ ] 实现获取修改文件列表
- [ ] 实现创建 ZIP 压缩包
- [ ] 实现自动清理旧压缩包

### 步骤 2：创建系统托盘模块
- [ ] 实现 `tray_icon.py`
- [ ] 加载用户提供的 PNG 图标
- [ ] 创建右键菜单
- [ ] 实现各菜单项功能

### 步骤 3：集成到主程序
- [ ] 修改 `backup_agent.py`
- [ ] 添加 `--tray` 参数（启动托盘模式）
- [ ] 修改 `scheduler.py`（整点备份后触发压缩）

### 步骤 4：更新配置和文档
- [ ] 更新 `config.json`
- [ ] 更新 `requirements.txt`
- [ ] 更新 `README.md`

### 步骤 5：测试
- [ ] 测试系统托盘功能
- [ ] 测试备份压缩功能
- [ ] 测试自动清理功能

---

## 六、配置示例

### config.json 新增配置

```json
{
  "tray_icon": {
    "enabled": true,
    "icon_path": "C:\\Users\\tanha\\Downloads\\server.png",
    "tooltip_format": "Backup Agent - 上次备份：{time_ago}"
  },
  "backup_compression": {
    "enabled": true,
    "compress_on": "hourly",
    "backup_dir": "backups",
    "keep_count": 10,
    "exclude_patterns": [".git", "node_modules", "__pycache__"]
  }
}
```

---

## 七、备注

- **图标文件**：用户提供的 `C:\Users\tanha\Downloads\server.png`
- **图标格式**：PNG（代码中自动转换，无需预先转换为 ICO）
- **压缩格式**：ZIP（Python 内置，无需额外依赖）
- **兼容性**：仅限 Windows（pystray 主要支持 Windows）

---

**文档版本**: v1.0
**最后更新**: 2026-02-26
