# exp10 — Phân tích sâu từng hội thoại (phần tất định + tool review)

Bóc tách mỗi cuộc gọi hai kênh thành một hồ sơ có cấu trúc, rút sự kiện barge-in ứng viên
kèm đầy đủ đặc trưng, và sinh tool để người soi và gắn nhãn.
Kế hoạch gốc: [PLAN.md](PLAN.md).

> **Phạm vi bản này:** chỉ phần **tất định** (Tầng A) + **tool review** (T1–T5).
> Phần agent tự phán "có phải barge-in không" (Tầng B) **để sau**, chạy khi phần tất định được duyệt.

---

## 1. Chạy

Pipeline cần model ASR nên chạy dưới venv `nvidia_asr_nemo` (có nemo + torch). Từ thư mục `fci_voice_agent`:

```bash
# B1 — bóc tách tất định toàn bộ 36 cuộc -> out/<call_id>.json + out/_index.json
uv run --project ../nvidia_asr_nemo python experiments/10_conversation_analysis/pipeline/run.py \
    --audio-dir data/audio_interrupt --out experiments/10_conversation_analysis/out

# B2 — gom sự kiện thành bảng review (CSV, mở LibreOffice/lọc được)
uv run --project ../nvidia_asr_nemo python experiments/10_conversation_analysis/tools/review_queue.py \
    --out experiments/10_conversation_analysis/out --csv experiments/10_conversation_analysis/out/review_events.csv

# B3 — bảng tổng corpus + phân bố đặc trưng
uv run --project ../nvidia_asr_nemo python experiments/10_conversation_analysis/tools/summary_md.py \
    --out experiments/10_conversation_analysis/out

# B4 — timeline hội thoại 1 cuộc (đọc trong IDE)
uv run --project ../nvidia_asr_nemo python experiments/10_conversation_analysis/tools/timeline_md.py \
    --call <uuid> --out experiments/10_conversation_analysis/out

# B5 — cắt clip nghe 1 sự kiện (kênh khách / bot / trộn stereo)
uv run --project ../nvidia_asr_nemo python experiments/10_conversation_analysis/tools/cut_clip.py \
    --call <uuid> --t <giây>

# B6 — web-tool review LOCAL (1 file HTML tự chứa, KHÔNG phải artifact claude.ai)
uv run --project ../nvidia_asr_nemo python experiments/10_conversation_analysis/tools/build_viewer.py \
    --out experiments/10_conversation_analysis/out
#   -> mở experiments/10_conversation_analysis/out/viewer.html bằng trình duyệt (xdg-open ...)
#   Nếu trình duyệt chặn file://, chạy server local:
#     ( cd experiments/10_conversation_analysis/out && python3 -m http.server 8731 )
#     rồi mở http://localhost:8731/viewer.html
```

`viewer.html`: danh sách 36 cuộc bên trái (sắp theo số ứng viên) + chi tiết mỗi cuộc dạng chat hai cột
(bot trái, khách phải), lượt barge-in viền đỏ kèm chip đặc trưng (nw, sir, slope, flat, SỐ/rỗng, bot DỪNG/TIẾP).
Có ô lọc call_id + toggle "chỉ hiện lượt barge-in" / "hiện đặc trưng".

- Cờ `--no-asr` ở `run.py` để test riêng phần tín hiệu, không nạp model.
- Model lấy từ HF cache (`kyle/vi-asr-fastconformer-114m`); đặt `FCI_ASR_NEMO=<path.nemo>` để dùng bản local khác.

---

## 2. Cấu trúc

- `pipeline/` — phần tất định:
  - `audio.py` — giải mã μ-law, tách kênh, VAD Otsu, đặc trưng âm học (rms, sir, snr, slope, zcr, spectral-flatness).
  - `asr.py` — nạp FastConformer 114M, transcribe theo lượt hai kênh.
  - `events.py` — dựng lượt, rút barge-in ứng viên, đặc trưng nội dung tất định, hành vi dừng của bot, readback mismatch, metrics.
  - `run.py` — orchestrate một hoặc toàn bộ cuộc, ghi dossier JSON.
  - `util.py` — ẩn dãy số dài (PII) khi ghi ra file.
- `tools/` — T1 `timeline_md` · T2 `cut_clip` · T3 `review_queue` · T5 `summary_md`.
- `out/` — hồ sơ sinh ra, **không commit** (chứa transcript chưa ẩn số + audio); xem `.gitignore`.

---

## 3. Đặc trưng mỗi sự kiện barge-in (giúp quyết định nhanh)

Mỗi onset khách khi bot đang nói là một ứng viên; các cột trong `review_events.csv`:

- **Thời gian:** `cust_dur_s` (khách nói bao lâu), `overlap_dur_s`, `into_bot_s` (chen vào giữa câu bot chỗ nào), `gap_before_s`.
- **Âm học:** `cust_rms_db`, `sir_db` (khách so bot trong overlap), `cust_snr_db`, `onset_slope_db` (độ dốc lên — chủ động hay không), `zcr`, `spec_flatness` (phân biệt tiếng nói vs nhiễu).
- **Nội dung tất định:** `n_words`, `has_digit`, `has_stopword` (dừng/khoan/chờ = Nhóm 6 FCI), `only_backchannel` (dạ/vâng = Nhóm 2), `is_empty`, `cust_text` (transcript đầy đủ — data là tester tự test, không mask; cờ `--mask` chỉ bật khi gặp data khách thật).
- **Hành vi thật của bot:** `bot_stopped` (bot có tắt tiếng sau khi bị chen không), `stop_latency_ms`, `readback_mismatch` (bot đọc lại số lệch lời khách = nghi ASR lỗi).
- **Nhãn để trống:** `label_is_bargein`, `label_group`, `label_note` — người hoặc agent điền sau.
- **Tiện nghe:** `listen_cmd` — lệnh cắt clip sẵn để dán chạy.

**Cách dùng soi TP/FP:** mở CSV, lọc/sắp theo `n_words`, `is_empty`, `sir_db` để thấy cụm true-positive
(nhiều từ, có số, sir cao) tách khỏi false-positive (rỗng, sir rất âm — thường là echo hoặc nhiễu, backchannel ngắn).

---

## 4. Trạng thái

- Phần tất định + tool: **chạy xong 36 cuộc** (xem `RESULT.md`).
- Chờ Kỳ review logic tất định; nếu ổn sẽ mở Tầng B để agent gán nhãn barge-in.
