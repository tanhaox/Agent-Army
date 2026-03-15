"""
Agent Army - 导出工具
PDF报告、Excel数据导出
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime
import io
import base64
from pathlib import Path

# 尝试导入PDF库（可选）
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PDFExporter:
    """PDF报告导出器"""

    @staticmethod
    def is_available() -> bool:
        """检查PDF功能是否可用"""
        return PDF_AVAILABLE

    @staticmethod
    def export_stock_analysis_report(
        stock_code: str,
        analysis_result: Dict,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        导出股票分析报告为PDF

        Args:
            stock_code: 股票代码
            analysis_result: 分析结果
            output_path: 输出路径（可选）

        Returns:
            PDF字节数据（如果output_path为None）
        """
        if not PDF_AVAILABLE:
            st.warning("⚠️ PDF功能不可用，请安装: pip install reportlab")
            return None

        # 创建PDF文档
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer if output_path is None else output_path,
            pagesize=A4
        )

        # 准备内容
        story = []
        styles = getSampleStyleSheet()

        # 标题
        title = f"股票分析报告 - {stock_code}"
        story.append(Paragraph(title, styles['Title']))
        story.append(Spacer(1, 12))

        # 基本信息
        info_data = [
            ['股票代码', stock_code],
            ['分析日期', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['分析Agent数', str(len(analysis_result))]
        ]

        info_table = Table(info_data, colWidths=[2*72, 4*72])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.grey),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (1, 0), (-1, -1), colors.beige),
            ('TEXTCOLOR', (1, 0), (-1, -1), colors.black),
            ('FONTNAME', (1, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (1, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(info_table)
        story.append(Spacer(1, 12))

        # Agent分析结果
        for agent_id, result in analysis_result.items():
            agent_title = f"{result['agent_name']} - {result['army']}"
            story.append(Paragraph(agent_title, styles['Heading2']))
            story.append(Spacer(1, 6))

            agent_data = [
                ['评分', f"{result['score']}/100"],
                ['推荐', result['recommendation']],
                ['置信度', f"{result['confidence']:.1%}"],
                ['分析结论', result['analysis']]
            ]

            agent_table = Table(agent_data, colWidths=[2*72, 4*72])
            agent_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))

            story.append(agent_table)
            story.append(Spacer(1, 12))

        # 构建PDF
        doc.build(story)

        # 返回字节数据
        if output_path is None:
            buffer.seek(0)
            return buffer.getvalue()

        return None

    @staticmethod
    def create_download_link(
        pdf_bytes: bytes,
        filename: str = "report.pdf"
    ) -> str:
        """
        创建下载链接

        Args:
            pdf_bytes: PDF字节数据
            filename: 文件名

        Returns:
            HTML下载链接
        """
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📥 下载PDF报告</a>'
        return href


class ExcelExporter:
    """Excel数据导出器"""

    @staticmethod
    def export_analysis_data(
        stock_code: str,
        analysis_result: Dict,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        导出分析数据为Excel

        Args:
            stock_code: 股票代码
            analysis_result: 分析结果
            output_path: 输出路径（可选）

        Returns:
            Excel字节数据（如果output_path为None）
        """
        # 创建Excel writer
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 汇总表
            summary_data = []
            for agent_id, result in analysis_result.items():
                summary_data.append({
                    'Agent ID': agent_id,
                    'Agent名称': result['agent_name'],
                    '所属军团': result['army'],
                    '评分': result['score'],
                    '推荐': result['recommendation'],
                    '置信度': f"{result['confidence']:.1%}",
                    '分析时间': result['timestamp']
                })

            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='分析汇总', index=False)

            # 详细分析表
            detail_data = []
            for agent_id, result in analysis_result.items():
                detail_data.append({
                    '股票代码': stock_code,
                    'Agent': result['agent_name'],
                    '分析结论': result['analysis'],
                    '评分': result['score'],
                    '推荐操作': result['recommendation']
                })

            df_detail = pd.DataFrame(detail_data)
            df_detail.to_excel(writer, sheet_name='详细分析', index=False)

        # 返回字节数据
        if output_path is None:
            buffer.seek(0)
            return buffer.getvalue()

        # 保存到文件
        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())

        return None

    @staticmethod
    def export_portfolio_data(
        portfolio_data: Dict,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        导出投资组合数据为Excel

        Args:
            portfolio_data: 投资组合数据
            output_path: 输出路径（可选）

        Returns:
            Excel字节数据（如果output_path为None）
        """
        buffer = io.BytesIO()

        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # 持仓明细
            holdings = portfolio_data.get('holdings', [])
            df_holdings = pd.DataFrame(holdings)
            df_holdings.to_excel(writer, sheet_name='持仓明细', index=False)

            # 风险指标
            risk_metrics = portfolio_data.get('risk_metrics', {})
            df_risk = pd.DataFrame([risk_metrics])
            df_risk.to_excel(writer, sheet_name='风险指标', index=False)

            # 业绩归因
            attribution = portfolio_data.get('attribution', {})
            df_attribution = pd.DataFrame([attribution])
            df_attribution.to_excel(writer, sheet_name='业绩归因', index=False)

        if output_path is None:
            buffer.seek(0)
            return buffer.getvalue()

        with open(output_path, 'wb') as f:
            f.write(buffer.getvalue())

        return None

    @staticmethod
    def create_download_link(
        excel_bytes: bytes,
        filename: str = "data.xlsx"
    ) -> str:
        """
        创建下载链接

        Args:
            excel_bytes: Excel字节数据
            filename: 文件名

        Returns:
            HTML下载链接
        """
        b64 = base64.b64encode(excel_bytes).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">📥 下载Excel数据</a>'
        return href


class ShareLinkGenerator:
    """分享链接生成器"""

    @staticmethod
    def generate_report_link(
        report_id: str,
        base_url: str = "http://localhost:8501"
    ) -> str:
        """
        生成报告分享链接

        Args:
            report_id: 报告ID
            base_url: 基础URL

        Returns:
            分享链接
        """
        return f"{base_url}/report?id={report_id}"

    @staticmethod
    def copy_to_clipboard_js(text: str) -> str:
        """
        生成复制到剪贴板的JavaScript代码

        Args:
            text: 要复制的文本

        Returns:
            JavaScript代码
        """
        return f"""
        <script>
        function copyToClipboard() {{
            navigator.clipboard.writeText("{text}").then(function() {{
                alert("链接已复制到剪贴板！");
            }});
        }}
        </script>
        """


# 导出
__all__ = [
    'PDFExporter',
    'ExcelExporter',
    'ShareLinkGenerator'
]
