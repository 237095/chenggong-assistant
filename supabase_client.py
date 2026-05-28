"""
Supabase 客户端管理模块 - 延迟加载，确保 Secrets 可用
"""

import streamlit as st
from supabase import create_client, Client

_supabase_client = None

def get_supabase_client() -> Client:
    """获取 Supabase 客户端（延迟加载，在第一次调用时才初始化）"""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    # 在函数内部读取 Secrets，此时 Streamlit 已经完全启动
    try:
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("❌ 配置错误：请在 Secrets 中配置 SUPABASE_URL 和 SUPABASE_KEY")
            return None
        
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        st.error(f"❌ Supabase 连接失败: {e}")
        return None
