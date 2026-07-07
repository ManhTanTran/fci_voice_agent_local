# exp11 — Benchmark WER ASR trên public data

Đo WER nhiều checkpoint ASR trên bộ manifest public tiếng Việt có ground-truth, ra một bảng so sánh.
Cách đo và chuẩn env chốt ở [SPEC.md](SPEC.md). Chạy trên DGX.

## Chạy nhanh

```bash
cd /home/dgxadmin/fci_voice_agent/experiments/11_asr_wer_bench
export HF_HOME=/srv/team-share/cache/hf
# QUAN TRỌNG: dùng .venv/bin/python trực tiếp, KHÔNG `uv run` (lock repo pin torch CPU -> revert GPU)
/srv/team-share/projects/nvidia_asr_nemo/.venv/bin/python run_bench.py \
    --models fc_s3,fc_s5,parakeet,chunkformer \
    --sets vivos,common_voice_vi,fleurs_vi,vlsp2020_100h,lsvsc,fosd,bud500,vietmed,vietsuperspeech \
    --out out
# smoke: thêm --limit 8
```

## Model đang so

- `fc_s3` — FastConformer 114M bản s3 (nền cũ, `s3-fc115m-full.nemo`).
- `fc_s5` — FastConformer 114M bản s5 mở rộng vocab f/j/w/z (`s5-vocabexp-full.nemo`).
- `parakeet` — `nvidia/parakeet-ctc-0.6b-Vietnamese`.
- `chunkformer` — `khanhld/chunkformer-ctc-large-vie` (CTC long-form, chạy CPU).

## Đầu ra

- `out/results.json` — WER và RTF chi tiết mỗi cặp model và tập.
- `out/table.md` — bảng WER, hàng là tập, cột là model.

## Bộ thư viện GPU đúng (đã kiểm chứng)

torch 2.12.1+cu130 · torchaudio 2.11.0+cu130 · torchvision 0.27.1+cu130 · chunkformer · jiwer.
Nếu `import nemo` báo `torchvision::nms does not exist` là torch đã bị tụt về CPU — xem SPEC.md mục 3.
