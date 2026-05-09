import hashlib
import json
from datetime import datetime

def generate_session_id(user_id=None):
    """生成会话ID"""
    if user_id:
        return hashlib.md5(f"{user_id}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]
    return hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:16]

def format_response(answer, source="hard"):
    """格式化回复"""
    if source == "hard":
        return f"【官方信息】\n{answer}\n\n---\n💬 还有其他问题吗？随时问我~"
    else:
        return f"【学长经验】\n{answer}\n\n---\n💬 以上是学长学姐的经验分享，仅供参考哦~"