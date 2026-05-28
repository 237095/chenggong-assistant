"""
学生管理模块 - 使用 Supabase 存储
"""

import streamlit as st
from datetime import datetime

def get_supabase():
    """从 session_state 获取 Supabase 客户端"""
    return st.session_state.get("supabase", None)

def get_all_students():
    supabase = get_supabase()
    if not supabase:
        return []
    
    try:
        response = supabase.table("students").select("*").order("student_id").execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"获取学生列表失败: {e}")
        return []

def get_student_by_id(student_id: str):
    supabase = get_supabase()
    if not supabase:
        return None
    
    try:
        response = supabase.table("students").select("*").eq("student_id", student_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"获取学生失败: {e}")
        return None

def verify_student(student_id: str, password: str):
    supabase = get_supabase()
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
    supabase = get_supabase()
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
    supabase = get_supabase()
    if not supabase:
        return False, "数据库连接失败"
    
    try:
        supabase.table("students").delete().eq("student_id", student_id).execute()
        return True, "删除成功"
    except Exception as e:
        return False, f"删除失败: {e}"

def update_student(student_id: str, name: str = None, password: str = None, phone: str = None, class_name: str = None):
    supabase = get_supabase()
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
    return update_student(student_id, password="237095")

def get_student_count():
    supabase = get_supabase()
    if not supabase:
        return 0
    
    try:
        response = supabase.table("students").select("id", count="exact").execute()
        return response.count if response.count else 0
    except:
        return 0
