"""
成工职小助手 - 主入口
成都工业职业技术学院
"""

import streamlit as st
from user_agents import parse
from supabase import create_client

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
if "docs_synced" not in st.session_state:
    st.session_state.docs_synced = False
if "supabase" not in st.session_state:
    st.session_state.supabase = None
if "supabase_ok" not in st.session_state:
    st.session_state.supabase_ok = False

# ========== 新增：Dify 相关状态 ==========
if "dify_conv_id" not in st.session_state:
    st.session_state.dify_conv_id = ""
if "dify_api_key" not in st.session_state:
    st.session_state.dify_api_key = ""

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
        import login
        login.show_login_page()
        return
    
    # ========== 已登录：根据角色初始化不同的服务 ==========
    
    # 1. 读取 Dify API Key（所有用户都需要）
    if not st.session_state.dify_api_key:
        st.session_state.dify_api_key = st.secrets.get("DIFY_API_KEY", "")
    
    # 2. 只有管理员才需要 Supabase（学生管理、文档管理）
    if st.session_state.user_role == "admin" and not st.session_state.supabase_ok:
        try:
            SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
            SUPABASE_KEY = st.secrets.get("SUPABASE_SERVICE_KEY", "")
            
            if SUPABASE_URL and SUPABASE_KEY:
                st.session_state.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                st.session_state.supabase_ok = True
            else:
                st.warning("⚠️ Supabase 配置缺失，管理员功能可能不可用")
        except Exception as e:
            st.error(f"Supabase 初始化失败: {e}")
            st.session_state.supabase = None
            st.session_state.supabase_ok = False
    
    # ========== 同步文档（仅管理员且 Supabase 可用时）==========
    if (st.session_state.user_role == "admin" and 
        not st.session_state.docs_synced and 
        st.session_state.supabase_ok):
        try:
            import load_docs
            with st.spinner("📚 正在同步学校文档..."):
                load_docs.load_documents(st.session_state.supabase)
                st.session_state.docs_synced = True
        except Exception as e:
            st.warning(f"文档同步失败: {e}")
            st.session_state.docs_synced = True
    
    # ========== 显示用户信息 ==========
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
            import login
            login.logout()
            st.rerun()
    
    st.markdown("---")
    
    # ========== 根据角色显示不同界面 ==========
    if st.session_state.user_role == "admin":
        import admin_panel
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
