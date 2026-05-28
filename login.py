"""
登录模块 - 成工职小助手
使用 students_id.py 存储学生信息
"""

import streamlit as st
import hashlib
from datetime import datetime
from openai import OpenAI

# 导入 RAG 检索模块
import rag_search

# ========== 配置（从 Secrets 读取 API Key）==========
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

if not DEEPSEEK_API_KEY:
    st.error("❌ 配置错误：请在 Streamlit Secrets 中配置 DEEPSEEK_API_KEY")
    st.stop()

# 创建 OpenAI 客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# ========== 人格设定 ==========
PERSONAS = {
    "longbiao": {
        "name": "尔主龙彪",
        "avatar": "👨‍💻",
        "greeting": "这个问题我来帮你分析一下...",
    },
    "qianpeng": {
        "name": "任乾鹏",
        "avatar": "📊",
        "greeting": "据我整理的数据显示...",
    },
    "tongyan": {
        "name": "童妍",
        "avatar": "👩‍💻",
        "greeting": "成工生活我超熟的！",
    }
}

def get_system_prompt(persona_key):
    """精简版系统提示词"""
    persona = PERSONAS[persona_key]
    return f"你是成都工业职业技术学院的AI助手{persona['name']}。说话亲切温暖，帮助解答问题。"

# ========== 导入学生数据 ==========
try:
    from students_id import STUDENTS
except ImportError:
    # 如果文件不存在，创建默认数据
    STUDENTS = {
        "2024001": {"name": "张三", "password": "237095", "student_id": "2024001"},
        "2024002": {"name": "李四", "password": "237095", "student_id": "2024002"},
        "2024003": {"name": "王五", "password": "237095", "student_id": "2024003"},
        "2024004": {"name": "赵六", "password": "237095", "student_id": "2024004"},
        "2024005": {"name": "小明", "password": "237095", "student_id": "2024005"},
    }

# 管理员配置
ADMIN = {
    "username": "admin",
    "password": "123456",
    "name": "系统管理员"
}

def hash_password(password):
    """密码加密"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_student(student_id, password):
    """验证学生登录"""
    if student_id in STUDENTS:
        student = STUDENTS[student_id]
        if student.get("password") == password:
            return {
                "role": "student",
                "name": student["name"],
                "user_id": student_id,
                "student_id": student_id
            }
    return None

def verify_admin(username, password):
    """验证管理员登录"""
    if username == ADMIN["username"] and password == ADMIN["password"]:
        return {
            "role": "admin",
            "name": ADMIN["name"],
            "user_id": username
        }
    return None

# ========== AI 调用函数（支持 RAG）==========
def call_deepseek(messages, persona_key, use_thinking=False, search_context=None, enable_rag=True):
    """调用 DeepSeek API - 支持 RAG 检索增强"""
    
    system_prompt = get_system_prompt(persona_key)
    
    # 获取用户最新问题
    user_query = messages[-1]["content"] if messages else ""
    
    # RAG 检索
    rag_context = ""
    if enable_rag and user_query:
        try:
            similar_docs = rag_search.search_similar_documents(user_query, match_count=3)
            if similar_docs:
                rag_context = "\n\n📚 **学校官方参考资料**：\n\n"
                for i, doc in enumerate(similar_docs, 1):
                    rag_context += f"【{doc.get('title', '文档')}】\n{doc.get('content', '')[:500]}...\n\n"
        except Exception as e:
            print(f"RAG检索失败: {e}")
    
    full_messages = [{"role": "system", "content": system_prompt}]
    
    if use_thinking:
        full_messages.append({"role": "user", "content": "请先展示你的💭思考过程，再给出最终答案。"})
    
    if search_context:
        full_messages.append({"role": "user", "content": f"🌐 联网搜索结果：\n{search_context}"})
    
    if rag_context:
        full_messages.append({"role": "user", "content": f"📖 学校官方资料：\n{rag_context}"})
    
    full_messages.extend(messages)
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            temperature=0.7,
            max_tokens=2000,
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

# ========== 登录页面 ==========
def show_login_page():
    """显示登录页面"""
    
    # 初始化错误信息
    if "login_error" not in st.session_state:
        st.session_state.login_error = None
    
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
    
    # 学生登录
    if login_tab == "👨‍🎓 学生登录":
        student_id = st.text_input("📚 学号", placeholder="请输入学号（如：2024001）", key="student_id_input")
        student_password = st.text_input("🔒 密码", type="password", placeholder="请输入密码（默认：237095）", key="student_password")
        
        if st.button("登 录", key="student_login_btn"):
            if not student_id or not student_password:
                st.session_state.login_error = "请填写学号和密码"
            else:
                user = verify_student(student_id, student_password)
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
    
    # 管理员登录
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
    
    # 演示账号提示
    with st.expander("📋 登录说明"):
        st.markdown("""
        **学生登录：**
        - 使用**学号**登录
        - 默认密码：`237095`
        
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
    """退出登录"""
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.session_state.user_name = None
    st.session_state.user_id = None
    st.session_state.user_student_id = None
    st.session_state.login_error = None
