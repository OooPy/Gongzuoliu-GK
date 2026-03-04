@echo off
setlocal

cd /d "%~dp0"

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
