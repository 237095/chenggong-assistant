"""
学生管理模块 - 使用 Supabase 存储
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime

# 全局变量缓存客户端
_supabase_client = None

def get_supabase_client() -> Client:
    """懒加载 Supabase 客户端"""
    global _supabase_client
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
        SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("请先在 Secrets 中配置 SUPABASE_URL 和 SUPABASE_KEY")
            return None
        
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client
    except Exception as e:
        st.error(f"Supabase 连接失败: {e}")
        return None

def get_all_students():
    """获取所有学生列表"""
    supabase = get_supabase_client()
    if not supabase:
        return []
    
    try:
        response = supabase.table("students").select("*").order("student_id").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"获取学生列表失败: {e}")
        return []

def get_student_by_id(student_id: str):
    """根据学号获取学生信息"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        response = supabase.table("students").select("*").eq("student_id", student_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"获取学生失败: {e}")
        return None

def verify_student(student_id: str, password: str):
    """验证学生登录"""
    supabase = get_supabase_client()
    if not supabase:
        return None
    
    try:
        response = supabase.table("students").select("*").eq("student_id", student_id).eq("password", password).execute()
        if response.data and len(response.data) > 0:
            student = response.data[0]
            return {
                "role": "student",
                "name": student["name"],
                "user_id": student["student_id"],
                "student_id": student["student_id"]
            }
        return None
    except Exception as e:
        print(f"验证学生失败: {e}")
        return None

def add_student(student_id: str, name: str, password: str = "237095", phone: str = "", class_name: str = ""):
    """添加学生"""
    supabase = get_supabase_client()
    if not supabase:
        return False, "数据库连接失败"
    
    existing = get_student_by_id(student_id)
    if existing:
        return False, f"学号 {student_id} 已存在"
    
    try:
        supabase.table("students").insert({
            "student_id": student_id,
            "name": name,
            "password": password,
            "phone": phone,
            "class_name": class_name,
            "created_at": datetime.now().isoformat()
        }).execute()
        return True, "添加成功"
    except Exception as e:
        return False, f"添加失败: {e}"

def delete_student(student_id: str):
    """删除学生"""
    supabase = get_supabase_client()
    if not supabase:
        return False, "数据库连接失败"
    
    try:
        supabase.table("students").delete().eq("student_id", student_id).execute()
        return True, "删除成功"
    except Exception as e:
        return False, f"删除失败: {e}"

def update_student(student_id: str, name: str = None, password: str = None, phone: str = None, class_name: str = None):
    """更新学生信息"""
    supabase = get_supabase_client()
    if not supabase:
        return False, "数据库连接失败"
    
    update_data = {}
    if name:
        update_data["name"] = name
    if password:
        update_data["password"] = password
    if phone:
        update_data["phone"] = phone
    if class_name:
        update_data["class_name"] = class_name
    
    if not update_data:
        return False, "没有要更新的内容"
    
    update_data["updated_at"] = datetime.now().isoformat()
    
    try:
        supabase.table("students").update(update_data).eq("student_id", student_id).execute()
        return True, "更新成功"
    except Exception as e:
        return False, f"更新失败: {e}"

def reset_student_password(student_id: str):
    """重置学生密码为默认值 237095"""
    return update_student(student_id, password="237095")

def get_student_count():
    """获取学生总数"""
    supabase = get_supabase_client()
    if not supabase:
        return 0
    
    try:
        response = supabase.table("students").select("id", count="exact").execute()
        return response.count if response.count else 0
    except:
        return 0
