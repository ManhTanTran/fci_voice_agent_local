#!/usr/bin/env bash
# Cài deps exp02 + chạy harness test thông luồng TRÊN DGX. Chạy sau sync_to_dgx.sh.
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "== [1/2] uv sync --extra exp02 (faster-whisper + datasets + jiwer + soundfile) =="
uv sync --extra exp02

echo "== [2/2] chạy harness E2E (tải LibriSpeech dummy + model base.en lần đầu) =="
uv run python experiments/02_e2e_flow_test/run_e2e.py
