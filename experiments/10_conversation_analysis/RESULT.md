# exp10 — Kết quả chạy lần đầu (phần tất định)

Chạy `pipeline/run.py` trên 36 cuộc `data/audio_interrupt`, model FastConformer 114M CPU.
Tổng thời gian ~2 phút 50 giây (nạp model 11s + transcribe). Chưa gắn nhãn barge-in thật.

---

## 1. Con số tổng

- **36 cuộc · 216 sự kiện barge-in ứng viên.**
- Bot đã dừng TTS: **100/216 (46%)**; còn tiếp: 116.
- Phân bố đặc trưng nội dung:
  - **rỗng** (VAD bắt nhầm, không có chữ): **50%** — nửa số ứng viên không phải tiếng nói đọc được,
  - có ít nhất 1 từ chữ số: **16%**,
  - chỉ backchannel: **6%**,
  - có từ khóa ngắt (dừng/khoan/chờ): **2%**.
- `n_words`: p10=0 · p50=0 · p90=10 → phân bố lưỡng cực, gần nửa rỗng, phần còn lại giàu nội dung.
- `sir_db`: p10=−27 · p50=−11 · p90=0 → khách gần như luôn nhỏ hơn bot trong overlap (AGC telephony).

---

## 2. Đọc nhanh cho việc soi TP/FP

- Cụm **false-positive lộ rõ:** `is_empty=1` cộng `sir_db` rất âm (dưới −20) — phần lớn là echo bot rò sang kênh khách hoặc tiếng thở, không phải khách chen thật.
- Cụm **true-positive lộ rõ:** `n_words` cao cộng `has_digit=1` cộng `sir_db` cao hơn (−6 tới 0) — khách đọc lại số hoặc phản đối.
- **Hành vi bot lệch nhu cầu:** nhiều cuộc `bot tiếp` lớn hơn `bot dừng` ở đúng các sự kiện `has_digit` — bot không dừng khi khách sửa số, đúng mô tả điểm đau.
- File `5634d6eb` (41 ứng viên) và `85fa33e2` (25) là hai cuộc đậm đặc nhất, hợp để soi trước.

---

## 3. File sinh ra (trong `out/`, không commit)

- `<call_id>.json` — hồ sơ mỗi cuộc: metrics, turns, events kèm đặc trưng.
- `_index.json` — chỉ số tổng mỗi cuộc.
- `review_events.csv` — 216 sự kiện, mỗi dòng đủ đặc trưng + cột nhãn để trống (worksheet gắn nhãn).
- `summary.md` — bảng tổng corpus + phân bố đặc trưng + ngưỡng tham khảo.
- `timeline_<8>.md` — timeline hội thoại một cuộc.
- `clips/` — clip wav cắt theo mốc để nghe.

---

## 4. So sánh 3 phiên bản STT (2026-07-07)

Tín hiệu tất định (VAD/acoustic/behavior) giống nhau mọi model — chỉ khác phần **text**.
Mỗi model lưu hồ sơ riêng `out/<model>/`, viewer ghép theo `(speaker, t_start)` để so cạnh nhau.

| Model | Kiểu giải mã | Nơi chạy | Tốc độ (36 cuộc, ~114 phút audio 2 kênh) | Đặc điểm text |
|---|---|---|---|---|
| **FastConformer 114M** (của Kỳ) | CTC | local CPU | ~2 phút | train 16kHz → lệch nhiều trên 8kHz |
| **ChunkFormer CTC** (khanhld) | CTC long-form | local CPU | vài phút (RTF ~0.06) | đọc 8kHz sạch hơn FastConformer |
| **Parakeet CTC 0.6B** (NVIDIA) | CTC | DGX GPU | **~1–2 phút** (0.5–4s/cuộc) | có dấu câu + viết hoa (PnC) |

**Quyết định: BỎ PhoWhisper (chốt không dùng).**
- Whisper giải mã *autoregressive* (sinh token tuần tự) → RTF ~0.25 trên GPU GB10, tức **~2 giờ** cho 36 cuộc, chậm hơn CTC **~50 lần**.
- Đổi `medium→small` không cứu được vì nút thắt là *số bước decode tuần tự*, không phải cỡ model.
- Parakeet CTC đã phủ vai trò "transformer có dấu câu" mà nhanh gấp 50 lần → không có lý do dùng Whisper.
- Đã gỡ khỏi `backends.py` / `run.py` / `run_on_dgx.sh` (giữ 1 dòng ghi chú lý do).

**Hạ tầng DGX đã dựng** (GB10 arm64, torch GPU = index `cu130` chạy native):
- `fci_stt_nemo_gpu` — env NeMo + torch cu130 cho Parakeet (tải file `.nemo` rồi `restore_from`, không dùng `from_pretrained`).
- Script `tools/run_on_dgx.sh parakeet` — rsync pipeline+audio lên DGX, chạy GPU, kéo `out/parakeet/` về.

---

## 5. Còn lại

- Chờ Kỳ review logic tất định (nhất là định nghĩa ứng viên, đặc trưng, cách đo `bot_stopped`).
- Sau khi duyệt: mở Tầng B cho agent gán `label_is_bargein` + `label_group` (6 nhóm FCI) trên `review_events.csv`.
- Điểm cần chỉnh có thể có: ngưỡng `cust_snr_db` (đang cao do noise-floor gồm digital-silence); tách echo khỏi barge-in thật ở nhóm `is_empty` + `sir` âm sâu.
