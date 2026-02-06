---
name: 电商创意图文案生成器 Skill
description: 批量分析竞品图片，结合产品卖点，自动生成符合营销逻辑的文案并输出 Word 工单。
---

# 电商创意图文案生成器 Skill

这是一个基于 Gemini AI 的自动化工具，能够批量分析竞品图片（文案结构、卖点），并针对您的产品自动生成逻辑一致、格式规范的营销文案，最终输出给设计师直接使用的 Word 工单。

> **核心原则**：本项目遵循“只带走配方，不带走厨房”原则。所有运行环境需在本地重新搭建，私钥需自行配置。

## 🎯 功能特点

- **智能分析**：自动识别竞品图的营销文案结构。
- **精准仿写**：生成字数、结构与竞品高度一致的新文案。
- **合规检查**：内置广告法规避逻辑。
- **自动归档**：生成格式化的 Word 文档，图片左对齐，去除非必要信息，设计师可直接使用。
- **稳定运行**：内置 API 错误自动重试机制。

## 🛠️ 厨房搭建指南 (环境配置)

### 1. 准备原料

确保您的电脑已安装 **Python 3.10+**。

### 2. 搭建灶台 (虚拟环境)

在项目根目录下运行终端命令：

```bash
# 创建虚拟环境
python -m venv .venv

# 激活环境 (Windows)
.venv\Scripts\activate

# 激活环境 (Mac/Linux)
source .venv/bin/activate
```

### 3. 加入佐料 (安装依赖)

```bash
pip install -r requirements.txt
```

### 4. 点火密钥 (配置私钥)

1. 复制模板文件：将 `.env.example` 复制一份并重命名为 `.env`。
2. 打开 `.env`，填入您的 Google API Key：

```text
GOOGLE_API_KEY=your_real_api_key_here
```

> ⚠️ 注意：`.env` 文件包含敏感信息，已被 `.gitignore` 忽略，请勿上传到任何公共库。

## 🚀 开始烹饪 (运行使用)

### 1. 准备食材

- **竞品图片**：将参考图放入 `20260206 竞品创意图` 文件夹（支持 jpg/png）。
- **产品卖点**：编辑 `雪叶红卖点.txt`，填入您的产品核心卖点。

### 2. 启动程序

```bash
python main.py
```

### 3. 获取大餐

运行完成后，请前往 `output/` 文件夹查看生成的 Word 文档。

---

## 📂 配方结构

```
.
├── main.py                # 主程序 (大厨)
├── gemini_analyzer.py     # AI 分析核心 (味觉系统)
├── document_generator.py  # 文档生成器 (摆盘系统)
├── product_reader.py      # 原料读取器
├── requirements.txt       # 佐料清单
├── .env.example           # 密钥模板
├── SKILL.md               # 本说明书
└── .gitignore             # 厨房过滤器
```
