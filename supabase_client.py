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
    
    # 调试：打印读取状态
    st.write("🔍 正在读取 Secrets...")
    
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    
    st.write(f"URL: {'已读取' if SUPABASE_URL else '未找到'}")
    st.write(f"Key: {'已读取' if SUPABASE_KEY else '未找到'}")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("❌ Secrets 中没有找到 SUPABASE_URL 或 SUPABASE_KEY")
        st.info("请在 Streamlit Cloud 的 Settings -> Secrets 中配置")
        return None
    
    try:
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        st.success("✅ Supabase 连接成功！")
        return _supabase
    except Exception as e:
        st.error(f"❌ Supabase 连接失败: {e}")
        return None
