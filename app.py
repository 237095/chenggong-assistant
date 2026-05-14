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
COURSE_SYSTEM_URL = "http://sw.cdivtc.edu.cn/app-web/#/login"

st.set_page_config(
    page_title=f"{SCHOOL_NAME} - 成工职小助手",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"  # 改为expanded，让用户可以折叠侧边栏
)

# ========== 检查校徽 ==========
logo_files = ["school_logo.png", "logo.png", "校徽.png", "school_logo.jpg", "logo.jpg"]
LOGO_PATH = None
for f in logo_files:
    if os.path.exists(f):
        LOGO_PATH = f
        break

# 加载校徽图片为base64（用于头像）
LOGO_BASE64 = None
if LOGO_PATH and os.path.exists(LOGO_PATH):
    try:
        with open(LOGO_PATH, "rb") as img_file:
            LOGO_BASE64 = base64.b64encode(img_file.read()).decode()
    except:
        pass

# ========== 官网新闻提取功能（增强版） ==========
def fetch_news_from_website():
    """从学校官网提取最新新闻 - 增强版，增加多种伪装和备用方案"""
    try:
        # 使用Session保持连接
        session = requests.Session()
        
        # 多个User-Agent轮换
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        # 尝试多个可能的新闻页面
        news_urls = [
            f"{SCHOOL_OFFICIAL_URL}/xwzx/xyyw.htm",
            f"{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm",
            f"{SCHOOL_OFFICIAL_URL}/index.htm",
            f"{SCHOOL_OFFICIAL_URL}/news/",
            f"{SCHOOL_OFFICIAL_URL}/xwzx.htm",
        ]
        
        all_news = []
        
        for url in news_urls:
            try:
                print(f"尝试访问: {url}")
                response = session.get(url, headers=headers, timeout=8)
                
                if response.status_code != 200:
                    print(f"访问失败，状态码: {response.status_code}")
                    continue
                
                # 尝试多种编码
                for encoding in ['utf-8', 'gbk', 'gb2312']:
                    try:
                        response.encoding = encoding
                        soup = BeautifulSoup(response.text, 'html.parser')
                        break
                    except:
                        continue
                
                # 多种选择器尝试
                selectors = [
                    'a', 
                    'a.title', 
                    '.news-title', 
                    '.tit', 
                    '.list-item', 
                    'li a',
                    '.cate_list a',
                    '.news_list a'
                ]
                
                found_news = []
                
                for selector in selectors:
                    links = soup.select(selector)
                    for link in links:
                        title = link.get_text(strip=True)
                        href = link.get('href', '')
                        
                        # 过滤有效新闻
                        if (len(title) > 8 and len(title) < 100 and 
                            any(word in title for word in ['通知', '公告', '活动', '比赛', '讲座', '招聘', '会议', '关于', '开展', '举办', '2025', '2026'])):
                            
                            # 处理相对链接
                            if href.startswith('/'):
                                href = SCHOOL_OFFICIAL_URL + href
                            elif href.startswith('./'):
                                href = SCHOOL_OFFICIAL_URL + href[1:]
                            elif href.startswith('..'):
                                href = SCHOOL_OFFICIAL_URL + href[2:]
                            elif not href.startswith('http'):
                                href = SCHOOL_OFFICIAL_URL + '/' + href
                            
                            # 去重
                            if not any(n['title'] == title for n in found_news):
                                found_news.append({'title': title, 'link': href})
                                
                    if len(found_news) >= 3:
                        break
                
                all_news.extend(found_news[:3])
                
                if len(all_news) >= 6:
                    break
                    
            except requests.Timeout:
                print(f"访问超时: {url}")
                continue
            except Exception as e:
                print(f"解析失败: {url}, 错误: {e}")
                continue
        
        return all_news[:6] if all_news else None
        
    except Exception as e:
        print(f"新闻提取失败: {e}")
        return None

def get_preset_news_links():
    """返回预设的新闻链接（当无法抓取时使用）"""
    return [
        {"title": "📢 访问学校官网获取最新通知公告", "link": SCHOOL_OFFICIAL_URL},
        {"title": "📚 教务系统 - 查询课表成绩", "link": COURSE_SYSTEM_URL},
        {"title": "🏫 招生就业信息", "link": f"{SCHOOL_OFFICIAL_URL}/zsjy.htm"},
        {"title": "🎓 学校新闻中心", "link": f"{SCHOOL_OFFICIAL_URL}/xwzx/xyyw.htm"},
    ]

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
        "avatar": "校徽" if LOGO_BASE64 else "👨‍💻",
        "title": "AI应用工程师 · 组长",
        "style": "技术控、逻辑清晰、耐心解答",
        "greeting": "这个问题我来帮你分析一下...",
    },
    "qianpeng": {
        "name": "任乾鹏",
        "avatar": "校徽" if LOGO_BASE64 else "📊",
        "title": "数据测试工程师",
        "style": "细心、严谨、数据敏感",
        "greeting": "据我整理的数据显示...",
    },
    "tongyan": {
        "name": "童妍",
        "avatar": "校徽" if LOGO_BASE64 else "👩‍💻",
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
    if LOGO_BASE64 and persona['avatar'] == "校徽":
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
3. 适当使用表情符号"""

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
    
    # 教务系统相关
    "课表": f"📅 **课表查询**\n\n请点击下方链接登录教务系统查看：\n\n🔗 {COURSE_SYSTEM_URL}\n\n💡 使用说明：\n1. 点击上方链接进入登录页面\n2. 使用教务系统账号密码登录\n3. 登录后即可查看个人课表",
    
    "成绩": f"📊 **成绩查询**\n\n请通过教务系统查询：\n🔗 {COURSE_SYSTEM_URL}\n\n登录后进入「成绩查询」模块即可查看各科考试成绩",
    
    "绩点": f"📈 **绩点(GPA)查询**\n\n教务系统链接：{COURSE_SYSTEM_URL}\n\n💡 登录后可查看各科绩点",
    
    "教务系统": f"🎓 **教务系统入口**\n\n地址：{COURSE_SYSTEM_URL}\n\n功能包括：选课、课表查询、成绩查询、考试安排",
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

# ========== 核心回复函数 ==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    # 教务系统链接查询
    if any(word in lower for word in ["课表", "课程表", "成绩", "绩点", "gpa", "教务系统", "选课系统", "成绩查询", "查成绩", "看成绩", "我的成绩"]):
        local_answer = get_local_answer(user_input)
        if local_answer:
            return local_answer
    
    # 官网链接查询
    if any(word in lower for word in ["官网链接", "官网地址", "学校官网", "学校网站", "学校网址"]):
        return f"🌐 {SCHOOL_NAME}官方网站：\n\n{SCHOOL_OFFICIAL_URL}\n\n你可以点击访问了解学校最新动态~"
    
    # 官网新闻/通知提取
    if any(word in lower for word in ["新闻", "通知", "公告", "最新", "最近", "有什么活动", "学校有什么", "校园新闻", "近期活动", "学校动态"]):
        with st.spinner("正在从官网获取最新信息..."):
            news = fetch_news_from_website()
            if news and len(news) > 0:
                summarized = summarize_news_with_ai(news, "news")
                if summarized:
                    return f"🔍 我从学校官网找到了这些最新信息：\n\n{summarized}\n\n---\n📌 以上信息来自学校官网，更多详情请点击链接查看~"
                else:
                    # 如果AI总结失败，直接显示新闻列表
                    news_text = "📢 学校官网最新动态：\n\n"
                    for n in news:
                        news_text += f"• {n['title']}\n  链接：{n['link']}\n\n"
                    return news_text
            else:
                # 抓取失败时，给出友好提示和备用链接
                return f"""😅 暂时无法从官网获取最新信息（可能是网络原因）

不过你可以直接访问以下链接查看：

**📌 学校官网**
🔗 {SCHOOL_OFFICIAL_URL}

**📌 新闻中心**
🔗 {SCHOOL_OFFICIAL_URL}/xwzx/xyyw.htm

**📌 通知公告**
🔗 {SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm

**📌 教务系统**
🔗 {COURSE_SYSTEM_URL}

💡 提示：如果链接无法直接访问，请复制到浏览器打开~"""
    
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
            return local if local else f"抱歉，我暂时无法回答「{user_input}」。\n\n试试问我：\n- 图书馆几点开门？\n- 食堂有什么好吃的？\n- 课表查询\n- 成绩查询\n- 学校有什么新闻？"

# ========== CSS 样式（移动端优化） ==========
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp {background: #fafafc;}
    
    /* 桌面端样式 */
    @media (min-width: 769px) {
        .main .block-container {
            max-width: 900px;
            margin: 0 auto;
            padding: 1rem 1rem 5rem 1rem;
        }
        
        .mobile-bottom-nav {
            display: none !important;
        }
    }
    
    /* 移动端样式 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem 0.8rem 70px 0.8rem !important;
        }
        
        .mobile-bottom-nav {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            display: flex;
            justify-content: space-around;
            padding: 8px 12px;
            border-top: 1px solid #e0e0e0;
            z-index: 1000;
            backdrop-filter: blur(10px);
            background: rgba(255,255,255,0.95);
        }
        
        .nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            text-decoration: none;
            color: #666;
            font-size: 0.7rem;
            flex: 1;
            text-align: center;
            padding: 6px 0;
            border-radius: 12px;
            transition: all 0.2s;
        }
        
        .nav-item:hover, .nav-item.active {
            background: #f0f0f0;
            color: #1a4d8c;
        }
        
        .nav-icon {
            font-size: 1.3rem;
        }
        
        [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
            padding: 10px 14px !important;
            font-size: 0.85rem !important;
        }
    }
    
    /* 消息气泡通用 */
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
    <a href="#" class="nav-item" onclick="sendMessage('学校官网'); return false;">
        <span class="nav-icon">🏫</span>
        <span>官网</span>
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
    
    # 模式设置
    enable_thinking = st.toggle("🧠 深度思考模式", value=False)
    enable_search = st.toggle("🌐 联网搜索", value=False)
    
    st.markdown("---")
    
    # 学校官网按钮
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
    if LOGO_BASE64:
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
- 📰 **学校新闻** → 提取最新通知

**试试问我：**
- "图书馆几点开门？"
- "课表查询"
- "我的成绩"
- "绩点怎么算？"
- "学校有什么新闻？"

有什么问题尽管问！😊"""
        })
    else:
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
- 📰 **学校新闻** → 提取最新通知

**试试问我：**
- "图书馆几点开门？"
- "课表查询"
- "我的成绩"
- "绩点怎么算？"
- "学校有什么新闻？"

有什么问题尽管问！😊"""
        })

# ========== 显示历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 快捷问题 ==========
quick_cols = st.columns(5)
quick_list = ["📚 图书馆几点开门", "🍽️ 食堂推荐", "📅 课表查询", "📊 成绩查询", "🏫 学校官网"]

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
