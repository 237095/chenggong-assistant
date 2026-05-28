"""
成工职小助手 - 主入口
成都工业职业技术学院
"""

import streamlit as st
from user_agents import parse

# ========== 首先初始化 Supabase 客户端 ==========
from supabase import create_client

# 强制从 Secrets 读取配置
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")

if SUPABASE_URL and SUPABASE_KEY:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase_client = None
    st.error("请先在 Secrets 中配置 SUPABASE_URL 和 SUPABASE_KEY")

# 将客户端存入 session_state
st.session_state.supabase_client = supabase_client

# ========== 导入其他模块 ==========
import login
import admin_panel
import load_docs

# ========== 初始化登录状态 ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_student_id" not in st.session_state:
    st.session_state.user_student_id = None
if "login_error" not in st.session_state:
    st.session_state.login_error = None
if "docs_loaded" not in st.session_state:
    st.session_state.docs_loaded = False

# ========== 页面配置 ==========
if not st.session_state.logged_in:
    st.set_page_config(
        page_title="成工职小助手 - 登录",
        page_icon="🔐",
        layout="centered"
    )
else:
    st.set_page_config(
        page_title="成工职小助手",
        page_icon="🎓",
        layout="wide"
    )

# ========== 主逻辑 ==========
def main():
    # 未登录：显示登录页面
    if not st.session_state.logged_in:
        login.show_login_page()
        return
    
    # 已登录：加载文档（仅首次）
    if not st.session_state.docs_loaded:
        with st.spinner("📚 正在加载学校文档到知识库，请稍候..."):
            try:
                load_docs.load_documents()
                st.session_state.docs_loaded = True
            except Exception as e:
                st.error(f"文档加载失败: {e}")
    
    # 显示用户信息
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        st.markdown("### 🎓 成工职小助手")
    with col2:
        if st.session_state.user_role == "admin":
            st.markdown("**👨‍💼 管理员**")
        else:
            st.markdown(f"**👨‍🎓 学生** | {st.session_state.user_student_id}")
    with col3:
        st.markdown(f"👤 {st.session_state.user_name}")
    with col4:
        if st.button("🚪 退出登录", use_container_width=True):
            login.logout()
            st.rerun()
    
    st.markdown("---")
    
    # 根据角色显示不同界面
    if st.session_state.user_role == "admin":
        admin_panel.show_admin_panel()
    else:
        user_agent_string = st.context.headers.get('User-Agent', '')
        user_agent = parse(user_agent_string)
        
        try:
            if user_agent.is_mobile:
                with open("mobile_app.py", "r", encoding="utf-8") as f:
                    exec(f.read(), globals())
            else:
                with open("desktop_app.py", "r", encoding="utf-8") as f:
                    exec(f.read(), globals())
        except FileNotFoundError as e:
            st.error(f"文件加载失败: {e}")
            st.info("请确保 mobile_app.py 和 desktop_app.py 文件在相同目录下")
        except Exception as e:
            st.error(f"加载界面时出错: {e}")

if __name__ == "__main__":
    main()
