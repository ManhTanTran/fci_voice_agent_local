#!/usr/bin/env bash
# Đồng bộ code repo này LÊN DGX qua rsync over `ssh dgx` (KHÔNG cần git push).
# Chạy ở MÁY LOCAL, tại repo root hoặc bất kỳ đâu.
#
#   bash experiments/01_pipecat_dgx_smoke/sync_to_dgx.sh [REMOTE_DIR]
#
# Mặc định đẩy vào ~/fci_voice_agent trên DGX. Trước khi chạy: `dgx-start` (token Access).
set -euo pipefail

# repo root = 2 cấp trên script
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
REMOTE_DIR="${1:-fci_voice_agent}"   # tương đối $HOME trên DGX

echo "== rsync $REPO_ROOT/  ->  dgx:~/$REMOTE_DIR/ =="
rsync -avz --delete \
  --exclude '.git/' \
  --exclude 'data/' \
  --exclude '**/results/' \
  --exclude '.venv/' \
  --exclude '__pycache__/' \
  --exclude '*.egg-info/' \
  -e ssh \
  "$REPO_ROOT"/ "dgx:$REMOTE_DIR/"

echo "== xong. Trên DGX chạy: =="
echo "   ssh dgx 'cd $REMOTE_DIR && bash experiments/01_pipecat_dgx_smoke/setup_dgx.sh'"
