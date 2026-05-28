"""
学生数据文件 - 成工职小助手
存储学生账号信息
"""

# 学生数据格式：学号 -> {姓名, 密码, 学号}
STUDENTS = {
    "2024001": {
        "name": "张三",
        "password": "237095",
        "student_id": "2024001"
    },
    "2024002": {
        "name": "李四",
        "password": "237095",
        "student_id": "2024002"
    },
    "2024003": {
        "name": "王五",
        "password": "237095",
        "student_id": "2024003"
    },
    "2024004": {
        "name": "赵六",
        "password": "237095",
        "student_id": "2024004"
    },
    "2024005": {
        "name": "小明",
        "password": "237095",
        "student_id": "2024005"
    },
    "2024006": {
        "name": "小红",
        "password": "237095",
        "student_id": "2024006"
    },
    "2024007": {
        "name": "小华",
        "password": "237095",
        "student_id": "2024007"
    },
}

def get_all_students():
    """获取所有学生列表"""
    return STUDENTS

def get_student(student_id):
    """获取单个学生信息"""
    return STUDENTS.get(student_id)

def add_student(student_id, name, password="237095"):
    """添加学生"""
    if student_id in STUDENTS:
        return False
    STUDENTS[student_id] = {
        "name": name,
        "password": password,
        "student_id": student_id
    }
    return True

def delete_student(student_id):
    """删除学生"""
    if student_id in STUDENTS:
        del STUDENTS[student_id]
        return True
    return False

def reset_password(student_id, new_password="237095"):
    """重置密码"""
    if student_id in STUDENTS:
        STUDENTS[student_id]["password"] = new_password
        return True
    return False
