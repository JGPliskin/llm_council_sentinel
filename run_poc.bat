@echo off
chcp 65001 > nul
echo [INFO] Repairing environment (Attempt 2)...

REM 1. Clean existing broken venv
if exist ".venv" (
    echo [INFO] Removing broken .venv...
    rmdir /s /q .venv
)

REM 2. Create fresh venv
echo [INFO] Creating fresh .venv...
python -m venv .venv
if %errorlevel% neq 0 (
    echo [FATAL] Failed to create venv.
    pause
    exit /b 1
)

REM 3. Ensure PIP exists (Critical Fix for Anaconda)
echo [INFO] Ensuring pip is installed...
.\.venv\Scripts\python.exe -m ensurepip --default-pip
if %errorlevel% neq 0 (
    echo [WARNING] ensurepip failed, attempting manual get-pip...
    REM Fallback if ensurepip is missing from base python
)

REM 4. Install Dependencies
echo [INFO] Installing dependencies (openai, rich)...
.\.venv\Scripts\python.exe -m pip install "openai>=1.0.0" rich python-dotenv

REM 5. Run Script
echo [INFO] Starting PoC...
echo ---------------------------------------------------
.\.venv\Scripts\python.exe thinking_stream_test.py %*

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Final execution failed.
    pause
)
