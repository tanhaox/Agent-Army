"""AST 硬约束检查: comfyui.py(瘦身) + comfyui_service.py.

检查项: 文件 ≤250 行, 函数 ≤40 行(编排 ≤65-70), 类 ≤200 行, 模块 ≤3 类,
`__init__.py` 含 `__all__`, 禁止 `from ... import *`.
用法: .venv/Scripts/python.exe scripts/_ast_check_comfyui.py
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / "app/routers/comfyui.py",
    ROOT / "app/services/comfyui_service.py",
    ROOT / "app/services/comfyui_client.py",
]
FILE_LIMIT = 250
FUNC_LIMIT = 40
ORCH_LIMIT = 70
CLASS_LIMIT = 200
MAX_CLASSES = 3


def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    src = path.read_text(encoding="utf-8")
    lines = src.splitlines()
    if len(lines) > FILE_LIMIT:
        problems.append(f"  {path.name}: {len(lines)} 行 > 上限 {FILE_LIMIT}")
    tree = ast.parse(src)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]
    if len(classes) > MAX_CLASSES:
        problems.append(f"  {path.name}: {len(classes)} 个类 > 上限 {MAX_CLASSES}")

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            body = node.end_lineno - node.lineno + 1
            limit = ORCH_LIMIT if node.name.startswith(("compose", "generate", "parse", "scan", "run")) else FUNC_LIMIT
            if body > limit:
                problems.append(
                    f"  {path.name}:{node.lineno} {node.name}() {body} 行 > 上限 {limit}"
                )
        elif isinstance(node, ast.ClassDef):
            body = node.end_lineno - node.lineno + 1
            if body > CLASS_LIMIT:
                problems.append(
                    f"  {path.name}:{node.lineno} class {node.name} {body} 行 > 上限 {CLASS_LIMIT}"
                )
        elif isinstance(node, ast.ImportFrom) and node.module and node.names and any(
            n.name == "*" for n in node.names
        ):
            problems.append(f"  {path.name}:{node.lineno} 禁止 `from {node.module} import *`")

    if path.name == "__init__.py":
        has_all = any(isinstance(n, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets
        ) for n in tree.body)
        if not has_all:
            problems.append(f"  {path.name}: 缺少 __all__")
    return problems


def main() -> int:
    all_problems: list[str] = []
    for path in FILES:
        if not path.exists():
            all_problems.append(f"  缺失: {path}")
            continue
        all_problems += check_file(path)
    if all_problems:
        print("❌ AST 硬约束违规:")
        print("\n".join(all_problems))
        return 1
    print("✅ AST 硬约束全部通过:")
    for path in FILES:
        print(f"   {path.name}: {len(path.read_text(encoding='utf-8').splitlines())} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
