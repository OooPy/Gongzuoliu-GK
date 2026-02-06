# -*- coding: utf-8 -*-
"""
电商创意图文案生成器 - 主程序
串联所有模块，完成从竞品分析到文档生成的完整流程
"""

import sys
from pathlib import Path

# 导入自定义模块
from product_reader import read_product_info, format_selling_points
from gemini_analyzer import batch_analyze
from document_generator import create_brief_document, create_simple_brief


# ============== 配置区域 ==============

# 竞品图片文件夹
COMPETITOR_FOLDER = "20260206 竞品创意图"

# 产品卖点文档
PRODUCT_DOC = "雪叶红卖点.txt"

# 输出文件夹
OUTPUT_FOLDER = "output"

# 作者名称
AUTHOR_NAME = "阳宏"

# 用户指定的文案方向（可选，留空则不指定）
# 例如："更偏向宫寒调理"、"主打孕妈补血"、"强调性价比"
USER_DIRECTION = ""

# API 调用间隔（秒），避免触发限流
API_DELAY = 1.5

# 最大处理图片数量（0表示不限制）
MAX_COUNT = 10

# =======================================


def main():
    """主程序入口"""
    print("=" * 60)
    print("  电商创意图文案生成器")
    print("  基于 Gemini AI 的智能文案生成工具")
    print("=" * 60)
    print()
    
    # 获取当前脚本所在目录
    base_dir = Path(__file__).parent.resolve()
    
    # 构建完整路径
    competitor_path = base_dir / COMPETITOR_FOLDER
    product_doc_path = base_dir / PRODUCT_DOC
    output_path = base_dir / OUTPUT_FOLDER
    
    # Step 1: 读取产品信息
    print("[Step 1] 读取产品卖点文档...")
    try:
        product_info = read_product_info(str(product_doc_path))
        product_name = product_info["product_name"]
        selling_points = format_selling_points(product_info["selling_points"])
        
        print(f"  ✓ 产品名称: {product_name}")
        print(f"  ✓ 卖点字数: {len(selling_points)} 字")
    except Exception as e:
        print(f"  ✗ 读取失败: {e}")
        return 1
    
    print()
    
    # Step 2: 检查竞品图片文件夹
    print("[Step 2] 检查竞品图片...")
    if not competitor_path.exists():
        print(f"  ✗ 竞品图片文件夹不存在: {competitor_path}")
        return 1
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    image_files = [f for f in competitor_path.iterdir() if f.suffix.lower() in image_extensions]
    
    if not image_files:
        print(f"  ✗ 未找到图片文件")
        return 1
    
    print(f"  ✓ 找到 {len(image_files)} 张竞品图片")
    print()
    
    # Step 3: 调用 Gemini AI 分析并生成文案
    print("[Step 3] 调用 Gemini AI 分析竞品图片并生成文案...")
    if USER_DIRECTION:
        print(f"  → 用户指定方向: {USER_DIRECTION}")
    
    print()
    
    try:
        results = batch_analyze(
            str(competitor_path),
            selling_points,
            user_direction=USER_DIRECTION,
            delay_seconds=API_DELAY,
            max_count=MAX_COUNT
        )
    except Exception as e:
        print(f"  ✗ AI 分析失败: {e}")
        return 1
    
    if not results:
        print("  ✗ 未生成任何结果")
        return 1
    
    print()
    
    # Step 4: 生成 Word 文档
    print("[Step 4] 生成 Word 工单文档...")
    try:
        doc_path = create_brief_document(
            results,
            str(output_path),
            product_name=product_name,
            author_name=AUTHOR_NAME
        )
        print(f"  ✓ Word 文档: {doc_path}")
        
        # 同时生成文本汇总
        txt_path = create_simple_brief(
            results,
            str(output_path),
            product_name=product_name
        )
        print(f"  ✓ 文案汇总: {txt_path}")
        
    except Exception as e:
        print(f"  ✗ 文档生成失败: {e}")
        return 1
    
    print()
    print("=" * 60)
    print("  ✓ 全部完成！")
    print(f"  → 请查看输出文件夹: {output_path}")
    print("=" * 60)
    
    return 0


def run_single(image_path: str, direction: str = ""):
    """
    单图测试模式
    
    Args:
        image_path: 单张竞品图片路径
        direction: 文案方向
    """
    from gemini_analyzer import analyze_and_generate
    
    base_dir = Path(__file__).parent.resolve()
    product_doc_path = base_dir / PRODUCT_DOC
    
    # 读取产品信息
    product_info = read_product_info(str(product_doc_path))
    selling_points = format_selling_points(product_info["selling_points"])
    
    # 分析单张图片
    result = analyze_and_generate(image_path, selling_points, direction)
    
    print("\n生成的文案：")
    print("-" * 50)
    print(result)
    print("-" * 50)
    
    return result


if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) > 1:
        # 单图测试模式
        img_path = sys.argv[1]
        direction = sys.argv[2] if len(sys.argv) > 2 else ""
        run_single(img_path, direction)
    else:
        # 批量处理模式
        exit_code = main()
        sys.exit(exit_code)
