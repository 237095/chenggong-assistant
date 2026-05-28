"""
Supabase 客户端管理 - 延迟加载
"""

import streamlit as st
from supabase import create_client

_supabase = None

def get_supabase():
    """获取 Supabase 客户端（延迟加载，只在第一次调用时初始化）"""
    global _supabase
    
    if _supabase is not None:
        return _supabase
    
    # 在函数内部读取 secrets，此时 Streamlit 已完全启动
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        # 不在这里报错，返回 None，让调用方处理
        return None
    
    _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase
