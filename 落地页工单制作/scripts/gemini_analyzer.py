# -*- coding: utf-8 -*-
"""
Gemini AI 文案分析与生成模块
提取竞品文案，结合产品卖点生成新文案
"""

import os
import re
import time
import random
import google.generativeai as genai
from pathlib import Path
from PIL import Image
from dotenv import load_dotenv

# 加载环境变量（从 Skill 根目录的 .env 文件）
script_dir = Path(__file__).parent.resolve()
env_path = script_dir.parent / '.env'
load_dotenv(env_path)

# Gemini 配置
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.0-flash"


def init_gemini():
    """初始化 Gemini API"""
    if not API_KEY:
        raise ValueError("请在 .env 文件中设置 GOOGLE_API_KEY")
    genai.configure(api_key=API_KEY)


def extract_copywriting(image_path: str, max_retries: int = 3) -> dict:
    """
    提取竞品图片中的核心文案
    
    Args:
        image_path: 图片路径
        max_retries: 最大重试次数
        
    Returns:
        dict: 包含 text_lines（文案行列表）和 word_count（总字数）
    """
    init_gemini()
    
    prompt = """你是一位资深电商运营专家。请仔细分析这张电商图片，提取其中的核心营销文案。

【提取规则】
1. 只提取设计师手动添加的营销文案（标题、副标题、卖点说明等）
2. 严禁提取：产品包装盒、瓶身上的产品固有标签、成分表、生产信息等
3. 严禁提取：品牌Logo中的文字（除非是主标题的一部分）
4. 按视觉层级排列：主标题 → 副标题 → 正文/卖点
5. 每行文案单独列出

请按以下格式返回：
主标题：[文案内容]
副标题：[文案内容]（如果有）
卖点1：[文案内容]
卖点2：[文案内容]
...

如果图片中没有明显的营销文案，返回：无营销文案"""

    for attempt in range(max_retries):
        try:
            img = Image.open(image_path)
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content([prompt, img])
            
            result_text = response.text.strip()
            
            # 解析结果
            lines = [line.strip() for line in result_text.split('\n') if line.strip()]
            
            # 计算总字数（只统计冒号后的内容）
            total_chars = 0
            clean_lines = []
            for line in lines:
                if '：' in line:
                    content = line.split('：', 1)[1].strip()
                    clean_lines.append(content)
                    total_chars += len(content)
                elif ':' in line:
                    content = line.split(':', 1)[1].strip()
                    clean_lines.append(content)
                    total_chars += len(content)
            
            return {
                "raw_text": result_text,
                "text_lines": clean_lines,
                "word_count": total_chars
            }
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 0.3 + random.uniform(0, 0.3)  # 短暂等待
                print(f"    ⚠ 提取失败，{wait_time:.1f}秒后重试: {e}")
                time.sleep(wait_time)
            else:
                return {"raw_text": "", "text_lines": [], "word_count": 0}
    
    return {"raw_text": "", "text_lines": [], "word_count": 0}


def generate_copywriting(
    image_path: str,
    product_info: str,
    direction: str = "",
    target_word_count: int = 0,
    max_retries: int = 3
) -> str:
    """
    基于产品卖点生成新文案
    
    Args:
        image_path: 竞品图片路径（用于参考布局和文案结构）
        product_info: 产品卖点文本
        direction: 文案方向（如"孕妇补铁"）
        target_word_count: 目标字数（与竞品差异控制在5字以内）
        max_retries: 最大重试次数
        
    Returns:
        str: 生成的文案
    """
    init_gemini()
    
    # 构建 Prompt - 强化电商运营专家思维
    direction_hint = f"【本次重点方向】{direction}" if direction else ""
    
    word_count_hint = ""
    if target_word_count > 0:
        min_count = max(5, target_word_count - 5)
        max_count = target_word_count + 5
        word_count_hint = f"【字数控制】{min_count}-{max_count} 字"
    
    prompt = f"""你是一位有10年电商运营经验的详情页文案专家。你深谙用户心理和转化漏斗，知道详情页每一屏的作用和文案策略。

【第一步：识别这张图在详情页中的角色】
请先分析这张竞品图片在整个详情页中承担的角色：

1. **首屏/钩子**：吸引停留，核心利益点一句话打动用户
2. **痛点共鸣**：描述用户困扰，引发"说的就是我"的感觉
3. **解决方案**：展示产品如何解决痛点
4. **功效说明**：具体功效或成分介绍
5. **信任背书**：权威认证、检测报告、品牌实力
6. **对比优势**：与竞品或传统方案的对比
7. **使用场景**：什么人、什么时候用
8. **用户证言**：好评、案例、效果展示
9. **行动号召**：促销信息、限时优惠

【第二步：针对角色输出文案】
根据识别出的角色，用对应的文案策略来写：

- 首屏：一句打动人心的核心利益点，不超过15字
- 痛点：用"你是否..."、"每天..."等句式引发共鸣
- 功效：用数据说话，如"3倍吸收"、"14天见效"
- 信任：突出权威性，如"国食健字号"、"百年老字号"
- 对比：用具体差异点，不要泛泛而谈

【我们的产品卖点素材库】
{product_info}

{direction_hint}
{word_count_hint}

【输出要求】
1. 只输出适合这张图角色的文案，不要堆砌所有卖点
2. 文案要有层次感：主标题 → 副标题/支撑点
3. 保持与原图相似的文案结构和长度
4. 使用电商高转化表达，避免说明书式描述

直接输出最终文案，不要解释角色分析过程。"""

    for attempt in range(max_retries):
        try:
            img = Image.open(image_path)
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content([prompt, img])
            
            return response.text.strip()
            
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 0.3 + random.uniform(0, 0.3)  # 短暂等待
                print(f"    ⚠ 生成失败，{wait_time:.1f}秒后重试: {e}")
                time.sleep(wait_time)
            else:
                raise RuntimeError(f"文案生成失败: {e}")
    
    return ""


def analyze_and_generate(
    image_path: str,
    product_info: str,
    direction: str = "",
    delay_seconds: float = 1.0
) -> dict:
    """
    完整流程：提取竞品文案 → 生成新文案
    
    Args:
        image_path: 竞品图片路径
        product_info: 产品卖点文本
        direction: 文案方向
        delay_seconds: API 调用间隔
        
    Returns:
        dict: 包含 image_path, image_name, competitor_copy, copywriting
    """
    img_path = Path(image_path)
    img_name = img_path.name
    
    print(f"  → 分析: {img_name}")
    
    # Step 1: 提取竞品文案
    competitor_result = extract_copywriting(image_path)
    target_count = competitor_result.get("word_count", 0)
    
    print(f"    - 竞品文案字数: {target_count}")
    
    # 短暂延迟
    time.sleep(delay_seconds)
    
    # Step 2: 生成新文案
    new_copy = generate_copywriting(
        image_path,
        product_info,
        direction=direction,
        target_word_count=target_count
    )
    
    # 统计生成文案的字数
    new_count = len(re.sub(r'\s+', '', new_copy))
    print(f"    - 生成文案字数: {new_count} (差异: {abs(new_count - target_count)} 字)")
    
    return {
        "image_path": str(image_path),
        "image_name": img_name,
        "competitor_copy": competitor_result.get("raw_text", ""),
        "competitor_word_count": target_count,
        "copywriting": new_copy,
        "new_word_count": new_count
    }


def batch_analyze(
    image_folder: str,
    product_info: str,
    direction: str = "",
    delay_seconds: float = 1.5,
    max_count: int = 0
) -> list:
    """
    批量分析图片并生成文案
    
    Args:
        image_folder: 图片文件夹路径
        product_info: 产品卖点文本
        direction: 文案方向
        delay_seconds: API 调用间隔
        max_count: 最大处理数量（0表示不限制）
        
    Returns:
        list: 结果列表
    """
    folder = Path(image_folder)
    
    # 查找所有图片
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = sorted([f for f in folder.iterdir() if f.suffix.lower() in image_extensions])
    
    if max_count > 0:
        images = images[:max_count]
    
    print(f"  共找到 {len(images)} 张图片")
    
    results = []
    
    for i, img_path in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}]")
        
        try:
            result = analyze_and_generate(
                str(img_path),
                product_info,
                direction=direction,
                delay_seconds=delay_seconds
            )
            results.append(result)
            print(f"    ✓ 完成")
            
        except Exception as e:
            print(f"    ✗ 失败: {e}")
            results.append({
                "image_path": str(img_path),
                "image_name": img_path.name,
                "copywriting": f"[处理失败: {e}]",
                "error": str(e)
            })
        
        # 除最后一张外，都要等待
        if i < len(images):
            time.sleep(delay_seconds)
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        test_info = sys.argv[2] if len(sys.argv) > 2 else "雪叶红口服液 - 气血双补，调经养颜"
        test_direction = sys.argv[3] if len(sys.argv) > 3 else ""
        
        print(f"测试图片: {test_image}")
        result = analyze_and_generate(test_image, test_info, test_direction)
        
        print("\n=== 竞品文案 ===")
        print(result.get("competitor_copy", ""))
        print("\n=== 生成文案 ===")
        print(result.get("copywriting", ""))
    else:
        print("用法: python gemini_analyzer.py <图片路径> [产品卖点] [方向]")
