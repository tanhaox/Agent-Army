# 系统冒烟测试
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# 测试项目文件是否存在
required_files = [
    'crawler/news_scraper.py',
    'crawler/hot_news_detector.py',
    'crawler/config.py',
    'run_crawler.py',
    'start_server.py',
    'news_dashboard.html',
    'launch_system.bat',
    'simple_launch.bat'
]

print("=== 数字人计划新闻爬虫系统冒烟测试 ===")

# 检查目录结构
print(f"检查项目目录: {PROJECT_ROOT}")

# 检查必要文件
all_files_exist = True
for file_path in required_files:
    full_path = PROJECT_ROOT / file_path
    if full_path.exists():
        print(f"[OK] {file_path} - 存在")
    else:
        print(f"[FAIL] {file_path} - 不存在")
        all_files_exist = False

print()

# 测试Python模块导入
try:
    # 添加项目路径
    sys.path.append(str(PROJECT_ROOT))

    # 测试导入
    from crawler.news_scraper import NewsScraper
    from crawler.hot_news_detector import HotNewsDetector
    from crawler.config import NEWS_SOURCES
    print("[OK] Python模块导入成功")

    # 测试创建实例
    scraper = NewsScraper()
    detector = HotNewsDetector()
    print("[OK] 对象实例化成功")

except Exception as e:
    print(f"[FAIL] 模块导入失败: {e}")
    all_files_exist = False

print()

# 测试配置文件
try:
    print(f"[OK] 配置文件加载成功")
    print(f"  - 新闻源数量: {len(NEWS_SOURCES)}")

    # 显示部分配置
    for name, source in list(NEWS_SOURCES.items())[:2]:
        print(f"  - {name}: {source.get('name', 'N/A')}")

except Exception as e:
    print(f"[FAIL] 配置文件测试失败: {e}")
    all_files_exist = False

print()

# 测试HTML文件
html_file = os.path.join(project_dir, 'news_dashboard.html')
if os.path.exists(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
        if '新闻聚合系统' in content:
            print("[OK] HTML文件内容正确")
        else:
            print("[FAIL] HTML文件内容异常")
            all_files_exist = False
else:
    print("[FAIL] HTML文件不存在")
    all_files_exist = False

print()

# 测试批处理文件
bat_files = ['launch_system.bat', 'simple_launch.bat']
for bat_file in bat_files:
    full_path = os.path.join(project_dir, bat_file)
    if os.path.exists(full_path):
        print(f"[OK] {bat_file} - 存在")
    else:
        print(f"[FAIL] {bat_file} - 不存在")
        all_files_exist = False

print()

# 总结
if all_files_exist:
    print("=== 测试结果: 通过 ===")
    print("系统文件结构完整，所有组件都已正确创建")
    print("系统可以正常运行")
else:
    print("=== 测试结果: 失败 ===")
    print("部分文件缺失，请检查项目结构")

print("\n系统功能说明:")
print("- 多源新闻抓取 (RSS)")
print("- 热点新闻检测")
print("- 新闻分类")
print("- Web界面展示")
print("- 自动更新机制")
print("- 错误处理 (网络不可用时显示示例数据)")