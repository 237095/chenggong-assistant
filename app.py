"""
成工职小助手 - 完整版（AI智能热点 + 长对话记忆）
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

# ========== AI智能热点获取功能 ==========
def get_ai_hot_trending(user_query):
    prompt = f"""用户问：{user_query}

请根据你掌握的知识，回答当前网络热点话题。

要求：
1. 列出10-15个当前热门话题（涵盖科技、娱乐、社会、教育、校园等）
2. 每个话题用一句话简单介绍
3. 用🔥📈💡✨🎯等表情符号标记热度
4. 分类展示：
   🔥 热搜爆款（最热门的3-5个）
   📈 持续热议（讨论度高的）
   💡 新鲜话题（刚出现的）
   🎯 校园相关（学生关心的）
5. 最后提示用户可以去百度热搜官网查看实时详情"""
    
    response = call_deepseek([{"role": "user", "content": prompt}], "tongyan", False, None)
    return response if response else get_hot_search_fallback()

def get_hot_search_fallback():
    return f"""🔥 **查看今日热点**

💡 想了解最新热点，你可以：

### 🔗 [点击查看百度热搜榜](https://top.baidu.com)
### 🔗 [点击查看微博热搜榜](https://s.weibo.com/top/summary)

---

**或者直接问我具体话题**，比如：
- "AI有什么新闻？"
- "最近有什么好看的电影？"
- "科技圈有什么大事？"
- "教育领域有什么新政策？"

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
            if len(all_news) >= 6:
                break
        return all_news[:6] if all_news else None
    except Exception as e:
        print(f"新闻提取失败: {e}")
        return None

def get_news_fallback_response():
    return f"""📢 **查看学校最新通知和新闻**

**🔗 通知公告** {SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm

**🔗 学校官网首页** {SCHOOL_OFFICIAL_URL}

**🔗 教务系统** {COURSE_SYSTEM_URL}"""

# ========== 三位学长学姐的人格设定 ==========
PERSONAS = {
    "longbiao": {
        "name": "尔主龙彪",
        "avatar": "👨‍💻",
        "title": "AI应用工程师 · 组长",
        "style": "技术控、逻辑清晰、耐心解答",
        "greeting": "这个问题我来帮你分析一下...",
    },
    "qianpeng": {
        "name": "任乾鹏",
        "avatar": "📊",
        "title": "数据测试工程师",
        "style": "细心、严谨、数据敏感",
        "greeting": "据我整理的数据显示...",
    },
    "tongyan": {
        "name": "童妍",
        "avatar": "👩‍💻",
        "title": "前端开发工程师",
        "style": "热情、细心、善于沟通", 
        "greeting": "成工生活我超熟的！",
    }
}

def select_persona(question):
    q = question.lower()
    if any(word in q for word in ["python", "java", "html", "代码", "编程", "选课"]):
        return "longbiao"
    elif any(word in q for word in ["考试", "复习", "数据", "表格", "成绩", "绩点", "课表", "成绩查询"]):
        return "qianpeng"
    elif any(word in q for word in ["食堂", "宿舍", "社团", "校园", "生活", "美食"]):
        return "tongyan"
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

## 你的人格特质
- {persona['style']}
- 说话温暖、亲切

## 回答要求
1. 用温暖亲切的语气
2. 重要信息用**加粗**标注
3. 适当使用表情符号
4. 记住之前的对话内容，保持上下文连贯"""

# ========== 本地知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 图书馆开放时间：周一至周五 8:00-22:00，周末 9:00-21:00\n\n💡 借阅规则：学生最多可借10册，借期30天",
    "食堂": "🍽️ 食堂营业时间：早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n\n🍜 推荐：二食堂牛肉面、一食堂冒菜",
    "选课": "📅 选课时间：预选第18周，正选开学前1周，补退选开学第1周\n\n💡 选课前请先查看培养方案",
    "宿舍": "🔧 宿舍报修：公众号「成工后勤」或联系楼栋管理员\n\n🕐 熄灯时间：23:00（周五周六23:30）",
    "校园卡": "💳 充值方式：微信公众号、支付宝、食堂自助机\n\n🔄 挂失补办：带上学生证到卡务中心",
    "奖学金": "🏆 国家奖学金8000元，申请时间每年9月\n🏆 国家励志奖学金5000元",
    "校医院": "🏥 24小时值班，急诊电话：1200\n💊 校医院地址：学生公寓6栋一楼",
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
    
    recent_messages = messages[-30:] if len(messages) > 30 else messages
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
        with st.spinner("AI正在为你整理热点话题..."):
            return get_ai_hot_trending(user_input)
    
    if any(word in lower for word in ["课表", "课程表", "成绩", "绩点", "gpa", "教务系统", "选课系统", "成绩查询", "查成绩", "看成绩", "我的成绩"]):
        local_answer = get_local_answer(user_input)
        if local_answer:
            return local_answer
    
    if any(word in lower for word in ["官网链接", "官网地址", "学校官网", "学校网站", "学校网址"]):
        return f"🌐 {SCHOOL_NAME}官方网站：\n\n{SCHOOL_OFFICIAL_URL}\n\n你可以点击访问了解学校最新动态~"
    
    if any(word in lower for word in ["新闻", "通知", "公告", "最新", "最近", "有什么活动", "学校有什么", "校园新闻", "近期活动", "学校动态"]):
        try:
            with st.spinner("正在获取官网信息..."):
                news = fetch_news_from_website()
                if news and len(news) > 0:
                    news_text = "📢 学校官网最新动态：\n\n"
                    for n in news:
                        news_text += f"• **{n['title']}**\n  链接：{n['link']}\n\n"
                    return news_text
        except:
            pass
        return get_news_fallback_response()
    
    if any(w in lower for w in ["python", "java", "html", "代码", "写一个", "编程", "计算器"]):
        full_prompt = f"请生成完整的代码：{user_input}\n要求：完整、有注释、可运行，用```语言名```格式。"
        response = call_deepseek([{"role": "user", "content": full_prompt}], persona_key, enable_thinking, None)
        return response if response else "代码生成暂时不可用"
    
    elif any(w in lower for w in ["表格", "表", "成绩单", "课程表"]):
        full_prompt = f"请生成Markdown表格：{user_input}\n要求：标准格式，包含列名和示例数据。"
        response = call_deepseek([{"role": "user", "content": full_prompt}], persona_key, enable_thinking, None)
        return response if response else "表格生成暂时不可用"
    
    else:
        search_ctx = None
        if enable_search and SEARCH_AVAILABLE:
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(user_input, max_results=2))
                    if results:
                        search_ctx = "\n".join([f"- {r['title']}: {r['body'][:200]}" for r in results])
            except:
                pass
        
        history_messages = st.session_state.messages[-30:] if len(st.session_state.messages) > 30 else st.session_state.messages
        messages_for_api = [{"role": msg["role"], "content": msg["content"]} for msg in history_messages]
        
        response = call_deepseek(messages_for_api, persona_key, enable_thinking, search_ctx)
        
        if response:
            return response
        else:
            local = get_local_answer(user_input)
            return local if local else f"抱歉，我暂时无法回答「{user_input}」。\n\n试试问我：\n- 图书馆几点开门？\n- 食堂有什么好吃的？\n- 课表查询\n- 成绩查询\n- 学校有什么新闻？\n- 今天有什么热点？"

# ========== CSS样式（完整版，不隐藏侧边栏）==========
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp {background: #fafafc;}
    
    /* 桌面端样式 */
    @media (min-width: 769px) {
        .main .block-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 1rem 2rem 5rem 2rem;
        }
        
        .mobile-bottom-nav {
            display: none !important;
        }
        
        /* 桌面端侧边栏正常显示 */
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid #e6e6e6;
            width: 280px;
            min-width: 280px;
        }
    }
    
    /* 移动端样式 */
    @media (max-width: 768px) {
        /* 移动端隐藏侧边栏，用底部导航栏代替 */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        /* 主内容区域全屏显示 */
        .main .block-container {
            padding: 0.5rem 0.8rem 80px 0.8rem !important;
            max-width: 100% !important;
            margin: 0 !important;
        }
        
        /* 消息气泡 */
        [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
            padding: 10px 14px !important;
            font-size: 0.85rem !important;
            max-width: 85%;
        }
        
        /* 输入框 */
        .stChatInput {
            position: fixed;
            bottom: 65px;
            left: 0;
            right: 0;
            background: #fafafc;
            padding: 8px 12px;
            z-index: 100;
            border-top: 1px solid #e0e0e0;
        }
        
        .stChatInput textarea {
            border-radius: 28px !important;
            border: 1px solid #e0e0e0 !important;
            padding: 12px 16px !important;
            font-size: 0.9rem !important;
        }
    }
    
    /* 消息气泡通用 */
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
    
    pre {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 12px;
        overflow-x: auto;
    }
</style>

<!-- 移动端底部导航栏 -->
<div class="mobile-bottom-nav" id="mobileNav">
    <a href="#" class="nav-item" onclick="sendMessage('图书馆几点开门？'); return false;">
        <span class="nav-icon">📚</span>
        <span>图书馆</span>
    </a>
    <a href="#" class="nav-item" onclick="sendMessage('课表查询'); return false;">
        <span class="nav-icon">📅</span>
        <span>课表</span>
    </a>
    <a href="#" class="nav-item" onclick="sendMessage('成绩查询'); return false;">
        <span class="nav-icon">📊</span>
        <span>成绩</span>
    </a>
    <a href="#" class="nav-item" onclick="sendMessage('今日热点'); return false;">
        <span class="nav-icon">🔥</span>
        <span>热搜</span>
    </a>
    <a href="#" class="nav-item" onclick="sendMessage('食堂有什么好吃的？'); return false;">
        <span class="nav-icon">🍽️</span>
        <span>食堂</span>
    </a>
</div>

<script>
function sendMessage(msg) {
    const input = document.querySelector('.stChatInput textarea');
    if (input) {
        input.value = msg;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        const button = document.querySelector('.stChatInput button');
        if (button) button.click();
    }
}
</script>
<div class="mobile-bottom-nav" id="mobileNav">
    <a href="#" class="nav-item" onclick="sendMessage('图书馆几点开门？'); return false;">
        <span class="nav-icon">📚</span>
        <span>图书馆</span>
    </a>
    <a href="#" class="nav-item" onclick="sendMessage('课表查询'); return false;">
        <span class="nav-icon">📅</span>
        <span>课表</span>
    </a>
    <a href="#" class="nav-item" onclick="sendMessage('成绩查询'); return false;">
        <span class="nav-icon">📊</span>
        <span>成绩</span>
    </a>
    <a href="#" class="nav-item" onclick="sendMessage('今日热点'); return false;">
        <span class="nav-icon">🔥</span>
        <span>热搜</span>
    </a>
    <a href="#" class="nav-item" onclick="sendMessage('食堂有什么好吃的？'); return false;">
        <span class="nav-icon">🍽️</span>
        <span>食堂</span>
    </a>
</div>

<script>
function sendMessage(msg) {
    const input = document.querySelector('.stChatInput textarea');
    if (input) {
        input.value = msg;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        const button = document.querySelector('.stChatInput button');
        if (button) button.click();
    }
}
</script>
""", unsafe_allow_html=True)

# ========== 侧边栏（完整功能）==========
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
    
    # 对话历史统计
    msg_count = len(st.session_state.get("messages", []))
    st.caption(f"📝 对话历史: {msg_count} 条")
    st.caption("✨ AI可记住最近30条")
    st.markdown("---")
    
    enable_thinking = st.toggle("🧠 深度思考模式", value=False)
    enable_search = st.toggle("🌐 联网搜索", value=False)
    
    st.markdown("---")
    st.markdown("### 🔥 热点板块")
    st.info("💡 问我「今日热点」即可获取AI整理的热点话题！")
    
    st.markdown("---")
    
    # 学校官网按钮（HTML样式）
    st.markdown(f"""
    <a href="{SCHOOL_OFFICIAL_URL}" target="_blank" style="
        display: block;
        width: 100%;
        background: linear-gradient(135deg, #e8a020 0%, #d4891a 100%);
        color: white;
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
        cursor: pointer;
    ">🏫 学校官网</a>
    """, unsafe_allow_html=True)
    
    # 教务系统按钮
    st.markdown(f"""
    <a href="{COURSE_SYSTEM_URL}" target="_blank" style="
        display: block;
        width: 100%;
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        color: white;
        text-decoration: none;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
        cursor: pointer;
    ">📚 教务系统</a>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
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
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"""# 🎓 {SCHOOL_NAME} - 成工职小助手

你好呀！我是由三位学长学姐共同组成的AI助手：

- 👨‍💻 **尔主龙彪学长**：AI、编程、选课
- 📊 **任乾鹏学长**：数据分析、表格、成绩查询
- 👩‍💻 **童妍学姐**：校园生活、社团

---

**📌 快捷功能：**
- 📅 **课表查询** → 教务系统链接
- 📊 **成绩查询** → 查看考试成绩和绩点
- 🏫 **学校官网** → 了解学校动态
- 🔥 **今日热点** → AI智能整理热点话题

**试试问我：**
- "图书馆几点开门？"
- "课表查询"
- "我的成绩"
- "今天有什么热点？"
- "用Python写一个计算器"

💡 **新功能**：我可以记住最近30条对话，连续聊天更流畅！

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
