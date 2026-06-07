@echo off
echo === PCare Automation Setup ===
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python belum terinstall.
    echo Download dari https://www.python.org/downloads/
    echo PASTIKAN centang "Add python.exe to PATH" saat install.
    pause
    exit /b 1
)

echo [1/3] Membuat virtual environment...
python -m venv pcare-venv

echo [2/3] Install dependencies...
pcare-venv\Scripts\pip install pandas playwright customtkinter

echo [3/3] Install browser Chromium...
pcare-venv\Scripts\playwright install chromium

echo.
echo === Setup selesai! ===
echo Jalankan "run.bat" untuk memulai automation.
pause
