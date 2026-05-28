"""
文档加载脚本 - 将 GitHub 仓库中的 Markdown 文件加载到 Supabase
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

def is_documents_loaded() -> bool:
    """检查是否已经加载过文档"""
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        response = supabase.table("documents").select("id", count="exact").limit(1).execute()
        return response.count > 0 if response.count else False
    except Exception as e:
        print(f"检查文档状态失败: {e}")
        return False

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
        
        # 清理内容（移除图片引用和 base64 图片）
        clean_content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        clean_content = re.sub(r'<img[^>]*>', '', clean_content)
        clean_content = re.sub(r'data:image/[^;]+;base64,[^\s]+', '', clean_content)
        clean_content = re.sub(r'\n{3,}', '\n\n', clean_content)
        
        documents.append({
            "title": title,
            "category": category,
            "content": clean_content,  # 不再限制长度
            "metadata": {"source": filename}
        })
        
        st.write(f"✅ 已读取: {filename} -> {category} ({len(clean_content)} 字符)")
    
    return documents

def upload_to_supabase(documents: list):
    """上传文档到 Supabase"""
    supabase = init_supabase()
    if not supabase:
        return 0
    
    count = 0
    for doc in documents:
        try:
            # 检查是否已存在（避免重复上传）
            existing = supabase.table("documents").select("id").eq("title", doc["title"]).execute()
            if existing.data:
                st.write(f"⏭️ 跳过已存在: {doc['title']}")
                continue
            
            supabase.table("documents").insert(doc).execute()
            count += 1
            st.write(f"📤 已上传: {doc['title']}")
        except Exception as e:
            st.error(f"❌ 上传失败 {doc['title']}: {e}")
    
    return count

def clear_all_documents():
    """清空所有文档（管理员功能）"""
    supabase = init_supabase()
    if not supabase:
        return False, "数据库连接失败"
    
    try:
        supabase.table("documents").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        return True, "已清空所有文档"
    except Exception as e:
        return False, f"清空失败: {e}"

def load_documents(force_reload: bool = False):
    """
    主函数：加载并上传文档
    force_reload: 是否强制重新加载（忽略已存在检查）
    """
    # 检查是否已有文档
    if not force_reload and is_documents_loaded():
        doc_count = get_document_count()
        st.info(f"📚 文档已加载，共 {doc_count} 个文档，无需重复加载")
        return doc_count
    
    if force_reload:
        st.info("🔄 强制重新加载模式，将重新导入所有文档...")
    
    st.info("📚 正在加载学校文档到知识库...")
    
    documents = read_markdown_files()
    if not documents:
        st.warning("未找到文档文件，请将 Markdown 文件放入 DOCS 文件夹")
        return 0
    
    st.write(f"共找到 {len(documents)} 个文档")
    
    count = upload_to_supabase(documents)
    st.success(f"✅ 成功加载 {count} 个文档到知识库！")
    
    return count

if __name__ == "__main__":
    load_documents()
