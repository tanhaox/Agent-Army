"""gpu_service_manager 包 AST 硬约束检查 (迁移自诊断脚本)."""
import ast, pathlib, sys

PKG = pathlib.Path("app/services/gpu_service_manager")
files = sorted(PKG.glob("*.py"))

def phys_lines(node):
    return max(stmt.end_lineno for stmt in ast.walk(node) if isinstance(stmt, ast.stmt)) - node.lineno + 1

problems = []
for path in files:
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    n_lines = len(src.splitlines())
    if n_lines > 250:
        problems.append(f"{path}: {n_lines} > 250 OVER")
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            n = phys_lines(node)
            if n > 40:
                problems.append(f"{path}: {node.name} {n} > 40 OVER")
        elif isinstance(node, ast.ClassDef):
            n = phys_lines(node)
            if n > 200:
                problems.append(f"{path}: {node.name} {n} > 200 OVER")
    # 模块级类数 (纯数据 dataclass 除外)
    def _is_dataclass(n):
        for d in n.decorator_list:
            if isinstance(d, ast.Name) and d.id == "dataclass":
                return True
            if isinstance(d, ast.Attribute) and d.attr == "dataclass":
                return True
        return False

    cls = [n for n in tree.body if isinstance(n, ast.ClassDef) and not _is_dataclass(n)]
    if len(cls) > 3:
        problems.append(f"{path}: {len(cls)} classes > 3 OVER")

for path in files:
    print(f"  {'✓' if path not in [p.split(':')[0] for p in problems] else '✗'} {path} ({len(path.read_text(encoding='utf-8').splitlines())} 行)")

for p in problems:
    print(f"  ✗ {p}")
if problems:
    print(f"\nFAIL: {len(problems)} 问题")
    sys.exit(1)
print("\nAST 0 问题 — 全部 OK")
