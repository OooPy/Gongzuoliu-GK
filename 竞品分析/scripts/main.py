# -*- coding: utf-8 -*-
"""
电商竞品分析 Agent - 主程序
医药保健品行业大师级竞品深度分析

流程：扫描竞品素材(图片+数据) → Gemini AI 多维度分析 → Word 报告输出
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# ============== 自动安装依赖 ==============
def check_and_install_dependencies():
    """检查并自动安装缺失的依赖"""
    required_packages = {
        'google-generativeai': 'google.generativeai',
        'python-docx': 'docx',
        'Pillow': 'PIL',
        'python-dotenv': 'dotenv',
        'openpyxl': 'openpyxl',
        'PyPDF2': 'PyPDF2',
        'PyMuPDF': 'fitz',
        'pdfplumber': 'pdfplumber',
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

from image_reader import scan_competitor_folder, scan_all_competitors, print_scan_summary
from gemini_analyzer import analyze_competitor
from document_generator import create_analysis_report, create_batch_reports


# ============== 配置区域 ==============

# 竞品素材根目录
# 支持两种模式：
#   1. 指向包含多个竞品子文件夹的目录 → 批量分析
#   2. 直接指向单个竞品文件夹（支持绝对路径）→ 单个分析
COMPETITORS_BASE_FOLDER = r"d:\竞品信息"

# 我方产品信息（可选，用于生成差异化分析建议）
OUR_PRODUCT_INFO = ""

# 电商平台（天猫/京东/拼多多/抖音）
PLATFORM = "天猫"

# API 调用间隔（秒），Tier 1 建议 15-20 秒确保不触发限频
API_DELAY = 20.0

# =======================================


def main():
    """主程序入口"""
    print()
    print("=" * 60)
    print("  🔬 医药保健品竞品深度分析 Agent")
    print("  素材扫描 → AI 多维度分析 → Word 报告")
    print("=" * 60)
    print()

    # 获取路径
    comp_folder = Path(COMPETITORS_BASE_FOLDER)
    if not comp_folder.is_absolute():
        script_dir = Path(__file__).parent.resolve()
        base_dir = script_dir.parent
        comp_folder = base_dir / COMPETITORS_BASE_FOLDER

    competitors_path = comp_folder

    # ====== Step 1: 扫描竞品素材 ======
    print("[Step 1] 扫描竞品素材与数据文件...")

    if not competitors_path.exists():
        print(f"  ✗ 竞品素材目录不存在: {competitors_path}")
        print(f"  请创建目录并放入竞品截图和数据文件，结构示例：")
        print(f"    竞品素材/")
        print(f"    ├── 竞品A_品牌名/")
        print(f"    │   ├── 主图+详情页/    # 图片文件")
        print(f"    │   ├── 详细信息.xlsx   # 运营数据")
        print(f"    │   └── 补充信息.txt    # 可选补充文字")
        print(f"    └── 竞品B_品牌名/")
        print(f"        └── ...")
        return 1

    # 判断是单个竞品还是多个竞品
    category_keywords = ["主图", "详情页", "价格促销", "评价", "销售数据"]
    has_category_folders = any(
        any(kw in item.name for kw in category_keywords)
        for item in competitors_path.iterdir()
        if item.is_dir()
    )
    image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    data_exts = {'.xlsx', '.xls', '.csv'}
    has_root_images = any(
        f.suffix.lower() in image_exts
        for f in competitors_path.iterdir()
        if f.is_file() and not f.name.startswith("~$")
    )
    has_root_data = any(
        f.suffix.lower() in data_exts
        for f in competitors_path.iterdir()
        if f.is_file() and not f.name.startswith("~$")
    )

    if has_category_folders or has_root_images or has_root_data:
        # 单个竞品
        competitors = [scan_competitor_folder(str(competitors_path))]
    else:
        # 多个竞品
        competitors = scan_all_competitors(str(competitors_path))

    if not competitors:
        print("  ✗ 未找到任何竞品素材")
        return 1

    print_scan_summary(competitors)
    print()

    # ====== Step 2: 逐个分析竞品 ======
    print("[Step 2] 开始 AI 深度分析...")
    print("  📋 9大分析维度（共4次API调用）：")
    print("     [视觉] 主图策略 → 详情页逻辑")
    print("     [数据] 规格设计 / 活动促销 / 评价 / 销售 / SKU / 搜索词 / 流量")
    print("     [总结] 综合竞品评估")
    print(f"  ⏱  API间隔 {API_DELAY}秒，预计单品分析 2-4 分钟")
    print()

    all_results = []

    for i, comp_data in enumerate(competitors, 1):
        print(f"\n{'━' * 60}")
        print(f"  [{i}/{len(competitors)}] 深度分析竞品: {comp_data['name']}")
        print(f"  图片 {comp_data['total_images']} 张 / "
              f"数据文件 {sum(len(v) for v in comp_data.get('data_files', {}).values())} 个")
        print(f"{'━' * 60}")

        try:
            result = analyze_competitor(
                comp_data,
                delay=API_DELAY,
                our_product_info=OUR_PRODUCT_INFO,
            )
            all_results.append(result)

            # 打印简要摘要
            _print_analysis_brief(result)

        except Exception as e:
            print(f"  ✗ 分析失败: {e}")
            import traceback
            traceback.print_exc()
            all_results.append({
                "competitor_name": comp_data["name"],
                "error": str(e),
            })

    print()

    # ====== Step 3: 生成报告 ======
    print("[Step 3] 生成分析报告...")

    # 生成 Word 报告（保存到竞品自身文件夹内）
    print("\n  📄 生成 Word 分析报告...")
    doc_paths = create_batch_reports(all_results, str(competitors_path))

    # 导出 JSON 备份（也保存到竞品文件夹内）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for result in all_results:
        comp_name = result.get("competitor_name", "未知")
        comp_folder = competitors_path / comp_name
        if not comp_folder.exists():
            comp_folder = competitors_path

        json_path = comp_folder / f"竞品分析_{timestamp}.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"  ✓ JSON 备份: {json_path}")
        except Exception as e:
            print(f"  ⚠ JSON 导出失败: {e}")

    print()
    print("=" * 60)
    print("  ✓ 竞品深度分析完成！")
    print(f"  → 分析了 {len(all_results)} 个竞品")
    for dp in doc_paths:
        print(f"  → 报告: {dp}")
    print()
    print("  📌 这是第一轮分析（约80分），你可以：")
    print("     - 针对某个维度要求更深入的分析")
    print("     - 提供更多数据补充分析")
    print("     - 提供我方产品信息获取差异化建议")
    print("=" * 60)

    return 0


def _print_analysis_brief(result: dict):
    """打印分析结果简要摘要"""
    name = result.get("competitor_name", "未知")

    main_strategy = result.get("main_images_strategy", {})
    product_name = main_strategy.get("product_name") or name

    print(f"\n  ┌─ 竞品：{product_name}")

    # 主图策略
    overall = main_strategy.get("overall_strategy")
    if overall:
        print(f"  │ 主图策略：{str(overall)[:60]}...")

    # 详情页
    detail = result.get("detail_page_logic", {})
    logic = detail.get("content_logic_flow")
    if logic:
        print(f"  │ 详情逻辑：{str(logic)[:60]}...")

    # 数据维度
    data = result.get("data_analysis", {})
    sales = data.get("sales_30days", {})
    if isinstance(sales, dict) and sales.get("total_sales"):
        print(f"  │ 30日销售：{sales['total_sales']}")

    reviews = data.get("reviews_analysis", {})
    if isinstance(reviews, dict) and reviews.get("total_volume"):
        print(f"  │ 评价量级：{reviews['total_volume']}")

    # 综合评估
    summary = result.get("competitive_summary", {})
    threat = summary.get("overall_threat_level")
    if threat:
        print(f"  │ 威胁评级：{str(threat)[:60]}")

    print(f"  └─────────────────────────")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
