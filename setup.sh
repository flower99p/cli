#!/usr/bin/env bash
set -eu

PYTHON_BIN="${PYTHON_BIN:-python3}"
PIP_BIN="${PIP_BIN:-pip3}"

if command -v pkg >/dev/null 2>&1; then
  echo "Detected Termux / Android environment"
  pkg update -y
  pkg install python git -y
  pkg install python-pillow -y
  PYTHON_BIN="${PYTHON_BIN:-python}"
  PIP_BIN="${PIP_BIN:-pip}"
elif command -v apt-get >/dev/null 2>&1; then
  echo "Detected Debian / Ubuntu / Linux environment"
  sudo apt-get update
  sudo apt-get install -y python3 python3-pip python3-venv git
elif command -v opkg >/dev/null 2>&1; then
  echo "Detected OpenWrt environment"
  opkg update
  opkg install python3 python3-pip python3-pil git
else
  echo "Tidak dapat mendeteksi package manager. Install Python 3 + pip terlebih dahulu lalu jalankan script ini lagi."
  exit 1
fi

"$PYTHON_BIN" -m pip install --upgrade pip
"$PYTHON_BIN" -m pip install -r requirements.txt

printf '\nSetup selesai.\n'
printf 'Jalankan aplikasi dengan: %s main.py\n' "$PYTHON_BIN"
