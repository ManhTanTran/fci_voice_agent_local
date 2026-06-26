#!/usr/bin/env bash
# Dựng env + chạy smoke TRÊN DGX. Chạy SAU khi đã sync code lên (sync_to_dgx.sh).
# Dùng `uv` (không cần root); cache uv/HF chung đã set sẵn ở /srv/team-share.
set -euo pipefail

# về repo root (script nằm ở experiments/01_pipecat_dgx_smoke/)
cd "$(dirname "$0")/../.."

echo "== [1/3] pin python 3.12 =="
uv python pin 3.12

echo "== [2/3] uv sync (resolve + cài pipecat base) =="
# Nếu bước này fail trên arm64 → CHÍNH LÀ phát hiện P0 (wheel không có cho aarch64)
uv sync

echo "== [3/3] chạy smoke + kiểm kê =="
uv run python experiments/01_pipecat_dgx_smoke/run_smoke.py
