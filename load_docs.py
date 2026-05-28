"""
文档加载脚本 - 支持增量更新
"""

import streamlit as st
import os
import re
import hashlib
from datetime import datetime
from supabase import create_client, Client

def init_supabase() -> Client:
    """初始化 Supabase 客户端"""
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_file_mtime(file_path: str) -> str:
    """获取文件的修改时间"""
    try:
        mtime = os.path.getmtime(file_path)
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ""

def get_file_hash(file_path: str) -> str:
    """计算文件内容的 MD5 哈希值"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return ""

def get_existing_documents():
    """获取已存在的文档信息（标题和修改时间）"""
    supabase = init_supabase()
    if not supabase:
        return {}
    
    try:
        response = supabase.table("documents").select("title, file_mtime, file_hash").execute()
        existing = {}
        for doc in (response.data or []):
            existing[doc["title"]] = {
                "file_mtime": doc.get("file_mtime", ""),
                "file_hash": doc.get("file_hash", "")
            }
        return existing
    except Exception as e:
        print(f"获取已存在文档失败: {e}")
        return {}

def delete_document_by_title(title: str):
    """根据标题删除文档"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        supabase.table("documents").delete().eq("title", title).execute()
        return True
    except Exception as e:
        print(f"删除文档失败: {e}")
        return False

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
        file_mtime = get_file_mtime(file_path)
        file_hash = get_file_hash(file_path)
        
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
        elif '实习' in filename:
            category = '实习管理'
        elif '社团' in filename:
            category = '社团管理'
        elif '助学' in filename or '困难' in filename:
            category = '助学帮困'
        elif '国法' in filename or '法规' in filename:
            category = '法律法规'
        elif '水电' in filename or '热水' in filename or '洗衣' in filename:
            category = '校园生活'
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
            "metadata": {"source": filename},
            "file_mtime": file_mtime,
            "file_hash": file_hash,
            "filename": filename
        })
    
    return documents

def sync_documents():
    """
    同步文档：只处理新增或更新的文件
    返回: (新增数量, 更新数量, 删除数量)
    """
    supabase = init_supabase()
    if not supabase:
        return 0, 0, 0
    
    # 1. 获取本地文件
    local_docs = read_markdown_files()
    local_dict = {doc["title"]: doc for doc in local_docs}
    
    # 2. 获取已存在的文档
    existing_dict = get_existing_documents()
    
    # 3. 统计
    new_count = 0
    update_count = 0
    delete_count = 0
    
    # 4. 处理新增和更新
    for title, doc in local_dict.items():
        if title not in existing_dict:
            # 新增文档
            supabase.table("documents").insert({
                "title": doc["title"],
                "category": doc["category"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "file_mtime": doc["file_mtime"],
                "file_hash": doc["file_hash"]
            }).execute()
            new_count += 1
            st.write(f"➕ 新增文档: {title}")
        elif doc["file_mtime"] != existing_dict[title].get("file_mtime"):
            # 文档有更新，先删除再插入
            supabase.table("documents").delete().eq("title", title).execute()
            supabase.table("documents").insert({
                "title": doc["title"],
                "category": doc["category"],
                "content": doc["content"],
                "metadata": doc["metadata"],
                "file_mtime": doc["file_mtime"],
                "file_hash": doc["file_hash"]
            }).execute()
            update_count += 1
            st.write(f"🔄 更新文档: {title}")
    
    # 5. 处理删除（本地已删除的文件）
    for title in existing_dict:
        if title not in local_dict:
            supabase.table("documents").delete().eq("title", title).execute()
            delete_count += 1
            st.write(f"🗑️ 删除文档: {title}")
    
    return new_count, update_count, delete_count

def get_document_count() -> int:
    """获取已加载的文档数量"""
    supabase = init_supabase()
    if not supabase:
        return 0
    
    try:
        response = supabase.table("documents").select("id", count="exact").execute()
        return response.count if response.count else 0
    except:
        return 0

def load_documents():
    """主函数：同步文档"""
    st.info("📚 正在同步学校文档到知识库...")
    
    new_count, update_count, delete_count = sync_documents()
    
    if new_count == 0 and update_count == 0 and delete_count == 0:
        st.info("✅ 所有文档已是最新，无需更新")
    else:
        st.success(f"✅ 同步完成！新增 {new_count} 个，更新 {update_count} 个，删除 {delete_count} 个")
    
    return get_document_count()
