"""
成工职小助手 - 手机端优化版
成都工业职业技术学院 | 三位学长学姐为你服务
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

# ========== AI智能热点获取功能（完整版） ==========
def get_ai_hot_trending(user_query):
    prompt = f"""用户问：{user_query}

请根据你掌握的知识，回答当前网络热点话题。

要求：
1. 列出8-10个当前热门话题（涵盖科技、娱乐、社会、教育、校园等）
2. 每个话题用一句话简单介绍
3. 用🔥📈💡✨🎯等表情符号标记热度
4. 分类展示：
   🔥 热搜爆款（最热门的3-5个）
   📈 持续热议（讨论度高的）
   💡 新鲜话题（刚出现的）
   🎯 校园相关（学生关心的）
5. 最后提示用户可以去百度热搜官网查看实时详情

注意：结合你的知识给出合理的热点推荐，越贴近学生生活越好。"""
    
    response = call_deepseek([{"role": "user", "content": prompt}], "tongyan", False, None)
    return response if response else get_hot_search_fallback()

def get_hot_search_fallback():
    return f"""🔥 **查看今日热点**

💡 想了解最新热点，你可以：

🔗 [点击查看百度热搜榜](https://top.baidu.com)

---

**或者直接问我具体话题**，比如：
- "AI有什么新闻？"
- "最近有什么好看的电影？"
- "科技圈有什么大事？"

我会根据我的知识为你解答！"""

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
                any(word in title for word in ['通知', '公告', '公示', '关于', '开展', '举办'])):
                if href.startswith('/'):
                    href = SCHOOL_OFFICIAL_URL + href
                elif not href.startswith('http'):
                    href = SCHOOL_OFFICIAL_URL + '/' + href
                if not any(n['title'] == title for n in all_news):
                    all_news.append({'title': title, 'link': href})
            if len(all_news) >= 5:
                break
        return all_news[:5] if all_news else None
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
        "title": "AI应用工程师 · 组长",
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
    if LOGO_BASE64:
        return f"**{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}**\n\n> *{persona['greeting']}*\n\n"
    else:
        return f"**{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}** {persona['avatar']}\n\n> *{persona['greeting']}*\n\n"

def get_system_prompt(persona_key):
    persona = PERSONAS[persona_key]
    return f"""你是"{SCHOOL_NAME}的成工职小助手"，你是{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}。

人格特质：{persona['style']}，说话温暖亲切。

回答要求：用温暖亲切的语气，重要信息用**加粗**，适当使用表情符号。"""

# ========== 本地知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 开放时间：周一至周五 8:00-22:00，周末 9:00-21:00",
    "食堂": "🍽️ 早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n🍜 推荐：二食堂牛肉面",
    "选课": "📅 预选第18周，正选开学前1周",
    "宿舍": "🔧 报修：公众号「成工后勤」",
    "校园卡": "💳 充值：微信公众号、支付宝",
    "奖学金": "🏆 国家奖学金8000元",
    "校医院": "🏥 24小时值班",
    "课表": f"📅 教务系统：{COURSE_SYSTEM_URL}",
    "成绩": f"📊 教务系统：{COURSE_SYSTEM_URL}",
}

def get_local_answer(question):
    q = question.lower()
    for key, answer in LOCAL_KNOWLEDGE.items():
        if key in q:
            return answer
    return None

# ========== AI 调用 ==========
def call_deepseek(messages, persona_key, use_thinking=False, search_context=None):
    full_messages = [{"role": "system", "content": get_system_prompt(persona_key)}]
    
    if use_thinking:
        full_messages.append({"role": "user", "content": "请展示思考过程。"})
    
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
    
    if any(word in lower for word in ["热点", "热搜", "百度热搜", "热门", "今天有什么热点", "最近什么火", "热搜榜", "今日热点", "trending"]):
        with st.spinner("AI正在整理热点..."):
            return get_ai_hot_trending(user_input)
    
    if any(word in lower for word in ["课表", "课程表", "成绩", "绩点", "教务系统", "成绩查询"]):
        local_answer = get_local_answer(user_input)
        if local_answer:
            return local_answer
    
    if any(word in lower for word in ["官网", "学校网址"]):
        return f"🌐 {SCHOOL_OFFICIAL_URL}"
    
    if any(word in lower for word in ["新闻", "通知", "公告"]):
        try:
            news = fetch_news_from_website()
            if news:
                news_text = "📢 最新通知：\n"
                for n in news[:3]:
                    news_text += f"• {n['title']}\n"
                return news_text
        except:
            pass
        return get_news_fallback_response()
    
    if any(w in lower for w in ["python", "java", "代码", "编程"]):
        full_prompt = f"生成代码：{user_input}"
        response = call_deepseek([{"role": "user", "content": full_prompt}], persona_key, enable_thinking, None)
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
    
    /* 主容器 */
    .main .block-container {
        padding: 0.5rem 0.8rem 70px 0.8rem !important;
        max-width: 100% !important;
    }
    
    /* 隐藏侧边栏 */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* ========== 顶部标题区 ========== */
    .app-header {
        text-align: center;
        padding: 0.3rem 0 0.8rem 0;
        margin-bottom: 0.3rem;
        border-bottom: 1px solid #e8e8e8;
    }
    
    .app-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1a4d8c;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
    }
    
    .app-motto {
        font-size: 0.6rem;
        color: #aaa;
        margin-top: 2px;
    }
    
    /* ========== 快捷按钮区域（2行布局）========== */
    .quick-section {
        background: white;
        border-radius: 16px;
        padding: 10px 12px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    
    .quick-title {
        font-size: 0.7rem;
        color: #888;
        margin-bottom: 8px;
        font-weight: 500;
    }
    
    .quick-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
    }
    
    .quick-item {
        background: #f8f9fa;
        border: none;
        border-radius: 30px;
        padding: 8px 0;
        font-size: 0.7rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
        color: #333;
    }
    
    .quick-item:active {
        background: #1a4d8c;
        color: white;
        transform: scale(0.96);
    }
    
    /* ========== 消息气泡 ========== */
    [data-testid="stChatMessage"] {
        margin-bottom: 0.6rem;
    }
    
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
        padding: 10px 14px !important;
        font-size: 0.85rem !important;
        line-height: 1.45 !important;
        max-width: 88% !important;
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
    
    /* ========== 输入框 ========== */
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 10px 12px;
        padding-bottom: calc(10px + env(safe-area-inset-bottom));
        border-top: 1px solid #e8e8e8;
        z-index: 100;
    }
    
    .stChatInput textarea {
        border-radius: 25px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 10px 16px !important;
        font-size: 0.85rem !important;
        background: #f8f9fa;
    }
    
    /* ========== 底部导航栏 ========== */
    .bottom-nav {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        display: flex;
        justify-content: space-around;
        padding: 6px 12px;
        padding-bottom: calc(6px + env(safe-area-inset-bottom));
        border-top: 1px solid #e8e8e8;
        z-index: 99;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.03);
    }
    
    .nav-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 2px;
        color: #999;
        font-size: 0.6rem;
        flex: 1;
        text-align: center;
        background: none;
        border: none;
        cursor: pointer;
        padding: 4px 0;
        border-radius: 8px;
    }
    
    .nav-item:active {
        background: #f0f0f0;
        color: #1a4d8c;
    }
    
    .nav-icon {
        font-size: 1.2rem;
    }
    
    /* ========== 高级设置 ========== */
    .streamlit-expanderHeader {
        font-size: 0.75rem;
        background: white;
        border-radius: 20px;
    }
    
    /* ========== 代码块 ========== */
    pre {
        background: #1e1e2e;
        border-radius: 10px;
        padding: 10px;
        font-size: 0.7rem;
        overflow-x: auto;
    }
</style>

<!-- 顶部标题 -->
<div class="app-header">
    <div class="app-title">
        <span>🎓</span> 成工职小助手
    </div>
    <div class="app-motto">立德树人 · 精工强技</div>
</div>

<!-- 快捷按钮区域 -->
<div class="quick-section">
    <div class="quick-title">⚡ 快捷提问</div>
    <div class="quick-grid">
        <div class="quick-item" onclick="sendMsg('图书馆几点开门？')">📚 图书馆</div>
        <div class="quick-item" onclick="sendMsg('课表查询')">📅 课表</div>
        <div class="quick-item" onclick="sendMsg('成绩查询')">📊 成绩</div>
        <div class="quick-item" onclick="sendMsg('今日热点')">🔥 热点</div>
        <div class="quick-item" onclick="sendMsg('食堂有什么好吃的？')">🍽️ 食堂</div>
        <div class="quick-item" onclick="sendMsg('选课')">📖 选课</div>
        <div class="quick-item" onclick="sendMsg('宿舍报修')">🔧 宿舍</div>
        <div class="quick-item" onclick="sendMsg('奖学金')">🏆 奖学金</div>
    </div>
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

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"""👋 你好！我是成工职小助手

由三位学长学姐为你服务：

👨‍💻 **尔主龙彪学长** - AI、编程
📊 **任乾鹏学长** - 成绩、课表  
👩‍💻 **童妍学姐** - 校园生活

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

# ========== 高级设置 ==========
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
