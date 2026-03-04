from pathlib import Path


BAT_TEMPLATE = r'''@echo off
setlocal

cd /d "{PROJECT_DIR}"

echo [1/4] Checking project directory...
if not exist "main.py" (
    echo [ERROR] Not a valid project directory: %cd%
    pause
    exit /b 1
)

echo [2/4] Checking virtual environment...
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    set "PYTHONW=.venv\Scripts\pythonw.exe"
) else if exist "..\.venv\Scripts\python.exe" (
    set "PYTHON=..\.venv\Scripts\python.exe"
    set "PYTHONW=..\.venv\Scripts\pythonw.exe"
) else if exist "..\..\.venv\Scripts\python.exe" (
    set "PYTHON=..\..\.venv\Scripts\python.exe"
    set "PYTHONW=..\..\.venv\Scripts\pythonw.exe"
) else (
    echo [ERROR] Virtual environment not found.
    echo Run: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo [3/4] Checking config file...
if not exist "config.json" (
    if exist "config.example.json" (
        copy /Y "config.example.json" "config.json" >nul
        echo [INFO] config.json has been created from config.example.json.
    ) else (
        echo [ERROR] Missing config.json and config.example.json
        pause
        exit /b 1
    )
)

echo [3.5/4] Checking required package: pystray...
"%PYTHON%" -c "import pystray" >nul 2>nul
if not "%ERRORLEVEL%"=="0" (
    echo [INFO] Installing dependencies from requirements.txt ...
    "%PYTHON%" -m pip install -r requirements.txt
    if not "%ERRORLEVEL%"=="0" (
        echo [ERROR] Dependency install failed.
        pause
        exit /b 1
    )
)

echo [4/4] Starting app...
if exist "%PYTHONW%" (
    start "" /B "%PYTHONW%" main.py
) else (
    start "" /B "%PYTHON%" main.py
)
exit /b 0
'''


MAC_TEMPLATE = '''#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "[1/4] Checking project directory..."
if [ ! -f "main.py" ]; then
    echo "[ERROR] Not a valid project directory: $(pwd)"
    read -r -p "Press Enter to exit..."
    exit 1
fi

echo "[2/4] Checking virtual environment..."
if [ -x ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -x "../.venv/bin/python" ]; then
    PYTHON="../.venv/bin/python"
elif [ -x "../../.venv/bin/python" ]; then
    PYTHON="../../.venv/bin/python"
else
    echo "[ERROR] Virtual environment not found."
    echo "Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    read -r -p "Press Enter to exit..."
    exit 1
fi

echo "[3/4] Checking config file..."
if [ ! -f "config.json" ]; then
    if [ -f "config.example.json" ]; then
        cp "config.example.json" "config.json"
        echo "[INFO] config.json has been created from config.example.json."
    else
        echo "[ERROR] Missing config.json and config.example.json"
        read -r -p "Press Enter to exit..."
        exit 1
    fi
fi

echo "[3.5/4] Checking required package: pystray..."
if ! "$PYTHON" -c "import pystray" >/dev/null 2>&1; then
    echo "[INFO] Installing dependencies from requirements.txt ..."
    "$PYTHON" -m pip install -r requirements.txt
fi

echo "[4/4] Starting app..."
nohup "$PYTHON" main.py >/dev/null 2>&1 &
echo "[OK] Started in background."
'''


def main():
    project_dir = Path(__file__).resolve().parent
    project_bat = project_dir / "eng_start.bat"
    project_mac = project_dir / "start_mac.command"
    old_cn_bat = project_dir / "启动截图学英语.bat"

    project_bat_content = BAT_TEMPLATE.replace("{PROJECT_DIR}", "%~dp0")

    project_bat.write_text(project_bat_content, encoding="utf-8")
    print(f"Created: {project_bat}")

    project_mac.write_text(MAC_TEMPLATE, encoding="utf-8")
    try:
        project_mac.chmod(0o755)
    except Exception:
        pass
    print(f"Created: {project_mac}")

    if old_cn_bat.exists():
        old_cn_bat.unlink()
        print(f"Removed: {old_cn_bat}")


if __name__ == "__main__":
    main()
