#!/usr/bin/env python3
"""
cli.py - OpenClaw Agent 命令行接口

作为 OpenClaw 工具调用的统一入口点。
接收用户自然语言，通过 UnifiedRouter 处理，返回 JSON。

用法：
  # 命令行
  python3 agent_army/cli.py 分析 600887
  python3 agent_army/cli.py 我的持仓

  # 管道输入
  echo "分析伊利股份" | python3 agent_army/cli.py

  # OpenClaw 工具调用
  python3 agent_army/cli.py --json "今日机会"

作者：AI Agent
日期：2026-04-16
"""

import sys
import os
import json

sys.path.insert(0, '/root/.openclaw/workspace')


def main():
    # 解析参数
    force_json = '--json' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--json']

    if args:
        user_input = ' '.join(args)
    elif not sys.stdin.isatty():
        user_input = sys.stdin.read().strip()
    else:
        user_input = '帮助'

    if not user_input:
        user_input = '帮助'

    # 路由处理
    from agent_army.unified_router import get_unified_router
    router = get_unified_router()
    response = router.route(user_input)

    # 输出
    if force_json or not sys.stdout.isatty():
        print(json.dumps(response, ensure_ascii=False, indent=2, default=str))
    else:
        # 人类可读格式
        status = response.get('status', 'unknown').upper()
        intent = response.get('intent', '')
        message = response.get('message', '')

        print(f"[{status}] {intent}")
        if message:
            print(message)
        if response.get('detail'):
            print(response['detail'])

        # 纪律因子输出
        data = response.get('data', {})
        discipline = data.get('discipline')
        if discipline:
            print("\n--- 持仓健康度 ---")
            for code, disc in discipline.items():
                name = disc.get('name', code)
                score = disc.get('score', 0)
                suggestion = disc.get('suggestion', '')
                stop_loss = disc.get('stop_loss_price')
                stop_triggered = disc.get('stop_triggered', False)
                factors = disc.get('factors', {})

                alert_mark = " ***" if suggestion in ('止损', '减仓') else ""
                trigger_mark = " [止损触发!]" if stop_triggered else ""
                print(f"  {code}: {score}/100 -> {suggestion}{trigger_mark}{alert_mark}")
                if factors:
                    factor_str = ' | '.join(
                        f"{k}:{v:.0f}" for k, v in factors.items()
                    )
                    print(f"    因子: {factor_str}")
                if stop_loss:
                    print(f"    止损价: {stop_loss}")

        # 分析结果中的纪律因子
        if intent == 'analyze' and data.get('discipline'):
            disc = data['discipline']
            print(f"\n--- 纪律因子 ---")
            print(f"  健康度: {disc.get('score', 'N/A')}/100")
            print(f"  建议: {disc.get('suggestion', 'N/A')}")
            print(f"  止损价: {disc.get('stop_loss_price', 'N/A')}")
            if disc.get('stop_loss_triggered'):
                print(f"  >>> 止损触发!")
            wp = data.get('weekly_percentile')
            if wp:
                print(f"  周线分位: {wp.get('position_pct', 'N/A')}% "
                      f"(范围 {wp.get('range_low')}-{wp.get('range_high')}, "
                      f"{wp.get('weekly_bars', '?')}周)")
            override = data.get('discipline_override', {})
            if override.get('overridden'):
                print(f"  原始建议 {override['original_recommendation']} -> {override['final_recommendation']}")
            factors = disc.get('factors', {})
            if factors:
                for name, f in factors.items():
                    print(f"    {name}: {f['score']:.0f} ({str(f.get('detail', ''))[:60]})")

        # 预警信息
        alerts = response.get('data', {}).get('alerts', [])
        if alerts:
            print("\n--- 持仓预警 ---")
            for a in alerts:
                print(f"  {a}")

        if response.get('suggestions'):
            for s in response['suggestions']:
                print(f"  -> {s}")


if __name__ == '__main__':
    main()
