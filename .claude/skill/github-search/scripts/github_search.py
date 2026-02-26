#!/usr/bin/env python3
"""
GitHub 项目搜索工具
使用 GitHub API 搜索项目，按优先级排序
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# Windows 控制台编码修复
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# 配置
GITHUB_API_URL = "https://api.github.com/search/repositories"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')  # 可选，提高 API 速率限制
PER_PAGE = 3  # 返回结果数量

# 本地 AI 配置
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen:1.8b')


def is_chinese(text):
    """检查文本是否包含中文字符"""
    return any('\u4e00' <= char <= '\u9fff' for char in text)


def translate_to_english(text):
    """
    使用本地 Ollama 将中文关键词翻译成英文

    Args:
        text: 中文关键词

    Returns:
        翻译后的英文关键词
    """
    prompt = f"""将以下中文技术关键词翻译成英文关键词，用于在 GitHub 上搜索相关项目。
要求：只返回英文关键词，用空格分隔，不要任何其他文字。

示例：
- PDF提取 → PDF extract
- 视频字幕 → video subtitle
- 爬虫框架 → web scraping framework
- 数据可视化 → data visualization

中文关键词：{text}

英文关键词："""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            translated = result.get('response', '').strip()
            # 清理可能的换行和多余字符
            translated = translated.split('\n')[0].strip()
            return translated if translated else text
        else:
            return text  # 翻译失败返回原文

    except Exception:
        return text  # 出错返回原文


def search_github(query, language=None, limit=3):
    """
    搜索 GitHub 仓库

    Args:
        query: 搜索关键词
        language: 编程语言（可选）
        limit: 返回结果数量

    Returns:
        推荐项目列表，按匹配度排序
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # 如果是中文，先翻译成英文
    original_query = query
    if is_chinese(query):
        print(f"🔄 检测到中文关键词，正在翻译...")
        query = translate_to_english(query)
        if query != original_query:
            print(f"✅ 翻译完成：{original_query} → {query}")
        else:
            print(f"⚠️  翻译失败，使用原关键词")

    # 构建搜索查询
    search_query = query
    if language:
        search_query += f" language:{language}"

    # 添加质量过滤：按 stars 排序
    search_query += " stars:>100"

    params = {
        "q": search_query,
        "sort": "stars",
        "order": "desc",
        "per_page": limit
    }

    try:
        response = requests.get(GITHUB_API_URL, headers=headers, params=params, timeout=10)

        if response.status_code == 403:
            # API 速率限制
            reset_time = response.headers.get('X-RateLimit-Reset', 0)
            reset_time = datetime.fromtimestamp(int(reset_time))
            return {
                "error": "API 速率限制已用完",
                "reset_time": reset_time.strftime("%Y-%m-%d %H:%M:%S"),
                "suggestion": "请配置 GITHUB_TOKEN 环境变量提高速率限制"
            }

        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
            return {"projects": []}

        # 评估项目质量和匹配度
        projects = []
        for item in data["items"]:
            project = evaluate_project(item, query)
            projects.append(project)

        # 按匹配度排序
        projects.sort(key=lambda x: x["match_score"], reverse=True)

        return {"projects": projects[:limit]}

    except requests.exceptions.Timeout:
        return {"error": "GitHub API 请求超时，请检查网络连接"}
    except requests.exceptions.RequestException as e:
        return {"error": f"GitHub API 请求失败: {str(e)}"}


def evaluate_project(item, query):
    """
    评估项目质量和匹配度

    Args:
        item: GitHub API 返回的项目信息
        query: 用户搜索关键词

    Returns:
        包含评分的项目信息
    """
    # 基础信息
    stars = item.get("stargazers_count", 0)
    forks = item.get("forks_count", 0)
    updated_at = item.get("updated_at", "")
    name = item.get("name", "")
    description = item.get("description", "无描述")
    language = item.get("language", "未知")
    url = item.get("html_url", "")
    license_data = item.get("license")
    license_info = license_data.get("name", "未知") if license_data else "未知"

    # 计算匹配度评分（0-100）
    match_score = 0
    match_reason = []

    # 1. Star 数评分（最高 40 分）
    if stars > 1000:
        match_score += 40
        match_reason.append("高热度 (⭐>1k)")
    elif stars > 500:
        match_score += 30
        match_reason.append("中高热度 (⭐>500)")
    elif stars > 100:
        match_score += 20
        match_reason.append("稳定项目 (⭐>100)")

    # 2. 活跃度评分（最高 30 分）
    if updated_at:
        try:
            update_date = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            days_since_update = (datetime.now(update_date.tzinfo) - update_date).days

            if days_since_update < 30:
                match_score += 30
                match_reason.append("最近活跃")
            elif days_since_update < 90:
                match_score += 20
                match_reason.append("近期有更新")
            elif days_since_update < 180:
                match_score += 10
                match_reason.append("半年内有更新")
        except:
            pass

    # 3. Fork 数评分（最高 10 分）
    if forks > 100:
        match_score += 10
        match_reason.append("活跃社区")
    elif forks > 50:
        match_score += 5

    # 4. 描述匹配度评分（最高 20 分）
    if description:
        query_lower = query.lower()
        desc_lower = description.lower()
        name_lower = name.lower()

        # 标题完全匹配
        if query_lower in name_lower:
            match_score += 20
            match_reason.append("标题精确匹配")
        # 描述完全匹配
        elif query_lower in desc_lower:
            match_score += 15
            match_reason.append("描述匹配")

    # 5. 许可证评分（最高 10 分）
    loose_licenses = ["mit", "apache-2.0", "bsd-3-clause", "unlicense"]
    if license_info.lower() in loose_licenses:
        match_score += 10
        match_reason.append("宽松许可证")

    return {
        "name": name,
        "url": url,
        "description": description[:100] + "..." if len(description) > 100 else description,
        "stars": stars,
        "forks": forks,
        "language": language,
        "license": license_info,
        "updated_at": updated_at[:10] if updated_at else "未知",
        "match_score": match_score,
        "match_reason": " | ".join(match_reason),
        "match_level": "完全匹配" if match_score > 70 else "相近匹配" if match_score > 40 else "一般匹配"
    }


def display_results(projects):
    """
    格式化展示搜索结果
    """
    if "error" in projects:
        print(f"❌ {projects['error']}")
        if "reset_time" in projects:
            print(f"⏰ 速率限制将在 {projects['reset_time']} 重置")
        if "suggestion" in projects:
            print(f"💡 建议: {projects['suggestion']}")
        return False

    if not projects.get("projects"):
        print("❌ 未找到匹配的项目")
        print("💡 建议：尝试更换关键词或使用中英文组合搜索")
        return False

    print("\n🔥 GitHub 项目推荐（按匹配度排序）")
    print("=" * 80)

    for i, p in enumerate(projects["projects"], 1):
        print(f"\n### [{p['match_level']}] {i}. {p['name']}")
        print(f"🔗 {p['url']}")
        print(f"⭐ Star: {p['stars']} | 📅 最后更新: {p['updated_at']} | 💻 语言: {p['language']}")
        print(f"📝 描述: {p['description']}")
        print(f"✨ 匹配度: {p['match_score']}/100 | 匹配理由: {p['match_reason']}")

    print("\n" + "=" * 80)
    return True


def main():
    import argparse

    parser = argparse.ArgumentParser(description='GitHub 项目搜索工具')
    parser.add_argument('query', help='搜索关键词')
    parser.add_argument('--language', '-l', help='编程语言过滤 (如 python, javascript)')
    parser.add_argument('--limit', '-n', type=int, default=3, help='返回结果数量')

    args = parser.parse_args()

    print(f"\n🔍 正在搜索 GitHub: {args.query}")
    result = search_github(args.query, args.language, args.limit)

    if display_results(result):
        print(f"\n请选择项目序号 [1-{args.limit}/0] (0=跳过，进入 AI 编程模式):")


if __name__ == "__main__":
    main()
