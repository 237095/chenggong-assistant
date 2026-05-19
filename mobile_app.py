"""
成工职小助手 - 移动端（顶部设置栏版）
成都工业职业技术学院 | 三位学长学姐为你服务
"""

import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import base64
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

LOGO_BASE64 = None
if LOGO_PATH and os.path.exists(LOGO_PATH):
    try:
        with open(LOGO_PATH, "rb") as img_file:
            LOGO_BASE64 = base64.b64encode(img_file.read()).decode()
    except:
        pass

# ========== 百度热搜 ==========
def fetch_baidu_hot_search(limit=10):
    try:
        url = "https://api.knowsafe.com/v1/api/hot/baidu"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 1:
                return data.get('data', [])[:limit]
        return None
    except:
        return None

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
                if len(news) >= 5:
                    break
        return news
    except:
        return None

# ========== 人格设定 ==========
PERSONAS = {
    "longbiao": {
        "name": "尔主龙彪",
        "avatar": "👨‍💻",
        "greeting": "这个问题我来帮你分析一下..."
    },
    "qianpeng": {
        "name": "任乾鹏",
        "avatar": "📊",
        "greeting": "据我整理的数据显示..."
    },
    "tongyan": {
        "name": "童妍",
        "avatar": "👩‍💻",
        "greeting": "成工生活我超熟的！"
    }
}

def select_persona(question):
    q = question.lower()
    if any(w in q for w in ["python", "java", "代码", "编程", "选课"]):
        return "longbiao"
    elif any(w in q for w in ["成绩", "课表", "数据", "表格", "绩点"]):
        return "qianpeng"
    return "tongyan"

def get_persona_prefix(persona_key):
    persona = PERSONAS[persona_key]
    return f"**{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}** {persona['avatar']}\n\n*{persona['greeting']}*\n\n"

def get_system_prompt(persona_key):
    persona = PERSONAS[persona_key]
    return f"你是{SCHOOL_NAME}小助手{persona['name']}，说话温暖亲切。"

# ========== 本地知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 开放时间：周一至周五 8:00-22:00，周末 9:00-21:00",
    "食堂": "🍽️ 早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n👍 推荐：二食堂牛肉面",
    "选课": "📅 预选第18周，正选开学前1周，补退选开学第1周",
    "宿舍": "🔧 报修：公众号「成工后勤」或联系楼栋管理员",
    "校园卡": "💳 充值：微信公众号、支付宝、食堂自助机",
    "奖学金": "🏆 国家奖学金8000元，申请时间每年9月",
    "校医院": "🏥 24小时值班，急诊电话：1200",
    "课表查询": f"🔗 [点击进入教务系统]({COURSE_SYSTEM_URL})",
    "成绩查询": f"🔗 [点击进入教务系统]({COURSE_SYSTEM_URL})",
    "绩点": f"🔗 [教务系统查询]({COURSE_SYSTEM_URL})",
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
        full.append({"role": "user", "content": "请先展示你的💭思考过程，再给出答案。"})
    
    if search_context:
        full.append({"role": "user", "content": f"参考信息：{search_context}"})
    
    full.extend(messages[-15:])
    
    try:
        r = client.chat.completions.create(
            model="deepseek-chat",
            messages=full,
            temperature=0.8,
            max_tokens=1500,
            timeout=30
        )
        return r.choices[0].message.content
    except:
        return None

# ========== 回复函数 ==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    # 热点查询
    if any(w in lower for w in ["热点", "热搜", "今日热点"]):
        hot_list = fetch_baidu_hot_search(10)
        if hot_list:
            response = "🔥 **今日热点**\n\n"
            for idx, item in enumerate(hot_list[:8], 1):
                keyword = item.get('keyword', '')[:30]
                icon = "🔥" if idx <= 3 else "📈"
                response += f"{icon} {idx}. {keyword}\n\n"
            return response
        return "暂时无法获取热搜数据"
    
    # 本地知识库
    local = get_local_answer(user_input)
    if local:
        return local
    
    # 新闻通知
    if any(w in lower for w in ["新闻", "通知", "公告"]):
        news = fetch_news_from_website()
        if news:
            return "📢 最新通知：\n\n" + "\n".join([f"• {n}" for n in news])
        return f"📢 [查看通知公告]({SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm)"
    
    # 联网搜索
    search_ctx = None
    if enable_search and SEARCH_AVAILABLE:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(user_input, max_results=2))
                if results:
                    search_ctx = "\n".join([f"- {r['title']}: {r['body'][:200]}" for r in results])
        except:
            pass
    
    # 调用AI
    history = st.session_state.messages[-15:] if len(st.session_state.messages) > 15 else st.session_state.messages
    msgs = [{"role": m["role"], "content": m["content"]} for m in history if m["role"] != "system"]
    resp = call_deepseek(msgs, persona_key, enable_thinking, search_ctx)
    
    if resp:
        return resp
    return f"抱歉，无法回答。试试问：图书馆几点开门？"

# ========== 初始化会话状态 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.enable_thinking = False
    st.session_state.enable_search = False
    st.session_state.show_settings = False  # 控制设置面板显示
    
    welcome_msg = """👋 **你好！我是成工职小助手**

---

**👨‍💻 尔主龙彪学长** - AI、编程、选课

**📊 任乾鹏学长** - 数据、成绩、表格

**👩‍💻 童妍学姐** - 校园生活、社团

---

💡 **试试问我：**
- 图书馆几点开门？
- 帮我写个Python代码
- 今日热点有哪些？"""
    
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# ========== CSS样式 ==========
st.markdown(f"""
<style>
    /* 隐藏默认元素 */
    #MainMenu, header, footer {{visibility: hidden; display: none;}}
    .stApp {{background: #f5f7fb;}}
    
    /* 主容器 */
    .main .block-container {{
        padding: 0.5rem 0.8rem 70px 0.8rem !important;
        max-width: 100% !important;
    }}
    
    /* 隐藏侧边栏 */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* 顶部栏 */
    .mobile-header {{
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        border-radius: 20px;
        padding: 12px 16px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    .mobile-logo {{
        width: 44px;
        height: 44px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        overflow: hidden;
        flex-shrink: 0;
    }}
    .mobile-logo img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}
    .mobile-title {{
        flex: 1;
    }}
    .mobile-title h3 {{
        color: white;
        margin: 0;
        font-size: 0.9rem;
        font-weight: 600;
    }}
    .mobile-title p {{
        color: rgba(255,255,255,0.85);
        margin: 2px 0 0 0;
        font-size: 0.65rem;
    }}
    
    /* 设置按钮 */
    .settings-btn {{
        background: rgba(255,255,255,0.2);
        border: none;
        border-radius: 30px;
        padding: 6px 12px;
        color: white;
        font-size: 0.7rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
    }}
    
    /* 设置面板 */
    .settings-panel {{
        background: white;
        border-radius: 16px;
        padding: 12px 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 1px solid #e8e8e8;
    }}
    
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
        transition: all 0.2s;
    }}
    .quick-btn:active {{
        background: #1a4d8c;
        color: white;
        transform: scale(0.96);
    }}
    
    /* 消息气泡 */
    [data-testid="stChatMessage"] {{
        margin-bottom: 12px !important;
    }}
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {{
        padding: 10px 14px !important;
        font-size: 0.85rem !important;
        line-height: 1.5 !important;
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
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        padding: 10px 12px 20px 12px;
        border-top: 1px solid rgba(0,0,0,0.05);
        z-index: 100;
    }}
    .stChatInput textarea {{
        border-radius: 25px !important;
        border: 1px solid #ddd !important;
        padding: 10px 16px !important;
        font-size: 0.85rem !important;
    }}
    
    /* 按钮样式 */
    .stButton button {{
        border-radius: 25px !important;
        background: #f0f2f5 !important;
        color: #1a4d8c !important;
        border: none !important;
        font-size: 0.75rem !important;
    }}
    
    /* 链接按钮 */
    .link-btn {{
        display: inline-block;
        background: linear-gradient(135deg, #e8a020 0%, #d4891a 100%);
        color: white;
        text-decoration: none;
        padding: 6px 12px;
        border-radius: 25px;
        font-size: 0.7rem;
        text-align: center;
        margin: 4px;
    }}
</style>

<div class="mobile-header">
    <div class="mobile-logo">
        {f'<img src="data:image/png;base64,{LOGO_BASE64}">' if LOGO_BASE64 else '🎓'}
    </div>
    <div class="mobile-title">
        <h3>{SCHOOL_NAME}</h3>
        <p>{SCHOOL_MOTTO}</p>
    </div>
    <button class="settings-btn" onclick="toggleSettings()">⚙️ 设置</button>
</div>

<div id="settingsPanel" class="settings-panel" style="display: none;">
    <div style="display: flex; gap: 12px; margin-bottom: 12px;">
        <a href="{SCHOOL_OFFICIAL_URL}" target="_blank" class="link-btn" style="flex:1; background: #e8a020;">🏫 官网</a>
        <a href="{COURSE_SYSTEM_URL}" target="_blank" class="link-btn" style="flex:1; background: #1a4d8c;">📚 教务系统</a>
    </div>
    <div style="margin-top: 8px;">
        <button class="stButton" onclick="clearChat()" style="width:100%;">🗑️ 清空对话</button>
    </div>
    <div style="text-align: center; margin-top: 8px; font-size: 0.6rem; color: #999;">
        📅 {datetime.now().strftime('%Y-%m-%d')}
    </div>
</div>

<div class="quick-btns">
    <span class="quick-btn" onclick="sendMsg('图书馆几点开门？')">📚 图书馆</span>
    <span class="quick-btn" onclick="sendMsg('食堂有什么好吃的？')">🍽️ 食堂</span>
    <span class="quick-btn" onclick="sendMsg('课表查询')">📅 课表</span>
    <span class="quick-btn" onclick="sendMsg('成绩查询')">📊 成绩</span>
    <span class="quick-btn" onclick="sendMsg('今日热点')">🔥 热点</span>
    <span class="quick-btn" onclick="sendMsg('奖学金')">🏆 奖学金</span>
</div>

<script>
function toggleSettings() {{
    var panel = document.getElementById('settingsPanel');
    if (panel.style.display === 'none') {{
        panel.style.display = 'block';
    }} else {{
        panel.style.display = 'none';
    }}
}}

function clearChat() {{
    // 通过Streamlit的rerun机制清空对话
    var input = document.createElement('input');
    input.type = 'hidden';
    input.id = 'clear_chat';
    input.value = 'true';
    document.body.appendChild(input);
    location.reload();
}}

function sendMsg(msg) {{
    const input = document.querySelector('.stChatInput textarea');
    if (input) {{
        input.value = msg;
        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
        setTimeout(() => {{
            const btn = document.querySelector('.stChatInput button');
            if (btn && !btn.disabled) btn.click();
        }}, 50);
    }}
}}

// 监听URL参数清空对话
if (window.location.search.includes('clear=true')) {{
    // 这里可以触发清空
}}
</script>
""", unsafe_allow_html=True)

# ========== 显示设置切换按钮（Streamlit原生）==========
# 在侧边栏位置放置一个简单的设置区域（使用columns布局）
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### 💬 对话")
with col2:
    if st.button("⚙️ 设置", use_container_width=True):
        st.session_state.show_settings = not st.session_state.show_settings

# 显示设置面板
if st.session_state.show_settings:
    with st.container():
        st.markdown("---")
        
        # 使用st.toggle（借鉴电脑端）
        enable_thinking = st.toggle("🧠 深度思考模式", value=st.session_state.enable_thinking)
        enable_search = st.toggle("🌐 联网搜索", value=st.session_state.enable_search)
        
        st.session_state.enable_thinking = enable_thinking
        st.session_state.enable_search = enable_search
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"[🏫 学校官网]({SCHOOL_OFFICIAL_URL})")
        with col2:
            st.markdown(f"[📚 教务系统]({COURSE_SYSTEM_URL})")
        
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.messages = []
            st.session_state.show_settings = False
            st.rerun()
        
        st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
        st.markdown("---")

# ========== 显示历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 输入处理 ==========
user_input = st.chat_input("输入你的问题...")
if user_input and user_input.strip():
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("学长学姐正在思考..."):
            persona = select_persona(user_input)
            prefix = get_persona_prefix(persona)
            response = get_ai_response(
                user_input, 
                persona, 
                st.session_state.enable_thinking, 
                st.session_state.enable_search
            )
            full_response = prefix + response
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    st.rerun()
