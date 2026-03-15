"""
股票代码智能识别工具
支持：股票代码、股票名称、拼音缩写
"""

import re
from typing import Optional, Dict, List


class StockCodeResolver:
    """股票代码解析器"""

    def __init__(self):
        # 常见股票映射表（可以扩展）
        self.stock_map = {
            # 蓝筹股
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000001": "平安银行",
            "000002": "万科A",
            "600036": "招商银行",
            "601318": "中国平安",
            "600000": "浦发银行",
            "601398": "工商银行",
            "601288": "农业银行",
            "601939": "建设银行",
            "601328": "交通银行",
            "600030": "中信证券",
            "600031": "三一重工",
            "600276": "恒瑞医药",
            "000333": "美的集团",
            "002594": "比亚迪",
            "300059": "东方财富",
            "600031": "三一重工",

            # 科技股
            "000063": "中兴通讯",
            "002415": "海康威视",
            "300750": "宁德时代",
            "688981": "中芯国际",
            "600900": "长江电力",

            # 新能源
            "002475": "立讯精密",
            "300124": "汇川技术",
            "002129": "中环股份",

            # 消费股
            "000568": "泸州老窖",
            "600809": "山西汾酒",
            "000596": "古井贡酒",
            "600887": "伊利股份",
            "002714": "牧原股份",

            # 医药股
            "000661": "长春高新",
            "300760": "迈瑞医疗",
            "002007": "华兰生物",
        }

        # 拼音缩写映射
        self.pinyin_map = {
            "GZMT": "600519",  # 贵州茅台
            "WLY": "000858",   # 五粮液
            "PAYH": "000001",  # 平安银行
            "ZGYH": "601398",  # 中国工商银行
            "ZGYH": "601398",
            "JSYH": "601939",  # 建设银行
            "NYYH": "601288",  # 农业银行
            "ZGPA": "601318",  # 中国平安
            "ZSQX": "601328",  # 中国证券
            "ZGYS": "600900",  # 中国长江电力
            "BYD": "002594",   # 比亚迪
            "MJDL": "600030",  # 民金证券
            "ZS": "600036",    # 招商
            "ZGYX": "600030",  # 中信证券
            "GFYH": "600000",  # 浦发银行
            "MYRL": "600519",  # 茅台
            "WL": "000858",    # 五粮液
        }

        # 创建反向映射（名称→代码）
        self.name_to_code = {v: k for k, v in self.stock_map.items()}

    def resolve(self, input_str: str) -> Optional[str]:
        """
        解析输入，返回股票代码

        支持格式：
        - 600519 (股票代码)
        - 贵州茅台 (股票名称)
        - GZMT (拼音缩写)
        """
        if not input_str:
            return None

        input_str = input_str.strip()

        # 1. 检查是否为6位数字（股票代码）
        if re.match(r'^\d{6}$', input_str):
            return input_str

        # 2. 检查是否为已知股票名称
        if input_str in self.name_to_code:
            return self.name_to_code[input_str]

        # 3. 检查模糊匹配（部分名称）
        for name, code in self.name_to_code.items():
            if input_str in name or name in input_str:
                return code

        # 4. 检查拼音缩写
        input_upper = input_str.upper()
        if input_upper in self.pinyin_map:
            return self.pinyin_map[input_upper]

        # 5. 尝试从拼音首字母匹配
        for name, code in self.name_to_code.items():
            # 简单的拼音首字母匹配（例如"贵州茅台" -> "GZMT"）
            if self._match_pinyin(input_upper, name):
                return code

        return None

    def _match_pinyin(self, input_str: str, stock_name: str) -> bool:
        """简单的拼音首字母匹配"""
        # 这里只是一个示例，实际需要完整的拼音库
        # 例如："GZMT" 可以匹配 "贵州茅台"
        pinyin_approx = {
            "贵": "G", "州": "Z", "茅": "M", "台": "T",
            "五": "W", "粮": "L", "液": "Y",
            "平": "P", "安": "A", "银": "Y", "行": "H",
            "招": "Z", "商": "S",
            "中": "Z", "国": "G",
            "工": "G", "商": "S",
            "建": "J", "设": "S",
            "农": "N", "业": "Y",
            "美": "M", "的": "D",
            "比": "B", "亚": "Y", "迪": "D",
        }

        # 生成股票名称的拼音首字母
        initials = ""
        for char in stock_name:
            if char in pinyin_approx:
                initials += pinyin_approx[char]

        return input_str == initials

    def get_stock_name(self, code: str) -> Optional[str]:
        """根据代码获取股票名称"""
        return self.stock_map.get(code)

    def search(self, keyword: str) -> List[Dict[str, str]]:
        """
        搜索股票（模糊匹配）

        返回: [{"code": "600519", "name": "贵州茅台"}, ...]
        """
        results = []

        # 按代码搜索
        for code, name in self.stock_map.items():
            if keyword in code or keyword in name:
                results.append({"code": code, "name": name})

        return results[:10]  # 返回前10个结果


# 全局实例
resolver = StockCodeResolver()


def resolve_stock_code(input_str: str) -> Optional[str]:
    """解析股票输入（便捷函数）"""
    return resolver.resolve(input_str)


def get_stock_name(code: str) -> Optional[str]:
    """获取股票名称（便捷函数）"""
    return resolver.get_stock_name(code)


def search_stocks(keyword: str) -> List[Dict[str, str]]:
    """搜索股票（便捷函数）"""
    return resolver.search(keyword)


if __name__ == "__main__":
    # 测试
    test_cases = [
        "600519",      # 代码
        "贵州茅台",      # 名称
        "GZMT",        # 拼音
        "茅台",         # 模糊
        "ZGPA",        # 中国平安拼音
        "中国平安",      # 全名
        "BYD",         # 比亚迪
        "比亚迪",        # 名称
    ]

    for case in test_cases:
        result = resolve_stock_code(case)
        name = get_stock_name(result) if result else None
        print(f"输入: {case:10} → 代码: {result:6} → 名称: {name}")
