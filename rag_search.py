"""
RAG 检索模块 - 从 Supabase 数据库检索相关文档
"""

import streamlit as st

def get_supabase():
    """从 session_state 获取 Supabase 客户端"""
    return st.session_state.get("supabase", None)

def search_similar_documents(query: str, match_count: int = 5) -> list:
    """搜索相关文档 - 同时搜索标题和内容"""
    supabase = get_supabase()
    if not supabase:
        return []
    
    try:
        # 方法1：搜索内容
        response = supabase.table("documents")\
            .select("title, category, content")\
            .ilike("content", f"%{query}%")\
            .limit(match_count)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data
        
        # 方法2：如果内容搜索不到，搜索标题
        response = supabase.table("documents")\
            .select("title, category, content")\
            .ilike("title", f"%{query}%")\
            .limit(match_count)\
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"搜索失败: {e}")
        return []

def format_search_results(results: list) -> str:
    """格式化搜索结果"""
    if not results:
        return ""
    
    formatted = "\n\n📚 **学校官方资料参考**：\n\n"
    for i, doc in enumerate(results, 1):
        title = doc.get('title', '学校文档')
        category = doc.get('category', '其他')
        content = doc.get('content', '')[:500]
        formatted += f"**【{i}】{title}** (来自：{category})\n"
        formatted += f"{content}\n\n"
    
    return formatted

def get_rag_context(user_query: str, match_count: int = 5) -> str:
    """获取 RAG 上下文"""
    similar_docs = search_similar_documents(user_query, match_count)
    return format_search_results(similar_docs)
