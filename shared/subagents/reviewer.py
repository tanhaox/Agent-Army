"""
AI-Agent-Local 代码审查器
基于 LLM-as-Judge 模式

功能：
- 自动化代码质量审查
- 问题分类和严重程度评估
- 最佳实践建议
- 代码质量评分

Version: 1.0.0
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import json
import re

logger = logging.getLogger(__name__)


# ==================== 数据结构 ====================

class Severity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"  # 必须立即修复
    IMPORTANT = "important"  # 下个任务前修复
    MINOR = "minor"        # 记录即可


class IssueCategory(Enum):
    """问题类别"""
    BUG = "bug"                    # 潜在 bug
    SECURITY = "security"          # 安全问题
    PERFORMANCE = "performance"    # 性能问题
    STYLE = "style"                # 代码风格
    ARCHITECTURE = "architecture"  # 架构问题
    DOCUMENTATION = "documentation"  # 文档问题
    TESTING = "testing"            # 测试问题
    MAINTAINABILITY = "maintainability"  # 可维护性


@dataclass
class CodeReviewIssue:
    """代码审查问题"""
    severity: Severity
    category: str
    description: str
    location: Optional[str] = None  # file:line
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "severity": self.severity.value,
            "category": self.category,
            "description": self.description,
            "location": self.location,
            "suggestion": self.suggestion,
            "code_snippet": self.code_snippet
        }


@dataclass
class CodeReview:
    """代码审查结果"""
    task_id: str
    overall_assessment: str  # excellent, good, needs_work, poor
    strengths: List[str] = field(default_factory=list)
    issues: List[CodeReviewIssue] = field(default_factory=list)
    score: float = 0.0  # 0.0-10.0
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "overall_assessment": self.overall_assessment,
            "strengths": self.strengths,
            "issues": [issue.to_dict() for issue in self.issues],
            "score": self.score,
            "recommendations": self.recommendations,
            "metadata": self.metadata
        }


# ==================== 审查规则 ====================

class ReviewRule:
    """审查规则基类"""

    def __init__(
        self,
        name: str,
        category: IssueCategory,
        default_severity: Severity = Severity.MINOR
    ):
        self.name = name
        self.category = category
        self.default_severity = default_severity

    def check(self, code: str, file_path: str = "") -> List[CodeReviewIssue]:
        """
        检查代码

        Args:
            code: 代码内容
            file_path: 文件路径

        Returns:
            发现的问题列表
        """
        raise NotImplementedError


class SecurityRule(ReviewRule):
    """安全规则"""

    def __init__(self):
        super().__init__(
            name="security_check",
            category=IssueCategory.SECURITY,
            default_severity=Severity.CRITICAL
        )

        # 危险模式
        self.dangerous_patterns = {
            r'eval\s*\(': "使用 eval() 可能导致代码注入漏洞",
            r'exec\s*\(': "使用 exec() 可能导致代码注入漏洞",
            r'shell=True': "shell=True 可能导致命令注入",
            r'pickle\.loads?\s*\(': "pickle 反序列化不安全，使用 json",
            r'random\.random\s*\([^)]*\)\s*\+.*\+.*\+.*\+.*random\.random': "弱随机数生成器",
            r'md5\s*\(': "MD5 哈希算法已过时，使用 SHA256",
            r'sha1\s*\(': "SHA1 哈希算法已过时，使用 SHA256",
            r'password\s*=\s*["\'].*["\']': "硬编码密码，使用环境变量",
            r'api_key\s*=\s*["\'].*["\']': "硬编码 API 密钥，使用环境变量",
            r'secret\s*=\s*["\'].*["\']': "硬编码密钥，使用环境变量",
            r'#[\s*]*TODO:[\s*]*fix': "已知的待修复安全问题",
            r'#[\s*]*FIXME:[\s*]*security': "已知的待修复安全问题",
        }

    def check(self, code: str, file_path: str = "") -> List[CodeReviewIssue]:
        """检查安全问题"""
        issues = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            for pattern, message in self.dangerous_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeReviewIssue(
                        severity=self.default_severity,
                        category=self.category.value,
                        description=message,
                        location=f"{file_path}:{line_num}",
                        suggestion="审查并修复此安全问题",
                        code_snippet=line.strip()
                    ))

        return issues


class PerformanceRule(ReviewRule):
    """性能规则"""

    def __init__(self):
        super().__init__(
            name="performance_check",
            category=IssueCategory.PERFORMANCE,
            default_severity=Severity.IMPORTANT
        )

        self.performance_patterns = {
            r'O\([n2]\)': "O(n²) 时间复杂度，考虑优化",
            r'for\s+\w+\s+in\s+.*:\s+for\s+\w+\s+in\s+.*:': "嵌套循环可能导致性能问题",
            r'\.sort\s*\(\)\s*\[.*\]': "对整个列表排序后只取部分，使用 heapq",
            r'list\(.*\.keys\(\)\)': "不必要的 list() 转换，直接使用 keys()",
            r'\+=.*\+.*\+': "字符串拼接使用 += 可能低效，使用 join()",
            r'response\s*=\s*requests\.\w+.*': "同步 HTTP 请求，考虑使用异步",
        }

    def check(self, code: str, file_path: str = "") -> List[CodeReviewIssue]:
        """检查性能问题"""
        issues = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            for pattern, message in self.performance_patterns.items():
                if re.search(pattern, line):
                    issues.append(CodeReviewIssue(
                        severity=self.default_severity,
                        category=self.category.value,
                        description=message,
                        location=f"{file_path}:{line_num}",
                        suggestion="审查并优化此性能问题",
                        code_snippet=line.strip()
                    ))

        return issues


class StyleRule(ReviewRule):
    """代码风格规则"""

    def __init__(self):
        super().__init__(
            name="style_check",
            category=IssueCategory.STYLE,
            default_severity=Severity.MINOR
        )

    def check(self, code: str, file_path: str = "") -> List[CodeReviewIssue]:
        """检查代码风格"""
        issues = []
        lines = code.split('\n')

        # 检查行长度
        for line_num, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append(CodeReviewIssue(
                    severity=self.default_severity,
                    category=self.category.value,
                    description=f"行过长 ({len(line)} > 100 字符)",
                    location=f"{file_path}:{line_num}",
                    suggestion="将长行拆分为多行",
                    code_snippet=line[:50] + "..."
                ))

        return issues


class DocumentationRule(ReviewRule):
    """文档规则"""

    def __init__(self):
        super().__init__(
            name="documentation_check",
            category=IssueCategory.DOCUMENTATION,
            default_severity=Severity.IMPORTANT
        )

    def check(self, code: str, file_path: str = "") -> List[CodeReviewIssue]:
        """检查文档"""
        issues = []
        lines = code.split('\n')

        # 检查函数是否有文档字符串
        in_function = False
        function_line = 0
        function_name = ""

        for line_num, line in enumerate(lines, 1):
            # 检测函数定义
            if re.match(r'^\s*def\s+\w+\s*\(', line):
                in_function = True
                function_line = line_num
                function_name = line.strip()

            # 检查函数后是否有文档字符串
            if in_function:
                if line_num == function_line + 1:
                    if not line.strip().startswith(('"""', "'''", '#')):
                        issues.append(CodeReviewIssue(
                            severity=self.default_severity,
                            category=self.category.value,
                            description=f"函数缺少文档字符串: {function_name}",
                            location=f"{file_path}:{function_line}",
                            suggestion="添加函数文档字符串说明参数和返回值",
                            code_snippet=function_name
                        ))
                    in_function = False

        return issues


class TestingRule(ReviewRule):
    """测试规则"""

    def __init__(self):
        super().__init__(
            name="testing_check",
            category=IssueCategory.TESTING,
            default_severity=Severity.IMPORTANT
        )

    def check(self, code: str, file_path: str = "") -> List[CodeReviewIssue]:
        """检查测试覆盖"""
        issues = []

        # 如果是测试文件，检查是否有断言
        if "test_" in file_path or "_test.py" in file_path:
            if "assert" not in code and "pytest" not in code:
                issues.append(CodeReviewIssue(
                    severity=Severity.CRITICAL,
                    category=self.category.value,
                    description=f"测试文件缺少断言: {file_path}",
                    location=file_path,
                    suggestion="添加适当的断言来验证测试结果"
                ))

        return issues


# ==================== 代码审查器 ====================

class CodeReviewer:
    """
    代码审查器

    使用规则引擎和 LLM-as-Judge 模式进行代码审查
    """

    def __init__(
        self,
        rules: Optional[List[ReviewRule]] = None,
        enable_llm_judge: bool = False,
        llm_model: str = "opus"
    ):
        """
        初始化代码审查器

        Args:
            rules: 自定义审查规则列表
            enable_llm_judge: 是否启用 LLM-as-Judge
            llm_model: LLM 模型名称
        """
        self.rules = rules or self._default_rules()
        self.enable_llm_judge = enable_llm_judge
        self.llm_model = llm_model
        self.logger = logging.getLogger("code_reviewer")

    def _default_rules(self) -> List[ReviewRule]:
        """获取默认规则"""
        return [
            SecurityRule(),
            PerformanceRule(),
            StyleRule(),
            DocumentationRule(),
            TestingRule(),
        ]

    async def review(
        self,
        code: str,
        file_path: str = "",
        task_id: str = ""
    ) -> CodeReview:
        """
        审查代码

        Args:
            code: 代码内容
            file_path: 文件路径
            task_id: 任务 ID

        Returns:
            代码审查结果
        """
        self.logger.info(f"[审查] 开始审查: {file_path or task_id}")

        issues = []
        strengths = []

        # 运行所有规则
        for rule in self.rules:
            try:
                rule_issues = rule.check(code, file_path)
                issues.extend(rule_issues)
            except Exception as e:
                self.logger.error(f"[审查] 规则 {rule.name} 执行失败: {e}")

        # LLM-as-Judge 深度分析（可选）
        if self.enable_llm_judge:
            llm_review = await self._llm_judge(code, file_path, task_id)
            if llm_review:
                issues.extend(llm_review.get("issues", []))
                strengths.extend(llm_review.get("strengths", []))

        # 计算分数和评估
        score = self._calculate_score(issues)
        assessment = self._get_assessment(score)

        # 生成建议
        recommendations = self._generate_recommendations(issues)

        self.logger.info(f"[审查] 完成审查: {file_path or task_id}, 分数: {score:.1f}")

        return CodeReview(
            task_id=task_id,
            overall_assessment=assessment,
            strengths=strengths or self._detect_strengths(code),
            issues=issues,
            score=score,
            recommendations=recommendations,
            metadata={
                "file_path": file_path,
                "lines_of_code": len(code.split('\n')),
                "review_time": datetime.now().isoformat()
            }
        )

    async def review_batch(
        self,
        code_items: List[Dict[str, str]]
    ) -> List[CodeReview]:
        """
        批量审查代码

        Args:
            code_items: 代码项列表，每项包含 {code, file_path, task_id}

        Returns:
            代码审查结果列表
        """
        self.logger.info(f"[批量审查] 开始审查 {len(code_items)} 个文件")

        reviews = []
        for item in code_items:
            review = await self.review(
                code=item.get("code", ""),
                file_path=item.get("file_path", ""),
                task_id=item.get("task_id", "")
            )
            reviews.append(review)

        self.logger.info(f"[批量审查] 完成审查: {len(reviews)} 个结果")
        return reviews

    async def _llm_judge(
        self,
        code: str,
        file_path: str,
        task_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        LLM-as-Judge 深度分析

        Args:
            code: 代码内容
            file_path: 文件路径
            task_id: 任务 ID

        Returns:
            LLM 审查结果
        """
        # TODO: 集成实际 LLM 调用
        # 这里需要集成到实际的 LLM API
        self.logger.info(f"[LLM Judge] 跳过（未集成 LLM）")

        return {
            "issues": [],
            "strengths": []
        }

    def _calculate_score(self, issues: List[CodeReviewIssue]) -> float:
        """
        计算代码质量分数

        Args:
            issues: 问题列表

        Returns:
            分数 (0.0-10.0)
        """
        if not issues:
            return 10.0

        # 根据严重程度扣分
        score = 10.0
        for issue in issues:
            if issue.severity == Severity.CRITICAL:
                score -= 2.0
            elif issue.severity == Severity.IMPORTANT:
                score -= 0.5
            else:  # MINOR
                score -= 0.1

        return max(0.0, min(10.0, score))

    def _get_assessment(self, score: float) -> str:
        """
        根据分数获取评估等级

        Args:
            score: 分数

        Returns:
            评估等级
        """
        if score >= 9.0:
            return "excellent"
        elif score >= 7.0:
            return "good"
        elif score >= 5.0:
            return "needs_work"
        else:
            return "poor"

    def _generate_recommendations(self, issues: List[CodeReviewIssue]) -> List[str]:
        """
        生成改进建议

        Args:
            issues: 问题列表

        Returns:
            建议列表
        """
        recommendations = []

        # 统计各类问题
        critical_count = sum(1 for i in issues if i.severity == Severity.CRITICAL)
        important_count = sum(1 for i in issues if i.severity == Severity.IMPORTANT)
        minor_count = sum(1 for i in issues if i.severity == Severity.MINOR)

        # 统计各类别
        categories = {}
        for issue in issues:
            categories[issue.category] = categories.get(issue.category, 0) + 1

        # 生成建议
        if critical_count > 0:
            recommendations.append(f"优先修复 {critical_count} 个关键问题")

        if important_count > 3:
            recommendations.append(f"优化 {important_count} 个重要问题以提升代码质量")

        if categories.get("security", 0) > 0:
            recommendations.append("关注安全问题，确保代码安全性")

        if categories.get("performance", 0) > 2:
            recommendations.append("优化性能瓶颈以提升执行效率")

        if categories.get("documentation", 0) > 3:
            recommendations.append("完善文档以提高代码可维护性")

        if not recommendations:
            recommendations.append("代码质量良好，继续保持")

        return recommendations

    def _detect_strengths(self, code: str) -> List[str]:
        """
        检测代码优点

        Args:
            code: 代码内容

        Returns:
            优点列表
        """
        strengths = []

        # 检查是否有文档字符串
        if '"""' in code or "'''" in code:
            strengths.append("良好的文档注释")

        # 检查是否有类型注解
        if ': ' in code and '->' in code:
            strengths.append("使用类型注解")

        # 检查是否有异常处理
        if 'try:' in code and 'except' in code:
            strengths.append("适当的异常处理")

        # 检查是否有日志
        if 'logger.' in code or 'logging.' in code:
            strengths.append("使用日志系统")

        # 检查是否有测试
        if 'test_' in code or 'pytest' in code:
            strengths.append("包含测试代码")

        if not strengths:
            strengths.append("代码结构清晰")

        return strengths


# ==================== 工厂函数 ====================

def create_reviewer(
    enable_llm_judge: bool = False,
    llm_model: str = "opus",
    custom_rules: Optional[List[ReviewRule]] = None
) -> CodeReviewer:
    """
    创建代码审查器

    Args:
        enable_llm_judge: 是否启用 LLM-as-Judge
        llm_model: LLM 模型名称
        custom_rules: 自定义规则

    Returns:
        CodeReviewer 实例
    """
    return CodeReviewer(
        rules=custom_rules,
        enable_llm_judge=enable_llm_judge,
        llm_model=llm_model
    )


# ==================== 示例使用 ====================

if __name__ == "__main__":
    import asyncio
    import sys
    import io

    # 修复 Windows 控制台编码
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    async def main():
        # 示例代码
        sample_code = '''
def calculate_sum(numbers):
    result = 0
    for num in numbers:
        result += num
    return result

def process_data(data, api_key="hardcoded_key"):
    """处理数据"""
    # TODO: fix security issue
    eval(data)
    return result
'''

        # 创建审查器
        reviewer = create_reviewer()

        # 审查代码
        review = await reviewer.review(
            code=sample_code,
            file_path="example.py",
            task_id="task-1"
        )

        # 输出结果
        print("\n=== 代码审查结果 ===")
        print(f"评估等级: {review.overall_assessment}")
        print(f"分数: {review.score:.1f}/10.0")
        print(f"\n优点 ({len(review.strengths)}):")
        for strength in review.strengths:
            print(f"  ✓ {strength}")

        print(f"\n问题 ({len(review.issues)}):")
        for issue in review.issues:
            print(f"  [{issue.severity.value.upper()}] {issue.category}")
            print(f"    {issue.description}")
            if issue.location:
                print(f"    位置: {issue.location}")
            if issue.suggestion:
                print(f"    建议: {issue.suggestion}")

        print(f"\n建议:")
        for rec in review.recommendations:
            print(f"  • {rec}")

    # 运行示例
    asyncio.run(main())
