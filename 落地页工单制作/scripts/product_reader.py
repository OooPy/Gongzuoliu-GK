# -*- coding: utf-8 -*-
"""
产品卖点读取模块
解析产品卖点文件，支持按方向过滤
"""

from pathlib import Path
import re


def read_product_info(file_path: str) -> dict:
    """
    读取产品卖点文件
    
    Args:
        file_path: 卖点文件路径
        
    Returns:
        dict: 包含 product_name 和 selling_points 的字典
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"卖点文件不存在: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 从文件名提取产品名称
    product_name = path.stem.replace("卖点", "").strip()
    if not product_name:
        product_name = "未命名产品"
    
    # 解析卖点分类
    selling_points = parse_selling_points(content)
    
    return {
        "product_name": product_name,
        "selling_points": selling_points,
        "raw_content": content
    }


def parse_selling_points(content: str) -> list:
    """
    解析卖点文件内容，提取结构化卖点
    
    Args:
        content: 文件内容
        
    Returns:
        list: 卖点列表，每项包含 category, title, description
    """
    points = []
    current_category = ""
    
    lines = content.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检测分类标题（如：一、核心功效与痛点）
        if re.match(r'^[一二三四五六七八九十]+[、\.]\s*', line):
            current_category = re.sub(r'^[一二三四五六七八九十]+[、\.]\s*', '', line)
            continue
        
        # 检测卖点条目（如：1. 【调经之王】直击月经紊乱）
        match = re.match(r'^\d+\.\s*【(.+?)】(.+)', line)
        if match:
            title = match.group(1)
            description = match.group(2)
            points.append({
                "category": current_category,
                "title": title,
                "description": description,
                "full_text": f"【{title}】{description}"
            })
    
    return points


def filter_by_direction(selling_points: list, direction: str) -> list:
    """
    按文案方向过滤卖点
    
    Args:
        selling_points: 卖点列表
        direction: 文案方向关键词（如"孕妇补铁"、"宫寒痛经"）
        
    Returns:
        list: 过滤后的卖点列表（相关性高的优先）
    """
    if not direction:
        return selling_points
    
    # 将方向拆分为关键词
    keywords = [kw.strip() for kw in re.split(r'[,，、\s]+', direction) if kw.strip()]
    
    # 计算每个卖点的相关性得分
    scored_points = []
    for point in selling_points:
        score = 0
        full_text = point.get("full_text", "") + point.get("category", "")
        
        for keyword in keywords:
            if keyword in full_text:
                score += 2  # 精确匹配
            elif any(char in full_text for char in keyword):
                score += 1  # 部分匹配
        
        scored_points.append((score, point))
    
    # 按得分排序，相关性高的优先
    scored_points.sort(key=lambda x: x[0], reverse=True)
    
    # 返回有相关性的卖点（如果都不相关则返回全部）
    relevant = [p for s, p in scored_points if s > 0]
    
    return relevant if relevant else selling_points


def format_selling_points(selling_points: list, direction: str = "") -> str:
    """
    格式化卖点为文本（供 AI 使用）
    
    Args:
        selling_points: 卖点列表
        direction: 可选的方向过滤
        
    Returns:
        str: 格式化后的卖点文本
    """
    if direction:
        selling_points = filter_by_direction(selling_points, direction)
    
    lines = []
    current_category = ""
    
    for point in selling_points:
        category = point.get("category", "")
        if category and category != current_category:
            current_category = category
            lines.append(f"\n## {category}")
        
        lines.append(f"- {point.get('full_text', '')}")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        direction = sys.argv[2] if len(sys.argv) > 2 else ""
        
        info = read_product_info(test_file)
        print(f"产品名称: {info['product_name']}")
        print(f"卖点数量: {len(info['selling_points'])}")
        print("\n格式化卖点:")
        print(format_selling_points(info['selling_points'], direction))
    else:
        print("用法: python product_reader.py <卖点文件路径> [方向关键词]")
