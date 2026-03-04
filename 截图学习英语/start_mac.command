#!/bin/bash
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
