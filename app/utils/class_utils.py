"""
工具函数：班级号相关操作

班级号格式规则：
- 完整班级号: 10位 (如 2021051002)
- 年级: 前4位 (如 2021)
- 专业代码: 前8位 (如 20210510)
"""

def get_grade(s_class: str) -> str:
    """从班级号提取年级（前4位）"""
    if s_class and len(s_class) >= 4:
        return s_class[:4]
    return ""


def get_major_code(s_class: str) -> str:
    """从班级号提取专业代码（前8位）"""
    if s_class and len(s_class) >= 8:
        return s_class[:8]
    return ""


def validate_class_number(s_class: str, s_id: str = None) -> str:
    """
    校验并修正班级号
    
    Args:
        s_class: 原始班级号
        s_id: 学号（用于推断班级号，可选）
    
    Returns:
        修正后的班级号
    """
    # 如果班级号长度不足8位，尝试从学号推断
    if len(s_class or "") < 8 and s_id and len(s_id) >= 10:
        return s_id[:10]
    return s_class or ""
