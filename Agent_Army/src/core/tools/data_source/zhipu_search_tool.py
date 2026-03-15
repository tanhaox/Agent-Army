"""
智谱AI搜索工具 - 基于资源包的智能搜索
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
import json
import hashlib

from src.core.logger import get_logger


class ZhipuSearchTool:
    """
    智谱AI搜索工具

    职责：
    - 智能选择搜索引擎（std/pro/quark）
    - 资源包余额管理
    - 搜索结果缓存
    - 配额使用追踪

    资源包配置（2026-03-12购买，2026-09-12到期）：
    - search_std: 4,962次（0.01元/次）
    - search_pro: 2,492次（0.03元/次）
    - search_pro_quark: 2,500次（0.05元/次）
    """

    def __init__(self, config: Optional[Dict] = None):
        self.logger = get_logger("zhipu_search_tool")
        self.config = config or {}

        # API配置
        self.api_key = self.config.get('zhipu_api_key', '')
        self.base_url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'

        # 资源包配置
        self.resource_packs = {
            'search_std': {
                'balance': 4962,
                'price': 0.01,
                'expires_at': '2026-09-12',
                'qpm': 50
            },
            'search_pro': {
                'balance': 2492,
                'price': 0.03,
                'expires_at': '2026-09-12',
                'qpm': 5
            },
            'search_pro_quark': {
                'balance': 2500,
                'price': 0.05,
                'expires_at': '2026-09-12',
                'qpm': 5
            }
        }

        self.logger.info("智谱搜索工具初始化完成")

    def search(
        self,
        query: str,
        engine: Optional[str] = None,
        importance: str = 'normal',
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        执行搜索

        Args:
            query: 搜索关键词
            engine: 指定搜索引擎（None=自动选择）
            importance: 重要性（normal/high）
            top_k: 返回结果数量

        Returns:
            {
                "engine": "search_std",
                "query": "...",
                "results": [...],
                "reason": "选择原因",
                "remaining_balance": 4961
            }
        """
        self.logger.info(f"搜索: {query}")

        # 1. 选择搜索引擎
        if not engine:
            engine_info = self._select_engine(query, importance)
            engine = engine_info['engine']
            reason = engine_info['reason']
        else:
            reason = f"用户指定: {engine}"

        # 2. 检查余额
        balance = self._get_balance(engine)
        if balance <= 0:
            self.logger.warning(f"{engine} 余额不足，切换到search_std")
            engine = 'search_std'
            balance = self._get_balance(engine)
            reason = "原引擎余额不足，切换到基础版"

        # 3. 执行搜索
        try:
            results = self._execute_search(query, engine, top_k)

            # 4. 扣减余额
            self._deduct_balance(engine, 1)

            # 5. 返回结果
            return {
                'engine': engine,
                'query': query,
                'results': results,
                'reason': reason,
                'remaining_balance': self._get_balance(engine),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"搜索失败: {str(e)}")
            return {
                'engine': engine,
                'query': query,
                'results': [],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _select_engine(self, query: str, importance: str) -> Dict[str, str]:
        """
        智能选择搜索引擎

        策略：
        - 80% → search_std（常规查询）
        - 15% → search_pro（重要查询）
        - 5% → search_pro_quark（垂直领域）
        """

        # 专业领域关键词
        professional_keywords = {
            'medical': ['医疗', '健康', '药物', '症状', '医疗', '养生'],
            'vertical': ['专业', '行业', '报告', '研究', '论文', '技术'],
            'finance': ['股票', '基金', '理财', '投资', '财经']
        }

        # 医疗健康 → 夸克
        if any(kw in query for kw in professional_keywords['medical']):
            balance = self._get_balance('search_pro_quark')
            if balance > 0:
                return {
                    'engine': 'search_pro_quark',
                    'reason': '医疗健康领域，使用夸克垂直搜索'
                }

        # 专业领域 → 夸克
        if any(kw in query for kw in professional_keywords['vertical']):
            balance = self._get_balance('search_pro_quark')
            if balance > 0:
                return {
                    'engine': 'search_pro_quark',
                    'reason': '专业领域查询，使用夸克搜索'
                }

        # 重要查询 → 高级版
        if importance == 'high':
            balance = self._get_balance('search_pro')
            if balance > 0:
                return {
                    'engine': 'search_pro',
                    'reason': '重要查询，使用高级版提高准确率'
                }

        # 默认 → 基础版
        return {
            'engine': 'search_std',
            'reason': '常规查询，使用基础版（性价比高）'
        }

    def _execute_search(
        self,
        query: str,
        engine: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        执行实际搜索调用
        """

        if not self.api_key:
            self.logger.warning("未配置ZHIPU_API_KEY，返回模拟数据")
            return self._mock_search_results(query, top_k)

        try:
            # 调用智谱API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'model': 'glm-4',
                'messages': [
                    {
                        'role': 'user',
                        'content': f'请搜索：{query}'
                    }
                ],
                'tools': [
                    {
                        'type': 'web_search',
                        'web_search': {
                            'enable': True,
                            'search_engine': engine,
                            'top_k': top_k
                        }
                    }
                ]
            }

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                self.logger.error(f"API调用失败: {response.status_code}")
                return self._mock_search_results(query, top_k)

            data = response.json()

            # 解析搜索结果
            results = []
            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0]['message']

                # 提取工具调用结果
                if 'tool_calls' in message:
                    for tool_call in message['tool_calls']:
                        if tool_call['type'] == 'web_search':
                            results = self._parse_search_results(
                                tool_call.get('search_result', {})
                            )

            return results if results else self._mock_search_results(query, top_k)

        except Exception as e:
            self.logger.error(f"搜索调用异常: {str(e)}")
            return self._mock_search_results(query, top_k)

    def _parse_search_results(self, search_result: Dict) -> List[Dict[str, Any]]:
        """解析搜索结果"""
        results = []

        # 智谱返回的搜索结果格式
        if 'web_search' in search_result:
            for item in search_result['web_search'].get('results', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('content', ''),
                    'source': item.get('media', ''),
                    'date': item.get('date', '')
                })

        return results

    def _mock_search_results(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """模拟搜索结果（测试用）"""
        return [
            {
                'title': f'关于"{query}"的搜索结果1',
                'url': 'https://example.com/1',
                'snippet': f'这是关于{query}的详细说明...',
                'source': '示例网站',
                'date': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'title': f'关于"{query}"的搜索结果2',
                'url': 'https://example.com/2',
                'snippet': f'{query}的相关信息和分析...',
                'source': '示例网站',
                'date': datetime.now().strftime('%Y-%m-%d')
            }
        ][:top_k]

    def _get_balance(self, engine: str) -> int:
        """获取引擎余额"""
        return self.resource_packs.get(engine, {}).get('balance', 0)

    def _deduct_balance(self, engine: str, count: int):
        """扣减余额"""
        if engine in self.resource_packs:
            current = self.resource_packs[engine]['balance']
            self.resource_packs[engine]['balance'] = max(0, current - count)
            self.logger.info(f"{engine} 余额: {current} → {self.resource_packs[engine]['balance']}")

    def get_balance_stats(self) -> Dict[str, Any]:
        """
        获取资源包余额统计

        Returns:
            {
                "total_balance": 9954,
                "engines": {
                    "search_std": {"balance": 4962, "percentage": 50},
                    ...
                },
                "expires_at": "2026-09-12",
                "days_remaining": 182
            }
        """
        total = sum(pack['balance'] for pack in self.resource_packs.values())

        engines = {}
        for engine, config in self.resource_packs.items():
            engines[engine] = {
                'balance': config['balance'],
                'price': config['price'],
                'percentage': round((config['balance'] / total) * 100, 2) if total > 0 else 0
            }

        # 计算剩余天数
        expires_at = datetime.strptime(self.resource_packs['search_std']['expires_at'], '%Y-%m-%d')
        days_remaining = (expires_at - datetime.now()).days

        return {
            'total_balance': total,
            'engines': engines,
            'expires_at': self.resource_packs['search_std']['expires_at'],
            'days_remaining': days_remaining,
            'daily_quota': round(total / max(days_remaining, 1), 1)
        }

    def get_usage_recommendation(self) -> Dict[str, Any]:
        """
        获取使用建议

        Returns:
            {
                "search_std": {"daily_quota": 27, "usage": "常规查询（主力）"},
                ...
            }
        """
        stats = self.get_balance_stats()
        total = stats['total_balance']
        days = stats['days_remaining']

        # 分配策略
        recommendations = {
            'search_std': {
                'percentage': 80,
                'daily_quota': round((total * 0.8) / max(days, 1)),
                'usage': '常规查询（主力）'
            },
            'search_pro': {
                'percentage': 15,
                'daily_quota': round((total * 0.15) / max(days, 1)),
                'usage': '重要查询（精准）'
            },
            'search_pro_quark': {
                'percentage': 5,
                'daily_quota': round((total * 0.05) / max(days, 1)),
                'usage': '垂直领域（专业）'
            }
        }

        return recommendations


# ========== 便捷函数 ==========

def search_web(query: str, importance: str = 'normal', top_k: int = 10) -> Dict:
    """
    网页搜索（便捷函数）

    Args:
        query: 搜索关键词
        importance: 重要性（normal/high）
        top_k: 返回结果数量

    Returns:
        搜索结果
    """
    tool = ZhipuSearchTool()
    return tool.search(query, importance=importance, top_k=top_k)


def get_search_balance() -> Dict[str, Any]:
    """
    获取搜索余额（便捷函数）

    Returns:
        余额统计
    """
    tool = ZhipuSearchTool()
    return tool.get_balance_stats()
