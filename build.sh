#!/usr/bin/env bash
set -e
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install --with-deps chromium
if ! command -v ffmpeg >/dev/null 2>&1 && command -v apt-get >/dev/null 2>&1; then
  apt-get update && apt-get install -y ffmpeg
fi
