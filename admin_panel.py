"""
管理员后台 - 使用 Supabase 管理学生
"""

import streamlit as st
import pandas as pd
import student_manager

def show_admin_panel():
    """显示管理员后台"""
    
    st.markdown("## 🔧 管理后台")
    
    # 统计卡片
    col1, col2 = st.columns(2)
    with col1:
        student_count = student_manager.get_student_count()
        st.metric("👨‍🎓 学生总数", student_count)
    with col2:
        st.metric("👨‍💼 管理员", 1)
    
    st.markdown("---")
    
    # 标签页
    tab1, tab2, tab3 = st.tabs(["📋 学生管理", "➕ 添加学生", "📜 操作日志"])
    
    # ========== 学生管理 ==========
    with tab1:
        st.markdown("### 学生列表")
        
        students = student_manager.get_all_students()
        if students:
            # 转换为DataFrame显示
            data = []
            for s in students:
                data.append({
                    "学号": s.get("student_id", ""),
                    "姓名": s.get("name", ""),
                    "密码": "••••••",
                    "班级": s.get("class_name", ""),
                    "手机号": s.get("phone", ""),
                    "注册时间": s.get("created_at", "")[:10] if s.get("created_at") else ""
                })
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            
            st.markdown("---")
            
            # 删除学生
            st.markdown("### 删除学生")
            col1, col2 = st.columns([3, 1])
            with col1:
                student_options = {s["student_id"]: f"{s['student_id']} - {s['name']}" for s in students}
                if student_options:
                    student_to_delete = st.selectbox(
                        "选择要删除的学生",
                        options=list(student_options.keys()),
                        format_func=lambda x: student_options[x]
                    )
                else:
                    student_to_delete = None
                    st.info("暂无学生数据")
            
            with col2:
                if student_to_delete and st.button("🗑️ 删除", key="delete_btn"):
                    success, msg = student_manager.delete_student(student_to_delete)
                    if success:
                        st.success(f"已删除学生: {student_to_delete}")
                        st.rerun()
                    else:
                        st.error(msg)
            
            # 重置密码
            st.markdown("### 重置学生密码")
            col1, col2 = st.columns([3, 1])
            with col1:
                if student_options:
                    student_to_reset = st.selectbox(
                        "选择要重置密码的学生",
                        options=list(student_options.keys()),
                        format_func=lambda x: student_options[x],
                        key="reset_select"
                    )
                else:
                    student_to_reset = None
                    st.info("暂无学生数据")
            
            with col2:
                if student_to_reset and st.button("🔄 重置密码", key="reset_btn"):
                    success, msg = student_manager.reset_student_password(student_to_reset)
                    if success:
                        st.success(f"已重置 {student_to_reset} 的密码为: 237095")
                        st.rerun()
                    else:
                        st.error(msg)
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
                new_class = st.text_input("班级", placeholder="例: 计算机1班")
                new_phone = st.text_input("手机号", placeholder="例: 13800138006")
            
            submitted = st.form_submit_button("➕ 添加学生", use_container_width=True)
            
            if submitted:
                if not new_student_id or not new_name:
                    st.error("请填写学号和姓名")
                else:
                    success, msg = student_manager.add_student(
                        student_id=new_student_id,
                        name=new_name,
                        password=new_password,
                        phone=new_phone,
                        class_name=new_class
                    )
                    if success:
                        st.success(f"成功添加学生: {new_name} (学号: {new_student_id}, 密码: {new_password})")
                        st.rerun()
                    else:
                        st.error(msg)
