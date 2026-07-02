# Phase 0 — Bộ sinh nhiễu tất định + Verifier chấm ASR (PhoWhisper)

Lát mỏng chạy được đầu tiên của hướng verify-first. Dựng **verifier trước model**: sinh
data nhiễu có nhãn by-construction, chấm PhoWhisper trên CPU, ra **bảng WER-theo-SNR thật**.

> Thiết kế/thảo luận nền (không phải code) nằm ở workspace-brain:
> `.agent/research/03_research_direction/04_phase0_synthetic_noise_verifier.md`.

## Kết quả

Xem `RESULTS.md`. Số WER thật do PhoWhisper chạy trên CPU, KHÔNG phải ước lượng.

## Cấu trúc

```
src/
  noise_gen.py       # sinh nhiễu tất định (white/pink/babble) + trộn theo SNR chính xác
  build_dataset.py   # chọn subset VIVOS sạch -> sinh mẫu nhiễu -> manifest CSV
  verify_asr.py      # chấm PhoWhisper -> WER theo (noise_type x SNR)
results/
  dataset_manifest.csv  # (path, transcript_goc, noise_type, snr_db) nhãn by-construction
  noisy_wav/            # audio nhiễu đã sinh
  samples/              # 3 wav mẫu để nghe (clean + babble5dB + white0dB)
  predictions.csv       # hyp thô + ref/hyp đã chuẩn hoá từng mẫu
  wer_by_snr.csv        # bảng WER cuối
```

## Data & Model

- **Data**: VIVOS test (tiếng Việt, local, có sẵn transcript) — subset 30 clip ngắn nhất.
  - manifest gốc: `nvidia_asr_nemo/data/manifests/vivos_test.jsonl`
  - KHÔNG tải gì mới.
- **Nhiễu**: TỰ SINH tất định (chưa có MUSAN local) — white, pink (1/f), babble (trộn clip khác).
- **Model**: `vinai/PhoWhisper-small`, chạy CPU (không GPU dùng được).

## Chạy lại

```bash
cd fci_voice_agent/experiments/09_asr_noise_verifier
uv sync   # tạo venv lần đầu

# 1) sinh dataset nhiễu (vài giây)
uv run python src/build_dataset.py

# 2) chấm PhoWhisper -> bảng WER (~15 phút CPU cho 390 mẫu)
export HF_HOME=/tmp/.../scratchpad/hf_cache   # cache model
export PHOWHISPER_MODEL=vinai/PhoWhisper-small # hoặc vinai/PhoWhisper-tiny nếu quá chậm
uv run python src/verify_asr.py
```

Toàn bộ tất định (seed cố định `GLOBAL_SEED`): chạy lại ra đúng cùng dataset và
cùng WER (trừ sai khác numeric nhỏ của model).

## Hạn chế (đọc kỹ trước khi trích số vào doc)

- CPU + subset nhỏ (30 clip) → WER có phương sai; chỉ để thấy XU HƯỚNG, không phải benchmark chuẩn.
- Nhiễu **synthetic cộng** (white/pink/babble), CHƯA phải MUSAN thật, CHƯA có RIR/reverb,
  CHƯA có codec băng hẹp → chưa phủ nhiễu convolutional đời thật.
- CHƯA có mỏ-neo real (data nhiễu thật FCI) → chưa đo được gap synthetic→real.
