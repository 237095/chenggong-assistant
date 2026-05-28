"""
登录模块 - 学生用 Supabase，管理员用本地验证
"""

import streamlit as st
from datetime import datetime
import student_manager

ADMIN = {
    "username": "admin",
    "password": "123456",
    "name": "系统管理员"
}

def verify_admin(username: str, password: str):
    if username == ADMIN["username"] and password == ADMIN["password"]:
        return {
            "role": "admin",
            "name": ADMIN["name"],
            "user_id": username
        }
    return None

def show_login_page():
    if "login_error" not in st.session_state:
        st.session_state.login_error = None
    
    st.markdown("""
    <style>
        #MainMenu, header, footer {visibility: hidden; display: none;}
        .stApp {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);}
        .main .block-container {
            padding: 2rem 1.5rem !important;
            max-width: 450px !important;
            margin: 0 auto !important;
        }
        .login-card {
            background: white;
            border-radius: 24px;
            padding: 32px 24px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }
        .logo-area {
            text-align: center;
            margin-bottom: 24px;
        }
        .logo-icon {
            font-size: 64px;
            background: linear-gradient(135deg, #1a4d8c, #2d6a4f);
            width: 80px;
            height: 80px;
            border-radius: 40px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .title {
            text-align: center;
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 8px;
        }
        .subtitle {
            text-align: center;
            font-size: 0.8rem;
            color: #666;
            margin-bottom: 28px;
        }
        .error-msg {
            background: #fee2e2;
            color: #dc2626;
            padding: 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            margin-bottom: 16px;
            text-align: center;
        }
        .school-badge {
            text-align: center;
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid #e8e8e8;
            font-size: 0.7rem;
            color: #999;
        }
        .stButton button {
            width: 100%;
            background: linear-gradient(135deg, #1a4d8c, #2d6a4f);
            color: white;
            border: none;
            padding: 10px;
            border-radius: 30px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        .stTextInput input {
            border-radius: 30px;
            border: 1px solid #ddd;
            padding: 10px 16px;
        }
        .stRadio > div {
            display: flex;
            gap: 16px;
            justify-content: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="login-card">
        <div class="logo-area">
            <div class="logo-icon">🎓</div>
        </div>
        <div class="title">成工职小助手</div>
        <div class="subtitle">成都工业职业技术学院 · 智能客服系统</div>
    """, unsafe_allow_html=True)
    
    login_tab = st.radio(
        "选择登录方式",
        ["👨‍🎓 学生登录", "👨‍💼 管理员登录"],
        horizontal=True,
        label_visibility="collapsed",
        key="login_tab"
    )
    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    if st.session_state.login_error:
        st.markdown(f'<div class="error-msg">⚠️ {st.session_state.login_error}</div>', unsafe_allow_html=True)
    
    if login_tab == "👨‍🎓 学生登录":
        student_id = st.text_input("📚 学号", placeholder="请输入学号（如：2024001）", key="student_id_input")
        student_password = st.text_input("🔒 密码", type="password", placeholder="请输入密码（默认：237095）", key="student_password")
        
        if st.button("登 录", key="student_login_btn"):
            if not student_id or not student_password:
                st.session_state.login_error = "请填写学号和密码"
            else:
                user = student_manager.verify_student(student_id, student_password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "student"
                    st.session_state.user_name = user["name"]
                    st.session_state.user_id = user["user_id"]
                    st.session_state.user_student_id = user["student_id"]
                    st.session_state.login_error = None
                    st.rerun()
                else:
                    st.session_state.login_error = "学号或密码错误"
    
    else:
        admin_username = st.text_input("👤 用户名", placeholder="请输入用户名", key="admin_user")
        admin_password = st.text_input("🔒 密码", type="password", placeholder="请输入密码", key="admin_pass")
        
        if st.button("登 录", key="admin_login_btn"):
            if not admin_username or not admin_password:
                st.session_state.login_error = "请填写用户名和密码"
            else:
                user = verify_admin(admin_username, admin_password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_role = "admin"
                    st.session_state.user_name = user["name"]
                    st.session_state.user_id = user["user_id"]
                    st.session_state.login_error = None
                    st.rerun()
                else:
                    st.session_state.login_error = "用户名或密码错误"
    
    with st.expander("📋 登录说明"):
        st.markdown("""
        **学生登录：**
        - 使用**学号**登录
        - 默认密码：`237095`
        - 示例学号：`2024001`, `2024002`, `2024003`
        
        **管理员登录：**
        - 用户名：`admin`
        - 密码：`123456`
        """)
    
    st.markdown(f"""
    <div class="school-badge">
        {datetime.now().strftime('%Y年%m月%d日')}<br>
        立德树人 精工强技
    </div>
    </div>
    """, unsafe_allow_html=True)

def logout():
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.user_id = None
    st.session_state.user_student_id = None
    st.session_state.login_error = None
