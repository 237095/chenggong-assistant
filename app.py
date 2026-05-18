import streamlit as st
from user_agents import parse

st.set_page_config(
    page_title="成工职小助手",
    page_icon="🎓",
    layout="wide"
)

# 检测设备类型
user_agent_string = st.context.headers.get('User-Agent', '')
user_agent = parse(user_agent_string)

if user_agent.is_mobile:
    # 手机端 - 使用 mobile_app.py
    with open("mobile_app.py", "r", encoding="utf-8") as f:
        exec(f.read())
else:
    # 电脑端 - 使用 desktop_app.py
    with open("desktop_app.py", "r", encoding="utf-8") as f:
        exec(f.read())
