#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Agent-Local 项目生成器

功能：
- 交互式创建新项目
- 自动生成标准目录结构
- 自动生成模板代码
- 自动配置日志系统
- 自动生成README

支持项目类型：
- skill: 技能类项目
- app: 应用类项目
- tool: 工具类项目

Author: AI-Agent-Local
Date: 2026-02-08
Version: 1.0.0
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import argparse


class ProjectGenerator:
    """项目生成器"""

    def __init__(self, root_dir: str = None):
        """初始化项目生成器

        Args:
            root_dir: AI-Agent-Local 根目录
        """
        if root_dir is None:
            self.root_dir = Path(__file__).parent.parent.parent
        else:
            self.root_dir = Path(root_dir)

        self.projects_dir = self.root_dir / "projects"
        self.shared_dir = self.root_dir / "shared"

        # 确保目录存在
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.shared_dir.mkdir(parents=True, exist_ok=True)

    def create_skill(self, name: str, description: str, author: str = "AI-Agent-Local"):
        """创建技能项目

        Args:
            name: 项目名称（英文小写+连字符）
            description: 项目描述
            author: 作者名称
        """
        project_dir = self.projects_dir / "skills" / name
        return self._create_project("skill", project_dir, name, description, author)

    def create_app(self, name: str, description: str, author: str = "AI-Agent-Local"):
        """创建应用项目

        Args:
            name: 项目名称（英文小写+连字符）
            description: 项目描述
            author: 作者名称
        """
        project_dir = self.projects_dir / "apps" / name
        return self._create_project("app", project_dir, name, description, author)

    def create_tool(self, name: str, description: str, author: str = "AI-Agent-Local"):
        """创建工具项目

        Args:
            name: 项目名称（英文小写+连字符）
            description: 项目描述
            author: 作者名称
        """
        project_dir = self.projects_dir / "tools" / name
        return self._create_project("tool", project_dir, name, description, author)

    def _create_project(self, project_type: str, project_dir: Path, name: str,
                       description: str, author: str):
        """创建项目（内部方法）

        Args:
            project_type: 项目类型（skill/app/tool）
            project_dir: 项目目录
            name: 项目名称
            description: 项目描述
            author: 作者名称
        """
        # 检查目录是否已存在
        if project_dir.exists():
            return {
                "success": False,
                "error": f"项目目录已存在: {project_dir}"
            }

        print(f"\n{'='*60}")
        print(f"开始创建 {project_type.upper()} 项目: {name}")
        print(f"{'='*60}\n")

        # 1. 创建目录结构
        print("[1/6] 创建目录结构...")
        self._create_directory_structure(project_type, project_dir)
        print("[OK] 目录结构已创建\n")

        # 2. 生成主要代码文件
        print("[2/6] 生成代码文件...")
        self._create_main_code(project_type, project_dir, name, description, author)
        print("[OK] 代码文件已生成\n")

        # 3. 生成配置文件
        print("[3/6] 生成配置文件...")
        self._create_config_files(project_type, project_dir, name)
        print("[OK] 配置文件已生成\n")

        # 4. 生成README
        print("[4/6] 生成 README.md...")
        self._create_readme(project_type, project_dir, name, description, author)
        print("[OK] README.md 已生成\n")

        # 5. 生成测试文件
        print("[5/6] 生成测试文件...")
        self._create_tests(project_type, project_dir, name)
        print("[OK] 测试文件已生成\n")

        # 6. 生成启动脚本
        print("[6/6] 生成启动脚本...")
        self._create_start_script(project_type, project_dir, name)
        print("[OK] 启动脚本已生成\n")

        print("="*60)
        print("[SUCCESS] 项目创建完成！")
        print("="*60)
        print(f"\n项目位置: {project_dir}")
        print("\n后续步骤:")
        print(f"  1. cd {project_dir}")
        print("  2. 编辑代码实现功能")
        print("  3. 运行测试: python -m pytest tests/")
        print(f"  4. 运行项目: python start_{name}.py")

        return {
            "success": True,
            "project_dir": str(project_dir),
            "project_type": project_type,
            "project_name": name
        }

    def _create_directory_structure(self, project_type: str, project_dir: Path):
        """创建目录结构"""
        project_dir.mkdir(parents=True, exist_ok=True)

        # 通用目录
        (project_dir / "logs").mkdir(exist_ok=True)
        (project_dir / "tests").mkdir(exist_ok=True)

        # 根据类型创建特定目录
        if project_type == "skill":
            (project_dir / "examples").mkdir(exist_ok=True)
            (project_dir / "docs").mkdir(exist_ok=True)
        elif project_type == "app":
            (project_dir / "backend").mkdir(exist_ok=True)
            (project_dir / "data").mkdir(exist_ok=True)
            (project_dir / "docs").mkdir(exist_ok=True)
        elif project_type == "tool":
            (project_dir / "utils").mkdir(exist_ok=True)

    def _create_main_code(self, project_type: str, project_dir: Path,
                          name: str, description: str, author: str):
        """创建主要代码文件"""
        class_name = self._to_pascal_case(name)
        var_name = name.replace("-", "_")

        if project_type == "skill":
            self._create_skill_code(project_dir, name, class_name, var_name, description, author)
        elif project_type == "app":
            self._create_app_code(project_dir, name, class_name, var_name, description, author)
        elif project_type == "tool":
            self._create_tool_code(project_dir, name, class_name, var_name, description, author)

    def _create_skill_code(self, project_dir: Path, name: str, class_name: str,
                          var_name: str, description: str, author: str):
        """创建技能项目代码"""
        # 修正文件名（避免双重后缀）
        if name.endswith("-skill"):
            file_name = name.replace("-", "_")  # demo-skill -> demo_skill
        else:
            file_name = var_name + "_skill"  # my-api -> my_api_skill

        # 主要技能文件
        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name} - {description}

主要功能：
- 功能1（待实现）
- 功能2（待实现）

Author: {author}
Date: {datetime.now().strftime("%Y-%m-%d")}
Version: 1.0.0
"""

import sys
from pathlib import Path
import logging

# 配置日志
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "{var_name}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class {class_name}Skill:
    """{class_name} 技能类"""

    def __init__(self):
        """初始化技能"""
        self.name = "{name}"
        self.description = "{description}"
        logger.info(f"{{self.name}} 技能初始化完成")

    def execute(self, **kwargs):
        """执行技能

        Args:
            **kwargs: 技能参数

        Returns:
            dict: 执行结果
        """
        logger.info(f"执行 {{self.name}} 技能")

        try:
            # TODO: 在这里实现你的技能逻辑
            result = {{
                "success": True,
                "message": "技能执行成功",
                "data": {{}}
            }}
            logger.info("技能执行完成")
            return result

        except Exception as e:
            logger.error(f"技能执行失败: {{e}}", exc_info=True)
            return {{
                "success": False,
                "error": str(e)
            }}

    def run(self, **kwargs):
        """运行技能（便捷方法）

        Args:
            **kwargs: 技能参数

        Returns:
            dict: 执行结果
        """
        return self.execute(**kwargs)


def main():
    """主函数（用于测试）"""
    skill = {class_name}Skill()
    result = skill.run()
    print(result)


if __name__ == "__main__":
    main()
'''
        (project_dir / f"{file_name}.py").write_text(code, encoding='utf-8')

        # __init__.py
        init_code = f'''"""
{name} 技能包
"""

from .{file_name.replace('.py', '')} import {class_name}Skill

__all__ = ['{class_name}Skill']
__version__ = '1.0.0'
'''
        (project_dir / "__init__.py").write_text(init_code, encoding='utf-8')

    def _create_app_code(self, project_dir: Path, name: str, class_name: str,
                         var_name: str, description: str, author: str):
        """创建应用项目代码"""
        # 主应用文件
        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name} - {description}

主要功能：
- 功能1（待实现）
- 功能2（待实现）

Author: {author}
Date: {datetime.now().strftime("%Y-%m-%d")}
Version: 1.0.0
"""

import sys
from pathlib import Path
import logging

# 配置日志
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "{var_name}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class {class_name}App:
    """{class_name} 应用类"""

    def __init__(self):
        """初始化应用"""
        self.name = "{name}"
        self.description = "{description}"
        logger.info(f"{{self.name}} 应用初始化完成")

    def run(self):
        """运行应用"""
        logger.info(f"启动 {{self.name}} 应用")

        try:
            # TODO: 在这里实现你的应用逻辑
            self.main_loop()

        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
        except Exception as e:
            logger.error(f"应用运行失败: {{e}}", exc_info=True)

    def main_loop(self):
        """主循环"""
        while True:
            # TODO: 实现主循环逻辑
            print(f"{{self.name}} 应用正在运行...")
            import time
            time.sleep(1)


def main():
    """主函数"""
    app = {class_name}App()
    app.run()


if __name__ == "__main__":
    main()
'''
        (project_dir / "main.py").write_text(code, encoding='utf-8')

    def _create_tool_code(self, project_dir: Path, name: str, class_name: str,
                          var_name: str, description: str, author: str):
        """创建工具项目代码"""
        code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name} - {description}

主要功能：
- 功能1（待实现）
- 功能2（待实现）

Author: {author}
Date: {datetime.now().strftime("%Y-%m-%d")}
Version: 1.0.0
"""

import sys
import argparse
from pathlib import Path
import logging

# 配置日志
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "{var_name}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class {class_name}Tool:
    """{class_name} 工具类"""

    def __init__(self):
        """初始化工具"""
        self.name = "{name}"
        self.description = "{description}"

    def run(self, args):
        """运行工具

        Args:
            args: 命令行参数
        """
        logger.info(f"运行 {{self.name}} 工具")

        try:
            # TODO: 在这里实现你的工具逻辑
            result = self.execute(args)
            return result

        except Exception as e:
            logger.error(f"工具运行失败: {{e}}", exc_info=True)
            return 1

    def execute(self, args):
        """执行工具逻辑

        Args:
            args: 解析后的参数

        Returns:
            int: 退出码（0表示成功）
        """
        # TODO: 实现具体逻辑
        print(f"{{self.name}} 工具正在执行...")
        return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="{description}",
        epilog=f"""
示例:
  %(prog)s --help
  %(prog)s --option value
        """
    )

    # TODO: 添加你的参数
    parser.add_argument("--option", help="选项说明")
    parser.add_argument("--verbose", action="store_true", help="详细输出")

    args = parser.parse_args()

    tool = {class_name}Tool()
    return tool.run(args)


if __name__ == "__main__":
    sys.exit(main())
'''
        (project_dir / "main.py").write_text(code, encoding='utf-8')

    def _create_config_files(self, project_type: str, project_dir: Path, name: str):
        """创建配置文件"""
        var_name = name.replace("-", "_")

        # requirements.txt
        requirements = []
        if project_type == "skill":
            requirements = [
                "# 项目依赖",
                "# 在下面添加你的依赖",
                "# requests>=2.31.0",
            ]
        elif project_type == "app":
            requirements = [
                "# 项目依赖",
                "# flask>=3.0.0",
                "# flask-cors>=4.0.0",
            ]
        elif project_type == "tool":
            requirements = [
                "# 工具依赖",
                "# 在下面添加你的依赖",
            ]

        (project_dir / "requirements.txt").write_text("\n".join(requirements), encoding='utf-8')

        # .gitignore
        gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/*.log
*.log

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
"""
        (project_dir / ".gitignore").write_text(gitignore, encoding='utf-8')

    def _create_readme(self, project_type: str, project_dir: Path,
                       name: str, description: str, author: str):
        """创建 README.md"""
        var_name = name.replace("-", "_")

        type_names = {
            "skill": "技能",
            "app": "应用",
            "tool": "工具"
        }

        readme = f"""# {name.replace('-', ' ').title()} {type_names[project_type]}

{description}

## 功能特点

- ✅ 功能1（待实现）
- ✅ 功能2（待实现）
- ✅ 功能3（待实现）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### {'技能' if project_type == 'skill' else '应用' if project_type == 'app' else '工具'}使用

```python
from {var_name}_{"skill" if project_type == "skill" else ""} import {self._to_pascal_case(name)}{"Skill" if project_type == "skill" else "App" if project_type == "app" else "Tool"}

# 创建实例
instance = {self._to_pascal_case(name)}{"Skill" if project_type == "skill" else "App" if project_type == "app" else "Tool"}()

# 运行
result = instance.run()
print(result)
```

### 命令行使用

```bash
# 运行项目
python start_{name}.py

# 运行测试
python -m pytest tests/
```

## 项目结构

```
{name}/
├── {var_name}_{"skill.py" if project_type == "skill" else "main.py"}  # 主程序
├── requirements.txt      # 依赖清单
├── start_{name}.py       # 启动脚本
├── tests/                # 测试目录
│   └── test_{var_name}.py
├── logs/                 # 日志目录
├── docs/                 # 文档目录（skill/app）
└── README.md             # 项目说明
```

## 开发信息

- **作者**: {author}
- **版本**: 1.0.0
- **创建日期**: {datetime.now().strftime("%Y-%m-%d")}
- **Python 版本**: 3.7+

## 测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行测试并显示覆盖率
python -m pytest tests/ --cov=.

# 查看测试报告
python -m pytest tests/ --html=report.html
```

## 许可证

MIT License

---

**注意**: 这是一个模板项目，请根据实际需求修改代码。
"""

        (project_dir / "README.md").write_text(readme, encoding='utf-8')

    def _create_tests(self, project_type: str, project_dir: Path, name: str):
        """创建测试文件"""
        var_name = name.replace("-", "_")
        class_name = self._to_pascal_case(name)

        if project_type == "skill":
            import_name = f"{var_name}_skill"
            class_import = f"{class_name}Skill"
        elif project_type == "app":
            import_name = "main"
            class_import = f"{class_name}App"
        else:  # tool
            import_name = "main"
            class_import = f"{class_name}Tool"

        test_code = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name} 测试
"""

import unittest
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from {import_name} import {class_import}


class Test{class_name}(unittest.TestCase):
    """{class_name} 测试类"""

    def setUp(self):
        """测试前准备"""
        self.instance = {class_import}()

    def tearDown(self):
        """测试后清理"""
        pass

    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.instance)
        self.assertEqual(self.instance.name, "{name}")

    def test_run(self):
        """测试运行"""
        # TODO: 添加你的测试逻辑
        result = self.instance.run()
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
'''
        (project_dir / "tests" / f"test_{var_name}.py").write_text(test_code, encoding='utf-8')

    def _create_start_script(self, project_type: str, project_dir: Path, name: str):
        """创建启动脚本"""
        var_name = name.replace("-", "_")
        module_name = var_name + "_skill" if project_type == "skill" else "main"

        # Python 启动脚本
        start_py = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name} 启动脚本
"""

import sys
from pathlib import Path

# 添加项目目录到路径
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

if __name__ == "__main__":
    from {module_name} import main
    sys.exit(main())
'''
        (project_dir / f"start_{name}.py").write_text(start_py, encoding='utf-8')

        # Batch 启动脚本（Windows）
        start_bat = f'''@echo off
REM {name} 启动脚本
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo =========================================================
echo   {name} 启动脚本
echo =========================================================
echo.

set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或不在 PATH 中
    pause
    exit /b 1
)
echo [OK] Python 已安装

REM 安装依赖
echo [信息] 检查依赖...
pip install -q -r requirements.txt 2>nul
echo [OK] 依赖检查完成

REM 启动信息
echo.
echo =========================================================
echo [启动] {name}
echo   停止服务: Ctrl+C
echo =========================================================
echo.

REM 启动应用
python start_{name}.py

pause
'''
        (project_dir / f"start_{name}.bat").write_text(start_bat, encoding='utf-8')

    def _to_pascal_case(self, name: str) -> str:
        """转换为 PascalCase

        Args:
            name: 项目名称（小写+连字符）

        Returns:
            str: PascalCase 格式的类名
        """
        parts = name.split("-")
        return "".join(p.capitalize() for p in parts)

    def list_projects(self):
        """列出所有现有项目"""
        print("\n" + "="*60)
        print("现有项目列表")
        print("="*60 + "\n")

        for project_type in ["skills", "apps", "tools"]:
            type_dir = self.projects_dir / project_type
            if type_dir.exists():
                projects = [d.name for d in type_dir.iterdir() if d.is_dir()]
                if projects:
                    print(f"[DIR] {project_type.upper()}:")
                    for p in sorted(projects):
                        print(f"   - {p}")
                    print()

        print("="*60 + "\n")


def interactive_mode():
    """交互式模式"""
    print("\n" + "="*60)
    print("  AI-Agent-Local 项目生成器")
    print("="*60 + "\n")

    generator = ProjectGenerator()

    # 选择项目类型
    print("请选择项目类型:")
    print("  1. skill  - 技能类项目（可复用的功能模块）")
    print("  2. app    - 应用类项目（完整的业务应用）")
    print("  3. tool   - 工具类项目（独立的小工具）")
    print("  4. list   - 列出现有项目")
    print("  5. quit   - 退出")
    print()

    choice = input("请选择 (1-5): ").strip()

    if choice == "1":
        return create_project_interactive(generator, "skill")
    elif choice == "2":
        return create_project_interactive(generator, "app")
    elif choice == "3":
        return create_project_interactive(generator, "tool")
    elif choice == "4":
        generator.list_projects()
        return
    elif choice == "5":
        print("再见！")
        return
    else:
        print("无效的选择")
        return


def create_project_interactive(generator: ProjectGenerator, project_type: str):
    """交互式创建项目

    Args:
        generator: 项目生成器
        project_type: 项目类型
    """
    print(f"\n创建 {project_type.upper()} 项目")
    print("-" * 40)

    # 项目名称
    while True:
        name = input("项目名称（英文小写+连字符，如 my-skill）: ").strip()
        if not name:
            print("❌ 项目名称不能为空")
            continue
        if not all(c.isalnum() or c in "-_" for c in name):
            print("❌ 项目名称只能包含字母、数字、连字符和下划线")
            continue
        if name.startswith("-") or name.endswith("-"):
            print("❌ 项目名称不能以连字符开头或结尾")
            continue
        break

    # 项目描述
    description = input("项目描述: ").strip() or f"{name} - {project_type} project"

    # 作者名称
    author = input("作者名称（默认: AI-Agent-Local）: ").strip() or "AI-Agent-Local"

    # 确认创建
    print(f"\n即将创建 {project_type.upper()} 项目:")
    print(f"  名称: {name}")
    print(f"  描述: {description}")
    print(f"  作者: {author}")
    print()

    confirm = input("确认创建？(yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("已取消")
        return

    # 创建项目
    if project_type == "skill":
        result = generator.create_skill(name, description, author)
    elif project_type == "app":
        result = generator.create_app(name, description, author)
    elif project_type == "tool":
        result = generator.create_tool(name, description, author)
    else:
        print(f"❌ 未知的项目类型: {project_type}")
        return

    if result.get("success"):
        print(f"\n✅ 项目创建成功！")
        print(f"   位置: {result['project_dir']}")
    else:
        print(f"\n❌ 项目创建失败: {result.get('error')}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI-Agent-Local 项目生成器",
        epilog="""
示例:
  %(prog)s                    # 交互式模式
  %(prog)s --type skill --name my-skill
  %(prog)s --type app --name my-app --description "My App"
        """
    )

    parser.add_argument("--type", choices=["skill", "app", "tool"],
                       help="项目类型")
    parser.add_argument("--name", help="项目名称（英文小写+连字符）")
    parser.add_argument("--description", help="项目描述")
    parser.add_argument("--author", default="AI-Agent-Local",
                       help="作者名称")
    parser.add_argument("--list", action="store_true",
                       help="列出现有项目")

    args = parser.parse_args()

    generator = ProjectGenerator()

    # 列出项目
    if args.list:
        generator.list_projects()
        return

    # 命令行模式
    if args.type and args.name:
        if args.type == "skill":
            generator.create_skill(args.name, args.description or "", args.author)
        elif args.type == "app":
            generator.create_app(args.name, args.description or "", args.author)
        elif args.type == "tool":
            generator.create_tool(args.name, args.description or "", args.author)
        return

    # 交互式模式
    interactive_mode()


if __name__ == "__main__":
    main()
