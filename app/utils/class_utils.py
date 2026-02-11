"""
工具函数：班级号相关操作

班级号格式规则：
- 完整班级号: 10位 (如 2021051002)
- 年级: 前4位 (如 2021)
- 专业代码: 前8位 (如 20210510)
"""

def get_major_code(s_class: str) -> str:
    """从班级号提取专业代码（前8位）"""
    if s_class and len(s_class) >= 8:
        return s_class[:8]
    return ""
