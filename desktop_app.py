"""
成工职小助手 - 电脑端（Dify增强版）
保留所有原有功能：热搜、新闻、本地知识库、人格切换等
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
# 从 Secrets 读取 API Key
DEEPSEEK_API_KEY = st.secrets.get("DEEPSEEK_API_KEY", "")
# 新增：从 session_state 或 secrets 读取 Dify API Key
DIFY_API_KEY = st.secrets.get("DIFY_API_KEY", "") or st.session_state.get("dify_api_key", "")

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DIFY_API_URL = "https://api.dify.ai/v1/chat-messages"

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

LOGO_BASE64 = None
if LOGO_PATH and os.path.exists(LOGO_PATH):
    try:
        with open(LOGO_PATH, "rb") as img_file:
            LOGO_BASE64 = base64.b64encode(img_file.read()).decode()
    except:
        pass

# ========== 获取 Supabase 客户端（仅用于其他功能）==========
def get_supabase_client():
    return st.session_state.get("supabase", None)

# ========== 调用 Dify API ==========
def call_dify_api(query: str, conversation_id: str = "") -> tuple:
    """调用 Dify 的对话 API"""
    if not DIFY_API_KEY:
        return None, ""
    
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conversation_id,
        "user": st.session_state.get("user_student_id", "anonymous")
    }
    
    try:
        response = requests.post(DIFY_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data.get("answer", ""), data.get("conversation_id", "")
    except Exception as e:
        print(f"Dify API 调用失败: {e}")
        return None, conversation_id

# ========== AI 调用（优先 Dify，降级 DeepSeek）==========
def call_ai_with_dify(user_input, conversation_id, rag_context=""):
    """优先使用 Dify，失败则降级到直接调用 DeepSeek"""
    # 尝试 Dify
    if DIFY_API_KEY:
        answer, new_id = call_dify_api(user_input, conversation_id)
        if answer:
            return answer, new_id
    
    # 降级：直接调用 DeepSeek（不经过 RAG）
    if DEEPSEEK_API_KEY:
        try:
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": user_input}],
                temperature=0.8,
                max_tokens=2000
            )
            return response.choices[0].message.content, conversation_id
        except Exception as e:
            print(f"DeepSeek 降级调用失败: {e}")
    
    return None, conversation_id

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

def get_hot_detail_with_ai(keyword):
    """使用AI获取热搜关键词的详细内容"""
    if not DEEPSEEK_API_KEY:
        return None
    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        prompt = f"""请帮我总结一下关于「{keyword}」这个热搜事件的核心内容。

要求：
1. 用2-3句话简洁概括事件
2. 说明为什么会成为热点
3. 给出关键信息点

格式：
📌 **{keyword}**
[事件概括]
🔍 热度原因：[原因说明]"""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300,
            timeout=15
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI总结失败: {e}")
        return None

def format_hot_search_response_with_summary(hot_list, enable_ai_summary=True):
    """格式化热搜数据（带AI总结）"""
    if not hot_list or len(hot_list) == 0:
        return None
    
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    response = f"""🔥 **百度热搜榜** 🔥

📅 更新时间：{now}

"""
    for item in hot_list[:10]:
        idx = item.get('rank', 0)
        keyword = item.get('keyword', '')
        
        if idx <= 3:
            icon = "🔥"
        elif idx <= 10:
            icon = "📈"
        else:
            icon = "●"
        
        response += f"{icon} **{idx}. {keyword}**\n"
        
        if enable_ai_summary:
            summary = get_hot_detail_with_ai(keyword)
            if summary:
                response += f"{summary}\n\n"
            else:
                response += f"> [点击查看详情](https://www.baidu.com/s?wd={keyword})\n\n"
        else:
            response += f"> [点击查看详情](https://www.baidu.com/s?wd={keyword})\n\n"
    return response

def format_hot_search_response_simple(hot_list):
    """简化版热搜显示（仅标题+链接）"""
    if not hot_list or len(hot_list) == 0:
        return None
    
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    response = f"""🔥 **百度热搜榜** 🔥

📅 更新时间：{now}

"""
    for item in hot_list[:15]:
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
    else:
        return "tongyan"

def get_persona_prefix(persona_key, question=None):
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
    persona = PERSONAS[persona_key]
    return f"""你是"{SCHOOL_NAME}的成工职小助手"，你是{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}。

## 你的人格特质
- 说话温暖、亲切、专业

## 回答要求
1. 用温暖亲切的语气
2. 重要信息用**加粗**标注
3. 适当使用表情符号
4. 如果是关于学校的问题，要结合成都工业职业技术学院的实际情况回答
5. 如果是专业推荐、就业等咨询类问题，要给出有建设性的建议"""

# ========== 本地知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 图书馆开放时间：周一至周五 8:00-22:00，周末 9:00-21:00\n📍 位置：图文信息中心1-4层\n💳 凭校园卡借阅，每人限借5本",
    "食堂": "🍽️ 食堂营业时间：早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n\n🍜 推荐：二食堂牛肉面、一食堂麻辣烫\n💳 支持校园卡/支付宝",
    "选课": "📅 选课时间：预选第18周，正选开学前1周，补退选开学第1周\n🔗 登录教务系统进行选课",
    "宿舍": "🔧 宿舍报修：公众号「成工后勤」或联系楼栋管理员\n⏰ 门禁：23:00\n💡 功率限制：800W",
    "校园卡": "💳 充值方式：微信公众号、支付宝、食堂自助机\n🔒 挂失：自助机或公众号",
    "奖学金": "🏆 国家奖学金8000元，申请时间每年9月\n🏆 国家励志奖学金5000元\n🏆 校级奖学金1000-3000元",
    "校医院": "🏥 24小时值班\n📞 急诊电话：1200\n📍 位置：学校西门旁",
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

# ========== 核心回复函数（已禁用 Supabase RAG）==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search, enable_hot_summary=False):
    """核心回复函数 - 优先使用 Dify，禁用 Supabase RAG"""
    
    lower = user_input.lower()
    
    # 百度热点查询
    if any(word in lower for word in ["热点", "热搜", "百度热搜", "热门", "今天有什么热点", "热搜榜", "今日热点"]):
        with st.spinner("正在获取百度热搜..."):
            hot_list = fetch_baidu_hot_search(10)
            if hot_list:
                if enable_hot_summary:
                    formatted = format_hot_search_response_with_summary(hot_list, enable_ai_summary=True)
                else:
                    formatted = format_hot_search_response_simple(hot_list)
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
        answer, _ = call_ai_with_dify(user_input, st.session_state.get("dify_conv_id", ""), "")
        if answer:
            return answer
        full_prompt = f"请生成完整的代码：{user_input}\n要求：完整、有注释、可运行，用```语言名```格式。"
        if DEEPSEEK_API_KEY:
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.8,
                max_tokens=2000
            )
            return response.choices[0].message.content
        return "代码生成暂时不可用"
    
    # 表格生成
    elif any(w in lower for w in ["表格", "表", "成绩单", "课程表"]):
        answer, _ = call_ai_with_dify(user_input, st.session_state.get("dify_conv_id", ""), "")
        if answer:
            return answer
        full_prompt = f"请生成Markdown表格：{user_input}\n要求：标准格式，包含列名和示例数据。"
        if DEEPSEEK_API_KEY:
            client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": full_prompt}],
                temperature=0.8,
                max_tokens=2000
            )
            return response.choices[0].message.content
        return "表格生成暂时不可用"
    
    # 普通问答
    else:
        conv_id = st.session_state.get("dify_conv_id", "")
        
        # 【已禁用】不再使用 Supabase RAG 检索
        # rag_context = search_school_documents(user_input, limit=3)
        
        # 直接调用 Dify，rag_context 传空字符串
        answer, new_conv_id = call_ai_with_dify(user_input, conv_id, "")
        
        if new_conv_id:
            st.session_state.dify_conv_id = new_conv_id
        
        if answer:
            return answer
        
        # 降级到本地知识库
        local = get_local_answer(user_input)
        if local:
            st.info("📖 使用本地知识库")
            return local
        
        return f"关于「{user_input}」，我正在学习中。\n\n💡 **你可以尝试：**\n- 换个方式描述问题\n- 询问校园相关问题（图书馆、食堂、课表等）\n- 问我「今天有什么热点」\n- 让我帮你写代码或生成表格"

# ========== CSS样式 ==========
st.markdown("""
<style>
    .stApp { background: #fafafc; }
    
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
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
        border-right: 1px solid #e6e6e6;
    }
    
    .stButton button {
        border-radius: 25px !important;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ========== 侧边栏 ==========
with st.sidebar:
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
    
    enable_thinking = st.toggle("🧠 深度思考模式", value=False, help="AI会展示思考过程")
    enable_search = st.toggle("🌐 联网搜索", value=False, help="搜索最新信息")
    enable_hot_summary = st.toggle("📝 AI热点总结", value=True, help="AI自动总结每个热点内容")
    
    st.markdown("---")
    
    st.markdown("### 🔥 热搜榜")
    show_hot_search = st.toggle("📊 显示百度热搜", value=True)
    
    if show_hot_search:
        @st.cache_data(ttl=300)
        def get_cached_hot_search():
            return fetch_baidu_hot_search(10)
        
        hot_data = get_cached_hot_search()
        if hot_data:
            st.markdown("---")
            for item in hot_data[:8]:
                idx = item.get('rank', 0)
                keyword = item.get('keyword', '')[:25]
                href = item.get('href', '')
                icon = "🔥" if idx <= 3 else "📌"
                if href:
                    st.markdown(f"{icon} {idx}. [{keyword}]({href})")
                else:
                    st.markdown(f"{icon} {idx}. {keyword}")
            now = datetime.now().strftime("%H:%M")
            st.caption(f"⏰ 更新 {now}")
        else:
            st.info("暂无法获取热搜数据")
    
    st.markdown("---")
    
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
    
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.session_state.dify_conv_id = ""
        st.rerun()
    
    st.markdown("---")
    
    st.markdown("### 👥 开发团队")
    st.markdown("- 尔主龙彪（组长）")
    st.markdown("- 任乾鹏")
    st.markdown("- 童妍")
    st.caption(f"© {SCHOOL_NAME}")

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.dify_conv_id = ""
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
- "有什么好的专业推荐？"
- "图书馆几点开门？"
- "帮我写一个Python排序代码"
- "今天有什么热点？"

有什么问题尽管问！😊"""
    })

# ========== 显示历史消息 ==========
MAX_DISPLAY_MESSAGES = 20
display_messages = st.session_state.messages[-MAX_DISPLAY_MESSAGES:] if len(st.session_state.messages) > MAX_DISPLAY_MESSAGES else st.session_state.messages

for msg in display_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 快捷问题 ==========
quick_cols = st.columns(5)
quick_list = [
    ("有什么好的专业推荐？", "📚 专业推荐"),
    ("图书馆几点开门？", "📚 图书馆"),
    ("课表怎么查？", "📅 课表查询"),
    ("成绩怎么查？", "📊 成绩查询"),
    ("今天有什么热点？", "🔥 今日热点")
]

for idx, (question, display) in enumerate(quick_list):
    with quick_cols[idx]:
        if st.button(display, key=f"quick_{idx}", use_container_width=True):
            with st.chat_message("user"):
                st.markdown(question)
            st.session_state.messages.append({"role": "user", "content": question})
            
            with st.chat_message("assistant"):
                with st.spinner("学长学姐正在思考..."):
                    persona_key = select_persona(question)
                    prefix = get_persona_prefix(persona_key, question)
                    response = get_ai_response(question, persona_key, enable_thinking, enable_search, enable_hot_summary)
                    
                    is_hot = any(word in question.lower() for word in ["热点", "热搜", "今日热点"])
                    if is_hot:
                        full_response = response
                    else:
                        full_response = prefix + response
                    
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()

# ========== 主输入框 ==========
user_input = st.chat_input("输入你的问题...")
if user_input and user_input.strip():
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("assistant"):
        with st.spinner("学长学姐正在思考..."):
            persona_key = select_persona(user_input)
            prefix = get_persona_prefix(persona_key, user_input)
            response = get_ai_response(user_input, persona_key, enable_thinking, enable_search, enable_hot_summary)
            
            is_hot = any(word in user_input.lower() for word in ["热点", "热搜", "今日热点"])
            if is_hot:
                full_response = response
            else:
                full_response = prefix + response
            
            st.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    st.rerun()
