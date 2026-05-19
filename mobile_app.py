"""
成工职小助手 - 手机端（优化版）
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

# ========== 检查并加载校徽（提前加载）==========
logo_files = ["school_logo.png", "logo.png", "校徽.png", "assets/logo.png"]
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
    "longbiao": {"name": "尔主龙彪", "role": "AI应用工程师", "avatar": "👨‍💻", "greeting": "我来帮你分析"},
    "qianpeng": {"name": "任乾鹏", "role": "数据测试工程师", "avatar": "📊", "greeting": "数据显示"},
    "tongyan": {"name": "童妍", "role": "前端开发工程师", "avatar": "👩‍💻", "greeting": "成工生活我超熟"},
}

def select_persona(question):
    q = question.lower()
    if any(w in q for w in ["python", "java", "代码", "编程", "ai", "人工智能"]):
        return "longbiao"
    elif any(w in q for w in ["成绩", "课表", "绩点", "数据", "表格"]):
        return "qianpeng"
    return "tongyan"

def get_persona_prefix(key):
    p = PERSONAS[key]
    role_tag = f" *{p['role']}*" if key != "tongyan" else ""
    return f"**{p['name']}{'学长' if key != 'tongyan' else '学姐'}** {p['avatar']}{role_tag}\n\n"

def get_system_prompt(key):
    p = PERSONAS[key]
    return f"你是{SCHOOL_NAME}小助手{p['name']}，说话温暖亲切。你是{p['role']}，擅长相关领域。"

# ========== 知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 开放时间：周一至周五 8:00-22:00，周末 9:00-21:00\n📍 位置：图文信息中心1-4层\n💳 凭校园卡借阅，每人限借5本",
    "食堂": "🍽️ 早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n👍 推荐：二食堂牛肉面、一食堂麻辣烫\n💳 支持校园卡/支付宝",
    "选课": "📅 预选第18周，正选开学前1周，补退选开学第1周\n🔗 登录教务系统进行选课",
    "宿舍": "🔧 报修：公众号「成工后勤」或联系楼栋管理员\n⏰ 门禁：23:00\n💡 功率限制：800W",
    "校园卡": "💳 充值：微信公众号、支付宝、食堂自助机\n🔒 挂失：自助机或公众号",
    "奖学金": "🏆 国家奖学金8000元，申请时间每年9月\n🏆 国家励志奖学金5000元\n🏆 校级奖学金1000-3000元",
    "校医院": "🏥 24小时值班\n📞 急诊电话：1200\n📍 位置：学校西门旁",
    "课表查询": f"🔗 [点击进入教务系统]({COURSE_SYSTEM_URL})",
    "成绩查询": f"🔗 [点击进入教务系统]({COURSE_SYSTEM_URL})",
    "绩点": f"🔗 [教务系统查询]({COURSE_SYSTEM_URL})",
    "官网": f"🌐 [学校官网]({SCHOOL_OFFICIAL_URL})",
}

def get_local_answer(question):
    q = question.lower()
    for key, ans in LOCAL_KNOWLEDGE.items():
        if key.lower() in q:
            return ans
    return None

# ========== AI调用 ==========
def call_deepseek(messages, persona_key, use_thinking, search_context):
    full = [{"role": "system", "content": get_system_prompt(persona_key)}]
    
    if use_thinking:
        full.append({"role": "user", "content": "请在回答前展示你的思考过程，用【思考】标注。"})
    
    if search_context:
        full.append({"role": "user", "content": f"以下是联网搜索到的参考信息：\n{search_context}\n请结合这些信息回答。"})
    
    full.extend(messages[-15:])
    
    try:
        r = client.chat.completions.create(
            model="deepseek-chat", 
            messages=full, 
            temperature=0.8, 
            max_tokens=2000, 
            timeout=30
        )
        return r.choices[0].message.content
    except Exception as e:
        print(f"API错误: {e}")
        return None

# ========== 回复函数 ==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    # 热点
    if any(w in lower for w in ["热点", "热搜", "今日热点", "热门"]):
        return get_ai_hot_trending(user_input)
    
    # 本地知识库
    local = get_local_answer(user_input)
    if local:
        return local
    
    # 新闻通知
    if any(w in lower for w in ["新闻", "通知", "公告"]):
        news = fetch_news_from_website()
        if news:
            return "📢 最新通知公告：\n" + "\n".join([f"• {n}" for n in news])
        return f"📢 [查看通知公告]({SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm)"
    
    # 联网搜索
    search_ctx = None
    if enable_search and SEARCH_AVAILABLE:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(user_input, max_results=2))
                if results:
                    search_ctx = "\n".join([f"- {r['title']}\n  {r['body'][:200]}" for r in results])
        except:
            pass
    
    # 调用AI
    history = st.session_state.messages[-15:] if len(st.session_state.messages) > 15 else st.session_state.messages
    msgs = [{"role": m["role"], "content": m["content"]} for m in history]
    resp = call_deepseek(msgs, persona_key, enable_thinking, search_ctx)
    
    if resp:
        return resp
    return f"抱歉，我暂时无法回答这个问题。试试问我：图书馆几点开门？课表怎么查？"

# ========== 自定义CSS（移动端优化）==========
st.markdown(f"""
<style>
    /* 隐藏默认元素 */
    #MainMenu, header, footer {{visibility: hidden; display: none;}}
    .stApp {{background: linear-gradient(135deg, #f5f7fa 0%, #e9edf2 100%);}}
    
    /* 主容器 - 移动端优化 */
    .main .block-container {{
        padding: 0.3rem 0.8rem 70px 0.8rem !important;
        max-width: 100% !important;
    }}
    
    /* 完全隐藏侧边栏 */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* 顶部栏 */
    .mobile-header {{
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        border-radius: 20px;
        padding: 12px 16px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }}
    .mobile-logo {{
        width: 48px;
        height: 48px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 28px;
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
        font-size: 1rem;
        font-weight: 600;
    }}
    .mobile-title p {{
        color: rgba(255,255,255,0.85);
        margin: 4px 0 0 0;
        font-size: 0.7rem;
    }}
    .mobile-motto {{
        background: rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 4px 10px;
        font-size: 0.65rem;
        color: white;
    }}
    
    /* 快捷按钮网格 */
    .quick-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 16px;
    }}
    .quick-card {{
        background: white;
        border: none;
        border-radius: 16px;
        padding: 10px 4px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        font-size: 0.75rem;
        font-weight: 500;
        color: #1a4d8c;
    }}
    .quick-card:active {{
        transform: scale(0.96);
        background: #1a4d8c;
        color: white;
    }}
    .quick-emoji {{
        font-size: 1.3rem;
        display: block;
        margin-bottom: 4px;
    }}
    
    /* 消息气泡优化 */
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
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        color: #1a1a2e;
    }}
    
    /* 输入框固定底部 */
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
        border-radius: 30px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 12px 18px !important;
        font-size: 0.85rem !important;
        background: white !important;
    }}
    .stChatInput button {{
        border-radius: 30px !important;
        background: linear-gradient(135deg, #1a4d8c, #2d6a4f) !important;
        color: white !important;
    }}
    
    /* 折叠菜单美化 */
    details {{
        background: white;
        border-radius: 16px;
        margin-bottom: 12px;
        border: none;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }}
    summary {{
        padding: 12px 16px;
        font-weight: 500;
        color: #1a4d8c;
        cursor: pointer;
        list-style: none;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    summary::-webkit-details-marker {{display: none;}}
    summary::before {{
        content: "⚙️";
        font-size: 1rem;
    }}
    details[open] summary::before {{
        content: "⚙️";
    }}
    .stButton button {{
        border-radius: 30px !important;
        background: #f0f2f5 !important;
        color: #1a4d8c !important;
        border: none !important;
        font-size: 0.75rem !important;
    }}
    
    /* 人格标识 */
    .persona-tag {{
        display: inline-block;
        background: #e8f0fe;
        border-radius: 20px;
        padding: 2px 8px;
        font-size: 0.65rem;
        margin-left: 6px;
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
    <div class="mobile-motto">
        智能小助手
    </div>
</div>

<div class="quick-grid">
    <div class="quick-card" onclick="sendQuickMsg('图书馆几点开门？')">
        <span class="quick-emoji">📚</span>
        图书馆
    </div>
    <div class="quick-card" onclick="sendQuickMsg('食堂有什么好吃的？')">
        <span class="quick-emoji">🍽️</span>
        食堂
    </div>
    <div class="quick-card" onclick="sendQuickMsg('课表查询')">
        <span class="quick-emoji">📅</span>
        课表
    </div>
    <div class="quick-card" onclick="sendQuickMsg('成绩查询')">
        <span class="quick-emoji">📊</span>
        成绩
    </div>
    <div class="quick-card" onclick="sendQuickMsg('今日热点')">
        <span class="quick-emoji">🔥</span>
        热点
    </div>
    <div class="quick-card" onclick="sendQuickMsg('奖学金')">
        <span class="quick-emoji">🏆</span>
        奖学金
    </div>
    <div class="quick-card" onclick="sendQuickMsg('宿舍报修')">
        <span class="quick-emoji">🔧</span>
        宿舍
    </div>
    <div class="quick-card" onclick="sendQuickMsg('校医院')">
        <span class="quick-emoji">🏥</span>
        校医院
    </div>
    <div class="quick-card" onclick="sendQuickMsg('学校官网')">
        <span class="quick-emoji">🌐</span>
        官网
    </div>
</div>

<script>
function sendQuickMsg(msg) {{
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
</script>
""", unsafe_allow_html=True)

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = """👋 你好！我是成工职小助手

---

**👨‍💻 尔主龙彪学长** *AI应用工程师*
> 擅长：AI技术、编程、选课策略
> “这个问题我来帮你分析一下...”

**📊 任乾鹏学长** *数据测试工程师*
> 擅长：考试复习、数据分析、表格
> “据我整理的数据显示...”

**👩‍💻 童妍学姐** *前端开发工程师*
> 擅长：校园生活、社团活动
> “成工生活我超熟的！”

---

💡 **试试问我：**
• 图书馆几点开门？
• 帮我写个Python排序代码
• 生成一张成绩表格
• 今日热点
• 课表怎么查？"""
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": welcome_msg
    })

# ========== 显示历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 折叠设置区（默认折叠）==========
with st.expander("⚙️ 设置与工具", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        enable_thinking = st.checkbox("🧠 深度思考模式", value=False, help="AI会展示思考过程")
    with col2:
        enable_search = st.checkbox("🌐 联网搜索", value=False, help="搜索最新信息")
    
    st.divider()
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🗑️ 清空对话", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col4:
        st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d')}")

# ========== 输入处理 ==========
user_input = st.chat_input("输入你的问题...")
if user_input and user_input.strip():
    # 添加用户消息
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 生成回复
    with st.chat_message("assistant"):
        with st.spinner("🤔 思考中..."):
            # 选择人格
            persona = select_persona(user_input)
            prefix = get_persona_prefix(persona)
            
            # 获取回复
            response = get_ai_response(
                user_input, 
                persona, 
                enable_thinking, 
                enable_search
            )
            
            full_response = prefix + response
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    st.rerun()
