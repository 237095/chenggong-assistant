"""
成工职小助手 - 手机端
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
    page_title=SCHOOL_NAME,
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

LOGO_BASE64 = None
if LOGO_PATH and os.path.exists(LOGO_PATH):
    try:
        with open(LOGO_PATH, "rb") as img_file:
            LOGO_BASE64 = base64.b64encode(img_file.read()).decode()
    except:
        pass

# ========== 热点功能 ==========
def get_ai_hot_trending(user_query):
    prompt = f"请回答当前网络热点话题，列出8-10个，用🔥📈标记热度：{user_query}"
    response = call_deepseek([{"role": "user", "content": prompt}], "tongyan", False, None)
    return response if response else "🔥 查看百度热搜：https://top.baidu.com"

# ========== 官网新闻 ==========
def fetch_news_from_website():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, 'html.parser')
        news = []
        for link in soup.find_all('a', href=True):
            title = link.get_text(strip=True)
            if len(title) > 8 and any(w in title for w in ['通知', '公告']):
                news.append(title)
                if len(news) >= 3:
                    break
        return news
    except:
        return None

# ========== 人格设定 ==========
PERSONAS = {
    "longbiao": {"name": "尔主龙彪", "avatar": "👨‍💻", "greeting": "我来帮你分析"},
    "qianpeng": {"name": "任乾鹏", "avatar": "📊", "greeting": "数据显示"},
    "tongyan": {"name": "童妍", "avatar": "👩‍💻", "greeting": "成工生活我超熟"},
}

def select_persona(question):
    q = question.lower()
    if any(w in q for w in ["python", "java", "代码"]):
        return "longbiao"
    elif any(w in q for w in ["成绩", "课表"]):
        return "qianpeng"
    return "tongyan"

def get_persona_prefix(key):
    p = PERSONAS[key]
    return f"**{p['name']}{'学长' if key != 'tongyan' else '学姐'}** {p['avatar']}\n\n"

def get_system_prompt(key):
    p = PERSONAS[key]
    return f"你是{SCHOOL_NAME}小助手{p['name']}，说话温暖亲切。"

# ========== 知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 周一至周五 8:00-22:00，周末 9:00-21:00",
    "食堂": "🍽️ 早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30，推荐二食堂牛肉面",
    "课表": f"📅 [教务系统]({COURSE_SYSTEM_URL})",
    "成绩": f"📊 [教务系统]({COURSE_SYSTEM_URL})",
    "官网": f"🌐 [学校官网]({SCHOOL_OFFICIAL_URL})",
}

def get_local_answer(question):
    q = question.lower()
    for key, ans in LOCAL_KNOWLEDGE.items():
        if key in q:
            return ans
    return None

# ========== AI调用 ==========
def call_deepseek(messages, persona_key, use_thinking, search_context):
    full = [{"role": "system", "content": get_system_prompt(persona_key)}]
    if use_thinking:
        full.append({"role": "user", "content": "展示思考过程"})
    if search_context:
        full.append({"role": "user", "content": f"参考：{search_context}"})
    full.extend(messages[-15:])
    try:
        r = client.chat.completions.create(model="deepseek-chat", messages=full, temperature=0.8, max_tokens=1500, timeout=30)
        return r.choices[0].message.content
    except:
        return None

# ========== 回复函数 ==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    if any(w in lower for w in ["热点", "热搜", "今日热点"]):
        return get_ai_hot_trending(user_input)
    
    local = get_local_answer(user_input)
    if local:
        return local
    
    if any(w in lower for w in ["新闻", "通知"]):
        news = fetch_news_from_website()
        if news:
            return "📢 最新通知：\n" + "\n".join([f"• {n}" for n in news])
        return f"📢 [通知公告]({SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm)"
    
    search_ctx = None
    if enable_search and SEARCH_AVAILABLE:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(user_input, max_results=2))
                if results:
                    search_ctx = "\n".join([f"- {r['title']}" for r in results])
        except:
            pass
    
    history = st.session_state.messages[-15:] if len(st.session_state.messages) > 15 else st.session_state.messages
    msgs = [{"role": m["role"], "content": m["content"]} for m in history]
    resp = call_deepseek(msgs, persona_key, enable_thinking, search_ctx)
    
    if resp:
        return resp
    return f"抱歉，无法回答。试试问：图书馆几点开门？"

# ========== UI ==========
st.markdown(f"""
<style>
    #MainMenu, header, footer {{visibility: hidden;}}
    .stApp {{background: #f5f7fb;}}
    .main .block-container {{padding: 0.5rem 0.8rem 70px 0.8rem !important; max-width: 100% !important;}}
    [data-testid="stSidebar"] {{display: none !important;}}
    
    /* 顶部栏 */
    .top-bar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: white;
        padding: 10px 16px;
        border-radius: 30px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .logo-area {{display: flex; align-items: center; gap: 10px;}}
    .logo-img {{width: 40px; height: 40px; border-radius: 50%; object-fit: cover;}}
    .logo-text {{font-size: 0.9rem; font-weight: 600; color: #1a4d8c;}}
    
    /* 快捷按钮 */
    .quick-btns {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 12px;
        justify-content: center;
    }}
    .quick-btn {{
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 30px;
        padding: 6px 14px;
        font-size: 0.7rem;
        cursor: pointer;
    }}
    .quick-btn:active {{background: #1a4d8c; color: white;}}
    
    /* 消息 */
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {{
        padding: 10px 14px !important;
        font-size: 0.85rem !important;
        max-width: 85% !important;
    }}
    [data-testid="stChatMessage"][data-testid="user"] [data-testid="stMarkdown"] {{
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        color: white;
        border-radius: 18px 18px 4px 18px !important;
    }}
    [data-testid="stChatMessage"][data-testid="assistant"] [data-testid="stMarkdown"] {{
        background: white;
        border-radius: 18px 18px 18px 4px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    
    /* 输入框 */
    .stChatInput {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px 12px;
        border-top: 1px solid #e8e8e8;
        z-index: 100;
    }}
    .stChatInput textarea {{
        border-radius: 25px !important;
        border: 1px solid #ddd !important;
        padding: 10px 16px !important;
        font-size: 0.85rem !important;
    }}
    
    /* 折叠菜单 */
    .streamlit-expanderHeader {{
        font-size: 0.7rem;
        background: white;
        border-radius: 20px;
    }}
</style>

<div class="top-bar">
    <div class="logo-area">
        {f'<img src="data:image/png;base64,{LOGO_BASE64}" class="logo-img">' if LOGO_BASE64 else '<span style="font-size: 32px;">🎓</span>'}
        <span class="logo-text">{SCHOOL_NAME}</span>
    </div>
    <div>🎓</div>
</div>

<div class="quick-btns">
    <span class="quick-btn" onclick="sendMsg('图书馆几点开门？')">📚 图书馆</span>
    <span class="quick-btn" onclick="sendMsg('食堂有什么好吃的？')">🍽️ 食堂</span>
    <span class="quick-btn" onclick="sendMsg('课表查询')">📅 课表</span>
    <span class="quick-btn" onclick="sendMsg('成绩查询')">📊 成绩</span>
    <span class="quick-btn" onclick="sendMsg('今日热点')">🔥 热点</span>
    <span class="quick-btn" onclick="sendMsg('学校官网')">🏫 官网</span>
</div>

<script>
function sendMsg(msg) {{
    const input = document.querySelector('.stChatInput textarea');
    if (input) {{
        input.value = msg;
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        const btn = document.querySelector('.stChatInput button');
        if (btn) btn.click();
    }}
}}
</script>
""", unsafe_allow_html=True)

# ========== 会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": "👋 你好！我是成工职小助手\n\n👨‍💻 尔主龙彪学长 - AI、编程\n📊 任乾鹏学长 - 成绩、课表\n👩‍💻 童妍学姐 - 校园生活\n\n试试问：**图书馆几点开门？**"
    })

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 设置（折叠）==========
with st.expander("⚙️ 设置"):
    enable_thinking = st.checkbox("🧠 深度思考", value=False)
    enable_search = st.checkbox("🌐 联网搜索", value=False)
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ========== 输入 ==========
user_input = st.chat_input("输入问题...")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            persona = select_persona(user_input)
            prefix = get_persona_prefix(persona)
            response = get_ai_response(user_input, persona, enable_thinking, enable_search)
            full = prefix + response
            st.markdown(full)
            st.session_state.messages.append({"role": "assistant", "content": full})
    st.rerun()
