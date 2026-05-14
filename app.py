"""
成工职小助手 - 官网新闻提取版（修复版）
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

st.set_page_config(
    page_title=f"{SCHOOL_NAME} - 成工职小助手",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
)

# ========== 检查校徽 ==========
logo_files = ["school_logo.png", "logo.png", "校徽.png", "school_logo.jpg", "logo.jpg"]
LOGO_PATH = None
for f in logo_files:
    if os.path.exists(f):
        LOGO_PATH = f
        break

# ========== 官网新闻提取功能 ==========
def fetch_news_from_website():
    """从学校官网提取最新新闻"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        news_urls = [
            f"{SCHOOL_OFFICIAL_URL}/xwzx/xyyw.htm",
            f"{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm",
            f"{SCHOOL_OFFICIAL_URL}/index.htm",
        ]
        
        all_news = []
        
        for url in news_urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.encoding = 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    title = link.get_text(strip=True)
                    href = link['href']
                    
                    if len(title) > 10 and any(word in title for word in ['通知', '公告', '活动', '比赛', '讲座', '招聘', '会议']):
                        if href.startswith('/'):
                            href = SCHOOL_OFFICIAL_URL + href
                        elif not href.startswith('http'):
                            href = SCHOOL_OFFICIAL_URL + '/' + href
                        
                        all_news.append({
                            'title': title,
                            'link': href,
                            'source': url
                        })
                        
                        if len(all_news) >= 8:
                            break
            except:
                continue
            
            if len(all_news) >= 8:
                break
        
        return all_news[:6]
    
    except Exception as e:
        print(f"新闻提取失败: {e}")
        return None

def summarize_news_with_ai(news_list, query_type="news"):
    """使用AI总结新闻内容"""
    if not news_list:
        return None
    
    news_text = ""
    for i, news in enumerate(news_list, 1):
        news_text += f"{i}. 【{news['title']}】\n   链接：{news['link']}\n\n"
    
    if query_type == "notice":
        prompt = f"""请根据以下学校通知公告，帮我总结成简洁的回答：

{news_text}

要求：
1. 用温暖亲切的语气回答
2. 列出最重要的3-5条通知
3. 每条通知用一句话概括
4. 提醒用户点击链接查看详情
5. 适当使用表情符号"""
    else:
        prompt = f"""请根据以下学校最新新闻，帮我总结成简洁的回答：

{news_text}

要求：
1. 用温暖亲切的语气回答
2. 列出最重要的3-5条新闻
3. 按时间或重要性排序
4. 提醒用户点击链接查看详情
5. 适当使用表情符号"""
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI总结失败: {e}")
        return None

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
    elif any(word in q for word in ["考试", "复习", "数据", "表格", "成绩"]):
        return "qianpeng"
    elif any(word in q for word in ["食堂", "宿舍", "社团", "校园", "生活", "美食"]):
        return "tongyan"
    else:
        return "tongyan"

def get_persona_prefix(persona_key):
    persona = PERSONAS[persona_key]
    return f"**{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}** {persona['avatar']}\n\n> *{persona['greeting']}*\n\n"

# ========== System Prompt ==========
def get_system_prompt(persona_key):
    persona = PERSONAS[persona_key]
    return f"""你是"{SCHOOL_NAME}的成工职小助手"，你是{persona['name']}{'学长' if persona_key != 'tongyan' else '学姐'}。

## 你的人格特质
- {persona['style']}
- 说话温暖、亲切

## 回答要求
1. 用温暖亲切的语气
2. 重要信息用**加粗**标注
3. 适当使用表情符号"""

# ========== 本地知识库 ==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 图书馆开放时间：周一至周五 8:00-22:00，周末 9:00-21:00",
    "食堂": "🍽️ 食堂营业时间：早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30\n\n🍜 推荐：二食堂牛肉面",
    "选课": "📅 选课时间：预选第18周，正选开学前1周，补退选开学第1周",
    "宿舍": "🔧 宿舍报修：公众号「成工后勤」或联系楼栋管理员",
    "校园卡": "💳 充值方式：微信公众号、支付宝、食堂自助机",
    "奖学金": "🏆 国家奖学金8000元，申请时间每年9月",
    "校医院": "🏥 24小时值班，急诊电话：1200",
    "官网": f"🌐 学校官网：{SCHOOL_OFFICIAL_URL}",
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
            max_tokens=1500,
            timeout=30
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"API调用失败: {e}")
        return None

# ========== 核心回复函数（已修复官网链接）==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    # ===== 官网链接查询（最高优先级）=====
    if any(word in lower for word in ["官网链接", "官网地址", "学校官网", "学校网站", "学校网址"]):
        return f"🌐 {SCHOOL_NAME}官方网站：\n\n{SCHOOL_OFFICIAL_URL}\n\n你可以点击访问了解学校最新动态、通知公告、招生就业等信息~"
    
    # ===== 官网新闻/通知提取 =====
    if any(word in lower for word in ["新闻", "通知", "公告", "最新", "最近", "有什么活动", "学校有什么", "校园新闻", "近期活动", "学校动态"]):
        # 排除纯官网查询
        if "官网" not in lower or ("新闻" in lower or "通知" in lower):
            with st.spinner("正在从官网获取最新信息..."):
                news = fetch_news_from_website()
                if news:
                    summarized = summarize_news_with_ai(news, "news")
                    if summarized:
                        return f"🔍 我从学校官网找到了这些最新信息：\n\n{summarized}\n\n---\n📌 以上信息来自学校官网，更多详情请点击链接查看~"
                    else:
                        news_text = "📢 学校官网最新动态：\n\n"
                        for n in news:
                            news_text += f"• {n['title']}\n  链接：{n['link']}\n\n"
                        return news_text
                else:
                    return f"抱歉，暂时无法获取官网信息。你可以直接访问学校官网：\n\n{SCHOOL_OFFICIAL_URL}"
    
    # ===== 代码生成 =====
    if any(w in lower for w in ["python", "java", "html", "代码", "写一个", "编程", "计算器"]):
        full_prompt = f"请生成完整的代码：{user_input}\n要求：完整、有注释、可运行，用```语言名```格式。"
        response = call_deepseek([{"role": "user", "content": full_prompt}], persona_key, enable_thinking, None)
        return response if response else "代码生成暂时不可用"
    
    # ===== 表格生成 =====
    elif any(w in lower for w in ["表格", "表", "成绩单", "课程表"]):
        full_prompt = f"请生成Markdown表格：{user_input}\n要求：标准格式，包含列名和示例数据。"
        response = call_deepseek([{"role": "user", "content": full_prompt}], persona_key, enable_thinking, None)
        return response if response else "表格生成暂时不可用"
    
    # ===== 普通问答 =====
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
            return local if local else f"抱歉，我暂时无法回答「{user_input}」。\n\n试试问我：\n- 图书馆几点开门？\n- 食堂有什么好吃的？\n- 学校有什么新闻？\n- 用Python写一个计算器"

# ========== CSS 样式 ==========
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp {background: #fafafc;}
    
    .main .block-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 1rem 1rem 5rem 1rem;
    }
    
    [data-testid="stChatMessage"] {
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
        padding: 12px 18px;
        border-radius: 20px;
        font-size: 0.95rem;
        line-height: 1.6;
        word-wrap: break-word;
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
    
    .stChatInput {
        position: sticky;
        bottom: 0;
        background: #fafafc;
        padding-top: 8px;
        z-index: 100;
    }
    
    .stChatInput textarea {
        border-radius: 28px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 12px 20px !important;
    }
    
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e6e6e6;
    }
    
    pre {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 12px;
        overflow-x: auto;
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
    
    if st.button("🏫 学校官网", use_container_width=True):
        import webbrowser
        webbrowser.open(SCHOOL_OFFICIAL_URL)
    
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
        "content": """# 🎓 成工职小助手

你好呀！我是由三位学长学姐共同组成的AI助手：

- 👨‍💻 **尔主龙彪学长**：AI、编程、选课
- 📊 **任乾鹏学长**：数据分析、表格
- 👩‍💻 **童妍学姐**：校园生活、社团

---

**试试问我：**
- "图书馆几点开门？"
- "学校官网" — 直接返回官网链接
- "学校有什么新闻？" — 提取最新通知
- "用Python写一个计算器"

有什么问题尽管问！😊"""
    })

# ========== 显示历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 快捷问题 ==========
quick_cols = st.columns(5)
quick_list = ["📚 图书馆几点开门", "🍽️ 食堂推荐", "📰 学校有什么新闻", "💻 Python计算器", "🏫 学校官网"]

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
