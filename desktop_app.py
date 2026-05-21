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

# ========== 百度热搜功能（新增）==========
@st.cache_data(ttl=300)
def fetch_baidu_hot_search(limit=12):
    """获取百度热搜榜数据"""
    try:
        url = "https://api.vvhan.com/api/hotlist/baiduRD"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                hot_list = data['data'][:limit]
                return hot_list
        return None
    except Exception as e:
        print(f"获取热搜失败: {e}")
        return None

def format_hot_search_response(hot_list):
    """格式化热搜为文本"""
    if not hot_list:
        return None
    
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    
    result = f"🔥 **百度热搜榜**\n\n📅 {now}\n\n"
    
    for idx, item in enumerate(hot_list, 1):
        title = item.get('title', '')[:45]
        
        if idx == 1:
            icon = "🥇"
        elif idx == 2:
            icon = "🥈"
        elif idx == 3:
            icon = "🥉"
        elif idx <= 5:
            icon = "🔥"
        else:
            icon = "📌"
        
        result += f"{icon} {idx}. {title}\n\n"
    
    result += "\n💡 数据来自百度热搜"
    return result

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
    if any(word in q for word in ["python", "java", "html", "代码", "编程", "写一个"]):
        return "longbiao"
    elif any(word in q for word in ["成绩", "绩点", "课表", "考试", "数据", "表格"]):
        return "qianpeng"
    elif any(word in q for word in ["食堂", "宿舍", "社团", "校园", "生活", "美食"]):
        return "tongyan"
    else:
        return "tongyan"

def get_persona_prefix(persona_key):
    persona = PERSONAS[persona_key]
    return f"**{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}** {persona['avatar']}\n\n> *{persona['greeting']}*\n\n"

def get_system_prompt(persona_key):
    persona = PERSONAS[persona_key]
    return f"""你是"{SCHOOL_NAME}的成工职小助手"，你是{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}。

人格特质：{persona['style']}，说话温暖亲切。重要信息用**加粗**。回答要详细有用，不要过于简短。"""

# ========== 本地知识库（扩展）==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 开放时间：周一至周五 8:00-22:00，周末 9:00-21:00\n\n借阅规则：学生最多可借10册，借期30天",
    "食堂": "🍽️ 早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n\n推荐：一食堂冒菜、二食堂牛肉面、三食堂自助餐",
    "宿舍": "🏠 报修：公众号「成工后勤」或联系楼栋管理员\n\n熄灯时间：23:00（周五周六23:30）",
    "校园卡": "💳 充值：微信公众号、支付宝、食堂自助机\n\n挂失补办：带学生证到卡务中心",
    "奖学金": "🏆 国家奖学金8000元、国家励志奖学金5000元\n\n申请时间：每年9月",
    "校医院": "🏥 24小时值班，急诊电话：1200\n\n地址：学生公寓6栋一楼",
    "选课": "📅 预选第18周，正选开学前1周，补退选开学第1周",
    "课表": f"📅 教务系统：{COURSE_SYSTEM_URL}",
    "成绩": f"📊 教务系统：{COURSE_SYSTEM_URL}",
    "绩点": f"📈 教务系统：{COURSE_SYSTEM_URL}",
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
        full_messages.append({"role": "user", "content": "请先展示思考过程，再给出答案。"})
    
    if search_context:
        full_messages.append({"role": "user", "content": f"参考信息：{search_context}"})
    
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
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

# ========== 联网搜索 ==========
def search_online(query):
    if not SEARCH_AVAILABLE:
        return None
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=2))
            if results:
                return "\n".join([f"- {r['title']}: {r['body'][:200]}" for r in results])
    except:
        return None
    return None

# ========== 核心回复函数 ==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    # ===== 热点查询（返回真实内容）=====
    if any(word in lower for word in ["热点", "热搜", "今日热点", "热搜榜"]):
        hot_list = fetch_baidu_hot_search(12)
        if hot_list:
            formatted = format_hot_search_response(hot_list)
            if formatted:
                return formatted
        # API失效时用AI生成热点内容
        prompt = f"""用户问：{user_input}

请根据你的知识，列出8-10个当前热门话题（涵盖科技、娱乐、社会、教育等），每个话题用一句话介绍，用表情符号标记热度。

要求：不要只给链接，要给出具体的热点内容。"""
        response = call_deepseek([{"role": "user", "content": prompt}], persona_key, enable_thinking, None)
        return response if response else "暂时无法获取热搜，请稍后再试~"
    
    # ===== 新闻通知 =====
    if any(word in lower for word in ["新闻", "通知", "公告"]):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            url = f"{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm"
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                news_list = []
                for link in soup.find_all('a', href=True):
                    title = link.get_text(strip=True)
                    if 8 < len(title) < 50 and any(kw in title for kw in ['通知', '公告']):
                        news_list.append(f"• {title}")
                    if len(news_list) >= 5:
                        break
                if news_list:
                    return "📢 **最新通知**\n\n" + "\n\n".join(news_list) + f"\n\n🔗 详情：{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm"
        except:
            pass
        return f"📢 查看通知公告：{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm"
    
    # ===== 教务链接 =====
    if any(word in lower for word in ["课表", "成绩", "绩点", "教务系统"]):
        local = get_local_answer(user_input)
        if local:
            return local
    
    # ===== 本地知识库 =====
    local_answer = get_local_answer(user_input)
    if local_answer:
        return local_answer
    
    # ===== 代码生成 =====
    if any(word in lower for word in ["代码", "写一个", "编程"]):
        prompt = f"""请生成完整代码：{user_input}
要求：代码完整、有注释、可运行，用```语言名```格式。"""
        response = call_deepseek([{"role": "user", "content": prompt}], persona_key, enable_thinking, None)
        return response if response else "代码生成失败，请稍后再试~"
    
    # ===== 普通问答 =====
    else:
        # 联网搜索
        search_ctx = None
        if enable_search and SEARCH_AVAILABLE:
            search_ctx = search_online(user_input)
        
        # 历史消息
        history_messages = st.session_state.messages[-15:] if len(st.session_state.messages) > 15 else st.session_state.messages
        messages_for_api = [{"role": msg["role"], "content": msg["content"]} for msg in history_messages if msg["role"] != "system"]
        messages_for_api.append({"role": "user", "content": user_input})
        
        response = call_deepseek(messages_for_api, persona_key, enable_thinking, search_ctx)
        
        if response:
            return response
        else:
            local = get_local_answer(user_input)
            return local if local else f"抱歉，无法回答「{user_input}」。\n\n试试问：\n- 图书馆几点开门？\n- 食堂有什么好吃的？\n- 课表查询\n- 今日热点"

# ========== CSS（原版样式）==========
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
    enable_search = st.toggle("🌐 联网搜索", value=False)
    
    st.markdown("---")
    st.markdown(f"[🏫 学校官网]({SCHOOL_OFFICIAL_URL})")
    st.markdown(f"[📚 教务系统]({COURSE_SYSTEM_URL})")
    st.markdown(f"[🔥 百度热搜](https://top.baidu.com)")
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
        "content": f"""# 🎓 {SCHOOL_NAME} - 成工职小助手

你好！我是由三位学长学姐共同组成的AI助手：

- 👨‍💻 **尔主龙彪学长**：AI、编程、选课
- 📊 **任乾鹏学长**：数据分析、成绩查询
- 👩‍💻 **童妍学姐**：校园生活、社团

---

**试试问我：**
- "图书馆几点开门？"
- "食堂有什么好吃的？"
- "课表查询"
- "我的成绩"
- "今日热点"
- "用Python写个计算器"
"""
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
                    response = get_ai_response(full_q, persona, enable_thinking, enable_search)
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
            response = get_ai_response(user_input, persona, enable_thinking, enable_search)
            st.markdown(prefix + response)
            st.session_state.messages.append({"role": "assistant", "content": prefix + response})
    st.rerun()
