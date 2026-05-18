"""
成工职小助手 - 手机端优化版
成都工业职业技术学院 | 三位学长学姐为你服务
"""

import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import time
import pandas as pd
import random
import requests
import json
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
SCHOOL_SHORT = "成工职院"
SCHOOL_MOTTO = "立德树人 精工强技"
SCHOOL_OFFICIAL_URL = "https://www.cdivtc.edu.cn"  
COURSE_SYSTEM_URL = "http://sw.cdivtc.edu.cn/app-web/#/login"

# ========== 页面配置 ==========
st.set_page_config(
    page_title=f"{SCHOOL_NAME} - 成工职小助手",
    page_icon="🎓",
    layout="centered",  # 改为centered更适合手机
    initial_sidebar_state="collapsed"  # 手机端默认收起侧边栏
)

# ========== 检查校徽 ==========
logo_files = ["school_logo.png", "logo.png", "校徽.png", "school_logo.jpg", "logo.jpg"]
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

# ========== AI智能热点获取功能 ==========
def get_ai_hot_trending(user_query):
    prompt = f"""用户问：{user_query}

请根据你掌握的知识，回答当前网络热点话题。

要求：
1. 列出8-10个当前热门话题
2. 每个话题用一句话简单介绍
3. 用🔥📈💡等表情符号标记热度
4. 最后提示用户可以去百度热搜官网查看实时详情"""
    
    response = call_deepseek([{"role": "user", "content": prompt}], "tongyan", False, None)
    return response if response else get_hot_search_fallback()

def get_hot_search_fallback():
    return f"""🔥 **查看今日热点**

### 🔗 [点击查看百度热搜榜](https://top.baidu.com)

直接问我具体话题也可以！"""

# ========== 官网新闻提取功能 ==========
def fetch_news_from_website():
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        url = f"{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            return None
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        all_news = []
        for link in soup.find_all('a', href=True):
            title = link.get_text(strip=True)
            href = link['href']
            if (len(title) > 8 and len(title) < 100 and 
                any(word in title for word in ['通知', '公告', '公示', '关于'])):
                if href.startswith('/'):
                    href = SCHOOL_OFFICIAL_URL + href
                elif not href.startswith('http'):
                    href = SCHOOL_OFFICIAL_URL + '/' + href
                if not any(n['title'] == title for n in all_news):
                    all_news.append({'title': title, 'link': href})
            if len(all_news) >= 6:
                break
        return all_news[:6] if all_news else None
    except Exception as e:
        print(f"新闻提取失败: {e}")
        return None

def get_news_fallback_response():
    return f"📢 查看通知：{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm"

# ========== 三位学长学姐的人格设定 ==========
PERSONAS = {
    "longbiao": {
        "name": "尔主龙彪",
        "avatar": "👨‍💻",
        "title": "AI应用工程师",
        "style": "技术控、逻辑清晰",
        "greeting": "我来帮你分析一下...",
    },
    "qianpeng": {
        "name": "任乾鹏",
        "avatar": "📊",
        "title": "数据测试工程师",
        "style": "细心、严谨",
        "greeting": "数据显示...",
    },
    "tongyan": {
        "name": "童妍",
        "avatar": "👩‍💻",
        "title": "前端开发工程师",
        "style": "热情、细心", 
        "greeting": "成工生活我超熟的！",
    }
}

def select_persona(question):
    q = question.lower()
    if any(word in q for word in ["python", "java", "代码", "编程"]):
        return "longbiao"
    elif any(word in q for word in ["成绩", "绩点", "课表"]):
        return "qianpeng"
    else:
        return "tongyan"

def get_persona_prefix(persona_key):
    persona = PERSONAS[persona_key]
    return f"**{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}** {persona['avatar']}\n> *{persona['greeting']}*\n\n"

def get_system_prompt(persona_key):
    persona = PERSONAS[persona_key]
    return f"""你是"{SCHOOL_NAME}的成工职小助手"，你是{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}。

人格特质：{persona['style']}，说话温暖亲切。

回答要求：用温暖亲切的语气，重要信息用**加粗**，适当使用表情符号。"""

# ========== 本地知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 开放时间：周一至周五 8:00-22:00，周末 9:00-21:00",
    "食堂": "🍽️ 早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n🍜 推荐：二食堂牛肉面",
    "选课": "📅 预选第18周，正选开学前1周，补退选开学第1周",
    "宿舍": "🔧 报修：公众号「成工后勤」",
    "校园卡": "💳 充值：微信公众号、支付宝",
    "奖学金": "🏆 国家奖学金8000元，申请时间每年9月",
    "校医院": "🏥 24小时值班，电话：1200",
    "课表": f"📅 教务系统：{COURSE_SYSTEM_URL}",
    "成绩": f"📊 教务系统：{COURSE_SYSTEM_URL}",
    "教务系统": f"🎓 入口：{COURSE_SYSTEM_URL}",
}

def get_local_answer(question):
    q = question.lower()
    for key, answer in LOCAL_KNOWLEDGE.items():
        if key in q:
            return answer
    return None

# ========== 联网搜索 ==========
def search_online(query, max_results=2):
    if not SEARCH_AVAILABLE:
        return None
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [{"title": r['title'], "body": r['body'][:300]} for r in results]
    except:
        return None

# ========== AI 调用 ==========
def call_deepseek(messages, persona_key, use_thinking=False, search_context=None):
    full_messages = [{"role": "system", "content": get_system_prompt(persona_key)}]
    
    if use_thinking:
        full_messages.append({"role": "user", "content": "请先展示你的💭思考过程。"})
    
    if search_context:
        full_messages.append({"role": "user", "content": f"参考：{search_context}"})
    
    recent_messages = messages[-20:] if len(messages) > 20 else messages
    full_messages.extend(recent_messages)
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            temperature=0.8,
            max_tokens=1500,
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

# ========== 核心回复函数 ==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    if any(word in lower for word in ["热点", "热搜", "今日热点"]):
        with st.spinner("整理热点..."):
            return get_ai_hot_trending(user_input)
    
    if any(word in lower for word in ["课表", "成绩", "绩点", "教务系统"]):
        local_answer = get_local_answer(user_input)
        if local_answer:
            return local_answer
    
    if any(word in lower for word in ["官网", "学校网址"]):
        return f"🌐 {SCHOOL_OFFICIAL_URL}"
    
    if any(word in lower for word in ["新闻", "通知", "公告"]):
        try:
            news = fetch_news_from_website()
            if news:
                text = "📢 最新通知：\n"
                for n in news[:3]:
                    text += f"• {n['title']}\n"
                return text
        except:
            pass
        return get_news_fallback_response()
    
    if any(w in lower for w in ["python", "java", "代码", "编程"]):
        response = call_deepseek([{"role": "user", "content": f"生成代码：{user_input}"}], persona_key, enable_thinking, None)
        return response if response else "代码生成暂时不可用"
    
    else:
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
        messages_for_api = [{"role": msg["role"], "content": msg["content"]} for msg in history]
        
        response = call_deepseek(messages_for_api, persona_key, enable_thinking, search_ctx)
        
        if response:
            return response
        else:
            local = get_local_answer(user_input)
            return local if local else f"抱歉，无法回答「{user_input}」。试试问：图书馆几点开门？"

# ========== 手机端优化CSS ==========
st.markdown("""
<style>
    /* 隐藏默认元素 */
    #MainMenu, header, footer {visibility: hidden;}
    .stApp {background: #f5f7fb;}
    
    /* 主容器 - 手机端优化 */
    .main .block-container {
        padding: 0.8rem 1rem 80px 1rem !important;
        max-width: 100% !important;
    }
    
    /* 标题区域 */
    .school-header {
        text-align: center;
        padding: 0.5rem 0 1rem 0;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    
    .school-name {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1a4d8c;
        margin: 0;
    }
    
    .school-motto {
        font-size: 0.7rem;
        color: #888;
        margin: 0;
    }
    
    /* 快捷按钮区域 */
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
        color: #333;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .quick-btn:active {
        background: #1a4d8c;
        color: white;
        transform: scale(0.96);
    }
    
    /* 消息气泡 */
    [data-testid="stChatMessage"] {
        margin-bottom: 0.8rem;
    }
    
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
        padding: 10px 14px !important;
        border-radius: 18px !important;
        font-size: 0.85rem !important;
        line-height: 1.5 !important;
        max-width: 85% !important;
    }
    
    [data-testid="stChatMessage"][data-testid="user"] {
        display: flex;
        justify-content: flex-end;
    }
    
    [data-testid="stChatMessage"][data-testid="user"] [data-testid="stMarkdown"] {
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        color: white;
        border-radius: 18px 18px 4px 18px !important;
    }
    
    [data-testid="stChatMessage"][data-testid="assistant"] [data-testid="stMarkdown"] {
        background: white;
        color: #333;
        border-radius: 18px 18px 18px 4px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* 输入框 */
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
        background: #f8f9fa;
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
        border-top: 1px solid #e0e0e0;
        z-index: 99;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.03);
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        text-decoration: none;
        color: #888;
        font-size: 0.65rem;
        flex: 1;
        text-align: center;
        padding: 4px 0;
        border-radius: 8px;
        background: transparent;
        border: none;
        cursor: pointer;
    }
    
    .nav-item:active {
        background: #f0f0f0;
    }
    
    .nav-icon {
        font-size: 1.2rem;
    }
    
    .nav-active {
        color: #1a4d8c;
        font-weight: 500;
    }
    
    /* 隐藏侧边栏（手机端） */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* 按钮样式 */
    .stButton button {
        background: #1a4d8c;
        color: white;
        border-radius: 25px;
        border: none;
        padding: 0.25rem 0.5rem;
        font-size: 0.7rem;
    }
    
    /* 隐藏Streamlit默认侧边栏按钮 */
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
</style>

<!-- 底部导航栏 -->
<div class="bottom-nav" id="bottomNav">
    <button class="nav-item" onclick="sendNavMessage('图书馆几点开门？')">
        <span class="nav-icon">📚</span>
        <span>图书馆</span>
    </button>
    <button class="nav-item" onclick="sendNavMessage('课表查询')">
        <span class="nav-icon">📅</span>
        <span>课表</span>
    </button>
    <button class="nav-item" onclick="sendNavMessage('成绩查询')">
        <span class="nav-icon">📊</span>
        <span>成绩</span>
    </button>
    <button class="nav-item" onclick="sendNavMessage('今日热点')">
        <span class="nav-icon">🔥</span>
        <span>热搜</span>
    </button>
    <button class="nav-item" onclick="sendNavMessage('食堂有什么好吃的？')">
        <span class="nav-icon">🍽️</span>
        <span>食堂</span>
    </button>
</div>

<!-- 标题区域 -->
<div class="school-header">
    <div class="school-name">🎓 成都工业职业技术学院</div>
    <div class="school-motto">立德树人 · 精工强技</div>
</div>

<script>
function sendNavMessage(msg) {
    const input = document.querySelector('.stChatInput textarea');
    if (input) {
        input.value = msg;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        const button = document.querySelector('.stChatInput button');
        if (button) button.click();
    }
}

// 移除侧边栏相关元素
setTimeout(() => {
    const sidebar = document.querySelector('[data-testid="stSidebar"]');
    if (sidebar) sidebar.remove();
}, 100);
</script>
""", unsafe_allow_html=True)

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"""你好呀！我是成工职小助手 👋

由三位学长学姐共同为你服务：

👨‍💻 **尔主龙彪学长** - AI、编程、选课
📊 **任乾鹏学长** - 成绩、课表、数据分析
👩‍💻 **童妍学姐** - 校园生活、社团

---

**试试问我：**
• "图书馆几点开门？"
• "课表查询"
• "我的成绩"
• "今天有什么热点？"

有什么问题尽管问！😊"""
    })

# ========== 显示历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 快捷按钮（HTML方式）==========
st.markdown("""
<div class="quick-buttons">
    <span class="quick-btn" onclick="sendNavMessage('图书馆几点开门？')">📚 图书馆</span>
    <span class="quick-btn" onclick="sendNavMessage('食堂有什么好吃的？')">🍽️ 食堂</span>
    <span class="quick-btn" onclick="sendNavMessage('课表查询')">📅 课表</span>
    <span class="quick-btn" onclick="sendNavMessage('成绩查询')">📊 成绩</span>
    <span class="quick-btn" onclick="sendNavMessage('今日热点')">🔥 热点</span>
</div>
""", unsafe_allow_html=True)

# ========== 设置开关（放在侧边栏隐藏后的替代位置）==========
with st.expander("⚙️ 高级设置"):
    enable_thinking = st.checkbox("🧠 深度思考模式", value=False)
    enable_search = st.checkbox("🌐 联网搜索", value=False)
    
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ========== 主输入框 ==========
user_input = st.chat_input("输入你的问题...")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            persona_key = select_persona(user_input)
            prefix = get_persona_prefix(persona_key)
            response = get_ai_response(user_input, persona_key, enable_thinking, enable_search)
            full_response = prefix + response
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    st.rerun()
