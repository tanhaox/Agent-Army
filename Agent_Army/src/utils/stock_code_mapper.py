"""
股票代码映射管理工具
使用 AKShare 获取实时股票代码和名称映射

版本: v1.0
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict
import streamlit as st


class StockCodeMapper:
    """股票代码映射管理器"""

    def __init__(self, cache_dir: str = "./data", cache_expiry_hours: int = 24):
        """
        初始化映射管理器

        Args:
            cache_dir: 缓存目录
            cache_expiry_hours: 缓存过期时间（小时）
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_file = self.cache_dir / "stock_code_map.json"
        self.cache_expiry_hours = cache_expiry_hours

        self.stock_map = {}
        self.name_to_code = {}
        self.code_to_name = {}

        # 尝试加载缓存
        self._load_cache()

    def _load_cache(self):
        """从缓存文件加载股票映射"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 检查缓存是否过期
                cache_time = data.get('timestamp', 0)
                current_time = time.time()
                age_hours = (current_time - cache_time) / 3600

                if age_hours < self.cache_expiry_hours:
                    self.stock_map = data.get('stock_map', {})
                    self.name_to_code = data.get('name_to_code', {})
                    self.code_to_name = data.get('code_to_name', {})
                    return True
                else:
                    st.info(f"📦 股票映射缓存已过期（{age_hours:.1f}小时前），正在更新...")

            except Exception as e:
                st.warning(f"⚠️ 加载缓存失败: {e}")

        return False

    def _save_cache(self):
        """保存股票映射到缓存文件"""
        try:
            data = {
                'timestamp': time.time(),
                'stock_map': self.stock_map,
                'name_to_code': self.name_to_code,
                'code_to_name': self.code_to_name,
                'total_count': len(self.stock_map)
            }

            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            st.error(f"❌ 保存缓存失败: {e}")
            return False

    def fetch_from_akshare(self) -> bool:
        """
        从 AKShare 获取股票代码映射

        Returns:
            bool: 是否成功获取
        """
        try:
            import akshare as ak

            with st.spinner("🔄 正在从 AKShare 获取股票代码映射..."):
                # 获取A股股票信息
                df = ak.stock_info_a_code_name()

                # 构建映射表
                self.stock_map = {}
                self.name_to_code = {}
                self.code_to_name = {}

                for _, row in df.iterrows():
                    code = row['code']      # 6位代码
                    name = row['name']      # 股票名称

                    # 存储映射
                    self.stock_map[code] = name
                    self.name_to_code[name] = code
                    self.code_to_name[code] = name

                # 保存缓存
                self._save_cache()

                st.success(f"✅ 成功获取 {len(self.stock_map)} 只股票的代码映射")
                return True

        except ImportError:
            st.error("❌ AKShare 未安装，请运行: pip install akshare")
            return False
        except Exception as e:
            st.error(f"❌ 获取股票映射失败: {e}")
            return False

    def name_to_code_convert(self, stock_name: str) -> Optional[str]:
        """
        将股票名称转换为代码

        Args:
            stock_name: 股票名称

        Returns:
            股票代码，如果找不到返回 None
        """
        # 精确匹配
        if stock_name in self.name_to_code:
            return self.name_to_code[stock_name]

        # 模糊匹配（包含关键词）
        for name, code in self.name_to_code.items():
            if stock_name in name or name in stock_name:
                return code

        return None

    def code_to_name_convert(self, stock_code: str) -> Optional[str]:
        """
        将股票代码转换为名称

        Args:
            stock_code: 股票代码

        Returns:
            股票名称，如果找不到返回 None
        """
        return self.code_to_name.get(stock_code)

    def get_stats(self) -> Dict:
        """获取映射统计信息"""
        return {
            'total_stocks': len(self.stock_map),
            'cache_exists': self.cache_file.exists(),
            'cache_age_hours': (time.time() - self.cache_file.stat().st_mtime) / 3600 if self.cache_file.exists() else 0
        }


# 全局实例
_mapper_instance: Optional[StockCodeMapper] = None


def get_stock_mapper() -> StockCodeMapper:
    """
    获取全局股票映射管理器实例

    Returns:
        StockCodeMapper: 映射管理器实例
    """
    global _mapper_instance

    if _mapper_instance is None:
        _mapper_instance = StockCodeMapper()

        # 如果缓存为空，尝试获取
        if len(_mapper_instance.stock_map) == 0:
            _mapper_instance.fetch_from_akshare()

    return _mapper_instance


def convert_stock_name_to_code_v2(stock_name: str) -> Optional[str]:
    """
    将股票名称转换为代码（使用 AKShare）

    Args:
        stock_name: 股票名称

    Returns:
        股票代码，如果找不到返回 None
    """
    mapper = get_stock_mapper()
    return mapper.name_to_code_convert(stock_name)


def convert_stock_code_to_name(stock_code: str) -> Optional[str]:
    """
    将股票代码转换为名称（使用 AKShare）

    Args:
        stock_code: 股票代码

    Returns:
        股票名称，如果找不到返回 None
    """
    mapper = get_stock_mapper()
    return mapper.code_to_name_convert(stock_code)


if __name__ == "__main__":
    """测试代码"""
    import streamlit as st

    st.title("🧪 股票代码映射测试")

    mapper = StockCodeMapper()

    # 显示统计信息
    stats = mapper.get_stats()
    st.json(stats)

    # 测试转换
    col1, col2 = st.columns(2)

    with col1:
        test_name = st.text_input("股票名称", value="贵州茅台")
        if st.button("转换为代码"):
            code = mapper.name_to_code_convert(test_name)
            st.success(f"✅ {test_name} → {code}")

    with col2:
        test_code = st.text_input("股票代码", value="600519")
        if st.button("转换为名称"):
            name = mapper.code_to_name_convert(test_code)
            st.success(f"✅ {test_code} → {name}")

    # 更新映射
    if st.button("🔄 从 AKShare 更新映射"):
        mapper.fetch_from_akshare()
        st.rerun()
