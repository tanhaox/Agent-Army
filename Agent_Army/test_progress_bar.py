"""
测试进度条显示
"""
import streamlit as st
import time

st.title("🧪 Progress Bar Test")

st.markdown("---")

# 测试1：基础进度条
st.subheader("Test 1: Basic Progress Bar")
progress_bar = st.progress(0, text="Loading...")

for i in range(100):
    progress_bar.progress(i + 1, text=f"Progress: {i+1}%")
    time.sleep(0.05)

st.success("✅ Test 1 Complete!")

st.markdown("---")

# 测试2：进度条 + 状态文本
st.subheader("Test 2: Progress Bar + Status")
progress_bar2 = st.progress(0)
status_text = st.empty()

steps = [
    (10, "Step 1: Loading modules..."),
    (30, "Step 2: Configuring..."),
    (50, "Step 3: Processing..."),
    (80, "Step 4: Analyzing..."),
    (100, "✅ Complete!")
]

for progress, status in steps:
    progress_bar2.progress(progress)
    status_text.text(status)
    time.sleep(1)

st.success("✅ Test 2 Complete!")

st.markdown("---")

# 测试3：进度条 + 计时器
st.subheader("Test 3: Progress Bar + Timer")
start_time = time.time()
progress_bar3 = st.progress(0, text="Starting...")
timer_placeholder = st.empty()

for i in range(10):
    elapsed = time.time() - start_time
    timer_placeholder.metric("⏱️ Elapsed Time", f"{elapsed:.1f}s")
    progress_bar3.progress((i + 1) * 10, text=f"Step {i+1}/10")
    time.sleep(0.5)

st.success("✅ Test 3 Complete!")
st.balloons()
