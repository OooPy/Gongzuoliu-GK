# -*- coding: utf-8 -*-
"""
产品信息提取模块
读取产品卖点文档，提取核心信息供 AI 文案生成使用
"""

import re
from pathlib import Path


def read_product_info(doc_path: str) -> dict:
    """
    读取产品文档，返回产品名称和卖点内容
    
    Args:
        doc_path: 产品文档路径（支持 .txt 格式）
    
    Returns:
        dict: 包含 product_name 和 selling_points 的字典
    """
    path = Path(doc_path)
    
    if not path.exists():
        raise FileNotFoundError(f"产品文档不存在: {doc_path}")
    
    # 读取文件内容
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 尝试从文件名提取产品名称
    product_name = extract_product_name(path.stem, content)
    
    return {
        "product_name": product_name,
        "selling_points": content,
        "file_path": str(path.absolute())
    }


def extract_product_name(filename: str, content: str) -> str:
    """
    从文件名或内容中提取产品名称
    
    Args:
        filename: 文件名（不含扩展名）
        content: 文档内容
    
    Returns:
        str: 产品名称
    """
    # 优先从文件名提取（如 "雪叶红卖点" -> "雪叶红"）
    name_patterns = [
        r'^(.+?)卖点',      # xxx卖点
        r'^(.+?)产品',      # xxx产品
        r'^(.+?)说明',      # xxx说明
    ]
    
    for pattern in name_patterns:
        match = re.match(pattern, filename)
        if match:
            return match.group(1)
    
    # 从内容中尝试提取（查找常见产品名称模式）
    content_patterns = [
        r'雪叶红\S*',       # 雪叶红系列
        r'口服液',
    ]
    
    for pattern in content_patterns:
        match = re.search(pattern, content)
        if match:
            return match.group(0)
    
    # 默认返回文件名
    return filename


def format_selling_points(selling_points: str, max_length: int = 3000) -> str:
    """
    格式化卖点文本，确保长度适中
    
    Args:
        selling_points: 原始卖点文本
        max_length: 最大字符数
    
    Returns:
        str: 格式化后的卖点文本
    """
    if len(selling_points) <= max_length:
        return selling_points
    
    # 截取并保持完整的段落
    truncated = selling_points[:max_length]
    last_newline = truncated.rfind('\n')
    
    if last_newline > max_length * 0.8:
        return truncated[:last_newline] + "\n..."
    
    return truncated + "..."


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        doc_path = sys.argv[1]
    else:
        doc_path = "雪叶红卖点.txt"
    
    try:
        info = read_product_info(doc_path)
        print(f"产品名称: {info['product_name']}")
        print(f"卖点字数: {len(info['selling_points'])} 字")
        print("-" * 50)
        print(info['selling_points'][:500] + "..." if len(info['selling_points']) > 500 else info['selling_points'])
    except Exception as e:
        print(f"错误: {e}")
