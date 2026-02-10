# -*- coding: utf-8 -*-
"""
数据读取模块
扫描竞品文件夹，按类别组织图片素材与数据文件
"""

from pathlib import Path
from typing import Optional


# 支持的图片格式
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}

# 支持的数据文件格式
DATA_EXTENSIONS = {'.xlsx', '.xls', '.csv'}

# PDF 文件
PDF_EXTENSIONS = {'.pdf'}

# 标准子文件夹名称 → 分析类别映射
FOLDER_CATEGORY_MAP = {
    "主图": "main_images",
    "详情页": "detail_pages",
    "价格促销": "price_promo",
    "评价": "reviews",
    "销售数据": "sales_data",
}

# 混合文件夹中，按文件名前缀/关键词分类
FILENAME_PREFIX_MAP = {
    "主图": "main_images",
    "详情": "detail_pages",
    "详情长图": "detail_pages",
    "价格": "price_promo",
    "促销": "price_promo",
    "评价": "reviews",
    "评论": "reviews",
    "销量": "sales_data",
    "销售": "sales_data",
    "排名": "sales_data",
    "首屏": "screenshots",
    "截图": "screenshots",
    "链接": "screenshots",
}


def scan_competitor_folder(folder_path: str) -> dict:
    """
    扫描单个竞品文件夹，返回按类别组织的图片列表和数据文件

    Args:
        folder_path: 竞品文件夹路径

    Returns:
        dict: {
            "name": 竞品名称,
            "path": 文件夹路径,
            "categories": {
                "main_images": [图片路径列表],
                "detail_pages": [...],
                "price_promo": [...],
                "reviews": [...],
                "sales_data": [...],
                "screenshots": [...],
            },
            "data_files": {
                "xlsx": [Excel路径列表],
                "pdf": [PDF路径列表],
                "csv": [CSV路径列表],
            },
            "text_info": 补充信息文本,
            "total_images": 总图片数
        }
    """
    folder = Path(folder_path)
    if not folder.exists():
        raise FileNotFoundError(f"竞品文件夹不存在: {folder_path}")

    result = {
        "name": folder.name,
        "path": str(folder),
        "categories": {},
        "data_files": {"xlsx": [], "pdf": [], "csv": []},
        "text_info": "",
        "total_images": 0,
    }

    # ====== 收集根目录的数据文件 ======
    for f in sorted(folder.iterdir()):
        if not f.is_file():
            continue
        # 跳过临时文件
        if f.name.startswith("~$"):
            continue
        suffix = f.suffix.lower()
        if suffix in {'.xlsx', '.xls'}:
            result["data_files"]["xlsx"].append(str(f))
        elif suffix == '.csv':
            result["data_files"]["csv"].append(str(f))
        elif suffix == '.pdf':
            result["data_files"]["pdf"].append(str(f))

    # ====== 扫描子文件夹中的图片 ======
    matched_folders = set()
    for sub in sorted(folder.iterdir()):
        if not sub.is_dir():
            continue
        sub_name = sub.name

        # 精确匹配标准类别文件夹
        if sub_name in FOLDER_CATEGORY_MAP:
            cat_key = FOLDER_CATEGORY_MAP[sub_name]
            images = _get_sorted_images(sub)
            result["categories"][cat_key] = images
            result["total_images"] += len(images)
            matched_folders.add(sub_name)
        else:
            # 混合文件夹（如 "主图+详情页"）：按文件名关键词分类
            is_mixed = any(kw in sub_name for kw in FOLDER_CATEGORY_MAP)
            if is_mixed or not matched_folders:
                images = _get_sorted_images(sub)
                if images:
                    classified = _classify_images_by_name(images)
                    for cat_key, cat_images in classified.items():
                        if cat_key not in result["categories"]:
                            result["categories"][cat_key] = []
                        result["categories"][cat_key].extend(cat_images)
                        result["total_images"] += len(cat_images)
                    matched_folders.add(sub_name)

    # ====== 扫描根目录的图片 ======
    root_images = _get_sorted_images(folder)
    if root_images:
        if result["total_images"] == 0:
            # 没有子文件夹分类，全部按文件名分类
            classified = _classify_images_by_name(root_images)
            for cat_key, cat_images in classified.items():
                if cat_key not in result["categories"]:
                    result["categories"][cat_key] = []
                result["categories"][cat_key].extend(cat_images)
                result["total_images"] += len(cat_images)
        else:
            # 有子文件夹但根目录也有图片，按文件名分类后合并
            classified = _classify_images_by_name(root_images)
            for cat_key, cat_images in classified.items():
                if cat_key not in result["categories"]:
                    result["categories"][cat_key] = []
                result["categories"][cat_key].extend(cat_images)
                result["total_images"] += len(cat_images)

    # ====== 读取补充信息文本 ======
    result["text_info"] = _read_text_info(folder)

    return result


def scan_all_competitors(base_path: str) -> list:
    """
    扫描基础目录下所有竞品文件夹

    Args:
        base_path: 包含多个竞品文件夹的基础路径

    Returns:
        list[dict]: 每个竞品的扫描结果
    """
    base = Path(base_path)
    if not base.exists():
        raise FileNotFoundError(f"基础目录不存在: {base_path}")

    competitors = []
    for item in sorted(base.iterdir()):
        if item.is_dir() and not item.name.startswith(('.', '_', 'output')):
            try:
                comp_data = scan_competitor_folder(str(item))
                if comp_data["total_images"] > 0 or any(comp_data["data_files"].values()):
                    competitors.append(comp_data)
            except Exception as e:
                print(f"  ⚠ 跳过 {item.name}: {e}")

    return competitors


def _classify_images_by_name(image_paths: list) -> dict:
    """根据文件名关键词将图片分类到不同类别"""
    classified = {}
    for img_path in image_paths:
        name = Path(img_path).stem
        matched_cat = None
        for prefix, cat_key in FILENAME_PREFIX_MAP.items():
            if name.startswith(prefix) or prefix in name:
                matched_cat = cat_key
                break
        if matched_cat is None:
            matched_cat = "uncategorized"
        if matched_cat not in classified:
            classified[matched_cat] = []
        classified[matched_cat].append(img_path)
    return classified


def _get_sorted_images(folder: Path) -> list:
    """获取文件夹中的图片列表（按名称排序）"""
    images = []
    for f in sorted(folder.iterdir()):
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
            # 跳过临时文件
            if not f.name.startswith("~$"):
                images.append(str(f))
    return images


def _read_text_info(folder: Path) -> str:
    """读取补充信息文本文件"""
    possible_names = [
        "补充信息.txt",
        "基本信息.txt",
        "信息.txt",
        "备注.txt",
        "info.txt",
    ]
    for name in possible_names:
        txt_path = folder / name
        if txt_path.exists():
            try:
                return txt_path.read_text(encoding='utf-8').strip()
            except Exception:
                try:
                    return txt_path.read_text(encoding='gbk').strip()
                except Exception:
                    pass
    return ""


def get_category_display_name(category_key: str) -> str:
    """获取类别的中文显示名称"""
    display_names = {
        "main_images": "主图",
        "detail_pages": "详情页",
        "price_promo": "价格促销",
        "reviews": "用户评价",
        "sales_data": "销售数据",
        "screenshots": "截图/首屏",
        "uncategorized": "未分类图片",
    }
    return display_names.get(category_key, category_key)


def print_scan_summary(competitors: list) -> None:
    """打印扫描结果摘要"""
    print(f"  共发现 {len(competitors)} 个竞品：")
    for comp in competitors:
        print(f"\n  📦 {comp['name']}（共 {comp['total_images']} 张图片）")
        for cat_key, images in comp["categories"].items():
            if images:
                print(f"     └─ {get_category_display_name(cat_key)}: {len(images)} 张")
        # 显示数据文件
        for ext, files in comp.get("data_files", {}).items():
            if files:
                print(f"     └─ {ext.upper()} 数据文件: {len(files)} 个")
        if comp["text_info"]:
            preview = comp["text_info"][:50] + "..." if len(comp["text_info"]) > 50 else comp["text_info"]
            print(f"     └─ 补充信息: {preview}")
