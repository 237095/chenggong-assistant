"""
成工职小助手 - 基于DeepSeek大模型
成都工业职业技术学院 | 智能AI客服 | 支持移动端 | 多功能增强版
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

# 尝试导入联网搜索
try:
    from duckduckgo_search import DDGS
    SEARCH_AVAILABLE = True
except ImportError:
    SEARCH_AVAILABLE = False

# ========== 配置 ==========
DEEPSEEK_API_KEY = "sk-a79bb0ea54fb499eb301759f8f0a3924"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"


# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL
)

# ========== 学校信息 ==========
SCHOOL_NAME = "成都工业职业技术学院"
SCHOOL_SHORT = "成工职院"
SCHOOL_MOTTO = "立德树人 精工强技"

# 页面配置
st.set_page_config(
    page_title=f"{SCHOOL_NAME} - 成工职小助手",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="auto"
)

# ========== 检查校徽图片 ==========
logo_files = ["school_logo.png", "logo.png", "校徽.png", "school_logo.jpg", "logo.jpg"]
LOGO_PATH = None
for f in logo_files:
    if os.path.exists(f):
        LOGO_PATH = f
        break

# ========== System Prompt ==========
SYSTEM_PROMPT = """你是"成工职小助手"，由三位亲切的学长学姐共同为你服务！

## 👨‍💻 三位学长学姐介绍

### 1. 尔主龙彪学长（项目组长/AI应用工程师）
- **擅长**：AI技术、编程问题、选课策略、代码生成、图片分析
- **口头禅**："这个问题我来帮你分析一下..."

### 2. 任乾鹏学长（数据测试工程师）
- **擅长**：考试复习、数据分析、表格生成、知识库整理
- **口头禅**："据我整理的数据显示..."

### 3. 童妍学姐（前端开发工程师）
- **擅长**：校园生活、社团活动、界面设计、创意写作
- **口头禅**："成工生活我超熟的！"

## 特殊能力
- **表格生成**：可以生成各种数据表格
- **代码生成**：可以编写Python、Java、HTML/CSS等代码
- **图片分析**：可以描述和分析图片内容
- **深度思考**：复杂问题会展示推理过程

## 回答规则
1. 根据问题类型，由最擅长的学长/学姐回答
2. 代码用```语言名```格式展示
3. 表格用markdown表格格式
4. 深度思考时展示💭思考过程
"""

# ========== 本地应急回复 ==========
LOCAL_RESPONSES = {
    "图书馆": "📚 图书馆开放时间：周一至周五 8:00-22:00，周末 9:00-21:00",
    "食堂": "🍽️ 食堂营业时间：早餐6:30-9:00，午餐11:00-13:30，晚餐17:00-19:30",
    "选课": "📖 选课时间：预选第18周，正选开学前1周",
    "宿舍": "🏠 宿舍报修：公众号「成工后勤」在线报修",
    "奖学金": "🏆 国家奖学金8000元，申请时间每年9月",
    "你好": "你好呀！我是成工职小助手，有什么可以帮你的？😊"
}

def get_local_response(question):
    q = question.lower()
    for key, resp in LOCAL_RESPONSES.items():
        if key in q:
            return resp
    return None

# ========== 移动端适配CSS ==========
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* 移动端适配 */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem !important;
        }
        .school-title h1 {
            font-size: 1.2rem !important;
        }
        .logo-placeholder {
            width: 50px !important;
            height: 50px !important;
        }
        .stButton > button {
            padding: 0.4rem 0.8rem !important;
            font-size: 0.8rem !important;
            min-height: 44px !important;
        }
        .stTextInput > div > div > input {
            padding: 0.6rem 0.8rem !important;
            font-size: 0.9rem !important;
            min-height: 44px !important;
        }
        .function-card {
            padding: 0.8rem !important;
        }
        .sidebar-title h3 {
            font-size: 1rem !important;
        }
    }
    
    /* 桌面端样式 */
    .main-header {
        background: linear-gradient(135deg, #1a4d8c 0%, #2d6a4f 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
    }
    .school-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 20px;
        flex-wrap: wrap;
    }
    .logo-placeholder {
        width: 80px;
        height: 80px;
        background: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .school-title {
        text-align: center;
    }
    .school-title h1 {
        color: white;
        font-size: 2rem;
        margin: 0;
    }
    .motto {
        color: #e8a020;
        font-style: italic;
        margin-top: 8px;
    }
    
    /* 侧边栏 */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a4d8c 0%, #0d3b66 100%);
        color: white;
    }
    
    /* 按钮 */
    .stButton > button {
        background: linear-gradient(135deg, #e8a020 0%, #d4891a 100%);
        color: white;
        border: none;
        border-radius: 25px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        opacity: 0.9;
    }
    
    /* 功能卡片 */
   /* 功能卡片 */
    .feature-card {
        background: rgba(26, 77, 140, 0.8);
        padding: 1rem;
        border-radius: 15px;
        margin: 10px 0;
        border-left: 4px solid #e8a020;
        color: white;
    }
    .function-card {
        background: rgba(26, 77, 140, 0.8);
        padding: 1rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        border: 1px solid rgba(255,255,255,0.2);
        text-align: center;
        color: white;
    }
    
    /* 侧边栏元素 */
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
    }
    .sidebar-title {
        text-align: center;
        margin-top: 1rem;
    }
    .sidebar-title h3 {
        color: white;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

# ========== 联网搜索功能 ==========
def search_online(query, max_results=3):
    if not SEARCH_AVAILABLE:
        return None
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if results:
                search_results = []
                for r in results:
                    search_results.append({
                        "title": r.get('title', ''),
                        "body": r.get('body', '')[:300],
                        "link": r.get('href', '')
                    })
                return search_results
    except Exception as e:
        print(f"搜索失败: {e}")
    return None

# ========== DeepSeek API 调用 ==========
def call_deepseek_api(messages, enable_thinking=False, search_results=None):
    """调用 DeepSeek API，支持深度思考"""
    
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # 添加深度思考提示
    if enable_thinking:
        thinking_hint = "请展示你的思考过程，用💭标记，然后给出最终答案。"
        full_messages.append({"role": "user", "content": thinking_hint})
    
    if search_results:
        search_context = "以下是联网搜索到的相关信息：\n\n"
        for r in search_results[:2]:
            search_context += f"- {r['title']}: {r['body'][:200]}\n"
        full_messages.append({"role": "user", "content": search_context})
    
    full_messages.extend(messages)
    
    # 重试机制
    for attempt in range(3):
        try:
            params = {
                "model": "deepseek-chat",
                "messages": full_messages,
                "temperature": 0.7,
                "max_tokens": 2000 if enable_thinking else 1200,
                "stream": False,
                "timeout": 45
            }
            
            response = client.chat.completions.create(**params)
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"API调用失败 (尝试 {attempt+1}/3): {e}")
            if attempt == 2:
                return None
            time.sleep(2)
    
    return None

# ========== 图片生成提示 ==========
def generate_image(prompt):
    """图片生成提示"""
    return f"""🎨 **图片生成请求**

你请求生成："{prompt}"

💡 提示：如需真正的AI图片生成，可以：
1. 使用 DALL-E API (OpenAI)
2. 使用 Stable Diffusion (本地部署)
3. 使用 Midjourney

**推荐提示词：**
{prompt}, 校园风格, 温馨, 专业

你可以复制上面的提示词到其他AI绘图工具使用。"""

# ========== 初始化会话 ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
    welcome_msg = f"""**你好呀！** 👋

我们是**{SCHOOL_NAME}的成工职小助手**团队！

## ✨ 我能帮你做什么？

### 📚 校园问答
图书馆、食堂、选课、宿舍、奖学金...

### 💻 代码生成
用Python写一个计算器、用HTML写一个网页...

### 📊 表格生成
生成成绩表、课程表、数据统计表...

### 🎨 图片分析
描述图片内容、生成图片提示词

### 🧠 深度思考
开启后我会展示推理过程

---

💡 **试试问我：**
- "用Python写一个计算器"
- "生成一个课程表"
- "图书馆几点开门？"
- "给我学习建议"

有什么问题尽管问，我们都会用心回答！😊"""
    
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# ========== 侧边栏 ==========
with st.sidebar:
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        try:
            logo = Image.open(LOGO_PATH)
            st.image(logo, width=80)
        except:
            st.markdown('<div style="font-size: 3rem; background: white; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">🎓</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-size: 3rem; background: white; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">🎓</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="sidebar-title">
        <h3>成工职小助手</h3>
        <p>成都工业职业技术学院</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # 功能设置
    st.markdown("### ⚙️ 设置")
    enable_thinking = st.toggle("🧠 深度思考模式", value=False, help="开启后AI会展示思考过程")
    enable_search = st.toggle("🌐 联网搜索", value=False, help="开启后可以搜索最新信息")
    
    st.markdown("---")
    
    # 团队成员卡片
    st.markdown("""
    <div class="feature-card">
        <strong>👥 开发团队</strong><br>
        👨‍💻 尔主龙彪 - AI应用工程师（组长）<br>
        👨‍💻 任乾鹏 - 数据测试工程师<br>
        👩‍💻 童妍 - 前端开发工程师
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        welcome_msg = f"""**你好呀！** 👋

我们是**{SCHOOL_NAME}的成工职小助手**团队！

✨ 我能帮你做校园问答、代码生成、表格生成、图片分析等

有什么问题尽管问！😊"""
        st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
        st.rerun()
    
    st.markdown("---")
    st.caption(f"© {SCHOOL_NAME} | 多功能增强版")

# ========== 主内容区 ==========
# 学校标题区
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    title_html = f"""
    <div class="main-header">
        <div class="school-header">
            <div class="logo-placeholder">
    """
    
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        try:
            img = Image.open(LOGO_PATH)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            title_html += f'<img src="data:image/png;base64,{img_str}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">'
        except:
            title_html += '🎓'
    else:
        title_html += '🎓'
    
    title_html += f"""
            </div>
            <div class="school-title">
                <h1>🏫 {SCHOOL_NAME}</h1>
                <p>成工职小助手 | 智能AI客服 | 多功能增强版</p>
                <div class="motto">「 {SCHOOL_MOTTO} 」</div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(title_html, unsafe_allow_html=True)

# 功能提示卡片
if enable_thinking:
    st.info("🧠 **深度思考模式已开启** - 我会展示思考过程，然后给出答案", icon="💭")
if enable_search:
    st.info("🌐 **联网搜索已开启** - 我会搜索最新信息来回答问题", icon="🔍")

# 状态指示
status_cols = st.columns(4)
with status_cols[0]:
    st.info("🤖 **AI在线**", icon="🤖")
with status_cols[1]:
    st.info("📚 **DeepSeek**", icon="📚")
with status_cols[2]:
    st.info(f"🧠 {'开启' if enable_thinking else '关闭'}", icon="💭")
with status_cols[3]:
    st.info(f"🌐 {'开启' if enable_search else '关闭'}", icon="🌐")

# 功能展示卡片
st.markdown("### ✨ 功能展示")
func_cols = st.columns(4)
with func_cols[0]:
    st.markdown('<div class="function-card">💻<br><strong>代码生成</strong><br><span style="font-size:0.7rem">Python/Java/HTML</span></div>', unsafe_allow_html=True)
with func_cols[1]:
    st.markdown('<div class="function-card">📊<br><strong>表格生成</strong><br><span style="font-size:0.7rem">数据表格/课程表</span></div>', unsafe_allow_html=True)
with func_cols[2]:
    st.markdown('<div class="function-card">🎨<br><strong>图片分析</strong><br><span style="font-size:0.7rem">描述/提示词生成</span></div>', unsafe_allow_html=True)
with func_cols[3]:
    st.markdown('<div class="function-card">🧠<br><strong>深度思考</strong><br><span style="font-size:0.7rem">推理过程展示</span></div>', unsafe_allow_html=True)

# ========== 图片上传功能 ==========
with st.expander("🖼️ 图片分析（上传图片进行分析）", expanded=False):
    uploaded_file = st.file_uploader("选择图片", type=["png", "jpg", "jpeg", "gif"], label_visibility="collapsed")
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, width=200)
        if st.button("分析图片", key="analyze_img"):
            st.session_state.messages.append({"role": "user", "content": f"[图片分析] 请分析这张图片的内容"})
            with st.spinner("正在分析图片..."):
                response = f"🎨 **图片分析结果**\n\n这是一张图片，根据文件名和内容推测：\n- 文件类型: {uploaded_file.type}\n- 图片尺寸: {image.size}\n\n如需更详细的分析，可以使用专业的图片识别API。"
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

# ========== 聊天消息显示 ==========
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages[-30:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# ========== 快捷问题 ==========
st.markdown("---")
st.caption("💡 快速提问")

quick_questions = [
    "📚 图书馆几点开门？",
    "🍽️ 食堂有什么好吃的？",
    "💻 用Python写一个猜数字游戏",
    "📊 生成一个成绩表格",
    "🎨 帮我写一个图片生成提示词"
]

cols = st.columns(5)
for i, q in enumerate(quick_questions):
    with cols[i]:
        if st.button(q, key=f"quick_{i}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": q})
            
            with st.spinner("三位学长学姐正在思考..."):
                # 限制历史长度
                MAX_HISTORY = 8
                recent = st.session_state.messages[-MAX_HISTORY:] if len(st.session_state.messages) > MAX_HISTORY else st.session_state.messages
                api_messages = [{"role": m["role"], "content": m["content"]} for m in recent if m["role"] != "system"]
                
                # 智能处理不同问题类型
                if "Python" in q or "代码" in q or "写" in q:
                    # 代码生成 - 真正的AI生成
                    code_prompt = f"""请根据以下需求生成完整的、可运行的代码：

需求：{q}

要求：
1. 代码要完整、可直接运行
2. 添加必要的注释说明
3. 包含示例用法
4. 用```语言名```格式包裹

请直接输出完整代码。"""
                    temp_messages = [{"role": "user", "content": code_prompt}]
                    response = call_deepseek_api(temp_messages, enable_thinking, None)
                    if response is None:
                        response = "```python\n# AI服务暂时不可用，请稍后重试\n```"
                elif "表格" in q or "成绩" in q:
                    # 表格生成
                    table_prompt = f"""请根据以下需求生成一个Markdown格式的表格：

需求：{q}

要求：
1. 用Markdown表格格式输出
2. 包含合适的列名
3. 提供3-5行示例数据

请直接输出表格。"""
                    temp_messages = [{"role": "user", "content": table_prompt}]
                    response = call_deepseek_api(temp_messages, enable_thinking, None)
                    if response is None:
                        response = "| 项目 | 内容 |\n|------|------|\n| 示例1 | 数据1 |\n| 示例2 | 数据2 |"
                elif "图片" in q or "提示词" in q:
                    response = generate_image(q)
                else:
                    search_results = None
                    if enable_search and SEARCH_AVAILABLE:
                        search_results = search_online(q)
                    response = call_deepseek_api(api_messages, enable_thinking, search_results)
                    
                    if response is None:
                        response = get_local_response(q)
                        if response is None:
                            response = "抱歉，AI服务暂时有点问题。你可以稍后再试。"
                
                st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()

# ========== 输入框 ==========
st.markdown("---")

with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input(
            "问题",
            placeholder="输入你的问题... 例如：用Python写一个计算器、生成课程表、图书馆几点开门",
            key="user_input",
            label_visibility="collapsed"
        )
    with col2:
        submitted = st.form_submit_button("发送 📤", use_container_width=True)
    
    if submitted and user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        with st.spinner("三位学长学姐正在思考..."):
            # 限制历史长度
            MAX_HISTORY = 8
            recent = st.session_state.messages[-MAX_HISTORY:] if len(st.session_state.messages) > MAX_HISTORY else st.session_state.messages
            api_messages = [{"role": m["role"], "content": m["content"]} for m in recent if m["role"] != "system"]
            
            # 智能识别功能类型
            user_lower = user_input.lower()
            
            # ===== 代码生成（真正由AI生成）=====
            if any(word in user_lower for word in ["python", "java", "html", "css", "javascript", "sql", "代码", "写一个", "编写", "编程"]):
                # 构建专门的代码生成提示
                code_prompt = f"""请根据以下需求生成完整的、可运行的代码：

需求：{user_input}

要求：
1. 代码要完整、可直接运行
2. 添加必要的注释说明
3. 包含示例用法或测试代码
4. 如果是Python，包含if __name__ == "__main__"入口
5. 如果是HTML/CSS，确保可以直接在浏览器打开
6. 代码用```语言名```格式包裹

请直接输出完整代码，不要只说"这是模板"。"""
                
                temp_messages = [{"role": "user", "content": code_prompt}]
                response = call_deepseek_api(temp_messages, enable_thinking, None)
                
                if response is None:
                    response = f"""```python
# {user_input}
# AI服务暂时不可用，请稍后重试

def solution():
    '''请根据具体需求实现'''
    pass

if __name__ == "__main__":
    solution()
```"""
            
            # ===== 表格生成 =====
            elif any(word in user_lower for word in ["表格", "表", "成绩单", "课程表", "数据表"]):
                table_prompt = f"""请根据以下需求生成一个Markdown格式的表格：

需求：{user_input}

要求：
1. 用Markdown表格格式输出
2. 包含合适的列名
3. 提供3-5行示例数据
4. 如果是课程表，包含时间、课程、地点等信息

请直接输出表格。"""
                
                temp_messages = [{"role": "user", "content": table_prompt}]
                response = call_deepseek_api(temp_messages, enable_thinking, None)
                
                if response is None:
                    response = f"**根据需求生成的示例表格：**\n\n| 项目 | 内容 |\n|------|------|\n| 示例1 | 数据1 |\n| 示例2 | 数据2 |\n\n💡 请告诉我更具体的需求。"
            
            # ===== 图片相关 =====
            elif any(word in user_lower for word in ["图片", "图像", "画", "生成图片", "绘图"]):
                response = generate_image(user_input)
            
            # ===== 普通问答 =====
            else:
                search_results = None
                if enable_search and SEARCH_AVAILABLE:
                    search_results = search_online(user_input)
                response = call_deepseek_api(api_messages, enable_thinking, search_results)
                
                if response is None:
                    response = get_local_response(user_input)
                    if response is None:
                        response = "抱歉，AI服务暂时有点问题。你可以稍后再试，或者问我图书馆、食堂、选课等问题。"
            
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# 页脚
st.markdown("---")
st.caption(f"💡 提示：\n• **代码生成** - 说\"用Python写...\"\n• **表格生成** - 说\"生成成绩表...\"\n• **图片** - 说\"生成图片提示词\"\n• **深度思考** - 侧边栏开启 | {SCHOOL_NAME} 智能客服系统 | 👥 尔主龙彪、任乾鹏、童妍 联合开发")
