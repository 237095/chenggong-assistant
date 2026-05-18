"""
成工职小助手 - 电脑端版
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

# ========== 页面配置 ==========
st.set_page_config(
    page_title=f"{SCHOOL_NAME} - 成工职小助手",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 检查校徽 ==========
logo_files = ["school_logo.png", "logo.png", "校徽.png"]
LOGO_PATH = None
for f in logo_files:
    if os.path.exists(f):
        LOGO_PATH = f
        break

# ========== 三位学长学姐的人格设定 ==========
PERSONAS = {
    "longbiao": {
        "name": "尔主龙彪",
        "avatar": "👨‍💻",
        "style": "技术控、逻辑清晰",
        "greeting": "这个问题我来帮你分析一下...",
    },
    "qianpeng": {
        "name": "任乾鹏",
        "avatar": "📊",
        "style": "细心、严谨",
        "greeting": "据我整理的数据显示...",
    },
    "tongyan": {
        "name": "童妍",
        "avatar": "👩‍💻",
        "style": "热情、细心", 
        "greeting": "成工生活我超熟的！",
    }
}

def select_persona(question):
    q = question.lower()
    if any(word in q for word in ["python", "java", "html", "代码"]):
        return "longbiao"
    elif any(word in q for word in ["成绩", "绩点", "课表"]):
        return "qianpeng"
    else:
        return "tongyan"

def get_persona_prefix(persona_key):
    persona = PERSONAS[persona_key]
    return f"**{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}** {persona['avatar']}\n\n> *{persona['greeting']}*\n\n"

def get_system_prompt(persona_key):
    persona = PERSONAS[persona_key]
    return f"""你是"{SCHOOL_NAME}的成工职小助手"，你是{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}。

人格特质：{persona['style']}，说话温暖亲切。重要信息用**加粗**。"""

# ========== 本地知识库 ==========
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
    full_messages.extend(messages[-20:])
    
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
        return "🔥 当前热点：AI技术发展、新能源突破、就业政策等。详情可查看百度热搜官网。"
    
    if any(word in lower for word in ["课表", "成绩"]):
        local = get_local_answer(user_input)
        if local:
            return local
    
    response = call_deepseek([{"role": "user", "content": user_input}], persona_key, enable_thinking)
    if response:
        return response
    local = get_local_answer(user_input)
    return local if local else f"抱歉，无法回答「{user_input}」。"

# ========== 电脑端CSS ==========
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp {background: #fafafc;}
    
    .main .block-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 1rem 2rem 5rem 2rem;
    }
    
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e6e6e6;
        width: 280px;
    }
    
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
        padding: 12px 18px;
        border-radius: 20px;
        font-size: 0.95rem;
    }
    
    [data-testid="stChatMessage"][data-testid="user"] [data-testid="stMarkdown"] {
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        color: white;
    }
    
    [data-testid="stChatMessage"][data-testid="assistant"] [data-testid="stMarkdown"] {
        background: white;
        color: #333;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    .stChatInput textarea {
        border-radius: 28px !important;
        border: 1px solid #ddd !important;
        padding: 12px 20px !important;
    }
</style>
""", unsafe_allow_html=True)

# ========== 侧边栏 ==========
with st.sidebar:
    if LOGO_PATH:
        try:
            st.image(Image.open(LOGO_PATH), width=100)
        except:
            st.markdown("## 🎓")
    else:
        st.markdown("## 🎓")
    
    st.markdown(f"### {SCHOOL_NAME}")
    st.markdown(f"*{SCHOOL_MOTTO}*")
    st.markdown("---")
    
    enable_thinking = st.toggle("🧠 深度思考模式", value=False)
    
    st.markdown("---")
    st.markdown(f"[🏫 学校官网]({SCHOOL_OFFICIAL_URL})")
    st.markdown(f"[📚 教务系统]({COURSE_SYSTEM_URL})")
    st.markdown("---")
    
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 👥 开发团队")
    st.markdown("- 尔主龙彪（组长）")
    st.markdown("- 任乾鹏")
    st.markdown("- 童妍")

# ========== 初始化 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"# 🎓 {SCHOOL_NAME} - 成工职小助手\n\n你好！我是AI助手：\n- 👨‍💻 **尔主龙彪学长**：AI、编程\n- 📊 **任乾鹏学长**：成绩、课表\n- 👩‍💻 **童妍学姐**：校园生活\n\n**试试问：**\n- \"图书馆几点开门？\"\n- \"课表查询\"\n- \"我的成绩\"\n- \"今天有什么热点？\""
    })

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 快捷按钮
quick_cols = st.columns(5)
quick_list = ["📚 图书馆", "🍽️ 食堂", "📅 课表", "📊 成绩", "🔥 热点"]

for idx, q in enumerate(quick_list):
    with quick_cols[idx]:
        if st.button(q, use_container_width=True):
            full_q = {"📚 图书馆": "图书馆几点开门？", "🍽️ 食堂": "食堂有什么好吃的？", 
                      "📅 课表": "课表查询", "📊 成绩": "成绩查询", "🔥 热点": "今日热点"}.get(q, q)
            with st.chat_message("user"):
                st.markdown(full_q)
            st.session_state.messages.append({"role": "user", "content": full_q})
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    persona = select_persona(full_q)
                    prefix = get_persona_prefix(persona)
                    response = get_ai_response(full_q, persona, enable_thinking)
                    st.markdown(prefix + response)
                    st.session_state.messages.append({"role": "assistant", "content": prefix + response})
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
