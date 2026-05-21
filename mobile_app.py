"""
成工职小助手 - 手机端（界面优化版）
成都工业职业技术学院 | 三位学长学姐为你服务
"""

import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import base64
import requests
import json
import re
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

# ========== 百度热搜获取功能 ==========
def fetch_baidu_hot_search(limit=15):
    """直接从百度热搜页面抓取数据"""
    try:
        url = "https://top.baidu.com/board?tab=realtime"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://top.baidu.com/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return None
        
        html_content = response.text
        json_match = re.search(r'<!--s-data:({.*?})-->', html_content, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(1)
            data = json.loads(json_str)
            cards = data.get('data', {}).get('cards', [])
            if cards:
                hot_list = cards[0].get('content', [])
                result = []
                for idx, item in enumerate(hot_list, 1):
                    if idx > limit:
                        break
                    keyword = item.get('query', '')
                    if not keyword:
                        continue
                    result.append({
                        'keyword': keyword,
                        'href': f"https://www.baidu.com/s?wd={keyword}",
                        'hot_score': item.get('hotScore', ''),
                        'rank': idx
                    })
                return result
        return None
    except Exception as e:
        print(f"获取百度热搜失败: {e}")
        return None

def format_hot_search_response_simple(hot_list):
    """简化版热搜显示"""
    if not hot_list or len(hot_list) == 0:
        return None
    
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    response = f"""🔥 **百度热搜榜** 🔥

📅 更新时间：{now}

"""
    for item in hot_list[:10]:
        idx = item.get('rank', 0)
        keyword = item.get('keyword', '')
        href = item.get('href', '')
        
        if idx <= 3:
            icon = "🔥"
        elif idx <= 10:
            icon = "📈"
        else:
            icon = "●"
        
        if href:
            response += f"{icon} **{idx}. [{keyword}]({href})**\n\n"
        else:
            response += f"{icon} **{idx}. {keyword}**\n\n"
    return response

# ========== 官网新闻提取 ==========
def fetch_news_from_website():
    """从学校官网提取最新新闻"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
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
            if len(all_news) >= 6:
                break
        return all_news[:6] if all_news else None
    except Exception as e:
        print(f"新闻提取失败: {e}")
        return None

def get_news_fallback_response():
    return f"""📢 **查看学校最新通知和新闻**

**🔗 通知公告**
{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm

**🔗 学校官网首页**
{SCHOOL_OFFICIAL_URL}

**🔗 教务系统**
{COURSE_SYSTEM_URL}"""

# ========== 三位学长学姐的人格设定 ==========
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

def select_persona(question):
    q = question.lower()
    if any(w in q for w in ["python", "java", "代码", "编程", "选课"]):
        return "longbiao"
    elif any(w in q for w in ["成绩", "课表", "数据", "表格", "绩点"]):
        return "qianpeng"
    return "tongyan"

def get_persona_prefix(persona_key, question=None):
    """获取人格前缀，只有校园生活问题才显示口头禅"""
    persona = PERSONAS[persona_key]
    base_prefix = f"**{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}** {persona['avatar']}"
    
    if question:
        q = question.lower()
        campus_keywords = ["食堂", "宿舍", "社团", "校园", "生活", "美食", "活动", "操场", "教学楼", "图书馆", "校医院", "奖学金"]
        is_campus_question = any(word in q for word in campus_keywords)
        
        if is_campus_question and persona_key == "tongyan":
            return f"{base_prefix}\n\n> *{persona['greeting']}*\n\n"
    
    return f"{base_prefix}\n\n"

def get_system_prompt(persona_key):
    """精简版系统提示词"""
    persona = PERSONAS[persona_key]
    return f"你是成都工业职业技术学院的AI助手{persona['name']}。说话亲切温暖，帮助解答问题。"

# ========== 本地知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 开放时间：周一至周五 8:00-22:00，周末 9:00-21:00\n📍 位置：图文信息中心1-4层",
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
def call_deepseek(messages, persona_key, use_thinking, search_context):
    """调用DeepSeek API - 使用deepseek-v4-flash模型"""
    system_prompt = get_system_prompt(persona_key)
    
    full = [{"role": "system", "content": system_prompt}]
    
    if use_thinking:
        full.append({"role": "user", "content": "请先展示你的💭思考过程，再给出答案。"})
    
    if search_context:
        full.append({"role": "user", "content": f"参考信息：\n{search_context}"})
    
    full.extend(messages[-10:])  # 限制历史消息为10轮
    
    try:
        r = client.chat.completions.create(
            model="deepseek-v4-flash",  # 使用最新V4模型
            messages=full,
            temperature=0.8,
            max_tokens=1500,
            timeout=30
        )
        return r.choices[0].message.content
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

# ========== 回复函数 ==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    # 热点查询
    if any(w in lower for w in ["热点", "热搜", "今日热点"]):
        hot_list = fetch_baidu_hot_search(10)
        if hot_list:
            formatted = format_hot_search_response_simple(hot_list)
            if formatted:
                return formatted
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
    history = st.session_state.messages[-10:] if len(st.session_state.messages) > 10 else st.session_state.messages
    msgs = [{"role": m["role"], "content": m["content"]} for m in history if m["role"] != "system"]
    resp = call_deepseek(msgs, persona_key, enable_thinking, search_ctx)
    
    if resp:
        return resp
    return f"抱歉，无法回答。试试问：图书馆几点开门？"

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.enable_thinking = False
    st.session_state.enable_search = False
    st.session_state.show_settings = False
    
    welcome_msg = """👋 **你好！我是成工职小助手**

---

**👨‍💻 尔主龙彪学长** - AI、编程、选课

**📊 任乾鹏学长** - 数据、成绩、表格

**👩‍💻 童妍学姐** - 校园生活、社团

---

💡 **试试问我：**
- 有什么好的专业推荐？
- 图书馆几点开门？
- 帮我写个Python代码
- 今日热点有哪些？"""
    
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# ========== 自定义CSS（移动端优化 - 带折叠按钮）==========
st.markdown(f"""
<style>
    /* 隐藏默认元素 */
    #MainMenu, header, footer {{visibility: hidden; display: none;}}
    .stApp {{background: #f5f7fb;}}
    
    /* 主容器 */
    .main .block-container {{
        padding: 0.3rem 0.8rem 70px 0.8rem !important;
        max-width: 100% !important;
    }}
    
    /* 隐藏侧边栏 */
    [data-testid="stSidebar"], [data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* 顶部栏 - 校徽始终显示 */
    .mobile-header {{
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        border-radius: 20px;
        padding: 10px 16px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
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
    
    /* 折叠设置按钮 - 固定在顶部右侧 */
    .settings-toggle-btn {{
        background: rgba(255,255,255,0.2);
        border: none;
        border-radius: 30px;
        padding: 6px 12px;
        color: white;
        font-size: 0.75rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
        transition: all 0.2s;
    }}
    .settings-toggle-btn:active {{
        background: rgba(255,255,255,0.35);
        transform: scale(0.96);
    }}
    
    /* 快捷按钮网格 - 3x3布局 */
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
        font-size: 0.7rem;
        font-weight: 500;
        color: #1a4d8c;
    }}
    .quick-card:active {{
        transform: scale(0.96);
        background: #1a4d8c;
        color: white;
    }}
    .quick-emoji {{
        font-size: 1.2rem;
        display: block;
        margin-bottom: 4px;
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
        border-radius: 25px !important;
        border: 1px solid #ddd !important;
        padding: 10px 16px !important;
        font-size: 0.85rem !important;
    }}
    
    /* Streamlit原生折叠按钮美化 */
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
    details[open] summary {{
        border-bottom: 1px solid #eee;
    }}
    
    /* 按钮样式 */
    .stButton button {{
        border-radius: 25px !important;
        background: #f0f2f5 !important;
        color: #1a4d8c !important;
        border: none !important;
        font-size: 0.75rem !important;
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
</div>

<div class="quick-grid">
    <div class="quick-card" onclick="sendMsg('有什么好的专业推荐？')">
        <span class="quick-emoji">📚</span>专业推荐
    </div>
    <div class="quick-card" onclick="sendMsg('图书馆几点开门？')">
        <span class="quick-emoji">📚</span>图书馆
    </div>
    <div class="quick-card" onclick="sendMsg('食堂有什么好吃的？')">
        <span class="quick-emoji">🍽️</span>食堂
    </div>
    <div class="quick-card" onclick="sendMsg('课表查询')">
        <span class="quick-emoji">📅</span>课表
    </div>
    <div class="quick-card" onclick="sendMsg('成绩查询')">
        <span class="quick-emoji">📊</span>成绩
    </div>
    <div class="quick-card" onclick="sendMsg('今日热点')">
        <span class="quick-emoji">🔥</span>热点
    </div>
    <div class="quick-card" onclick="sendMsg('奖学金')">
        <span class="quick-emoji">🏆</span>奖学金
    </div>
    <div class="quick-card" onclick="sendMsg('宿舍报修')">
        <span class="quick-emoji">🔧</span>宿舍
    </div>
    <div class="quick-card" onclick="sendMsg('校医院')">
        <span class="quick-emoji">🏥</span>校医院
    </div>
</div>

<script>
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
</script>
""", unsafe_allow_html=True)

# ========== 显示历史消息（限制显示数量）==========
MAX_DISPLAY_MESSAGES = 15
display_messages = st.session_state.messages[-MAX_DISPLAY_MESSAGES:] if len(st.session_state.messages) > MAX_DISPLAY_MESSAGES else st.session_state.messages

for msg in display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 折叠设置面板（使用Streamlit原生expander）==========
with st.expander("⚙️ 设置与工具", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        enable_thinking = st.toggle("🧠 深度思考", value=st.session_state.enable_thinking)
        st.session_state.enable_thinking = enable_thinking
    with col2:
        enable_search = st.toggle("🌐 联网搜索", value=st.session_state.enable_search)
        st.session_state.enable_search = enable_search
    
    st.divider()
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown(f"[🏫 官网]({SCHOOL_OFFICIAL_URL})")
    with col4:
        st.markdown(f"[📚 教务系统]({COURSE_SYSTEM_URL})")
    
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d')}")

# ========== 输入处理 ==========
user_input = st.chat_input("输入你的问题...")
if user_input and user_input.strip():
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("学长学姐正在思考..."):
            persona = select_persona(user_input)
            prefix = get_persona_prefix(persona, user_input)
            response = get_ai_response(
                user_input, 
                persona, 
                st.session_state.enable_thinking, 
                st.session_state.enable_search
            )
            
            # 热点查询不加人格前缀
            is_hot = any(word in user_input.lower() for word in ["热点", "热搜", "今日热点"])
            if is_hot:
                full_response = response
            else:
                full_response = prefix + response
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    st.rerun()
