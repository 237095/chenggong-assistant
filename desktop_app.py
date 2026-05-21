"""
成工职小助手 - 电脑端
成都工业职业技术学院 | 三位学长学姐为你服务
"""

import streamlit as st
import os
from openai import OpenAI
from datetime import datetime
import base64
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
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== 检查校徽 ==========
logo_files = ["school_logo.png", "logo.png", "校徽.png", "school_logo.jpg", "logo.jpg"]
LOGO_PATH = None
for f in logo_files:
    if os.path.exists(f):
        LOGO_PATH = f
        break

# 加载校徽图片为base64
LOGO_BASE64 = None
if LOGO_PATH and os.path.exists(LOGO_PATH):
    try:
        with open(LOGO_PATH, "rb") as img_file:
            LOGO_BASE64 = base64.b64encode(img_file.read()).decode()
    except:
        pass

# ========== 百度热搜获取功能 ==========
def fetch_baidu_hot_search(limit=15):
    """获取百度热搜榜数据"""
    try:
        url = "https://api.knowsafe.com/v1/api/hot/baidu"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 1:
                hot_list = data.get('data', [])
                return hot_list[:limit]
        return None
    except Exception as e:
        print(f"获取百度热搜失败: {e}")
        return None

def format_hot_search_response(hot_list):
    """格式化热搜数据"""
    if not hot_list or len(hot_list) == 0:
        return None
    
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    
    response = f"""🔥 **百度热搜榜** 🔥

📅 更新时间：{now}

"""
    for idx, item in enumerate(hot_list, 1):
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
    
    response += """
---
💡 **小提示**：
- 点击标题可查看详情
- 数据来自百度热搜，实时更新
"""
    return response

# ========== 官网新闻提取 ==========
def fetch_news_from_website():
    """从学校官网提取最新新闻"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
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
        "title": "AI应用工程师 · 组长",
        "greeting": "这个问题我来帮你分析一下...",
    },
    "qianpeng": {
        "name": "任乾鹏",
        "avatar": "📊",
        "title": "数据测试工程师",
        "greeting": "据我整理的数据显示...",
    },
    "tongyan": {
        "name": "童妍",
        "avatar": "👩‍💻",
        "title": "前端开发工程师",
        "greeting": "成工生活我超熟的！",
    }
}

def select_persona(question):
    q = question.lower()
    if any(word in q for word in ["python", "java", "html", "代码", "编程", "选课", "ai", "人工智能"]):
        return "longbiao"
    elif any(word in q for word in ["考试", "复习", "数据", "表格", "成绩", "绩点", "课表", "成绩查询"]):
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

## 你的人格特质
- 说话温暖、亲切

## 回答要求
1. 用温暖亲切的语气
2. 重要信息用**加粗**标注
3. 适当使用表情符号"""

# ========== 本地知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 图书馆开放时间：周一至周五 8:00-22:00，周末 9:00-21:00\n📍 位置：图文信息中心1-4层\n💳 凭校园卡借阅，每人限借5本",
    "食堂": "🍽️ 食堂营业时间：早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n\n🍜 推荐：二食堂牛肉面、一食堂麻辣烫\n💳 支持校园卡/支付宝",
    "选课": "📅 选课时间：预选第18周，正选开学前1周，补退选开学第1周\n🔗 登录教务系统进行选课",
    "宿舍": "🔧 宿舍报修：公众号「成工后勤」或联系楼栋管理员\n⏰ 门禁：23:00\n💡 功率限制：800W",
    "校园卡": "💳 充值方式：微信公众号、支付宝、食堂自助机\n🔒 挂失：自助机或公众号",
    "奖学金": "🏆 国家奖学金8000元，申请时间每年9月\n🏆 国家励志奖学金5000元\n🏆 校级奖学金1000-3000元",
    "校医院": "🏥 24小时值班\n📞 急诊电话：1200\n📍 位置：学校西门旁",
    "官网": f"🌐 学校官网：{SCHOOL_OFFICIAL_URL}",
    
    "课表": f"📅 **课表查询**\n\n🔗 {COURSE_SYSTEM_URL}",
    "成绩": f"📊 **成绩查询**\n\n🔗 {COURSE_SYSTEM_URL}",
    "绩点": f"📈 **绩点查询**\n\n🔗 {COURSE_SYSTEM_URL}",
    "教务系统": f"🎓 **教务系统**\n\n🔗 {COURSE_SYSTEM_URL}",
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
        full_messages.append({"role": "user", "content": "请先展示你的💭思考过程，再给出最终答案。"})
    
    if search_context:
        full_messages.append({"role": "user", "content": f"参考信息：\n{search_context}"})
    
    full_messages.extend(messages)
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=full_messages,
            temperature=0.8,
            max_tokens=2000,
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

# ========== 核心回复函数 ==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    # 百度热点查询
    if any(word in lower for word in ["热点", "热搜", "百度热搜", "热门", "今天有什么热点", "热搜榜", "今日热点"]):
        with st.spinner("正在获取百度热搜..."):
            hot_list = fetch_baidu_hot_search(15)
            if hot_list:
                formatted = format_hot_search_response(hot_list)
                if formatted:
                    return formatted
            return "😅 暂时无法获取热搜数据，请稍后再试～"
    
    # 教务系统链接查询
    if any(word in lower for word in ["课表", "课程表", "成绩", "绩点", "gpa", "教务系统", "选课系统", "成绩查询", "查成绩"]):
        local_answer = get_local_answer(user_input)
        if local_answer:
            return local_answer
    
    # 官网链接查询
    if any(word in lower for word in ["官网链接", "官网地址", "学校官网", "学校网站", "学校网址"]):
        return f"🌐 {SCHOOL_NAME}官方网站：\n\n{SCHOOL_OFFICIAL_URL}"
    
    # 官网新闻/通知提取
    if any(word in lower for word in ["新闻", "通知", "公告", "最新", "最近", "有什么活动", "校园新闻"]):
        try:
            news = fetch_news_from_website()
            if news and len(news) > 0:
                news_text = "📢 学校官网最新动态：\n\n"
                for n in news:
                    news_text += f"• **{n['title']}**\n  链接：{n['link']}\n\n"
                return news_text
        except:
            pass
        return get_news_fallback_response()
    
    # 代码生成
    if any(w in lower for w in ["python", "java", "html", "代码", "写一个", "编程", "计算器"]):
        full_prompt = f"请生成完整的代码：{user_input}\n要求：完整、有注释、可运行，用```语言名```格式。"
        response = call_deepseek([{"role": "user", "content": full_prompt}], persona_key, enable_thinking, None)
        return response if response else "代码生成暂时不可用"
    
    # 表格生成
    elif any(w in lower for w in ["表格", "表", "成绩单", "课程表"]):
        full_prompt = f"请生成Markdown表格：{user_input}\n要求：标准格式，包含列名和示例数据。"
        response = call_deepseek([{"role": "user", "content": full_prompt}], persona_key, enable_thinking, None)
        return response if response else "表格生成暂时不可用"
    
    # 本地知识库
    local = get_local_answer(user_input)
    if local:
        return local
    
    # 普通问答
    else:
        search_ctx = None
        if enable_search and SEARCH_AVAILABLE:
            sr = search_online(user_input)
            if sr:
                search_ctx = "\n".join([f"- {s['title']}: {s['body'][:200]}" for s in sr])
        
        response = call_deepseek([{"role": "user", "content": user_input}], persona_key, enable_thinking, search_ctx)
        
        if response:
            return response
        else:
            local = get_local_answer(user_input)
            return local if local else f"抱歉，我暂时无法回答「{user_input}」。\n\n试试问我：\n- 图书馆几点开门？\n- 课表查询\n- 成绩查询\n- 今天有什么热点？"

# ========== CSS样式 ==========
st.markdown("""
<style>
    /* 基本样式 */
    .stApp {
        background: #fafafc;
    }
    
    /* 消息气泡 */
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
        padding: 12px 18px;
        border-radius: 20px;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    [data-testid="stChatMessage"][data-testid="user"] [data-testid="stMarkdown"] {
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        color: white;
        border-radius: 20px 20px 5px 20px;
    }
    
    [data-testid="stChatMessage"][data-testid="assistant"] [data-testid="stMarkdown"] {
        background: white;
        color: #1e1e2f;
        border-radius: 20px 20px 20px 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
        border-right: 1px solid #e6e6e6;
    }
    
    /* 按钮样式 */
    .stButton button {
        border-radius: 25px !important;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* 快捷按钮行 */
    .quick-buttons {
        display: flex;
        gap: 10px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
</style>
""", unsafe_allow_html=True)

# ========== 侧边栏 ==========
with st.sidebar:
    # 校徽和标题
    if LOGO_BASE64:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="data:image/png;base64,{LOGO_BASE64}" width="80" style="border-radius: 50%;">
            <h3 style="margin-top: 10px; color: #1a4d8c;">{SCHOOL_NAME}</h3>
            <p style="color: #666; font-size: 0.8rem;">{SCHOOL_MOTTO}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 20px;">
            <div style="font-size: 60px;">🎓</div>
            <h3 style="margin-top: 10px; color: #1a4d8c;">{SCHOOL_NAME}</h3>
            <p style="color: #666; font-size: 0.8rem;">{SCHOOL_MOTTO}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 模式设置
    st.markdown("### ⚙️ 模式设置")
    enable_thinking = st.toggle("🧠 深度思考模式", value=False, help="AI会展示思考过程")
    enable_search = st.toggle("🌐 联网搜索", value=False, help="搜索最新信息")
    
    st.markdown("---")
    
    # 热点板块
    st.markdown("### 🔥 热搜榜")
    show_hot_search = st.toggle("📊 显示百度热搜", value=True)
    
    if show_hot_search:
        @st.cache_data(ttl=300)
        def get_cached_hot_search():
            return fetch_baidu_hot_search(10)
        
        hot_data = get_cached_hot_search()
        if hot_data:
            st.markdown("---")
            for idx, item in enumerate(hot_data[:8], 1):
                keyword = item.get('keyword', '')[:25]
                href = item.get('href', '')
                
                if idx <= 3:
                    icon = "🔥"
                else:
                    icon = "📌"
                
                if href:
                    st.markdown(f"{icon} {idx}. [{keyword}]({href})")
                else:
                    st.markdown(f"{icon} {idx}. {keyword}")
            
            now = datetime.now().strftime("%H:%M")
            st.caption(f"⏰ 更新 {now}")
        else:
            st.info("暂无法获取热搜数据")
    
    st.markdown("---")
    
    # 快捷链接
    st.markdown("### 🔗 快捷链接")
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; gap: 8px;">
        <a href="{SCHOOL_OFFICIAL_URL}" target="_blank" style="
            background: linear-gradient(135deg, #e8a020 0%, #d4891a 100%);
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: bold;
            text-align: center;
        ">🏫 学校官网</a>
        <a href="{COURSE_SYSTEM_URL}" target="_blank" style="
            background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: bold;
            text-align: center;
        ">📚 教务系统</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 清空对话
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # 开发团队
    st.markdown("### 👥 开发团队")
    st.markdown("- 尔主龙彪（组长）")
    st.markdown("- 任乾鹏")
    st.markdown("- 童妍")
    
    st.caption(f"© {SCHOOL_NAME}")

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"""# 🎓 {SCHOOL_NAME} - 成工职小助手

你好呀！我是由三位学长学姐共同组成的AI助手：

- 👨‍💻 **尔主龙彪学长**：AI、编程、选课
- 📊 **任乾鹏学长**：数据分析、表格、成绩查询
- 👩‍💻 **童妍学姐**：校园生活、社团

---

**📌 快捷功能：**
- 📅 课表查询
- 📊 成绩查询
- 🏫 学校官网
- 🔥 百度热搜

**试试问我：**
- "图书馆几点开门？"
- "课表查询"
- "我的成绩"
- "今天有什么热点？"

有什么问题尽管问！😊"""
    })

# ========== 显示历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 快捷问题 ==========
quick_cols = st.columns(5)
quick_list = ["📚 图书馆几点开门", "🍽️ 食堂推荐", "📅 课表查询", "📊 成绩查询", "🔥 今日热点"]

for idx, q in enumerate(quick_list):
    with quick_cols[idx]:
        if st.button(q, key=f"quick_{idx}", use_container_width=True):
            with st.chat_message("user"):
                st.markdown(q)
            st.session_state.messages.append({"role": "user", "content": q})
            
            with st.chat_message("assistant"):
                with st.spinner("学长学姐正在思考..."):
                    persona_key = select_persona(q)
                    prefix = get_persona_prefix(persona_key)
                    response = get_ai_response(q, persona_key, enable_thinking, enable_search)
                    full_response = prefix + response
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()

# ========== 主输入框 ==========
user_input = st.chat_input("输入你的问题...")
if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("学长学姐正在思考..."):
            persona_key = select_persona(user_input)
            prefix = get_persona_prefix(persona_key)
            response = get_ai_response(user_input, persona_key, enable_thinking, enable_search)
            full_response = prefix + response
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    st.rerun()
