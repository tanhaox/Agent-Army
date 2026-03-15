"""
测试多个政府网站是否有JSON接口
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests


def test_json_interface():
    """测试政府网站的JSON接口"""

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
    }

    # 测试列表
    test_cases = [
        {
            "name": "中国政府网-最新政策",
            "url": "https://www.gov.cn/zhengce/zuixin/ZUIXINZHENGCE.json",
            "base": "https://www.gov.cn/zhengce/zuixin/"
        },
        {
            "name": "中国政府网-政策文件库",
            "url": "https://www.gov.cn/zhengce/zhengceku/ZHENGCEKU.json",
            "base": "https://www.gov.cn/zhengce/zhengceku/"
        },
        {
            "name": "发改委-政策发布",
            "url": "https://www.ndrc.gov.cn/xxgk/zcfb/zcfb_list.json",
            "base": "https://www.ndrc.gov.cn/xxgk/zcfb/"
        },
        {
            "name": "央行-政策公告",
            "url": "https://www.pbc.gov.cn/zhengwugongkai/135933/135944/list.json",
            "base": "https://www.pbc.gov.cn/zhengwugongkai/135933/index.html"
        },
        {
            "name": "证监会-政策公告",
            "url": "https://www.csrc.gov.cn/csrc/c101928/c101929/list.json",
            "base": "https://www.csrc.gov.cn/csrc/c101928/c101929/list.shtml"
        },
    ]

    print("\n" + "="*80)
    print("政府网站JSON接口测试")
    print("="*80 + "\n")

    results = []

    for test in test_cases:
        print(f"测试: {test['name']}")
        print(f"JSON URL: {test['url']}")
        print(f"列表页: {test['base']}")

        try:
            response = requests.get(test['url'], headers=headers, timeout=10)

            if response.status_code == 200:
                try:
                    data = response.json()
                    count = len(data) if isinstance(data, list) else len(data.get('data', []))
                    print(f"✅ 成功! 获取 {count} 条数据")
                    results.append({
                        "name": test['name'],
                        "status": "成功",
                        "count": count,
                        "url": test['url']
                    })
                except:
                    # 可能是HTML页面
                    content_type = response.headers.get('Content-Type', '')
                    print(f"❌ 不是JSON (返回: {content_type})")
                    results.append({
                        "name": test['name'],
                        "status": "不是JSON",
                        "count": 0,
                        "url": test['url']
                    })
            else:
                print(f"❌ HTTP {response.status_code}")
                results.append({
                    "name": test['name'],
                    "status": f"HTTP {response.status_code}",
                    "count": 0,
                    "url": test['url']
                })

        except requests.exceptions.Timeout:
            print(f"❌ 超时")
            results.append({
                "name": test['name'],
                "status": "超时",
                "count": 0,
                "url": test['url']
            })
        except Exception as e:
            print(f"❌ 错误: {str(e)[:50]}")
            results.append({
                "name": test['name'],
                "status": "错误",
                "count": 0,
                "url": test['url']
            })

        print()

    # 汇总结果
    print("="*80)
    print("测试结果汇总")
    print("="*80 + "\n")

    success_count = 0
    for r in results:
        status_icon = "✅" if r['status'] == "成功" else "❌"
        print(f"{status_icon} {r['name']}")
        print(f"   状态: {r['status']}")
        if r['count'] > 0:
            print(f"   数量: {r['count']} 条")
        print(f"   URL: {r['url']}")
        print()

        if r['status'] == "成功":
            success_count += 1

    print("="*80)
    print(f"总计: {success_count}/{len(results)} 个网站有JSON接口")
    print("="*80 + "\n")


if __name__ == '__main__':
    test_json_interface()
