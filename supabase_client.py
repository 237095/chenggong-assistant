"""
Supabase 客户端管理 - 延迟加载
"""

import streamlit as st
from supabase import create_client

_supabase = None

def get_supabase():
    """获取 Supabase 客户端（延迟加载）"""
    global _supabase
    
    if _supabase is not None:
        return _supabase
    
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    # 优先使用 Service Role Key（有写入权限）
    SUPABASE_KEY = st.secrets.get("SUPABASE_SERVICE_KEY", "") or st.secrets.get("SUPABASE_KEY", "")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("❌ Secrets 中没有找到 Supabase 配置")
        return None
    
    _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase
