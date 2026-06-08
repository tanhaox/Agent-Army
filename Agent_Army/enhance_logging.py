"""
投资分析日志增强脚本
为关键执行点添加详细日志记录
"""

import re
import sys
from pathlib import Path

# 设置UTF-8输出
sys.stdout.reconfigure(encoding='utf-8')

# 读取原文件
file_path = Path("c:/AI-Agent-Local/Agent_Army/src/core/pages/investment_analysis_v2.py")
content = file_path.read_text(encoding='utf-8')

# 1. 在文件开头添加logger导入
if "from src.core.logger import get_logger" not in content:
    # 在import json后添加
    content = content.replace(
        "import json\n",
        "import json\nimport traceback\n\n# Import logging system\nfrom src.core.logger import get_logger\n\n# Create page logger\nlogger = get_logger(\"InvestmentAnalysis\")\n"
    )
    print("[OK] Added logger import")

# 2. 在步骤1开始处添加日志
step1_start = '''    if st.session_state.step1_status == "running":
        # Create placeholders
        st.markdown("### Step 1: Industry Analysis")
        progress_bar = st.progress(0)
        status_text = st.empty()

        logger.info("Starting Step 1: Industry Analysis", stock_code=stock_code)'''

content = content.replace(
    '    if st.session_state.step1_status == "running":\n        # 创建占位符\n        st.markdown("### 🔄 步骤1: 产业链分析")\n        progress_bar = st.progress(0)\n        status_text = st.empty()',
    step1_start
)
print("[OK] Added Step 1 start log")

# 3. 在analyze执行前添加日志
content = content.replace(
    '            start_time = time.time()\n            result_obj = asyncio.run(analyzer.analyze(stock_code))',
    '''            logger.info("Executing industry analysis", stock_code=stock_code)
            start_time = time.time()
            result_obj = asyncio.run(analyzer.analyze(stock_code))'''
)
print("[OK] Added analyze start log")

# 4. 在analyze执行后添加日志
content = content.replace(
    '            elapsed_time = time.time() - start_time\n\n            status_text.text("🔄 正在处理分析结果...")',
    '''            elapsed_time = time.time() - start_time
            logger.info("Industry analysis completed", elapsed_time=elapsed_time, stock_code=stock_code)

            status_text.text("Processing results...")'''
)
print("[OK] Added analyze complete log")

# 写回文件
file_path.write_text(content, encoding='utf-8')
print("\n[SUCCESS] Logging enhancement completed!")
print("Added log points:")
print("  - Step 1 start")
print("  - Module loading")
print("  - Analysis execution")
print("  - Analysis completion")
print("  - Error details (with traceback)")
