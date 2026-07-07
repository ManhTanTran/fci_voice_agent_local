#!/usr/bin/env bash
# Chay STT nang tren DGX GB10 (GPU) roi keo ket qua ve local.
# YEU CAU: da `dgx-start` (tunnel Cloudflare Access) truoc; kiem bang `ssh dgx hostname`.
#
# Dung:
#   bash experiments/10_conversation_analysis/tools/run_on_dgx.sh parakeet
#
# Kien truc env tren DGX (GB10 arm64, torch GPU = index cu130):
#   parakeet -> can NeMo (torch cu130) -> project /srv/team-share/projects/fci_stt_nemo_gpu
# Path DGX phai la TUYET DOI (khong dung ~ vi ~ expand o may local khi ssh "..." ).
#
# PhoWhisper DA BO 2026-07-07: Whisper autoregressive RTF ~0.25 (~2h/36 cuoc), cham
# hon CTC ~50x. Parakeet CTC thay the (co dau cau). Khong chay Whisper nua.
set -euo pipefail
STT="${1:?stt = parakeet}"
LOCAL_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"   # fci_voice_agent
EXP=experiments/10_conversation_analysis

case "$STT" in
  parakeet)   PROJ=/srv/team-share/projects/fci_stt_nemo_gpu ;;
  *) echo "stt khong ho tro tren GPU: $STT (chi con parakeet)"; exit 1 ;;
esac
WORK="$PROJ/exp10"   # noi dat pipeline + audio + out tren DGX

echo "[1] kiem tra DGX ..."
ssh dgx "hostname; nvidia-smi --query-gpu=name --format=csv,noheader | head -1"

echo "[2] rsync pipeline + audio len DGX ($WORK) ..."
ssh dgx "mkdir -p '$WORK/data'"
rsync -az --delete "$LOCAL_ROOT/$EXP/pipeline"  "dgx:$WORK/"
rsync -az "$LOCAL_ROOT/data/audio_interrupt"    "dgx:$WORK/data/"

echo "[3] chay STT '$STT' tren GPU DGX (project $PROJ) ..."
# Parakeet doc FCI_ASR_GPU=1 de dung GPU.
ssh dgx "cd '$WORK' && FCI_ASR_GPU=1 HF_HOME=/srv/team-share/cache/hf uv run --project '$PROJ' \
    python pipeline/run.py --audio-dir data/audio_interrupt --out out --stt $STT"

echo "[4] keo dossier ve local -> out/$STT/ ..."
mkdir -p "$LOCAL_ROOT/$EXP/out/$STT"
rsync -az "dgx:$WORK/out/$STT/" "$LOCAL_ROOT/$EXP/out/$STT/"
echo "[xong] out/$STT/ da co tren local. Chay build_viewer.py de gop so sanh."
