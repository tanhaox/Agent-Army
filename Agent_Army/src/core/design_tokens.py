"""
设计令牌（Design Tokens）

统一的视觉设计变量系统，包括颜色、字体、间距、圆角、阴影和动画。

用途：确保整个应用程序的视觉一致性和可维护性
"""

class DesignTokens:
    """设计令牌系统"""

    class Colors:
        """颜色系统"""

        # 主色调（Primary） - 用于主要操作、激活状态
        PRIMARY = "#1E88E5"
        PRIMARY_DARK = "#1565C0"
        PRIMARY_LIGHT = "#42A5F5"
        PRIMARY_CONTRAST = "#FFFFFF"

        # 辅助色（Secondary） - 用于次要操作、成功状态
        SECONDARY = "#43A047"
        SECONDARY_DARK = "#2E7D32"
        SECONDARY_LIGHT = "#66BB6A"
        SECONDARY_CONTRAST = "#FFFFFF"

        # 强调色（Accent） - 用于警告、重要提示
        ACCENT = "#FB8C00"
        ACCENT_DARK = "#F57C00"
        ACCENT_LIGHT = "#FFA726"
        ACCENT_CONTRAST = "#FFFFFF"

        # 功能色
        SUCCESS = "#4CAF50"
        WARNING = "#FF9800"
        ERROR = "#F44336"
        INFO = "#2196F3"

        # 中性色（Grayscale） - 用于文本、背景、边框
        WHITE = "#FFFFFF"
        BLACK = "#000000"

        # 灰色阶梯
        GRAY_50 = "#FAFAFA"
        GRAY_100 = "#F5F5F5"
        GRAY_200 = "#EEEEEE"
        GRAY_300 = "#E0E0E0"
        GRAY_400 = "#BDBDBD"
        GRAY_500 = "#9E9E9E"
        GRAY_600 = "#757575"
        GRAY_700 = "#616161"
        GRAY_800 = "#424242"
        GRAY_900 = "#212121"

        # 背景色
        BG_PRIMARY = "#FFFFFF"
        BG_SECONDARY = "#F5F5F5"
        BG_CARD = "#FFFFFF"
        BG_HOVER = "#F5F5F5"
        BG_ACTIVE = "#E3F2FD"
        BG_DISABLED = "#F5F5F5"

        # 文本色
        TEXT_PRIMARY = "#212121"
        TEXT_SECONDARY = "#757575"
        TEXT_DISABLED = "#BDBDBD"
        TEXT_HINT = "#9E9E9E"
        TEXT_CONTRAST = "#FFFFFF"

        # 边框色
        BORDER_DEFAULT = "#E0E0E0"
        BORDER_FOCUS = "#1E88E5"
        BORDER_ERROR = "#F44336"
        BORDER_SUCCESS = "#4CAF50"

        # 军团主题色（用于区分不同军团）
        # 热点捕捉军团
        ARMY_HOTSPOT = "#FF5722"
        # 产业分析军团
        ARMY_INDUSTRY = "#2196F3"
        # 个股挖掘军团
        ARMY_STOCK = "#4CAF50"
        # 目标预测军团
        ARMY_TARGET = "#FF9800"
        # 策略执行军团
        ARMY_STRATEGY = "#9C27B0"
        # 结果验证军团
        ARMY_VALIDATION = "#00BCD4"
        # 战略层
        ARMY_STRATEGIC = "#E91E63"

    class Typography:
        """字体系统"""

        # 字体家族（优先使用中文字体）
        FONT_FAMILY = "'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif"

        # 字体大小
        H1 = "2.5rem"      # 40px - 页面主标题
        H2 = "2.0rem"      # 32px - 章节标题
        H3 = "1.75rem"     # 28px - 小节标题
        H4 = "1.5rem"      # 24px - 卡片标题
        H5 = "1.25rem"     # 20px - 小标题
        H6 = "1.0rem"      # 16px - 正文
        BODY = "1.0rem"    # 16px - 正文
        SMALL = "0.875rem" # 14px - 辅助文本
        XSMALL = "0.75rem" # 12px - 标签、注释

        # 字体粗细
        WEIGHT_LIGHT = 300
        WEIGHT_REGULAR = 400
        WEIGHT_MEDIUM = 500
        WEIGHT_SEMIBOLD = 600
        WEIGHT_BOLD = 700

        # 行高
        LINE_HEIGHT_TITLE = "1.2"
        LINE_HEIGHT_BODY = "1.6"
        LINE_HEIGHT_COMPACT = "1.4"

    class Spacing:
        """间距系统（基于8px网格）"""

        # 内边距（Padding）
        P_NONE = "0"
        P_XS = "4px"
        P_SM = "8px"
        P_MD = "16px"
        P_LG = "24px"
        P_XL = "32px"
        P_XXL = "48px"

        # 外边距（Margin）
        M_NONE = "0"
        M_XS = "4px"
        M_SM = "8px"
        M_MD = "16px"
        M_LG = "24px"
        M_XL = "32px"
        M_XXL = "48px"

        # 卡片间距
        CARD_PADDING = "24px"
        CARD_GAP = "16px"

        # 列间距
        COLUMN_GAP = "16px"

    class Radius:
        """圆角系统"""

        NONE = "0"
        XS = "2px"
        SM = "4px"
        MD = "8px"
        LG = "12px"
        XL = "16px"
        XXL = "24px"
        FULL = "9999px"  # 圆形

    class Shadow:
        """阴影系统"""

        NONE = "none"

        # 浅阴影（卡片、按钮）
        XS = "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
        SM = "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)"
        MD = "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
        LG = "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)"
        XL = "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)"

        # 内阴影
        INSET = "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)"

    class Animation:
        """动画系统"""

        # 过渡时长
        DURATION_FAST = "150ms"
        DURATION_NORMAL = "300ms"
        DURATION_SLOW = "500ms"

        # 缓动函数
        EASING_DEFAULT = "cubic-bezier(0.4, 0, 0.2, 1)"
        EASING_IN = "cubic-bezier(0.4, 0, 1, 1)"
        EASING_OUT = "cubic-bezier(0, 0, 0.2, 1)"
        EASING_IN_OUT = "cubic-bezier(0.4, 0, 0.6, 1)"

        # 常用过渡（可直接用于CSS transition）
        TRANSITION_FAST = f"all {DURATION_FAST} {EASING_DEFAULT}"
        TRANSITION_NORMAL = f"all {DURATION_NORMAL} {EASING_DEFAULT}"
        TRANSITION_SLOW = f"all {DURATION_SLOW} {EASING_DEFAULT}"

    class Layout:
        """布局系统"""

        # 容器最大宽度
        CONTAINER_MAX_WIDTH = "1400px"
        CONTAINER_NARROW = "960px"

        # 断点（响应式设计）
        BREAKPOINT_SM = "640px"   # 手机横屏
        BREAKPOINT_MD = "768px"   # 平板
        BREAKPOINT_LG = "1024px"  # 小桌面
        BREAKPOINT_XL = "1280px"  # 桌面
        BREAKPOINT_XXL = "1536px" # 大桌面

        # 侧边栏宽度
        SIDEBAR_WIDTH = "280px"
        SIDEBAR_COLLAPSED = "72px"

        # 顶部栏高度
        HEADER_HEIGHT = "64px"

    class ZIndex:
        """层级系统（z-index）"""

        BASE = 0
        DROPDOWN = 1000
        STICKY = 1020
        FIXED = 1030
        MODAL_BACKDROP = 1040
        MODAL = 1050
        POPOVER = 1060
        TOOLTIP = 1070


# 颜色工具函数
def get_army_color(army_name: str) -> str:
    """根据军团名称获取对应的主题色"""
    army_colors = {
        "热点捕捉军团": DesignTokens.Colors.ARMY_HOTSPOT,
        "产业分析军团": DesignTokens.Colors.ARMY_INDUSTRY,
        "个股挖掘军团": DesignTokens.Colors.ARMY_STOCK,
        "目标预测军团": DesignTokens.Colors.ARMY_TARGET,
        "策略执行军团": DesignTokens.Colors.ARMY_STRATEGY,
        "结果验证军团": DesignTokens.Colors.ARMY_VALIDATION,
        "战略层": DesignTokens.Colors.ARMY_STRATEGIC,
    }
    return army_colors.get(army_name, DesignTokens.Colors.PRIMARY)


def rgba(hex_color: str, alpha: float) -> str:
    """将十六进制颜色转换为RGBA格式"""
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


# 示例：打印所有设计令牌（用于调试）
if __name__ == "__main__":
    print("Design Tokens System")
    print("=" * 60)
    print(f"\n主色调: {DesignTokens.Colors.PRIMARY}")
    print(f"辅助色: {DesignTokens.Colors.SECONDARY}")
    print(f"强调色: {DesignTokens.Colors.ACCENT}")
    print(f"\n标题字体: {DesignTokens.Typography.H1} ({DesignTokens.Typography.FONT_FAMILY})")
    print(f"正文字体: {DesignTokens.Typography.BODY}")
    print(f"\n卡片间距: {DesignTokens.Spacing.CARD_PADDING}")
    print(f"圆角: {DesignTokens.Radius.LG}")
    print(f"阴影: {DesignTokens.Shadow.MD}")
    print(f"\n军团主题色: {get_army_color('热点捕捉军团')}")
