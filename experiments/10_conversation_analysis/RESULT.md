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

## 4b. Review chất lượng STT trên data FPT (2026-07-07, đo trên 1483 lượt / 36 cuộc)

Không có ground-truth → so 3 model chéo nhau + suy luận theo tính hợp lý. Số đo bằng script trên `out/`.

**Đặc điểm loại dataset (insight):**
- **CSKH ngân hàng qua tổng đài, 8kHz 2 kênh.** Nội dung xoay quanh xác minh danh tính: **đọc/đọc-lại chuỗi số** (căn cước, số điện thoại, thẻ). Có **155 lượt chứa ≥3 từ chữ số** — đây vừa là nội dung *quan trọng nhất* vừa *khó nhất*.
- **~30% ứng viên barge-in là NON-SPEECH** (echo bot rò kênh, tiếng thở, VAD bắt nhầm): cả 3 model đồng thuận rỗng ~30% (fast 31% · chunk 33% · para 29%). Khớp nhận định "VAD over-trigger" ở §1.
- Barge-in điển hình = **khách đọc lại/sửa số khi bot đọc nhầm** (đúng điểm đau); overlap có AGC telephony nén khách nhỏ (`sir` âm sâu).

**Cảm quan model tốt nhất: Parakeet CTC 0.6B** (rồi ChunkFormer, cuối là FastConformer):
- Chuỗi số **sạch nhất**: không token OOV, không gom số sai. Có dấu câu + viết hoa → gần văn bản, dễ đọc.
- ⚠️ **Mặt trái:** phun **mảnh rác ở 197 lượt** (`"."`, `"Đ."`, âm tiết cụt `"d ây k."`) trên đoạn non-speech mà 2 model CTC đúng khi để rỗng → **cần lọc hậu kỳ** (bỏ lượt chỉ có dấu câu / độ dài < ngưỡng). "Rỗng thấp 15%" ban đầu là ảo do đếm nhầm `"."` là có chữ.
- **ChunkFormer:** nhiều chữ nhất (9943 từ), đọc 8kHz tốt, **nhưng gom số thành số-đếm** — chèn nhầm `nghìn/trăm/linh` vào chuỗi ID ở **93 lượt** (vd `"sáu bảy nghìn tám"` thay vì đọc rời `"sáu bảy tám"`). Sai cho bài toán đọc-số-ID.

**FastConformer (bản cũ của Kỳ) dở điểm gì — và improve được không:**
- **Lỗi chí mạng: phun ký tự OOV `⁇` ở 47% lượt có chuỗi số** (73/155 lượt; tổng 134 ký tự `⁇` trên 76 lượt) — mất hẳn dãy số, đúng phần nội dung quan trọng nhất. Ví dụ: bot đọc lại căn cước → FastConformer ra `"...của chị là ⁇ 4 năm ⁇"` (chỉ vớt được `"4 năm"`), trong khi Chunk/Parakeet ra đủ dãy số.
- Nguyên nhân (giả thuyết, cần xác nhận): (1) **train 16kHz, chạy 8kHz telephony** narrowband → mất phần cao tần phân biệt số đọc nhanh; (2) thiếu data **chuỗi số đọc liền (connected digits)** trong tập train; (3) tokenizer/vocab phun OOV khi acoustic bí thay vì đoán số.
- **CÓ thể improve** — và đúng hướng cả exp đang xây: **fine-tune trên chính data 8kHz telephony FCI + augment chuỗi số đọc rời**; kiểm tra vocab có đủ token số. Đây là bằng chứng số cụ thể để xin data readback-số từ FCI (bổ sung §3.3 doc request).

> Script đo: chạy trực tiếp trên `out/<model>/*.json` (đếm `⁇`, lượt số ≥3, mảnh rác, rỗng-sau-lọc). Con số ở trên tái lập được.

---

## 5. Còn lại

- Chờ Kỳ review logic tất định (nhất là định nghĩa ứng viên, đặc trưng, cách đo `bot_stopped`).
- Sau khi duyệt: mở Tầng B cho agent gán `label_is_bargein` + `label_group` (6 nhóm FCI) trên `review_events.csv`.
- Điểm cần chỉnh có thể có: ngưỡng `cust_snr_db` (đang cao do noise-floor gồm digital-silence); tách echo khỏi barge-in thật ở nhóm `is_empty` + `sir` âm sâu.
