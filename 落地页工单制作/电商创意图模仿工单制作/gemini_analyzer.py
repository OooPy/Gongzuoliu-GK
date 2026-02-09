# -*- coding: utf-8 -*-
"""
Gemini AI 文案生成核心模块
分析竞品图片，结合产品卖点生成新文案
"""

import os
import google.generativeai as genai
from pathlib import Path
from PIL import Image
import time
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# Gemini API 配置
API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.0-flash"  # 稳定的视觉模型


def init_gemini():
    """初始化 Gemini API"""
    if not API_KEY:
        raise ValueError("请在 .env 文件中配置 GOOGLE_API_KEY")
    genai.configure(api_key=API_KEY)
    return genai.GenerativeModel(MODEL_NAME)


def create_system_prompt(user_direction: str = "") -> str:
    """
    创建系统提示词
    
    Args:
        user_direction: 用户指定的文案方向
    
    Returns:
        str: 完整的系统提示词
    """
    base_prompt = """你是一位资深电商策划专家。请仔细分析这张竞品创意图。

【重要识别规则】
1. 只识别图片中的"营销文案"，即那些用于宣传、刺激购买的广告语
2. 不要识别产品包装上的文字（如成分表、生产信息、品牌logo文字等）
3. 不要识别图片中的产品名称、规格等非营销性文字

【分析与输出要求】
1. 分析竞品图中营销文案的字数和结构
2. 使用提供的【产品卖点】，模仿竞品图的文案结构，为我们的产品写新文案
3. 【极其重要】你生成的新文案字数必须与竞品图文案字数完全一致或非常接近
4. 每个文案区块的字数也要与对应的竞品文案区块字数一致

【文案风格要求】
1. 保持竞品图的视觉冲击力和痛点刺激方式
2. 紧密结合产品的核心卖点（中草药调理方向）
3. 符合电商广告法规范，避免虚假承诺

【输出格式 - 极其重要】
- 直接输出文案内容，不要任何前言、解释、标签或说明
- 不要输出"[竞品文案字数: X字]"这样的标注
- 不要输出"根据要求..."这样的说明
- 按视觉层次分段（主标题、副标题、正文等）
- 用空行分隔不同区块
- 只要最终的文案结果，设计师可以直接使用"""

    if user_direction:
        base_prompt += f"\n\n【用户指定方向】：{user_direction}"
    
    return base_prompt


import random
import time

def analyze_and_generate(
    competitor_img_path: str,
    product_info_text: str,
    user_direction: str = "",
    max_retries: int = 5
) -> str:
    """
    分析竞品图片并生成新文案（带重试机制）
    
    Args:
        competitor_img_path: 竞品图片路径
        product_info_text: 产品卖点文本
        user_direction: 用户指定的文案方向
        max_retries: 最大重试次数
    
    Returns:
        str: 生成的文案内容
    """
    # 检查图片文件
    img_path = Path(competitor_img_path)
    if not img_path.exists():
        raise FileNotFoundError(f"竞品图片不存在: {competitor_img_path}")
    
    # 初始化模型
    model = init_gemini()
    
    # 加载图片
    try:
        image = Image.open(img_path)
    except Exception as e:
        return f"【图片加载失败】{str(e)}"
    
    # 构建提示词
    system_prompt = create_system_prompt(user_direction)
    
    user_prompt = f"""【产品卖点库】
{product_info_text}

请分析上方的竞品图片，并基于以上产品卖点，生成模仿其结构的新文案。"""

    # 重试循环
    delay = 2  # 初始等待时间（秒）
    
    for attempt in range(max_retries + 1):
        try:
            response = model.generate_content(
                [system_prompt, image, user_prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2000,
                )
            )
            return response.text.strip()
            
        except Exception as e:
            error_str = str(e)
            
            # 判断是否是可以重试的错误
            is_retryable = False
            if "429" in error_str or "Resource exhausted" in error_str:
                print(f"[警告] 触发限流 (429)，等待 {delay} 秒后重试...")
                is_retryable = True
            elif "500" in error_str or "Internal error" in error_str:
                print(f"[警告] 服务器错误 (500)，等待 {delay} 秒后重试...")
                is_retryable = True
            elif "503" in error_str or "Service Unavailable" in error_str:
                print(f"[警告] 服务不可用 (503)，等待 {delay} 秒后重试...")
                is_retryable = True
                
            if is_retryable and attempt < max_retries:
                time.sleep(delay)
                # 指数退避 + 随机抖动
                delay = delay * 2 + random.uniform(0, 1)
                continue
            else:
                error_msg = f"Gemini API 调用失败: {error_str}"
                print(f"[错误] {error_msg}")
                return f"【文案生成失败】\n{error_msg}"


def batch_analyze(
    image_folder: str,
    product_info_text: str,
    user_direction: str = "",
    delay_seconds: float = 1.0,
    max_count: int = 0
) -> list:
    """
    批量分析竞品图片
    
    Args:
        image_folder: 竞品图片文件夹路径
        product_info_text: 产品卖点文本
        user_direction: 用户指定的文案方向
        delay_seconds: 每次 API 调用之间的延迟（避免限流）
        max_count: 最大处理图片数量，0表示不限制
    
    Returns:
        list: 包含 (图片路径, 生成文案) 的元组列表
    """
    folder = Path(image_folder)
    if not folder.exists():
        raise FileNotFoundError(f"图片文件夹不存在: {image_folder}")
    
    # 支持的图片格式
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
    
    # 获取所有图片文件
    image_files = sorted([
        f for f in folder.iterdir()
        if f.suffix.lower() in image_extensions
    ])
    
    if not image_files:
        print(f"[警告] 文件夹中没有找到图片: {image_folder}")
        return []
    
    # 限制处理数量
    total_found = len(image_files)
    if max_count > 0 and len(image_files) > max_count:
        image_files = image_files[:max_count]
        print(f"[信息] 找到 {total_found} 张竞品图片，限制处理前 {max_count} 张...")
    else:
        print(f"[信息] 找到 {len(image_files)} 张竞品图片，开始分析...")
    
    total = len(image_files)
    results = []
    for i, img_path in enumerate(image_files, 1):
        print(f"[进度] 正在处理第 {i}/{total} 张: {img_path.name}")
        
        try:
            copywriting = analyze_and_generate(
                str(img_path),
                product_info_text,
                user_direction
            )
            results.append({
                "image_path": str(img_path),
                "image_name": img_path.name,
                "copywriting": copywriting
            })
            
            # 延迟避免 API 限流
            if i < len(image_files):
                time.sleep(delay_seconds)
                
        except Exception as e:
            print(f"[错误] 处理 {img_path.name} 时失败: {e}")
            results.append({
                "image_path": str(img_path),
                "image_name": img_path.name,
                "copywriting": f"【处理失败】{str(e)}"
            })
    
    print(f"[完成] 已处理 {len(results)} 张图片")
    return results


if __name__ == "__main__":
    # 测试代码
    import sys
    
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
        test_selling_points = "雪叶红口服液 - 调经补血，温暖宫寒"
        
        print(f"测试分析图片: {test_image}")
        result = analyze_and_generate(test_image, test_selling_points)
        print("\n生成的文案:")
        print("-" * 50)
        print(result)
    else:
        print("用法: python gemini_analyzer.py <图片路径>")
