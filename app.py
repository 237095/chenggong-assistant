"""
成工职小助手 - 主入口
成都工业职业技术学院
"""

import streamlit as st
from user_agents import parse

# ========== 初始化登录状态（不导入 student_manager）==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:"""
成工职小助手 - 主入口
成都工业职业技术学院
"""

import streamlit as st
from user_agents import parse

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
    
    # ========== 已登录：同步文档（增量更新）==========
    import load_docs
    
    with st.spinner("📚 正在同步学校文档..."):
        load_docs.load_documents()
    
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
        # 学生：显示聊天界面，检测设备类型
        user_agent_string = st.context.headers.get('User-Agent', '')
        user_agent = parse(user_agent_string)
        
        try:
            if user_agent.is_mobile:
                # 手机端
                with open("mobile_app.py", "r", encoding="utf-8") as f:
                    exec(f.read(), globals())
            else:
                # 电脑端
                with open("desktop_app.py", "r", encoding="utf-8") as f:
                    exec(f.read(), globals())
        except FileNotFoundError as e:
            st.error(f"文件加载失败: {e}")
            st.info("请确保 mobile_app.py 和 desktop_app.py 文件在相同目录下")
        except Exception as e:
            st.error(f"加载界面时出错: {e}")

if __name__ == "__main__":
    main()
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
        # 延迟导入 login 模块
        import login
        login.show_login_page()
        return
    
    # 已登录：加载文档（仅首次）
    if not st.session_state.docs_loaded:
        with st.spinner("📚 正在加载学校文档到知识库，请稍候..."):
            try:
                import load_docs
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
            import login
            login.logout()
            st.rerun()
    
    st.markdown("---")
    
    # 根据角色显示不同界面
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
