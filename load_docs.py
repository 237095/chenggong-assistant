"""
文档加载脚本 - 手动同步，不在启动时自动执行
"""

import streamlit as st
import os
import re
from supabase import create_client, Client

def init_supabase() -> Client:
    """初始化 Supabase 客户端"""
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_document_count() -> int:
    """获取已加载的文档数量"""
    supabase = init_supabase()
    if not supabase:
        return 0
    
    try:
        response = supabase.table("documents").select("id", count="exact").limit(1).execute()
        return response.count if response.count else 0
    except:
        return 0

def read_markdown_files(docs_dir: str = "DOCS") -> list:
    """读取 DOCS 文件夹中的所有 Markdown 文件"""
    documents = []
    
    if not os.path.exists(docs_dir):
        st.warning(f"文件夹 {docs_dir} 不存在")
        return documents
    
    files = os.listdir(docs_dir)
    
    for filename in files:
        if not filename.endswith('.md'):
            continue
        
        file_path = os.path.join(docs_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取标题
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
        
        # 清理内容
        clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        clean_content = re.sub(r'<img[^>]*>', '', content)
        clean_content = re.sub(r'data:image/[^;]+;base64,[^\s]+', '', content)
        clean_content = re.sub(r'\n{3,}', '\n\n', clean_content)
        
        documents.append({
            "title": title,
            "category": category,
            "content": clean_content[:5000],
            "metadata": {"source": filename}
        })
    
    return documents

def sync_documents():
    """手动同步文档：清空并重新加载"""
    supabase = init_supabase()
    if not supabase:
        return 0, "数据库连接失败"
    
    # 1. 读取本地文件
    local_docs = read_markdown_files()
    if not local_docs:
        return 0, "未找到文档文件"
    
    # 2. 清空现有文档
    try:
        supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    except:
        pass
    
    # 3. 插入新文档
    count = 0
    for doc in local_docs:
        try:
            supabase.table("documents").insert(doc).execute()
            count += 1
        except Exception as e:
            st.error(f"上传失败 {doc['title']}: {e}")
    
    return count, f"成功加载 {count} 个文档"

def load_documents():
    """主函数：手动同步"""
    count, msg = sync_documents()
    if count > 0:
        st.success(f"✅ {msg}")
    else:
        st.warning(f"⚠️ {msg}")
    return count
