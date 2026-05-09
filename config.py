# 配置文件
import os
import streamlit as st

# ========== 安全读取 API Key ==========
# 优先从 Streamlit Secrets 读取
try:
    DEEPSEEK_API_KEY = st.secrets["DEEPSEEK_API_KEY"]
except:
    # 其次从环境变量读取
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# ========== 应用信息 ==========
APP_NAME = "成工职小助手"
APP_ICON = "🎓"
APP_DESCRIPTION = "你的校园智能伙伴 | 7×24小时在线"

# ========== 校园信息 ==========
CAMPUS_NAME = "成都工业职业技术学院"
CAMPUS_SHORT_NAME = "成工职院"