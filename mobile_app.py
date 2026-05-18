"""
成工职小助手 - 手机端版
成都工业职业技术学院
"""

import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import base64
from PIL import Image
import requests
from bs4 import BeautifulSoup

# 尝试导入联网搜索
try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

# ========== 配置 ==========
DEEPSEEK_API_KEY = "sk-a79bb0ea54fb499eb301759f8f0a3924"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# ========== 学校信息 ==========
SCHOOL_NAME = "成都工业职业技术学院"
SCHOOL_MOTTO = "立德树人 精工强技"
SCHOOL_OFFICIAL_URL = "https://www.cdivtc.edu.cn"  
COURSE_SYSTEM_URL = "http://sw.cdivtc.edu.cn/app-web/#/login"

# ========== 页面配置（手机端）==========
st.set_page_config(
    page_title=f"{SCHOOL_NAME} - 成工职小助手",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ========== 检查校徽 ==========
logo_files = ["school_logo.png", "logo.png", "校徽.png"]
LOGO_PATH = None
for f in logo_files:
    if os.path.exists(f):
        LOGO_PATH = f
        break

# ========== 人格设定 ==========
PERSONAS = {
    "longbiao": {"name": "尔主龙彪", "avatar": "👨‍💻", "style": "技术控", "greeting": "我来帮你分析..."},
    "qianpeng": {"name": "任乾鹏", "avatar": "📊", "style": "细心", "greeting": "数据显示..."},
    "tongyan": {"name": "童妍", "avatar": "👩‍💻", "style": "热情", "greeting": "成工生活我超熟！"},
}

def select_persona(question):
    q = question.lower()
    if any(word in q for word in ["python", "java", "代码"]):
        return "longbiao"
    elif any(word in q for word in ["成绩", "课表"]):
        return "qianpeng"
    else:
        return "tongyan"

def get_persona_prefix(persona_key):
    persona = PERSONAS[persona_key]
    return f"**{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}** {persona['avatar']}\n> *{persona['greeting']}*\n\n"

def get_system_prompt(persona_key):
    persona = PERSONAS[persona_key]
    return f"你是{SCHOOL_NAME}小助手{persona['name']}，{persona['style']}，说话温暖亲切。"

LOCAL_KNOWLEDGE = {
    "图书馆": "📚 开放时间：周一至周五 8:00-22:00，周末 9:00-21:00",
    "食堂": "🍽️ 早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n🍜 推荐：二食堂牛肉面",
    "课表": f"📅 教务系统：{COURSE_SYSTEM_URL}",
    "成绩": f"📊 教务系统：{COURSE_SYSTEM_URL}",
}

def get_local_answer(question):
    q = question.lower()
    for key, answer in LOCAL_KNOWLEDGE.items():
        if key in q:
            return answer
    return None

def call_deepseek(messages, persona_key, use_thinking=False):
    full_messages = [{"role": "system", "content": get_system_prompt(persona_key)}]
    if use_thinking:
        full_messages.append({"role": "user", "content": "请展示思考过程。"})
    full_messages.extend(messages[-15:])
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            temperature=0.8,
            max_tokens=1500,
            timeout=30
        )
        return response.choices[0].message.content
    except:
        return None

def get_ai_response(user_input, persona_key, enable_thinking):
    lower = user_input.lower()
    if any(word in lower for word in ["热点", "热搜"]):
        return "🔥 当前热点趋势：AI技术、就业政策、校园活动等。详见百度热搜官网。"
    if any(word in lower for word in ["课表", "成绩"]):
        local = get_local_answer(user_input)
        if local:
            return local
    response = call_deepseek([{"role": "user", "content": user_input}], persona_key, enable_thinking)
    if response:
        return response
    local = get_local_answer(user_input)
    return local if local else f"抱歉，无法回答「{user_input}」。\n试试问：图书馆几点开门？"

# ========== 手机端CSS ==========
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp {background: #f5f7fb;}
    
    .main .block-container {
        padding: 0.5rem 0.8rem 80px 0.8rem !important;
        max-width: 100% !important;
    }
    
    /* 隐藏侧边栏 */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* 快捷按钮 */
    .quick-buttons {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 1rem;
        justify-content: center;
    }
    
    .quick-btn {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 30px;
        padding: 6px 14px;
        font-size: 0.75rem;
        cursor: pointer;
    }
    
    .quick-btn:active {
        background: #1a4d8c;
        color: white;
    }
    
    /* 消息气泡 */
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
        padding: 10px 14px !important;
        font-size: 0.85rem !important;
        max-width: 85% !important;
    }
    
    [data-testid="stChatMessage"][data-testid="user"] [data-testid="stMarkdown"] {
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        color: white;
    }
    
    [data-testid="stChatMessage"][data-testid="assistant"] [data-testid="stMarkdown"] {
        background: white;
        color: #333;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* 底部输入框 */
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px 12px;
        border-top: 1px solid #e0e0e0;
        z-index: 100;
    }
    
    .stChatInput textarea {
        border-radius: 25px !important;
        border: 1px solid #ddd !important;
        padding: 10px 16px !important;
        font-size: 0.85rem !important;
    }
    
    /* 底部导航栏 */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        display: flex;
        justify-content: space-around;
        padding: 8px 12px;
        padding-bottom: calc(8px + env(safe-area-inset-bottom));
        border-top: 1px solid #e0e0e0;
        z-index: 99;
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        color: #888;
        font-size: 0.65rem;
        flex: 1;
        text-align: center;
        background: none;
        border: none;
        cursor: pointer;
    }
    
    .nav-item:active {
        color: #1a4d8c;
    }
    
    .nav-icon {
        font-size: 1.2rem;
    }
    
    /* 可折叠区域 */
    .streamlit-expanderHeader {
        font-size: 0.8rem;
    }
</style>

<!-- 快捷按钮 -->
<div class="quick-buttons">
    <span class="quick-btn" onclick="sendMsg('图书馆几点开门？')">📚 图书馆</span>
    <span class="quick-btn" onclick="sendMsg('食堂有什么好吃的？')">🍽️ 食堂</span>
    <span class="quick-btn" onclick="sendMsg('课表查询')">📅 课表</span>
    <span class="quick-btn" onclick="sendMsg('成绩查询')">📊 成绩</span>
    <span class="quick-btn" onclick="sendMsg('今日热点')">🔥 热点</span>
</div>

<!-- 底部导航栏 -->
<div class="bottom-nav">
    <button class="nav-item" onclick="sendMsg('图书馆几点开门？')">
        <span class="nav-icon">📚</span>
        <span>图书馆</span>
    </button>
    <button class="nav-item" onclick="sendMsg('课表查询')">
        <span class="nav-icon">📅</span>
        <span>课表</span>
    </button>
    <button class="nav-item" onclick="sendMsg('成绩查询')">
        <span class="nav-icon">📊</span>
        <span>成绩</span>
    </button>
    <button class="nav-item" onclick="sendMsg('今日热点')">
        <span class="nav-icon">🔥</span>
        <span>热搜</span>
    </button>
    <button class="nav-item" onclick="sendMsg('食堂有什么好吃的？')">
        <span class="nav-icon">🍽️</span>
        <span>食堂</span>
    </button>
</div>

<script>
function sendMsg(msg) {
    const input = document.querySelector('.stChatInput textarea');
    if (input) {
        input.value = msg;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        const btn = document.querySelector('.stChatInput button');
        if (btn) btn.click();
    }
}
</script>
""", unsafe_allow_html=True)

# ========== 侧边栏（手机端隐藏）==========
# 手机端不显示侧边栏，设置放在可折叠区域

# ========== 初始化 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"# 🎓 {SCHOOL_NAME}\n\n你好！我是AI助手：\n- 👨‍💻 **尔主龙彪学长**：AI、编程\n- 📊 **任乾鹏学长**：成绩、课表\n- 👩‍💻 **童妍学姐**：校园生活\n\n**试试问：**\n- \"图书馆几点开门？\"\n- \"课表查询\""
    })

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 高级设置（可折叠）
with st.expander("⚙️ 高级设置"):
    enable_thinking = st.checkbox("🧠 深度思考模式", value=False)
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 输入框
user_input = st.chat_input("输入你的问题...")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            persona = select_persona(user_input)
            prefix = get_persona_prefix(persona)
            response = get_ai_response(user_input, persona, enable_thinking)
            st.markdown(prefix + response)
            st.session_state.messages.append({"role": "assistant", "content": prefix + response})
    st.rerun()
