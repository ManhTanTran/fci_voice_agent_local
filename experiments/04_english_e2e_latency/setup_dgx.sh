#!/usr/bin/env bash
# Full loop English + latency + TTS Piper thật. Chạy TRÊN DGX (deps exp02/03 đã cache).
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "== [1/3] đảm bảo deps (STT + LLM torch cu130) =="
uv sync --extra exp02 --extra exp03

echo "== [2/3] đảm bảo piper-tts (TTS thật) =="
uv pip install piper-tts >/dev/null 2>&1 || echo "  (piper-tts cài lỗi → sẽ fallback placeholder)"

echo "== [3/3] chạy full loop English + đo latency (tải voice Piper lần đầu) =="
uv run python experiments/04_english_e2e_latency/run_e2e_en.py
