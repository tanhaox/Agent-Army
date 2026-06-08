#!/usr/bin/env python3
"""
test_router.py - 统一流程路由器测试

测试意图识别和各处理器的功能。
不修改任何数据，仅验证路由正确性。
"""

import sys
import json

sys.path.insert(0, '/root/.openclaw/workspace')

from agent_army.unified_router import UnifiedRouter


def test_intent_recognition(router: UnifiedRouter):
    """测试意图识别"""
    print("=" * 60)
    print("  意图识别测试")
    print("=" * 60)

    test_cases = [
        # (输入, 期望意图)
        ("分析600887", "analyze"),
        ("600887怎么样", "analyze"),
        ("伊利股份走势如何", "analyze"),
        ("我的持仓", "holdings"),
        ("当前持仓情况", "holdings"),
        ("总资产", "assets"),
        ("账户概览", "assets"),
        ("今日机会", "opportunities"),
        ("扫描好股", "opportunities"),
        ("清仓600887", "clear"),
        ("止损清仓000651", "clear"),
        ("清仓格力电器", "clear"),
        ("关注600887", "add_watch"),
        ("加入关注000651", "add_watch"),
        ("关注池", "watchlist"),
        ("我的关注列表", "watchlist"),
        ("预测准确率", "predict"),
        ("历史操作记录", "history"),
        ("帮助", "help"),
        ("help", "help"),
        ("600728", "analyze"),  # 纯代码默认分析
        ("减仓600887", "reduce"),
    ]

    passed = 0
    failed = 0
    for text, expected in test_cases:
        intent, params = router._parse_intent(text)
        ok = intent == expected
        symbol = "OK" if ok else "FAIL"
        if not ok:
            print(f"  {symbol} '{text}' -> {intent} (期望 {expected})")
            failed += 1
        else:
            passed += 1

    print(f"\n  意图识别: {passed}/{passed + failed} 通过")
    return failed == 0


def test_handlers(router: UnifiedRouter):
    """测试各处理器（只读操作，不修改数据）"""
    print("\n" + "=" * 60)
    print("  处理器功能测试")
    print("=" * 60)

    tests = [
        ("holdings", "我的持仓", {}),
        ("assets", "总资产", {}),
        ("watchlist", "关注池", {}),
        ("predict", "预测准确率", {}),
        ("help", "帮助", {}),
    ]

    results = {}
    for name, query, extra in tests:
        print(f"\n  --- {name}: '{query}' ---")
        try:
            response = router.route(query)
            status = response.get('status', 'unknown')
            message = response.get('message', '')[:100]
            data_keys = list(response.get('data', {}).keys())[:5]
            print(f"  状态: {status}")
            print(f"  消息: {message}")
            print(f"  数据键: {data_keys}")
            results[name] = status == 'ok'
        except Exception as e:
            print(f"  异常: {e}")
            results[name] = False

    return results


def test_analyze(router: UnifiedRouter):
    """测试分析功能（可能较慢）"""
    print("\n" + "=" * 60)
    print("  分析功能测试")
    print("=" * 60)

    # 先测意图识别
    intent, params = router._parse_intent("分析600887")
    print(f"  意图: {intent}, 参数: {params}")

    if intent != 'analyze':
        print(f"  SKIP: 意图识别失败")
        return False

    try:
        response = router.route("分析600887")
        status = response.get('status', 'unknown')
        message = response.get('message', '')[:100]
        data = response.get('data', {})

        print(f"  状态: {status}")
        print(f"  消息: {message}")
        if data:
            print(f"  数据键: {list(data.keys())[:8]}")
            if 'error' in data:
                print(f"  错误: {data['error'][:100]}")

        return status == 'ok'
    except Exception as e:
        print(f"  异常: {e}")
        return False


def test_opportunities(router: UnifiedRouter):
    """测试机会扫描"""
    print("\n" + "=" * 60)
    print("  机会扫描测试")
    print("=" * 60)

    try:
        response = router.route("今日机会")
        status = response.get('status', 'unknown')
        message = response.get('message', '')[:100]
        data = response.get('data', {})

        print(f"  状态: {status}")
        print(f"  消息: {message}")

        if 'opportunities' in data:
            opps = data['opportunities']
            print(f"  机会数: {len(opps)}")
            for opp in opps[:3]:
                print(f"    {opp.get('name', '')}({opp.get('code', '')}): {opp.get('score', 0)}分")
        elif 'raw_output' in data:
            print(f"  原始输出: {data['raw_output'][:100]}")

        return status == 'ok'
    except Exception as e:
        print(f"  异常: {e}")
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("  统一流程路由器 - 完整测试")
    print("=" * 60)

    router = UnifiedRouter()

    # 1. 意图识别
    intent_ok = test_intent_recognition(router)

    # 2. 处理器功能
    handler_results = test_handlers(router)

    # 3. 分析功能
    analyze_ok = test_analyze(router)

    # 4. 机会扫描
    opp_ok = test_opportunities(router)

    # 汇总
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)

    all_results = {
        '意图识别': intent_ok,
        '分析功能': analyze_ok,
        '机会扫描': opp_ok,
        **handler_results,
    }

    total_pass = sum(1 for v in all_results.values() if v)
    total = len(all_results)

    for name, ok in all_results.items():
        symbol = "PASS" if ok else "FAIL"
        print(f"  {symbol} {name}")

    print(f"\n  总计: {total_pass}/{total}")
    print("=" * 60)
