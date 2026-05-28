"""
RAG 检索模块 - 从 Supabase 向量数据库检索相关文档
"""

import streamlit as st
import os
import openai
from supabase import create_client, Client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-key")

# 初始化 OpenAI（用于 embedding）
openai.api_key = os.getenv("OPENAI_API_KEY", "")

@st.cache_resource
def init_supabase() -> Client:
    """初始化 Supabase 客户端"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_embedding(text: str) -> list:
    """获取文本的向量嵌入"""
    try:
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=text[:8000]
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Embedding 生成失败: {e}")
        return None

def search_similar_documents(query: str, match_count: int = 5) -> list:
    """搜索相似文档"""
    supabase = init_supabase()
    
    # 生成查询向量
    query_embedding = get_embedding(query)
    if not query_embedding:
        return []
    
    try:
        # 使用向量相似度搜索
        response = supabase.rpc(
            "match_documents",
            {
                "query_embedding": query_embedding,
                "match_threshold": 0.5,
                "match_count": match_count
            }
        ).execute()
        
        return response.data
    except Exception as e:
        print(f"搜索失败: {e}")
        
        # 备用方案：使用全文搜索
        try:
            response = supabase.table("documents")\
                .select("title, category, content")\
                .text_search("content", query)\
                .limit(match_count)\
                .execute()
            return response.data
        except:
            return []

def format_search_results(results: list) -> str:
    """格式化搜索结果"""
    if not results:
        return ""
    
    formatted = "\n\n📚 **参考资料**：\n\n"
    for i, doc in enumerate(results, 1):
        formatted += f"**{i}. {doc.get('title', '文档')}** (来自 {doc.get('category', '其他')})\n"
        formatted += f"> {doc.get('content', '')[:300]}...\n\n"
    
    return formatted

def get_rag_response(user_query: str, enable_rag: bool = True) -> str:
    """获取 RAG 增强的 AI 回复"""
    
    # 1. 检索相关文档
    if enable_rag:
        similar_docs = search_similar_documents(user_query, match_count=5)
        context = format_search_results(similar_docs)
    else:
        context = ""
    
    # 2. 构建 prompt
    system_prompt = """你是成都工业职业技术学院的智能客服助手。请根据提供的参考资料，准确、详细地回答学生的问题。

要求：
1. 优先使用参考资料中的官方信息回答问题
2. 如果参考资料中有相关信息，请明确引用
3. 如果参考资料中没有相关信息，请根据你的知识合理回答
4. 回答要亲切、专业、准确
5. 重要信息用**加粗**标注
"""

    full_prompt = f"{context}\n\n用户问题：{user_query}\n\n请回答："
    
    return full_prompt, context
