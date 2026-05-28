"""
文档处理脚本 - 将学校文档分块并存入 Supabase 向量数据库
仅在本地执行一次
"""

import os
import re
import json
import tiktoken
from supabase import create_client, Client
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-anon-key")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "your-service-role-key")

# 初始化 Supabase 客户端（使用 service key 以绕过 RLS）
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# 初始化 tokenizer（用于计算 token 数）
enc = tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> list:
    """将文本分块，每块不超过 max_tokens"""
    # 按段落分割
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = len(enc.encode(para))
        
        if current_tokens + para_tokens > max_tokens and current_chunk:
            # 保存当前块
            chunks.append('\n\n'.join(current_chunk))
            # 保留 overlap 内容
            overlap_text = '\n\n'.join(current_chunk[-overlap:]) if overlap > 0 else ''
            current_chunk = [overlap_text] if overlap_text else []
            current_tokens = len(enc.encode(overlap_text)) if overlap_text else 0
        
        current_chunk.append(para)
        current_tokens += para_tokens
    
    # 添加最后一块
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks

def extract_text_from_markdown(content: str) -> str:
    """从 Markdown 内容中提取纯文本（去除图片链接等）"""
    # 移除图片链接 ![alt](url)
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
    # 移除图片标签 <img...>
    content = re.sub(r'<img[^>]*>', '', content)
    # 移除 HTML 标签
    content = re.sub(r'<[^>]+>', '', content)
    # 移除 base64 图片数据
    content = re.sub(r'data:image/[^;]+;base64,[^\s]+', '', content)
    # 清理多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()

def process_markdown_file(file_path: str, category: str) -> list:
    """处理单个 Markdown 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取标题（第一个 # 开头的行）
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else os.path.basename(file_path)
    
    # 提取纯文本
    text = extract_text_from_markdown(content)
    
    # 分块
    chunks = chunk_text(text, max_tokens=500, overlap=50)
    
    result = []
    for i, chunk in enumerate(chunks):
        result.append({
            "title": title,
            "category": category,
            "chunk_index": i,
            "content": chunk,
            "file_name": os.path.basename(file_path)
        })
    
    return result

def create_vector_table():
    """创建向量存储表（如果不存在）"""
    
    # 首先安装 pgvector 扩展（需要在 Supabase 控制台执行一次）
    # 执行：CREATE EXTENSION IF NOT EXISTS vector;
    
    # 创建文档表
    sql_documents = """
    CREATE TABLE IF NOT EXISTS documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        content TEXT NOT NULL,
        embedding vector(1536),
        metadata JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    
    # 创建向量相似度搜索函数
    sql_search_function = """
    CREATE OR REPLACE FUNCTION match_documents(
        query_embedding vector(1536),
        match_threshold float,
        match_count int
    )
    RETURNS TABLE(
        id UUID,
        title TEXT,
        category TEXT,
        content TEXT,
        similarity float
    )
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RETURN QUERY
        SELECT
            documents.id,
            documents.title,
            documents.category,
            documents.content,
            1 - (documents.embedding <=> query_embedding) as similarity
        FROM documents
        WHERE 1 - (documents.embedding <=> query_embedding) > match_threshold
        ORDER BY documents.embedding <=> query_embedding
        LIMIT match_count;
    END;
    $$;
    """
    
    try:
        supabase.sql(sql_documents).execute()
        print("✅ 创建 documents 表成功")
    except Exception as e:
        print(f"创建表时出错: {e}")
    
    try:
        supabase.sql(sql_search_function).execute()
        print("✅ 创建搜索函数成功")
    except Exception as e:
        print(f"创建函数时出错: {e}")

def get_embedding(text: str) -> list:
    """获取文本的向量嵌入"""
    # 注意：这里需要使用 DeepSeek 或其他 Embedding 模型
    # 由于 DeepSeek 不提供 embedding API，我们使用 OpenAI 的
    
    import openai
    openai.api_key = os.getenv("OPENAI_API_KEY")  # 需要 OpenAI API Key
    
    response = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text[:8000]  # 限制长度
    )
    return response.data[0].embedding

def process_and_upload():
    """处理所有文档并上传到 Supabase"""
    
    # 文档目录
    docs_dir = "docs"  # 将您的 Markdown 文件放在这个目录下
    
    if not os.path.exists(docs_dir):
        print(f"请创建 {docs_dir} 目录并将 Markdown 文件放入")
        return
    
    all_chunks = []
    
    # 遍历所有 Markdown 文件
    for filename in os.listdir(docs_dir):
        if filename.endswith('.md'):
            file_path = os.path.join(docs_dir, filename)
            
            # 根据文件名确定分类
            if '图书馆' in filename or 'library' in filename.lower():
                category = '图书馆'
            elif '学籍' in filename or 'student_status' in filename.lower():
                category = '学籍管理'
            elif '违纪' in filename or 'discipline' in filename.lower():
                category = '学生违纪'
            elif '奖学金' in filename or 'scholarship' in filename.lower():
                category = '奖学金'
            elif '一卡通' in filename or 'card' in filename.lower():
                category = '校园生活'
            elif '宿舍' in filename or 'dorm' in filename.lower():
                category = '宿舍管理'
            elif '转专业' in filename or 'transfer' in filename.lower():
                category = '教学管理'
            else:
                category = '其他'
            
            print(f"处理文件: {filename} -> 分类: {category}")
            chunks = process_markdown_file(file_path, category)
            all_chunks.extend(chunks)
            print(f"  生成 {len(chunks)} 个文本块")
    
    print(f"\n总共生成 {len(all_chunks)} 个文本块")
    
    # 上传到 Supabase
    for i, chunk in enumerate(all_chunks):
        try:
            # 生成 embedding（可选，也可以后续批量处理）
            # embedding = get_embedding(chunk['content'])
            
            data = {
                "title": chunk['title'],
                "category": chunk['category'],
                "content": chunk['content'],
                "metadata": {
                    "chunk_index": chunk['chunk_index'],
                    "file_name": chunk['file_name']
                }
            }
            
            # 如果有 embedding，可以添加
            # data["embedding"] = embedding
            
            supabase.table("documents").insert(data).execute()
            
            if (i + 1) % 10 == 0:
                print(f"已上传 {i + 1}/{len(all_chunks)} 个块")
                
        except Exception as e:
            print(f"上传失败: {e}")
    
    print("✅ 所有文档上传完成！")

def create_embedding_column():
    """创建 embedding 列（如果不存在）"""
    try:
        # 先添加列
        supabase.sql("ALTER TABLE documents ADD COLUMN IF NOT EXISTS embedding vector(1536);").execute()
        print("✅ embedding 列已创建")
    except Exception as e:
        print(f"创建列时出错: {e}")

if __name__ == "__main__":
    print("开始处理学校文档...")
    
    # 1. 创建表
    create_vector_table()
    
    # 2. 创建 embedding 列
    create_embedding_column()
    
    # 3. 处理并上传文档
    process_and_upload()
    
    print("\n请先在 Supabase 控制台执行以下 SQL 安装 pgvector 扩展：")
    print("CREATE EXTENSION IF NOT EXISTS vector;")
