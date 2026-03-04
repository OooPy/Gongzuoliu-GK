# 📸 截图并且学习英语

截图后自动 OCR → 提取英文 → 翻译 → 记录到你选的同步目标（飞书或本地文件）。

这个仓库现在默认是 **开箱可用**：不填飞书也能直接跑（写入本地文件）。

## 核心思路（重点）

项目把流程拆成 4 个模块，便于替换：

1. **输入层**：`clipboard_monitor.py` 监听截图
2. **理解层**：`ocr_engine.py` + `text_processor.py` 提取并分类英文
3. **语言层**：`translator.py` 根据配置做多语言翻译
4. **存储层**：`sync_backend.py` 选择 `feishu` 或 `local`

这样你可以：
- 继续用飞书多维表格
- 改成自己常用工具（先走本地文件，再接你自己的 Notion/Excel/数据库脚本）

## 功能

- 剪切板自动监控截图
- OCR 识别 + 英文词条提取
- 词条分类（代码/术语/日常）与去重计数
- 语言可配置（如 `en -> zh-CN`、`en -> ja`）
- 同步后端可切换：`local` / `feishu`

## 安装

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置

复制配置模板：

```bash
# Windows
copy config.example.json config.json

# macOS
cp config.example.json config.json
```

示例：

```json
{
    "sync": {
        "provider": "local",
        "local_output": "data/learning_items.jsonl"
    },
    "language": {
        "source": "en",
        "target": "zh-CN"
    },
    "feishu": {
        "app_id": "your_app_id_here",
        "app_secret": "your_app_secret_here",
        "app_token": "your_bitable_app_token_here",
        "table_id": "your_table_id_here"
    },
    "monitor": {
        "poll_interval": 3,
        "min_word_length": 3,
        "max_phrase_words": 8
    }
}
```

### 1) 默认开箱（本地模式）

- `sync.provider = local`
- 识别结果写到 `data/learning_items.jsonl`
- 不需要飞书凭据

### 2) 切到飞书模式

- `sync.provider = feishu`
- 填写 `feishu.app_id/app_secret/app_token/table_id`

飞书多维表字段建议：

| 字段名 | 类型 |
|---|---|
| 英语 | 文本（索引） |
| 中文 | 文本 |
| 类别 | 单选 |
| 长短 | 单选 |
| 出现次数 | 数字 |

## 运行

### 一键启动（推荐，零额外步骤）

- Windows：双击 `eng_start.bat`
- macOS：双击 `start_mac.command`

两端都不需要额外启动命令。

### 直接命令方式（仅给开发调试）

```bash
# Windows
.venv\Scripts\activate
python main.py

# macOS
source .venv/bin/activate
python main.py
```

`eng_start.bat` 和 `start_mac.command` 都会自动完成：
- 检查项目目录
- 检查 venv
- 自动生成 `config.json`（若缺失）
- 必要时安装依赖
- 后台启动程序

## 安全上传（避免敏感信息）

已忽略：`config.json`、`tokens.json`、`logs/`、`data/`、`.venv/`。

推送前请执行：

```bash
git status
git rm --cached config.json tokens.json 2>nul
git rm --cached -r data logs 2>nul
```

确认没有飞书密钥、个人截图数据后再 `commit/push`。

## 目录

- `main.py`：程序入口与托盘
- `clipboard_monitor.py`：截图监听与处理流程
- `translator.py`：翻译（可配置源/目标语言）
- `sync_backend.py`：同步后端选择器
- `local_sync.py`：本地文件同步实现
- `feishu_sync.py`：飞书同步实现

## License

MIT
