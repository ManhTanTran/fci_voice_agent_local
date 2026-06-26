#!/usr/bin/env bash
# Cài LLM (torch cu130 + transformers) + thử TTS Piper, rồi chạy full loop. Chạy TRÊN DGX.
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "== [1/3] uv sync --extra exp02 --extra exp03 (STT + torch cu130 + transformers) =="
# torch cu130 ~vài GB, lần đầu lâu. exp02 để có sẵn STT cho full loop.
uv sync --extra exp02 --extra exp03

echo "== [2/3] thử cài Piper TTS (best-effort, có thể fail build arm64 → fallback placeholder) =="
uv pip install piper-tts || echo "  (piper-tts không cài được — full loop dùng WAV placeholder)"

echo "== [3/3] chạy full loop + hội thoại (tải Qwen2.5-1.5B lần đầu) =="
uv run python experiments/03_full_loop_conversation/run_loop.py
