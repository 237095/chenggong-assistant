"""
登录模块 - 成工职小助手
成都工业职业技术学院
"""

import streamlit as st
import random
import hashlib
import json
import os
from datetime import datetime, timedelta

# ========== 用户数据存储文件 ==========
USER_DATA_FILE = "users.json"

def load_users():
    """加载用户数据"""
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """保存用户数据"""
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def init_default_users():
    """初始化默认用户"""
    users = load_users()
    
    # 管理员账号
    if "admin" not in users:
        users["admin"] = {
            "role": "admin",
            "name": "管理员",
            "password_hash": hashlib.sha256("123456".encode()).hexdigest(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    # 示例学生账号
    demo_students = [
        {"phone": "13800138000", "name": "张三", "student_id": "2024001"},
        {"phone": "13900139000", "name": "李四", "student_id": "2024002"},
        {"phone": "13700137000", "name": "王五", "student_id": "2024003"}
    ]
    
    for student in demo_students:
        if student["phone"] not in users:
            users[student["phone"]] = {
                "role": "student",
                "name": student["name"],
                "phone": student["phone"],
                "student_id": student["student_id"],
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    save_users(users)

# 初始化默认用户
init_default_users()

def show_login_page():
    """显示登录页面，返回登录是否成功"""
    
    # 初始化登录相关状态
    if "login_error" not in st.session_state:
        st.session_state.login_error = None
    if "verification_code" not in st.session_state:
        st.session_state.verification_code = {}
    
    # 登录页面CSS
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
        
        .success-msg {
            background: #dcfce7;
            color: #16a34a;
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
    
    # 登录方式切换
    login_tab = st.radio(
        "选择登录方式",
        ["👨‍🎓 学生登录", "👨‍💼 管理员登录"],
        horizontal=True,
        label_visibility="collapsed",
        key="login_tab"
    )
    
    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
    
    # 显示错误信息
    if st.session_state.login_error:
        st.markdown(f'<div class="error-msg">⚠️ {st.session_state.login_error}</div>', unsafe_allow_html=True)
    
    # ========== 学生登录 ==========
    if login_tab == "👨‍🎓 学生登录":
        phone = st.text_input("📱 手机号", placeholder="请输入11位手机号", key="student_phone")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            verification_code = st.text_input("📧 验证码", placeholder="请输入6位验证码", key="student_code")
        with col2:
            if st.button("获取验证码", key="get_code"):
                if phone and len(phone) == 11 and phone.isdigit():
                    code = generate_verification_code(phone)
                    st.markdown(f'<div class="success-msg">✅ 验证码：{code}</div>', unsafe_allow_html=True)
                else:
                    st.session_state.login_error = "请输入正确的手机号"
                    st.rerun()
        
        if st.button("登 录", key="student_login_btn"):
            success = student_login(phone, verification_code)
            if success:
                st.rerun()
    
    # ========== 管理员登录 ==========
    else:
        admin_username = st.text_input("👤 用户名", placeholder="请输入用户名", key="admin_user")
        admin_password = st.text_input("🔒 密码", type="password", placeholder="请输入密码", key="admin_pass")
        
        if st.button("登 录", key="admin_login_btn"):
            success = admin_login(admin_username, admin_password)
            if success:
                st.rerun()
    
    # 演示账号提示
    with st.expander("📋 演示账号"):
        st.markdown("""
        **管理员账号：**
        - 用户名：`admin`
        - 密码：`123456`
        
        **学生账号（验证码登录）：**
        - `13800138000`（张三）
        - `13900139000`（李四）
        - `13700137000`（王五）
        
        > 验证码为6位数字，点击获取验证码后会显示
        """)
    
    st.markdown(f"""
    <div class="school-badge">
        {datetime.now().strftime('%Y年%m月%d日')}<br>
        立德树人 精工强技
    </div>
    </div>
    """, unsafe_allow_html=True)

def generate_verification_code(phone):
    """生成验证码（模拟）"""
    code = str(random.randint(100000, 999999))
    if "verification_codes" not in st.session_state:
        st.session_state.verification_codes = {}
    st.session_state.verification_codes[phone] = {
        "code": code,
        "expires_at": datetime.now() + timedelta(minutes=5)
    }
    return code

def verify_code(phone, code):
    """验证验证码"""
    if "verification_codes" not in st.session_state:
        return False
    if phone not in st.session_state.verification_codes:
        return False
    
    code_data = st.session_state.verification_codes[phone]
    if datetime.now() > code_data["expires_at"]:
        del st.session_state.verification_codes[phone]
        return False
    
    if code_data["code"] == code:
        del st.session_state.verification_codes[phone]
        return True
    
    return False

def student_login(phone, verification_code):
    """学生手机验证码登录"""
    if not phone or not verification_code:
        st.session_state.login_error = "请填写手机号和验证码"
        return False
    
    if len(phone) != 11 or not phone.isdigit():
        st.session_state.login_error = "请输入正确的11位手机号"
        return False
    
    if not verify_code(phone, verification_code):
        st.session_state.login_error = "验证码错误或已过期"
        return False
    
    users = load_users()
    if phone in users and users[phone]["role"] == "student":
        st.session_state.logged_in = True
        st.session_state.user_role = "student"
        st.session_state.user_name = users[phone]["name"]
        st.session_state.user_id = phone
        st.session_state.login_error = None
        return True
    else:
        # 新用户自动注册
        users[phone] = {
            "role": "student",
            "name": f"同学{phone[-4:]}",
            "phone": phone,
            "student_id": f"AUTO{int(datetime.now().timestamp())}",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_users(users)
        
        st.session_state.logged_in = True
        st.session_state.user_role = "student"
        st.session_state.user_name = users[phone]["name"]
        st.session_state.user_id = phone
        st.session_state.login_error = None
        return True

def admin_login(username, password):
    """管理员账号密码登录"""
    if not username or not password:
        st.session_state.login_error = "请填写用户名和密码"
        return False
    
    users = load_users()
    if username in users and users[username]["role"] == "admin":
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if users[username]["password_hash"] == password_hash:
            st.session_state.logged_in = True
            st.session_state.user_role = "admin"
            st.session_state.user_name = users[username]["name"]
            st.session_state.user_id = username
            st.session_state.login_error = None
            return True
    
    st.session_state.login_error = "用户名或密码错误"
    return False

def logout():
    """退出登录"""
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.user_id = None
    st.session_state.login_error = None

def check_login_status():
    """检查登录状态"""
    return st.session_state.get("logged_in", False)

def get_current_user():
    """获取当前用户信息"""
    return {
        "role": st.session_state.get("user_role"),
        "name": st.session_state.get("user_name"),
        "id": st.session_state.get("user_id")
    }
