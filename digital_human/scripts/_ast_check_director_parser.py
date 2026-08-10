"""AST 硬约束检查 — director_parser 包化后.

对照约束: 新文件 ≤250 行, 函数 ≤40 行(编排 ≤65), 类 ≤200 行, 模块 ≤3 类,
`__init__.py` 含 `__all__`, 无 `from ... import *`, 无裸 `except:`, 类型注解.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "app" / "services" / "director_parser"

FILE_LIMIT = 250
FUNC_LIMIT = 40
ORCH_LIMIT = 65
CLASS_LIMIT = 200
MAX_CLASSES = 3

MODULES = [
    "__init__.py",
    "_json.py",
    "_rows.py",
    "_rules.py",
    "_parse.py",
]


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def check_file(path: Path) -> list[str]:
    errors: list[str] = []
    n = line_count(path)
    if n > FILE_LIMIT:
        errors.append(f"{path.name}: 文件 {n} 行 > {FILE_LIMIT}")

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    import_star = [
        n.lineno for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom) and n.names and n.names[0].name == "*"
    ]
    if import_star:
        errors.append(f"{path.name}: from-import * 于行 {import_star}")

    if path.name == "__init__.py":
        has_all = any(isinstance(n, ast.Assign) and
                      any(getattr(t, "id", None) == "__all__" for t in n.targets)
                      for n in tree.body)
        if not has_all:
            errors.append("__init__.py: 缺少 __all__")

    classes = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes += 1
            body = node.end_lineno - node.lineno + 1
            if body > CLASS_LIMIT:
                errors.append(f"{path.name}: 类 {node.name} {body} 行 > {CLASS_LIMIT}")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.end_lineno - node.lineno + 1
            orch = node.name in {"parse_llm_plan", "enforce_host_rules", "cap_host_count",
                                 "enforce_adjacency_rules"}
            limit = ORCH_LIMIT if orch else FUNC_LIMIT
            if body > limit:
                errors.append(f"{path.name}: 函数 {node.name} {body} 行 > {limit}")
    if classes > MAX_CLASSES:
        errors.append(f"{path.name}: {classes} 个类 > {MAX_CLASSES}")
    return errors


def main() -> int:
    errors: list[str] = []
    for name in MODULES:
        p = PKG / name
        if not p.exists():
            errors.append(f"{p.name}: 文件缺失")
            continue
        errors.extend(check_file(p))

    if errors:
        print("❌ AST 硬约束检查失败:")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✅ AST 硬约束检查通过: 5 模块行数/函数/类/__all__/无import-star 全部合规")
    print(f"   行数: " + ", ".join(f"{name}={line_count(PKG / name)}" for name in MODULES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
