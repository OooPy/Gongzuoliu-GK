# -*- coding: utf-8 -*-
"""
飞书多维表格写入模块
将竞品分析结果写入飞书 Bitable

注意：此模块设计为通过 Copilot 的飞书 MCP 工具调用，
而非直接通过 API。主程序会生成结构化数据，
由 Copilot Agent 负责调用飞书 MCP 写入。
"""

import json
from typing import Optional


# 飞书多维表格字段定义
BITABLE_FIELDS = [
    {"field_name": "竞品名称", "type": 1},       # 文本（索引字段）
    {"field_name": "平台", "type": 3,             # 单选
     "property": {"options": [
         {"name": "天猫"},
         {"name": "京东"},
         {"name": "拼多多"},
         {"name": "抖音"},
         {"name": "其他"},
     ]}},
    {"field_name": "价格区间", "type": 1},         # 文本
    {"field_name": "核心卖点", "type": 1},         # 文本
    {"field_name": "文案策略", "type": 1},         # 文本
    {"field_name": "目标人群", "type": 1},         # 文本
    {"field_name": "核心成分", "type": 1},         # 文本
    {"field_name": "功效宣称", "type": 1},         # 文本
    {"field_name": "促销策略", "type": 1},         # 文本
    {"field_name": "用户好评要点", "type": 1},     # 文本
    {"field_name": "用户差评要点", "type": 1},     # 文本
    {"field_name": "月销量级", "type": 1},         # 文本
    {"field_name": "综合评分", "type": 1},         # 文本
    {"field_name": "竞品优势", "type": 1},         # 文本
    {"field_name": "竞品劣势", "type": 1},         # 文本
    {"field_name": "差异化机会", "type": 1},       # 文本
    {"field_name": "竞争策略建议", "type": 1},     # 文本
    {"field_name": "分析日期", "type": 5,          # 日期
     "property": {"date_formatter": "yyyy/MM/dd"}},
]


def _safe_join(data, key, separator="、"):
    """安全地将列表字段拼接为字符串"""
    value = data.get(key, [])
    if isinstance(value, list):
        return separator.join(str(v) for v in value if v)
    return str(value) if value else ""


def format_record_for_bitable(analysis_result: dict, platform: str = "天猫") -> dict:
    """
    将分析结果格式化为飞书多维表格的记录格式
    
    Args:
        analysis_result: 完整的竞品分析结果（来自 gemini_analyzer.analyze_competitor）
        platform: 电商平台
        
    Returns:
        dict: 适合写入飞书 Bitable 的 fields 字典
    """
    # 从各维度提取数据
    main = analysis_result.get("main_images", {})
    detail = analysis_result.get("detail_pages", {})
    price = analysis_result.get("price_promo", {})
    reviews = analysis_result.get("reviews", {})
    sales = analysis_result.get("sales_data", {})
    uncategorized = analysis_result.get("uncategorized", {})
    opportunity = analysis_result.get("opportunity_analysis", {})
    
    # 构建记录
    import time
    
    # 价格信息：合并日常价和促销价
    price_info = ""
    regular = price.get("regular_price") or main.get("price_range") or uncategorized.get("price_range", "")
    promo = price.get("promo_price", "")
    if regular and promo and promo != "无":
        price_info = f"日常价: {regular} / 促销价: {promo}"
    elif regular:
        price_info = str(regular)
    
    record = {
        "竞品名称": main.get("product_name") or uncategorized.get("product_name") or analysis_result.get("competitor_name", ""),
        "平台": platform,
        "价格区间": price_info,
        "核心卖点": _safe_join(main, "top_selling_points") or _safe_join(uncategorized, "top_selling_points"),
        "文案策略": main.get("copy_strategy") or uncategorized.get("copy_strategy", ""),
        "目标人群": main.get("target_audience") or uncategorized.get("target_audience", ""),
        "核心成分": detail.get("core_ingredients") or uncategorized.get("core_ingredients", ""),
        "功效宣称": _safe_join(detail, "efficacy_claims") or _safe_join(uncategorized, "efficacy_claims"),
        "促销策略": price.get("promo_strategy") or uncategorized.get("promo_strategy", ""),
        "用户好评要点": _safe_join(reviews, "positive_highlights") or _safe_join(uncategorized, "positive_highlights"),
        "用户差评要点": _safe_join(reviews, "negative_highlights") or _safe_join(uncategorized, "negative_highlights"),
        "月销量级": sales.get("monthly_sales") or uncategorized.get("monthly_sales", ""),
        "综合评分": reviews.get("overall_rating") or sales.get("store_rating") or uncategorized.get("overall_rating", ""),
        "竞品优势": opportunity.get("competitor_strengths", ""),
        "竞品劣势": opportunity.get("competitor_weaknesses", ""),
        "差异化机会": opportunity.get("opportunity", ""),
        "竞争策略建议": opportunity.get("strategy_suggestion", ""),
        "分析日期": int(time.time()) * 1000,  # 飞书日期字段需要毫秒时间戳
    }
    
    return record


def format_all_records(all_results: list, platform: str = "天猫") -> list:
    """
    批量格式化所有竞品的分析结果
    
    Args:
        all_results: 所有竞品的分析结果列表
        platform: 电商平台
        
    Returns:
        list[dict]: 记录列表
    """
    records = []
    for result in all_results:
        record = format_record_for_bitable(result, platform)
        records.append(record)
    return records


def print_analysis_summary(analysis_result: dict) -> None:
    """打印分析结果摘要（用于终端预览）"""
    main = analysis_result.get("main_images", {})
    detail = analysis_result.get("detail_pages", {})
    price = analysis_result.get("price_promo", {})
    reviews = analysis_result.get("reviews", {})
    opportunity = analysis_result.get("opportunity_analysis", {})
    
    name = main.get("product_name") or analysis_result.get("competitor_name", "未知")
    
    print(f"\n  ┌─ 竞品：{name}")
    
    if main.get("price_range"):
        print(f"  │ 价格：{main['price_range']}")
    
    if main.get("top_selling_points"):
        points = "、".join(main["top_selling_points"][:3])
        print(f"  │ 卖点：{points}")
    
    if main.get("target_audience"):
        print(f"  │ 人群：{main['target_audience']}")
    
    if detail.get("core_ingredients"):
        print(f"  │ 成分：{detail['core_ingredients'][:50]}")
    
    if price.get("promo_strategy"):
        print(f"  │ 促销：{price['promo_strategy'][:50]}")
    
    if reviews.get("positive_highlights"):
        print(f"  │ 好评：{'、'.join(reviews['positive_highlights'][:3])}")
    
    if opportunity.get("opportunity"):
        print(f"  │ 机会：{opportunity['opportunity'][:60]}")
    
    print(f"  └─────────────────────────")


def export_to_json(all_results: list, output_path: str) -> str:
    """
    将分析结果导出为 JSON 文件（备份用）
    
    Args:
        all_results: 所有竞品的分析结果
        output_path: 输出文件路径
        
    Returns:
        str: 输出文件路径
    """
    from pathlib import Path
    
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    return str(output)
