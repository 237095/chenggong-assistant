"""
RAG 检索模块 - 从 Supabase 数据库检索相关文档（使用全文搜索）
"""

import streamlit as st
from supabase import create_client, Client

@st.cache_resource
def init_supabase() -> Client:
    """初始化 Supabase 客户端"""
    try:
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("请先在 Secrets 中配置 SUPABASE_URL 和 SUPABASE_KEY")
            return None
        
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase 初始化失败: {e}")
        return None

def search_similar_documents(query: str, match_count: int = 5) -> list:
    """搜索相关文档（使用全文搜索，不依赖 OpenAI embedding）"""
    supabase = init_supabase()
    if not supabase:
        return []
    
    try:
        # 使用全文搜索（中文需要配置，先用简单 LIKE）
        response = supabase.table("documents")\
            .select("title, category, content")\
            .ilike("content", f"%{query}%")\
            .limit(match_count)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data
        return []
    except Exception as e:
        print(f"搜索失败: {e}")
        
        # 备用方案：尝试全文搜索
        try:
            response = supabase.table("documents")\
                .select("title, category, content")\
                .text_search("content", query)\
                .limit(match_count)\
                .execute()
            return response.data if response.data else []
        except:
            return []

def format_search_results(results: list) -> str:
    """格式化搜索结果"""
    if not results:
        return ""
    
    formatted = "\n\n📚 **参考资料**：\n\n"
    for i, doc in enumerate(results, 1):
        title = doc.get('title', '文档')
        category = doc.get('category', '其他')
        content = doc.get('content', '')[:300]
        formatted += f"**{i}. {title}** (来自：{category})\n"
        formatted += f"> {content}...\n\n"
    
    return formatted

def get_rag_response(user_query: str, enable_rag: bool = True):
    """获取 RAG 增强的内容"""
    if not enable_rag:
        return "", []
    
    similar_docs = search_similar_documents(user_query, match_count=5)
    context = format_search_results(similar_docs)
    
    return context, similar_docs
