"""
文档加载脚本 - 接收 supabase 客户端
"""

import streamlit as st
import os
import re

def read_markdown_files(docs_dir: str = "DOCS") -> list:
    """读取 DOCS 文件夹中的所有 Markdown 文件"""
    documents = []
    
    if not os.path.exists(docs_dir):
        st.warning(f"文件夹 {docs_dir} 不存在")
        return documents
    
    files = os.listdir(docs_dir)
    st.info(f"发现 {len(files)} 个文件")
    
    for filename in files:
        if not filename.endswith('.md'):
            continue
        
        file_path = os.path.join(docs_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else filename.replace('.md', '')
        
        # 判断分类
        if '图书馆' in filename or '畅想书海' in filename:
            category = '图书馆'
        elif '学籍' in filename:
            category = '学籍管理'
        elif '违纪' in filename or '处分' in filename:
            category = '学生违纪'
        elif '奖学金' in filename:
            category = '奖学金'
        elif '一卡通' in filename:
            category = '校园生活'
        elif '宿舍' in filename or '公寓' in filename:
            category = '宿舍管理'
        elif '转专业' in filename:
            category = '教学管理'
        elif '评优' in filename:
            category = '评优奖励'
        else:
            category = '学校文档'
        
        clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        clean_content = re.sub(r'<img[^>]*>', '', clean_content)
        clean_content = re.sub(r'data:image/[^;]+;base64,[^\s]+', '', clean_content)
        clean_content = re.sub(r'\n{3,}', '\n\n', clean_content)
        
        documents.append({
            "title": title,
            "category": category,
            "content": clean_content,
            "metadata": {"source": filename}
        })
        
        st.write(f"✅ 已读取: {filename} -> {category} ({len(clean_content)} 字符)")
    
    return documents

def load_documents(supabase):
    """加载文档到 Supabase"""
    
    # 先清空现有文档
    try:
        supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        st.write("🗑️ 已清空现有文档")
    except Exception as e:
        st.write(f"清空文档时出错: {e}")
    
    # 读取本地文件
    documents = read_markdown_files()
    if not documents:
        st.warning("未找到文档文件")
        return 0
    
    st.write(f"共找到 {len(documents)} 个文档")
    
    # 插入文档
    count = 0
    for doc in documents:
        try:
            supabase.table("documents").insert(doc).execute()
            count += 1
            st.write(f"📤 已上传: {doc['title']}")
        except Exception as e:
            st.error(f"❌ 上传失败 {doc['title']}: {e}")
    
    st.success(f"✅ 成功加载 {count} 个文档")
    return count
