"""
管理员后台 - 成工职小助手
仅管理员可访问
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# 导入学生数据
try:
    from students_id import STUDENTS, add_student, delete_student, reset_password
except ImportError:
    from students_id import STUDENTS, add_student, delete_student, reset_password

def show_admin_panel():
    """显示管理员后台"""
    
    st.markdown("## 🔧 管理后台")
    
    # 统计卡片
    col1, col2 = st.columns(2)
    with col1:
        st.metric("👨‍🎓 学生总数", len(STUDENTS))
    with col2:
        st.metric("👨‍💼 管理员", 1)
    
    st.markdown("---")
    
    # 标签页
    tab1, tab2, tab3 = st.tabs(["📋 学生管理", "➕ 添加学生", "📜 操作日志"])
    
    # ========== 学生管理 ==========
    with tab1:
        st.markdown("### 学生列表")
        
        if STUDENTS:
            # 转换为DataFrame显示
            data = []
            for sid, info in STUDENTS.items():
                data.append({
                    "学号": sid,
                    "姓名": info["name"],
                    "密码": info["password"],
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 删除学生")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                student_to_delete = st.selectbox(
                    "选择要删除的学生",
                    options=list(STUDENTS.keys()),
                    format_func=lambda x: f"{x} - {STUDENTS[x]['name']}",
                    key="delete_select"
                )
            with col2:
                if st.button("🗑️ 删除", key="delete_btn"):
                    if delete_student(student_to_delete):
                        st.success(f"已删除学生: {student_to_delete}")
                        st.rerun()
                    else:
                        st.error("删除失败")
            
            st.markdown("### 重置学生密码")
            col1, col2 = st.columns([3, 1])
            with col1:
                student_to_reset = st.selectbox(
                    "选择要重置密码的学生",
                    options=list(STUDENTS.keys()),
                    format_func=lambda x: f"{x} - {STUDENTS[x]['name']}",
                    key="reset_select"
                )
            with col2:
                if st.button("🔄 重置密码", key="reset_btn"):
                    if reset_password(student_to_reset, "237095"):
                        st.success(f"已重置 {student_to_reset} 的密码为: 237095")
                        st.rerun()
                    else:
                        st.error("重置失败")
        else:
            st.info("暂无学生数据")
    
    # ========== 添加学生 ==========
    with tab2:
        st.markdown("### 添加新学生")
        
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_student_id = st.text_input("学号 *", placeholder="例: 2024008")
                new_name = st.text_input("姓名 *", placeholder="例: 张三")
            with col2:
                new_password = st.text_input("密码", placeholder="默认为 237095", value="237095")
            
            submitted = st.form_submit_button("➕ 添加学生", use_container_width=True)
            
            if submitted:
                if not new_student_id or not new_name:
                    st.error("请填写学号和姓名")
                else:
                    success = add_student(new_student_id, new_name, new_password)
                    if success:
                        st.success(f"成功添加学生: {new_name} (学号: {new_student_id}, 密码: {new_password})")
                        st.rerun()
                    else:
                        st.error("添加失败，学号可能已存在")
    
    # ========== 操作日志 ==========
    with tab3:
        st.markdown("### 操作日志")
        st.info("日志功能开发中...")

def is_admin():
    """检查当前用户是否为管理员"""
    return st.session_state.get("user_role") == "admin"
