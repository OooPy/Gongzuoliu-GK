# -*- coding: utf-8 -*-
"""
落地页工单制作 Agent - 主程序
分析竞品图片，识别详情页角色，生成标准化设计工单
"""

import sys
import time
import subprocess
from pathlib import Path

# ============== 自动安装依赖 ==============
def check_and_install_dependencies():
    """检查并自动安装缺失的依赖"""
    required_packages = {
        'google-generativeai': 'google.generativeai',
        'python-docx': 'docx',
        'Pillow': 'PIL',
        'python-dotenv': 'dotenv'
    }
    
    missing = []
    for package, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"[安装依赖] 正在安装缺失的包: {', '.join(missing)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q'] + missing)
        print("[安装依赖] ✓ 完成")

check_and_install_dependencies()
# ==========================================

# 导入自定义模块
from product_reader import read_product_info, format_selling_points
from gemini_analyzer import analyze_and_generate, batch_analyze
from document_generator import create_work_order


# ============== 配置区域 ==============

# 竞品素材文件夹（包含"主图"和"详情页（切图）"子文件夹）
COMPETITOR_FOLDER = "yanbloom富铁饮"

# 产品卖点文档
PRODUCT_DOC = "雪叶红卖点.txt"

# 产品名称（用于工单标题）
PRODUCT_NAME = "雪叶红口服液"

# 输出文件夹
OUTPUT_FOLDER = "output"

# 负责人名称
AUTHOR_NAME = "阳宏"

# 文案方向（重点突出的卖点方向）
# 例如："孕妇补铁"、"宫寒痛经"、"气血双补"
COPY_DIRECTION = "气血虚补血"

# API 调用间隔（秒）- Gemini 2 Flash 限速 2000 RPM，可以更快
API_DELAY = 0.5

# 最大处理主图数量（0表示不限制）
MAX_MAIN_COUNT = 0

# =======================================


def main():
    """主程序入口"""
    print("=" * 60)
    print("  落地页工单制作 Agent")
    print("  电商专家思维 + 角色识别 + 文案生成")
    print("=" * 60)
    print()
    
    # 获取 Skill 根目录（scripts 的父目录）
    script_dir = Path(__file__).parent.resolve()
    base_dir = script_dir.parent  # Skill 根目录
    
    # 构建完整路径
    competitor_path = base_dir / COMPETITOR_FOLDER
    product_doc_path = base_dir / PRODUCT_DOC
    output_path = base_dir / OUTPUT_FOLDER
    
    # Step 1: 读取产品卖点
    print("[Step 1] 读取产品卖点文档...")
    try:
        product_info = read_product_info(str(product_doc_path))
        selling_points_text = format_selling_points(
            product_info["selling_points"],
            direction=COPY_DIRECTION
        )
        print(f"  ✓ 产品名称: {PRODUCT_NAME}")
        print(f"  ✓ 卖点数量: {len(product_info['selling_points'])} 条")
        print(f"  ✓ 文案方向: {COPY_DIRECTION}")
    except Exception as e:
        print(f"  ✗ 读取失败: {e}")
        return 1
    
    print()
    
    # Step 2: 检查竞品素材文件夹结构
    print("[Step 2] 检查竞品素材文件夹...")
    
    main_folder = competitor_path / "主图"
    detail_folder = competitor_path / "详情页（切图）"  # 使用已切好的详情页图片
    
    if not competitor_path.exists():
        print(f"  ✗ 竞品文件夹不存在: {competitor_path}")
        return 1
    
    # 检查主图
    main_images = []
    if main_folder.exists():
        image_exts = {'.jpg', '.jpeg', '.png', '.webp'}
        main_images = sorted([f for f in main_folder.iterdir() if f.suffix.lower() in image_exts])
        print(f"  ✓ 主图文件夹: {len(main_images)} 张")
    else:
        print(f"  ⚠ 主图文件夹不存在: {main_folder}")
    
    # 检查详情页切图
    detail_images = []
    if detail_folder.exists():
        image_exts = {'.jpg', '.jpeg', '.png', '.webp'}
        detail_images = sorted([f for f in detail_folder.iterdir() if f.suffix.lower() in image_exts])
        print(f"  ✓ 详情页切图文件夹: {len(detail_images)} 张")
    else:
        print(f"  ⚠ 详情页切图文件夹不存在: {detail_folder}")
    
    if not main_images and not detail_images:
        print("  ✗ 未找到任何竞品图片")
        return 1
    
    print()
    
    # Step 3: 处理主图（优先）
    main_results = []
    if main_images:
        print("[Step 3] 处理主图（优先输出）...")
        
        # 限制数量
        if MAX_MAIN_COUNT > 0:
            main_images = main_images[:MAX_MAIN_COUNT]
        
        for i, img_path in enumerate(main_images, 1):
            print(f"\n  [{i}/{len(main_images)}] 处理: {img_path.name}")
            
            try:
                result = analyze_and_generate(
                    str(img_path),
                    selling_points_text,
                    direction=COPY_DIRECTION,
                    delay_seconds=API_DELAY
                )
                main_results.append(result)
                
            except Exception as e:
                print(f"  ✗ 处理失败: {e}")
                main_results.append({
                    "image_path": str(img_path),
                    "image_name": img_path.name,
                    "copywriting": f"[处理失败: {e}]"
                })
            
            if i < len(main_images):
                time.sleep(API_DELAY)
        
        print(f"\n  ✓ 主图处理完成，共 {len(main_results)} 张")
    
    print()
    
    # Step 4: 处理详情页（已切好的图片，直接生成文案）
    detail_results = []
    if detail_images:
        print("[Step 4] 处理详情页切图...")
        
        for i, img_path in enumerate(detail_images, 1):
            print(f"\n  [{i}/{len(detail_images)}] 处理: {img_path.name}")
            
            try:
                result = analyze_and_generate(
                    str(img_path),
                    selling_points_text,
                    direction=COPY_DIRECTION,
                    delay_seconds=API_DELAY
                )
                detail_results.append(result)
                
            except Exception as e:
                print(f"  ✗ 处理失败: {e}")
                detail_results.append({
                    "image_path": str(img_path),
                    "image_name": img_path.name,
                    "copywriting": f"[处理失败: {e}]"
                })
            
            if i < len(detail_images):
                time.sleep(API_DELAY)
        
        print(f"\n  ✓ 详情页处理完成，共 {len(detail_results)} 张")
    
    print()
    
    # Step 5: 生成工单文档
    print("[Step 5] 生成 Word 工单文档...")
    
    try:
        doc_path = create_work_order(
            detail_results,
            main_results,
            str(output_path),
            product_name=PRODUCT_NAME,
            author_name=AUTHOR_NAME
        )
        
    except Exception as e:
        print(f"  ✗ 文档生成失败: {e}")
        return 1
    
    print()
    print("=" * 60)
    print("  ✓ 全部完成！")
    print(f"  → 工单文档: {doc_path}")
    print(f"  → 详情页: {len(detail_results)} 屏")
    print(f"  → 主图: {len(main_results)} 张")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
