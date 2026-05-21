"""
成工职小助手 - 电脑端版（增强版）
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
import json

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

# ========== 百度热搜功能 ==========
@st.cache_data(ttl=300)
def fetch_baidu_hot_search(limit=15):
    """获取百度热搜榜数据"""
    try:
        url = "https://api.vvhan.com/api/hotlist/baiduRD"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('data'):
                hot_list = data['data'][:limit]
                formatted = []
                for idx, item in enumerate(hot_list, 1):
                    formatted.append({
                        'rank': idx,
                        'title': item.get('title', '')[:50],
                        'hot': item.get('hot', '')
                    })
                return formatted
        return None
    except Exception as e:
        print(f"获取热搜失败: {e}")
        return None

def format_hot_search_response(hot_list):
    """格式化热搜响应"""
    if not hot_list:
        return None
    
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    
    response = f"""🔥 **百度实时热搜榜** 🔥

📅 更新时间：{now}

"""
    for item in hot_list[:12]:
        rank = item['rank']
        title = item['title']
        
        if rank == 1:
            icon = "🥇"
        elif rank == 2:
            icon = "🥈"
        elif rank == 3:
            icon = "🥉"
        elif rank <= 5:
            icon = "🔥"
        elif rank <= 8:
            icon = "📈"
        else:
            icon = "📌"
        
        response += f"{icon} **{rank}. {title}**\n\n"
    
    response += """---
💡 **小提示**：
- 数据来自百度热搜，实时更新
- 点击侧边栏链接可查看完整榜单
"""
    return response

# ========== 官网新闻提取 ==========
@st.cache_data(ttl=600)
def fetch_news_from_website():
    """获取学校官网新闻"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        url = f"{SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm"
        response = requests.get(url, headers=headers, timeout=8)
        if response.status_code != 200:
            return None
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        news_list = []
        for link in soup.find_all('a', href=True):
            title = link.get_text(strip=True)
            href = link['href']
            if 8 < len(title) < 60 and any(kw in title for kw in ['通知', '公告', '公示', '关于']):
                if href.startswith('/'):
                    href = SCHOOL_OFFICIAL_URL + href
                elif not href.startswith('http'):
                    href = SCHOOL_OFFICIAL_URL + '/' + href
                news_list.append({'title': title, 'link': href})
            if len(news_list) >= 5:
                break
        return news_list if news_list else None
    except:
        return None

# ========== 三位学长学姐的人格设定 ==========
PERSONAS = {
    "longbiao": {
        "name": "尔主龙彪",
        "avatar": "👨‍💻",
        "style": "技术控、逻辑清晰",
        "greeting": "这个问题我来帮你分析一下...",
        "expertise": "AI技术、编程开发、选课策略"
    },
    "qianpeng": {
        "name": "任乾鹏",
        "avatar": "📊",
        "style": "细心、严谨",
        "greeting": "据我整理的数据显示...",
        "expertise": "数据分析、成绩查询、考试复习"
    },
    "tongyan": {
        "name": "童妍",
        "avatar": "👩‍💻",
        "style": "热情、细心", 
        "greeting": "成工生活我超熟的！",
        "expertise": "校园生活、社团活动、食堂美食"
    }
}

def select_persona(question):
    q = question.lower()
    if any(word in q for word in ["python", "java", "html", "代码", "编程", "写一个", "计算器"]):
        return "longbiao"
    elif any(word in q for word in ["成绩", "绩点", "课表", "考试", "复习", "数据", "表格"]):
        return "qianpeng"
    elif any(word in q for word in ["食堂", "宿舍", "社团", "校园", "生活", "美食", "活动"]):
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
- {persona['style']}
- 擅长：{persona['expertise']}
- 说话温暖、亲切、有耐心

## 回答要求
1. 用温暖亲切的语气回复，像学长学姐一样帮助同学
2. 重要信息用**加粗**标注
3. 适当使用表情符号让回复更生动
4. 回复要详细、有帮助，不要过于简短
5. 如果是问路、问时间等生活问题，给出具体建议
6. 如果是学习问题，耐心解答并给出学习方法

## 学校信息
- 学校名称：{SCHOOL_NAME}
- 校训：{SCHOOL_MOTTO}
- 官网：{SCHOOL_OFFICIAL_URL}
- 教务系统：{COURSE_SYSTEM_URL}"""

# ========== 本地知识库（扩展版）==========
LOCAL_KNOWLEDGE = {
    "图书馆": "📚 **图书馆信息**\n\n⏰ 开放时间：周一至周五 8:00-22:00，周末 9:00-21:00\n\n📖 借阅规则：学生最多可借10册，借期30天\n\n📍 位置：学校正门右侧，教学楼A栋旁",
    "食堂": "🍽️ **食堂指南**\n\n⏰ 营业时间：\n- 早餐：6:30-9:00\n- 午餐：11:00-13:30\n- 晚餐：17:00-19:30\n\n🍜 推荐美食：\n- 一食堂：冒菜、小炒\n- 二食堂：牛肉面、盖浇饭\n- 三食堂：自助餐、麻辣烫",
    "宿舍": "🏠 **宿舍信息**\n\n🔧 报修方式：\n- 公众号「成工后勤」\n- 联系楼栋管理员\n- 拨打后勤电话\n\n🕐 熄灯时间：23:00（周五周六23:30）\n\n💡 温馨提示：注意用电安全，不使用违规电器",
    "选课": "📅 **选课指南**\n\n⏰ 时间安排：\n- 预选：第18周\n- 正选：开学前1周\n- 补退选：开学第1周\n\n💡 选课建议：\n1. 提前查看培养方案\n2. 了解课程考核方式\n3. 咨询学长学姐经验",
    "校园卡": "💳 **校园卡使用指南**\n\n💰 充值方式：\n- 微信公众号充值\n- 支付宝充值\n- 食堂自助机充值\n\n🔄 挂失补办：带上学生证到卡务中心办理\n\n📍 卡务中心：学生服务中心一楼",
    "奖学金": "🏆 **奖学金信息**\n\n💰 国家奖学金：8000元/年（每年9月申请）\n💰 国家励志奖学金：5000元/年\n💰 学校奖学金：一等2000元、二等1000元、三等500元\n\n📝 申请条件：成绩优异、综合表现突出",
    "校医院": "🏥 **校医院信息**\n\n⏰ 门诊时间：8:30-17:30\n🚑 急诊：24小时值班\n📞 急诊电话：1200\n📍 地址：学生公寓6栋一楼\n\n💊 就诊流程：带上校园卡和学生证",
    "转专业": "📝 **转专业流程**\n\n⏰ 申请时间：大一第二学期\n📋 申请条件：\n- 第一学期成绩排名前30%\n- 无违纪记录\n\n📌 流程：提交申请→学院审核→面试→公示",
    "社团": "🎉 **社团活动**\n\n📌 主要社团：\n- 学生会\n- 社团联合会\n- 青年志愿者协会\n- 各专业协会\n\n📅 招新时间：每年9-10月\n💡 建议：参加1-2个感兴趣的社团即可",
    "就业": "💼 **就业指导**\n\n📌 服务内容：\n- 职业规划咨询\n- 简历修改指导\n- 模拟面试练习\n- 招聘信息发布\n\n📍 就业指导中心：行政楼203室",
}

def get_local_answer(question):
    q = question.lower()
    for key, answer in LOCAL_KNOWLEDGE.items():
        if key in q:
            return answer
    return None

# ========== AI 调用（增强版）==========
def call_deepseek(messages, persona_key, use_thinking=False, search_context=None):
    full_messages = [{"role": "system", "content": get_system_prompt(persona_key)}]
    
    if use_thinking:
        full_messages.append({"role": "user", "content": "请先展示你的💭思考过程，再给出最终答案。"})
    
    if search_context:
        full_messages.append({"role": "user", "content": f"以下是一些参考信息，可以帮助你回答：\n{search_context}"})
    
    # 取最近30条对话保持上下文
    recent_messages = messages[-30:] if len(messages) > 30 else messages
    full_messages.extend(recent_messages)
    
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

# ========== 核心回复函数（增强版）==========
def get_ai_response(user_input, persona_key, enable_thinking, enable_search):
    lower = user_input.lower()
    
    # ===== 热点查询 =====
    if any(word in lower for word in ["热点", "热搜", "今日热点", "热搜榜", "最近什么火", "今天有什么热点"]):
        with st.spinner("正在获取百度热搜..."):
            hot_list = fetch_baidu_hot_search(15)
            if hot_list:
                formatted = format_hot_search_response(hot_list)
                if formatted:
                    return formatted
            # 热点查询的AI备用方案
            prompt = f"""用户问：{user_input}

请根据你的知识，分享当前比较热门的网络话题（8-10个），涵盖科技、娱乐、社会、教育等领域。

要求：
1. 分类展示（如：科技圈、娱乐圈、社会热点等）
2. 每个话题用一句话简单介绍
3. 用🔥📈✨🎯等表情符号标记热度
4. 最后提醒用户可以去百度热搜查看实时详情

请用温暖亲切的语气回复。"""
            response = call_deepseek([{"role": "user", "content": prompt}], persona_key, enable_thinking, None)
            return response if response else "🔥 查看百度热搜：https://top.baidu.com"
    
    # ===== 学校新闻 =====
    if any(word in lower for word in ["新闻", "通知", "公告", "学校动态", "校园新闻", "最新通知"]):
        with st.spinner("正在获取学校最新通知..."):
            news = fetch_news_from_website()
            if news:
                response = "📢 **学校官网最新通知**\n\n"
                for n in news:
                    response += f"• **{n['title']}**\n  🔗 [查看详情]({n['link']})\n\n"
                return response
            else:
                return f"📢 暂时无法获取最新通知\n\n🔗 [点击访问学校官网]({SCHOOL_OFFICIAL_URL}/xwzx/tzgg.htm) 查看公告"
    
    # ===== 教务链接 =====
    if any(word in lower for word in ["课表", "课程表", "成绩", "绩点", "gpa", "教务系统", "选课"]):
        local = get_local_answer(user_input)
        if local:
            return local + f"\n\n🔗 [点击进入教务系统]({COURSE_SYSTEM_URL})"
    
    # ===== 本地知识库查询 =====
    local_answer = get_local_answer(user_input)
    if local_answer:
        return local_answer
    
    # ===== 代码生成 =====
    if any(word in lower for word in ["代码", "写一个", "编程", "python", "java", "javascript", "html", "css"]):
        prompt = f"""用户要求：{user_input}

请生成完整的代码，要求：
1. 代码要完整可运行
2. 添加详细注释
3. 用```语言名```格式包裹
4. 附带简单的使用说明"""
        response = call_deepseek([{"role": "user", "content": prompt}], persona_key, enable_thinking, None)
        return response if response else "代码生成失败，请稍后再试~"
    
    # ===== 通用问答（增强版）=====
    else:
        # 联网搜索
        search_ctx = None
        if enable_search and SEARCH_AVAILABLE:
            with st.spinner("正在联网搜索..."):
                search_ctx = search_online(user_input)
        
        # 获取历史消息
        history_messages = st.session_state.messages[-15:] if len(st.session_state.messages) > 15 else st.session_state.messages
        messages_for_api = []
        for msg in history_messages:
            if msg["role"] in ["user", "assistant"]:
                messages_for_api.append({"role": msg["role"], "content": msg["content"][:500]})  # 限制长度
        
        messages_for_api.append({"role": "user", "content": user_input})
        
        response = call_deepseek(messages_for_api, persona_key, enable_thinking, search_ctx)
        
        if response:
            return response
        else:
            return f"抱歉，我暂时无法回答「{user_input}」。\n\n试试问我：\n- 图书馆几点开门？\n- 食堂有什么好吃的？\n- 课表查询\n- 成绩查询\n- 今天有什么热点？"

# ========== CSS样式 ==========
st.markdown("""
<style>
    #MainMenu, header, footer {visibility: hidden;}
    .stApp {background: #f5f7fb;}
    
    .main .block-container {
        max-width: 900px;
        margin: 0 auto;
        padding: 1rem 2rem 5rem 2rem;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8f9fa 100%);
        border-right: 1px solid #e6e6e6;
        width: 280px;
    }
    
    [data-testid="stChatMessage"] [data-testid="stMarkdown"] {
        padding: 14px 20px;
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
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .stChatInput textarea {
        border-radius: 28px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 12px 20px !important;
        font-size: 0.95rem !important;
    }
    
    .stButton button {
        border-radius: 25px !important;
        background: #f0f2f5 !important;
        transition: all 0.2s;
    }
    
    .stButton button:hover {
        background: #e0e4e8 !important;
        transform: translateY(-1px);
    }
    
    pre {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 14px;
        overflow-x: auto;
    }
    
    code {
        font-family: 'Fira Code', monospace;
        font-size: 0.85rem;
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
    
    # 设置选项
    enable_thinking = st.toggle("🧠 深度思考模式", value=False, help="AI会展示思考过程")
    enable_search = st.toggle("🌐 联网搜索", value=False, help="搜索最新信息（需要联网）")
    
    st.markdown("---")
    
    # 快捷链接
    st.markdown("### 🔗 快捷链接")
    st.markdown(f"[🏫 学校官网]({SCHOOL_OFFICIAL_URL})")
    st.markdown(f"[📚 教务系统]({COURSE_SYSTEM_URL})")
    st.markdown(f"[🔥 百度热搜](https://top.baidu.com)")
    
    st.markdown("---")
    
    # 对话统计
    msg_count = len(st.session_state.get("messages", []))
    st.caption(f"📝 对话条数：{msg_count}")
    st.caption("✨ AI可记住最近20条对话")
    
    st.markdown("---")
    
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 👥 开发团队")
    st.markdown("- 👨‍💻 **尔主龙彪**（组长）")
    st.markdown("- 📊 **任乾鹏**")
    st.markdown("- 👩‍💻 **童妍**")
    st.markdown("---")
    st.caption(f"© {SCHOOL_NAME} | 成工职小助手")

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"""# 🎓 {SCHOOL_NAME} - 成工职小助手

> 你的校园智能助手，随时为你服务！

---

## 👥 三位学长学姐为你服务

| 成员 | 角色 | 擅长领域 |
|------|------|----------|
| 👨‍💻 **尔主龙彪学长** | AI应用工程师 | AI技术、编程开发、选课策略 |
| 📊 **任乾鹏学长** | 数据测试工程师 | 数据分析、成绩查询、考试复习 |
| 👩‍💻 **童妍学姐** | 前端开发工程师 | 校园生活、社团活动、食堂美食 |

---

## 💡 试试问这些：

| 类别 | 问题示例 |
|------|----------|
| 📚 校园生活 | "图书馆几点开门？"、"食堂有什么好吃的？" |
| 📅 学习相关 | "课表查询"、"成绩查询"、"奖学金怎么申请？" |
| 🔥 热点资讯 | "今日热点"、"学校有什么新闻？" |
| 💻 技术帮助 | "用Python写个计算器"、"帮我写一段代码" |

---

## ✨ 特色功能

- 🧠 **深度思考模式**：查看AI的推理过程
- 🌐 **联网搜索**：获取最新信息
- 📊 **表格生成**：自动生成Markdown表格
- 💬 **连续对话**：记住上下文，聊天更自然

有什么问题尽管问我！😊
"""
    })

# ========== 显示历史消息 ==========
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ========== 快捷按钮 ==========
quick_cols = st.columns(5)
quick_questions = [
    ("📚 图书馆", "图书馆几点开门？"),
    ("🍽️ 食堂", "食堂有什么好吃的？"),
    ("📅 课表", "课表查询"),
    ("📊 成绩", "成绩查询"),
    ("🔥 热点", "今日热点")
]

for idx, (btn_text, full_q) in enumerate(quick_questions):
    with quick_cols[idx]:
        if st.button(btn_text, key=f"quick_{idx}", use_container_width=True):
            with st.chat_message("user"):
                st.markdown(full_q)
            st.session_state.messages.append({"role": "user", "content": full_q})
            
            with st.chat_message("assistant"):
                with st.spinner("学长学姐正在思考..."):
                    persona_key = select_persona(full_q)
                    prefix = get_persona_prefix(persona_key)
                    response = get_ai_response(full_q, persona_key, enable_thinking, enable_search)
                    full_response = prefix + response
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.rerun()

# ========== 主输入框 ==========
user_input = st.chat_input("输入你的问题，学长学姐为你解答...")
if user_input and user_input.strip():
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
