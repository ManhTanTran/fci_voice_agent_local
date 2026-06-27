#!/usr/bin/env bash
# Exp 05 — chạy gym-env text mode với LLMPolicy (Qwen 1.5B) trên DGX.
# Tiền đề: đã sync repo lên DGX (experiments/01_pipecat_dgx_smoke/sync_to_dgx.sh)
#          và đã có extra exp03 (torch cu130 + transformers) như exp03/04.
set -euo pipefail

cd "$(dirname "$0")/../.."   # về repo root

echo ">> [1/2] đồng bộ deps exp03 (torch cu130 + transformers)..."
uv sync --extra exp03

echo ">> [2/2] chạy gym-env text mode với policy=LLM..."
FCI_POLICY=llm uv run python experiments/05_gym_env_text_smoke/run_gym_text.py
