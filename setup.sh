#!/bin/bash
echo "=== PCare Automation Setup ==="
echo

if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 belum terinstall."
    echo "Install via: brew install python3"
    exit 1
fi

cd "$(dirname "$0")"

echo "[1/3] Membuat virtual environment..."
python3 -m venv pcare-venv

echo "[2/3] Install dependencies..."
pcare-venv/bin/pip install pandas playwright customtkinter

echo "[3/3] Install browser Chromium..."
pcare-venv/bin/playwright install chromium

echo
echo "=== Setup selesai! ==="
echo "Jalankan ./run.sh untuk memulai automation."
