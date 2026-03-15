"""
Agent Army - 配置系统黑盒测试
测试配置加载、验证、切换等功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.blackbox.utils.base import BlackBoxTestCase


class ConfigSystemTest(BlackBoxTestCase):
    """配置系统测试"""

    def __init__(self):
        super().__init__(
            name="配置系统测试",
            description="测试配置文件的加载、验证和获取功能"
        )

    def run(self):
        """运行测试"""
        # 步骤1: 导入配置模块
        self.log_step("导入配置模块")
        try:
            from src.core.config import get_model_config, list_model_configs
            self.log_step("配置模块导入成功", "PASS")
        except Exception as e:
            self.log_step(f"配置模块导入失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'ImportError',
                'message': str(e)
            })
            return

        # 步骤2: 列出所有配置
        self.log_step("查询所有可用配置")
        try:
            configs = list_model_configs()
            self.assert_not_none(configs, "配置列表不为空")
            self.assert_greater(len(configs), 0, "至少有一个配置")
            self.log_step(f"找到 {len(configs)} 个配置", "PASS")

            # 列出所有配置名称
            for config_name in configs:
                self.log_step(f"  - {config_name}", "INFO")

        except Exception as e:
            self.log_step(f"配置查询失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'QueryError',
                'message': str(e)
            })

        # 步骤3: 获取默认配置
        self.log_step("获取默认配置")
        try:
            config = get_model_config("default")
            self.assert_not_none(config, "默认配置不为空")
            self.log_step("默认配置加载成功", "PASS")

            # 检查必需字段
            required_fields = ['model_name', 'provider', 'api_key']
            for field in required_fields:
                if field in config:
                    self.log_step(f"  配置包含字段: {field}", "PASS")
                else:
                    self.log_step(f"  配置缺少字段: {field}", "FAIL")

        except Exception as e:
            self.log_step(f"配置加载失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'LoadError',
                'message': str(e)
            })

        # 步骤4: 验证配置有效性
        self.log_step("验证配置有效性")
        try:
            config = get_model_config("default")

            # 检查模型名称
            model_name = config.get('model_name', '')
            self.assert_true(
                len(model_name) > 0,
                f"模型名称不为空 (实际: '{model_name}')"
            )

            # 检查提供商
            provider = config.get('provider', '')
            valid_providers = ['openai', 'anthropic', 'zhipu', 'deepseek']
            self.assert_true(
                provider in valid_providers,
                f"提供商有效 (实际: '{provider}')"
            )

            self.log_step("配置验证通过", "PASS")

        except Exception as e:
            self.log_step(f"配置验证失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'ValidationError',
                'message': str(e)
            })


class DesignTokensTest(BlackBoxTestCase):
    """Design Tokens 系统测试"""

    def __init__(self):
        super().__init__(
            name="Design Tokens 测试",
            description="测试设计令牌系统的颜色、字体、间距等配置"
        )

    def run(self):
        """运行测试"""
        # 步骤1: 导入 Design Tokens
        self.log_step("导入 DesignTokens")
        try:
            from src.core.design_tokens import DesignTokens
            self.log_step("DesignTokens 导入成功", "PASS")
        except Exception as e:
            self.log_step(f"DesignTokens 导入失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'ImportError',
                'message': str(e)
            })
            return

        # 步骤2: 检查颜色配置
        self.log_step("检查颜色配置")
        try:
            colors = DesignTokens.Colors

            # 必需的颜色字段
            required_colors = [
                'PRIMARY', 'SECONDARY', 'SUCCESS', 'WARNING', 'ERROR',
                'TEXT_PRIMARY', 'TEXT_SECONDARY', 'BACKGROUND', 'BORDER_DEFAULT'
            ]

            for color_name in required_colors:
                if hasattr(colors, color_name):
                    color_value = getattr(colors, color_name)
                    self.assert_true(
                        isinstance(color_value, str) and color_value.startswith('#'),
                        f"颜色 {color_name} 格式正确"
                    )
                else:
                    self.log_step(f"缺少颜色定义: {color_name}", "FAIL")

        except Exception as e:
            self.log_step(f"颜色配置检查失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'ColorConfigError',
                'message': str(e)
            })

        # 步骤3: 检查字体配置
        self.log_step("检查字体配置")
        try:
            typography = DesignTokens.Typography

            required_fonts = ['FONT_FAMILY', 'FONT_SIZE_BASE', 'FONT_WEIGHT']
            for font_name in required_fonts:
                if hasattr(typography, font_name):
                    self.log_step(f"字体属性存在: {font_name}", "PASS")
                else:
                    self.log_step(f"字体属性缺失: {font_name}", "FAIL")

        except Exception as e:
            self.log_step(f"字体配置检查失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'FontConfigError',
                'message': str(e)
            })

        # 步骤4: 检查间距配置
        self.log_step("检查间距配置")
        try:
            spacing = DesignTokens.Spacing

            required_spacing = ['SPACING_SM', 'SPACING_MD', 'SPACING_LG']
            for spacing_name in required_spacing:
                if hasattr(spacing, spacing_name):
                    value = getattr(spacing, spacing_name)
                    self.assert_true(
                        isinstance(value, (int, float)),
                        f"间距 {spacing_name} 是数字"
                    )
                else:
                    self.log_step(f"间距定义缺失: {spacing_name}", "FAIL")

        except Exception as e:
            self.log_step(f"间距配置检查失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'SpacingConfigError',
                'message': str(e)
            })


class EnvironmentConfigTest(BlackBoxTestCase):
    """环境配置测试"""

    def __init__(self):
        super().__init__(
            name="环境配置测试",
            description="测试环境变量和 .env 文件配置"
        )

    def run(self):
        """运行测试"""
        # 步骤1: 检查 .env 文件
        self.log_step("检查 .env 文件")
        try:
            env_file = Path(__file__).parent.parent.parent.parent / '.env'

            if env_file.exists():
                self.log_step(f".env 文件存在: {env_file}", "PASS")

                # 读取文件内容
                with open(env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                self.log_step(f".env 文件有 {len(lines)} 行", "INFO")
            else:
                self.log_step(".env 文件不存在（可能使用默认配置）", "INFO")

        except Exception as e:
            self.log_step(f".env 文件检查失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'EnvFileError',
                'message': str(e)
            })

        # 步骤2: 检查关键环境变量
        self.log_step("检查关键环境变量")
        try:
            import os

            # 检查一些常见的环境变量（不检查实际值，只检查是否可访问）
            env_keys = ['PATH', 'HOME' if sys.platform != 'win32' else 'USERPROFILE']

            for key in env_keys:
                if key in os.environ:
                    self.log_step(f"环境变量可访问: {key}", "PASS")
                else:
                    self.log_step(f"环境变量不存在: {key}", "WARN")

        except Exception as e:
            self.log_step(f"环境变量检查失败: {str(e)}", "FAIL")
            self.results['errors'].append({
                'type': 'EnvVarError',
                'message': str(e)
            })
