"""
成工职小助手 - 移动端极简版（类DeepSeek设计）
成都工业职业技术学院
"""

import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import base64
from PIL import Image
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
SCHOOL_MOTTO = "立德树人 精工强技"
SCHOOL_OFFICIAL_URL = "https://www.cdivtc.edu.cn"  
COURSE_SYSTEM_URL = "http://sw.cdivtc.edu.cn/app-web/#/login"

# ========== 页面配置 ==========
st.set_page_config(
    page_title=f"{SCHOOL_NAME} - 成工职小助手",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed"
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
    return f"🔥 查看热点：[百度热搜榜](https://top.baidu.com)"

# ========== 官网新闻提取 ==========
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
                any(word in title for word in ['通知', '公告', '公示'])):
                if href.startswith('/'):
                    href = SCHOOL_OFFICIAL_URL + href
                elif not href.startswith('http'):
                    href = SCHOOL_OFFICIAL_URL + '/' + href
                if not any(n['title'] == title for n in all_news):
                    all_news.append({'title': title, 'link': href})
            if len(all_news) >= 5:
                break
        return all_news[:5] if all_news else None
    except:
        return None

# ========== 人格设定 ==========
PERSONAS = {
    "longbiao": {"name": "尔主龙彪", "avatar": "👨‍💻", "style": "技术控", "greeting": "我来帮你分析一下..."},
    "qianpeng": {"name": "任乾鹏", "avatar": "📊", "style": "细心", "greeting": "数据显示..."},
    "tongyan": {"name": "童妍", "avatar": "👩‍💻", "style": "热情", "greeting": "成工生活我超熟的！"},
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
    p = PERSONAS[persona_key]
    return f"**{p['name']}{'学长' if persona_key != 'tongyan' else '学姐'}** {p['avatar']}\n> *{p['greeting']}*\n\n"

def get_system_prompt(persona_key):
    p = PERSONAS[persona_key]
    return f"你是{SCHOOL_NAME}小助手{p['name']}，{p['style']}，说话温暖亲切。"

# ========== 本地知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 开放时间：周一至周五 8:00-22:00，周末 9:00-21:00",
    "食堂": "🍽️ 早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n🍜 推荐：二食堂牛肉面",
    "课表": f"📅 [教务系统]({COURSE_SYSTEM_URL})",
    "成绩": f"📊 [教务系统]({COURSE_SYSTEM_URL})",
    "官网": f"🌐 [学校官网]({SCHOOL_OFFICIAL_URL})",
    "选课": "📅 预选第18周，正选开学前1周",
    "宿舍": "🔧 报修：公众号「成工后勤」",
    "奖学金": "🏆 国家奖学金8000元，申请时间每年9月",
}

def get_local_answer(question):
    q = question.lower()
    for key, answer in LOCAL_KNOWLEDGE.items():
        if key in q:
            return answer
    return None

# ========== AI调用 ==========
def call_deepseek(messages, persona_key, use_thinking=False, search_context=None):
    full_messages = [{"role": "system", "content": get_system_prompt(persona_key)}]
    if use_thinking:
        full_messages.append({"role": "user", "content": "请展示思考过程。"})
    if search_context:
        full_messages.append({"role": "user", "content": f"参考：{search_context}"})
    recent = messages[-20:] if len(messages) > 20 else messages
    full_messages.extend(recent)
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

# ========== 核心回复 ==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    if any(word in lower for word in ["热点", "热搜", "今日热点"]):
        with st.spinner("整理热点..."):
            return get_ai_hot_trending(user_input)
    
    if any(word in lower for word in ["课表", "成绩", "官网", "选课", "宿舍", "奖学金", "图书馆", "食堂"]):
        local = get_local_answer(user_input)
        if local:
            return local
    
    if any(word in lower for word in ["新闻", "通知"]):
        news = fetch_news_from_website()
        if news:
            text = "📢 最新通知：\n"
            for n in news[:3]:
                text += f"• [{n['title']}]({n['link']})\n"
            return text
        return f"📢 [通知公告]({SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm)"
    
    if any(w in lower for w in ["python", "java", "代码"]):
        resp = call_deepseek([{"role": "user", "content": f"生成代码：{user_input}"}], persona_key, enable_thinking, None)
        return resp if resp else "代码生成失败"
    
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
        msgs = [{"role": m["role"], "content": m["content"]} for m in history]
        resp = call_deepseek(msgs, persona_key, enable_thinking, search_ctx)
        if resp:
            return resp
        local = get_local_answer(user_input)
        return local if local else f"抱歉，无法回答。试试问：图书馆几点开门？"

# ========== 极简CSS（类DeepSeek设计）==========
# 生成校徽头像
if LOGO_BASE64:
    avatar_html = f'<img src="data:image/png;base64,{LOGO_BASE64}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;">'
else:
    avatar_html = '<span style="font-size: 32px;">🎓</span>'

st.markdown(f"""
<style>
    /* 隐藏所有默认元素 */
    #MainMenu, header, footer {{visibility: hidden;}}
    .stApp {{background: #ffffff;}}
    
    /* 主容器 - 极简 */
    .main .block-container {{
        padding: 0.5rem 1rem 70px 1rem !important;
        max-width: 100% !important;
    }}
    
    /* 隐藏侧边栏 */
    [data-testid="stSidebar"] {{display: none !important;}}
    
    /* 顶部标题栏 - 只显示头像和标题 */
    .app-bar {{
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 0;
        margin-bottom: 8px;
        border-bottom: 1px solid #f0f0f0;
    }}
    .app-title {{
        font-size: 1rem;
        font-weight: 500;
        color: #333;
    }}
    
    /* 消息气泡 - 紧凑 */
    [data-testid="stChatMessage"] {{margin-bottom: 0.8rem;}}
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {{
        padding: 10px 14px !important;
        font-size: 0.85rem !important;
        line-height: 1.45 !important;
        max-width: 85% !important;
    }}
    
    /* 用户消息 - 右对齐 */
    [data-testid="stChatMessage"][data-testid="user"] {{
        display: flex;
        justify-content: flex-end;
    }}
    [data-testid="stChatMessage"][data-testid="user"] [data-testid="stMarkdown"] {{
        background: #e8f4e8;
        color: #1a4d8c;
        border-radius: 18px 18px 4px 18px !important;
    }}
    
    /* AI消息 - 左对齐，带头像 */
    [data-testid="stChatMessage"][data-testid="assistant"] {{
        display: flex;
        align-items: flex-start;
        gap: 8px;
    }}
    [data-testid="stChatMessage"][data-testid="assistant"] [data-testid="stMarkdown"] {{
        background: #f5f5f5;
        color: #333;
        border-radius: 18px 18px 18px 4px !important;
    }}
    
    /* AI头像 */
    .ai-avatar {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #1a4d8c;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        flex-shrink: 0;
        margin-top: 2px;
    }}
    
    /* 输入框 - 固定在底部 */
    .stChatInput {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px 12px;
        padding-bottom: calc(10px + env(safe-area-inset-bottom));
        border-top: 1px solid #e8e8e8;
        z-index: 100;
    }}
    .stChatInput textarea {{
        border-radius: 25px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 10px 16px !important;
        font-size: 0.9rem !important;
        background: #f8f9fa;
    }}
    
    /* 折叠菜单样式 - 简洁 */
    .streamlit-expanderHeader {{
        font-size: 0.75rem;
        background: #f8f9fa;
        border-radius: 20px;
        padding: 6px 12px;
        margin-bottom: 5px;
    }}
    .streamlit-expanderContent {{
        background: #f8f9fa;
        border-radius: 16px;
        padding: 10px;
        margin-bottom: 10px;
    }}
    
    /* 快捷链接卡片 */
    .link-card {{
        background: white;
        border-radius: 12px;
        padding: 8px 12px;
        margin-bottom: 8px;
        border: 1px solid #f0f0f0;
        font-size: 0.8rem;
    }}
</style>

<!-- 顶部栏：AI头像 + 标题 -->
<div class="app-bar">
    {avatar_html}
    <div class="app-title">{SCHOOL_NAME}</div>
</div>

<script>
// 为每条AI消息添加头像
function addAvatars() {{
    const messages = document.querySelectorAll('[data-testid="stChatMessage"][data-testid="assistant"]');
    messages.forEach(msg => {{
        if (!msg.querySelector('.ai-avatar')) {{
            const avatar = document.createElement('div');
            avatar.className = 'ai-avatar';
            avatar.innerHTML = `{avatar_html if LOGO_BASE64 else '🎓'}`;
            msg.insertBefore(avatar, msg.firstChild);
        }}
    }});
}}

setTimeout(addAvatars, 100);
setInterval(addAvatars, 500);
</script>
""", unsafe_allow_html=True)

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"""你好！我是成工职小助手 👋

由三位学长学姐为你服务：

• 👨‍💻 **尔主龙彪学长** - AI、编程、选课
• 📊 **任乾鹏学长** - 成绩、课表、数据分析  
• 👩‍💻 **童妍学姐** - 校园生活、社团

试试问我：**图书馆几点开门？**"""
    })

# ========== 显示消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 折叠菜单（所有功能放这里）==========
with st.expander("☰ 功能菜单"):
    st.markdown("### 🔗 快捷链接")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"[🏫 学校官网]({SCHOOL_OFFICIAL_URL})")
        st.markdown(f"[📚 教务系统]({COURSE_SYSTEM_URL})")
        st.markdown(f"[🔥 百度热搜](https://top.baidu.com)")
    with col2:
        st.markdown(f"[📖 选课系统]({COURSE_SYSTEM_URL})")
        st.markdown(f"[📊 成绩查询]({COURSE_SYSTEM_URL})")
        st.markdown(f"[📢 通知公告]({SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm)")
    
    st.markdown("---")
    st.markdown("### ⚙️ 设置")
    
    enable_thinking = st.checkbox("🧠 深度思考模式", value=False)
    enable_search = st.checkbox("🌐 联网搜索", value=False)
    
    st.markdown("---")
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 👥 开发团队")
    st.markdown("- 尔主龙彪（组长）")
    st.markdown("- 任乾鹏")
    st.markdown("- 童妍")

# ========== 快捷输入提示 ==========
quick_list = ["📚 图书馆", "🍽️ 食堂", "📅 课表", "📊 成绩", "🔥 热点", "🏫 官网"]
cols = st.columns(6)
for idx, q in enumerate(quick_list):
    with cols[idx]:
        full_q = {
            "📚 图书馆": "图书馆几点开门？",
            "🍽️ 食堂": "食堂有什么好吃的？",
            "📅 课表": "课表查询",
            "📊 成绩": "成绩查询",
            "🔥 热点": "今日热点",
            "🏫 官网": "学校官网"
        }.get(q, q)
        if st.button(q, key=f"quick_{idx}", use_container_width=True):
            with st.chat_message("user"):
                st.markdown(full_q)
            st.session_state.messages.append({"role": "user", "content": full_q})
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    persona = select_persona(full_q)
                    prefix = get_persona_prefix(persona)
                    response = get_ai_response(full_q, persona, enable_thinking, enable_search)
                    st.markdown(prefix + response)
                    st.session_state.messages.append({"role": "assistant", "content": prefix + response})
            st.rerun()

# ========== 主输入框 ==========
user_input = st.chat_input("输入你的问题...")
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
