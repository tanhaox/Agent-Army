"""AST 硬约束检查 — director_service 包.

对每个模块: 文件 ≤250 行; 函数 ≤40 行 (--orch 名单内的编排函数 ≤70);
类 ≤200 行; 模块 ≤3 个类; 无 `from xxx import *`; __init__.py 含 __all__。

用法: .venv/Scripts/python.exe scripts/_ast_check_director_service.py
      --orch create_director_plan replace_failed_slot _align_fast_or_whisper ...
      (声明编排函数, 上限放宽到 70)
"""
import argparse
import ast
import pathlib
import sys

PKG = pathlib.Path("app/services/director_service")
MAX_FILE = 250
MAX_FUNC = 40
MAX_ORCH = 70
MAX_CLASS = 200
MAX_CLASSES = 3


def module_level_funcs(tree: ast.Module) -> list[ast.FunctionDef]:
    """模块级函数 = 直接挂 body 下的 def (不含类内方法/嵌套函数)."""
    funcs = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            funcs.append(node)
    return funcs


def physical_lines(node: ast.AST) -> int:
    """函数物理行 = 函数体内所有语句最大 end_lineno - 起始 + 1."""
    body_stmts = [s for s in ast.walk(node) if isinstance(s, ast.stmt)]
    max_end = max(s.end_lineno for s in body_stmts) if body_stmts else node.lineno
    return max_end - node.lineno + 1


def check_file(f: pathlib.Path, orch_names: set[str]) -> list[tuple[str, str, int, bool]]:
    """返回 [(member, size, is_over)], 并输出测量行."""
    src = f.read_text(encoding="utf-8")
    file_len = len(src.splitlines())
    tree = ast.parse(src)
    results: list[tuple[str, str, int, bool]] = [("文件", "", file_len, file_len > MAX_FILE)]

    for cls in [n for n in tree.body if isinstance(n, ast.ClassDef)]:
        size = physical_lines(cls)
        results.append((f"class {cls.name}", "", size, size > MAX_CLASS))
    if sum(1 for n in tree.body if isinstance(n, ast.ClassDef)) > MAX_CLASSES:
        results.append(("模块类数", "", 0, True))

    for fn in module_level_funcs(tree):
        size = physical_lines(fn)
        limit = MAX_ORCH if fn.name in orch_names else MAX_FUNC
        results.append((f"def {fn.name}", "", size, size > limit))

    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names):
            results.append((f"import * L{n.lineno}", "", 0, True))

    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--orch", nargs="*", default=[], help="编排函数名 (上限 70)")
    args = ap.parse_args()
    orch = set(args.orch)

    all_rows: list[tuple[str, str, int, bool]] = []
    errors: list[str] = []
    for f in sorted(PKG.glob("*.py")):
        try:
            rows = check_file(f, orch)
        except SyntaxError as e:
            errors.append(f"[{f.name}] 语法错误: {e}")
            continue
        all_rows.extend((f.name, member, size, over) for member, _, size, over in rows)
        for member, _, size, over in rows:
            if over:
                errors.append(f"[{f.name}] {member} {size} 行超限")

        if f.name == "__init__.py":
            src = f.read_text(encoding="utf-8")
            if "__all__" not in src:
                errors.append("[__init__.py] 缺少 __all__")

    print("== director_service 包测量 ==")
    for name, member, size, over in all_rows:
        print(f"{name:<22} {member:<28} {size:>4}  {'OVER' if over else 'OK'}")
    print(f"\n问题数: {len(errors)}")
    for e in errors:
        print(f"  ✗ {e}")
    if not errors:
        print("  ✓ 全部通过")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
