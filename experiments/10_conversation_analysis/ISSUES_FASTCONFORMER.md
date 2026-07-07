# Trace lỗi FastConformer trên data FCI — bàn giao để tìm hướng cải tiến

Mục đích: cung cấp **bằng chứng cụ thể (call_id + timestamp + text 3 model)** về các loại lỗi STT,
tập trung vào FastConformer 114M (bản của Kỳ), để agent/người khác đề xuất hướng cải tiến.

- Nguồn: `out/{fastconformer,chunkformer,parakeet}/*.json` · 36 cuộc · 1483 lượt.
- Không có ground-truth → so 3 model chéo nhau. Parakeet = tham chiếu mềm cho chuỗi số (sạch nhất), ChunkFormer = đối chứng.
- Sinh lại đầy đủ: `python tools/trace_stt_issues.py --out out --report-dir out/issues` → `00_summary.md` + CSV mỗi loại.

## Glossary
- **`⁇`** (U+2047): token *unknown/OOV* NeMo phun ra khi acoustic không map được vào vocab.
- **readback**: bot đọc lại thông tin (căn cước / sđt / thẻ) để xác minh — nơi chuỗi số xuất hiện dày nhất.
- **connected digits**: dãy số đọc liền không ngắt (vd "một hai ba bốn năm...").
- **degenerate decoding**: model xuất một khuôn output gần như cố định, bất kể input thật.

---

## 1. Phát hiện chính (headline)

**FastConformer sụp đổ trên chuỗi số theo kiểu *degenerate*, không phải lỗi ngẫu nhiên.**

- Trên **73/155 lượt có chuỗi số (47%)**, FastConformer phun `⁇` thay cho dãy số → mất hẳn nội dung quan trọng nhất của data này.
- **67% trong số đó (49/73) ra đúng một khuôn `... ⁇ 4 năm ⁇`** — cùng một chuỗi lặp lại bất kể số thật là gì. Top output lặp:
  - `8×` `"số căn cước công dân là ⁇ 4 năm ⁇"`
  - `7×` `"số căn cước công dân ⁇ 4 năm ⁇"`
  - `5×` `"số điện thoại ⁇"`
- Đối chiếu cùng lượt: ChunkFormer + Parakeet **đọc ra đủ dãy số** (`⁇`=0 ở cả hai). → lỗi thuộc riêng FastConformer, không phải audio quá khó.

**Ý nghĩa cho việc cải tiến:** fragment `"4 năm"` (= "bốn năm") sống sót đều đặn trong khi phần còn lại thành `⁇`
gợi ý model **không map được connected-digits ở 8kHz vào token số**, chỉ neo được 1-2 token quen nhất rồi bỏ phần còn lại.
Đây là dấu hiệu **out-of-distribution về cả acoustic (8kHz telephony) lẫn cách biểu diễn số** (xem §4 giả thuyết).

---

## 2. Bảng các loại issue (số lượng + call dính)

| Loại | Mô tả | Số lượt | Số call | File CSV |
|---|---|---|---|---|
| **A** `fast_oov_digit` | FastConformer phun `⁇` trên lượt **có chuỗi số** — lỗi chí mạng | 73 | 14 | `out/issues/A_fast_oov_digit.csv` |
| **B** `fast_oov_other` | FastConformer phun `⁇` trên lượt không phải chuỗi số | 3 | 3 | `.../B_fast_oov_other.csv` |
| **C** `chunk_digitgroup` | ChunkFormer gom số thành số-đếm (chèn `nghìn/trăm/linh`) | 105 | 14 | `.../C_chunk_digitgroup.csv` |
| **D** `para_junk` | Parakeet phun mảnh rác trên đoạn non-speech | 142 | 22 | `.../D_para_junk.csv` |
| **E** `fast_diverge` | FastConformer lệch hẳn cả 2 model kia (lỗi không phải số) | 6 | 6 | `.../E_fast_diverge.csv` |

Đọc: FastConformer có **2 mặt yếu** — (A) chuỗi số (nặng, 73 lượt) và (E) fragment ngắn (nhẹ, 6 lượt).
C và D là điểm yếu của 2 model kia, đưa vào để tránh chọn nhầm baseline.

---

## 3. Call_id cụ thể theo từng loại (để nghe + phân tích)

Nghe 1 mốc: `python tools/cut_clip.py --call <call_id> --t <t0>` (cắt clip wav quanh mốc để nghe kênh tương ứng).

### A. FastConformer OOV trên chuỗi số (ưu tiên phân tích)
Call đậm đặc nhất: **`5634d6eb`** (21 lượt) · `fde2515f` (9) · `115cfbb0` (7) · `c6c00bcd` (7) · `dd95d9dd` (7) · `084bea35` (6).

Ví dụ chuẩn để soi (bot readback số căn cước):
- `0718d87c` · bot @ 74.4s
  - fast: `... số căn cước công dân là ⁇`
  - chun: `... số căn cước công dân là ba sáu bảy tám chín nghìn tám trăm sáu mươi tám`
  - para: `... số căn cước công dân là ba sáu bảy tám chín tám sáu tám.`
- `115cfbb0` · bot @ 45.2s và @ 54.9s (hai readback liên tiếp, fast ra y hệt `⁇ 4 năm ⁇`)
- `084bea35` · bot @ 81.4s (câu dài 12s có 3 trường số: căn cước + sđt + 4 số cuối thẻ → fast phun `⁇` cả 3)
- `026be254` · cust @ 77.6s (khách tự đọc số căn cước — fast cũng `⁇ 4 năm ⁇`)

### B. FastConformer OOV không phải chuỗi số (hiếm)
Call: `dd95d9dd`, `c6c00bcd`, `62173ce1` — xem CSV (3 lượt, không phải trọng tâm).

### E. FastConformer lệch trên fragment ngắn (tên riêng / lệnh ngắn, 0.9–3s)
- `5b16eff7` · cust @ 29.9s — fast `tôn hỉ hồng` vs chun `tô thị hồng` (sai tên riêng)
- `c341f057` · cust @ 25.3s — fast `tô thị hầu nghe mạng` vs chun `tô thị hồng em ạ`
- `5b09f032` · cust @ 3.7s — fast `tất hẻ mười` vs chun `cho chị phá thẻ thôi` (lệnh "phá thẻ")
- `3f1c7d62` · cust @ 19.5s — fast `quá trẻ luôn` vs chun `đừng như xóa thẻ luôn`

> Cả 3 model đều yếu ở nhóm E (fragment 8kHz ngắn, chồng tiếng) — không riêng FastConformer.

---

## 4. Giả thuyết nguyên nhân (để agent khác kiểm chứng, chưa xác nhận)

1. **Acoustic 8kHz telephony vs train 16kHz.** Model train 16kHz; telephony 8kHz mất dải cao → connected-digits đọc nhanh bị nhòe. Kiểm: đo WER trên digit-only ở 8kHz vs 16kHz cùng câu.
2. **Biểu diễn số khi train khác readback.** `⁇ 4 năm ⁇` degenerate + "bốn năm→4 năm" gợi ý train normalize số dạng **chữ số Ả Rập**, nên spoken-digit readback là OOD. Kiểm: xem text-normalization của tập fine-tune (số ghi "4" hay "bốn"?).
3. **Vocab/tokenizer thiếu token số đọc-rời.** `⁇` = tokenizer không có token phù hợp. Kiểm: tần suất token số trong tokenizer + trong data train; thử `model_inspector` soi vocab.
4. **Thiếu data connected-digits trong fine-tune.** Kiểm: tỉ lệ câu chứa dãy ≥6 số trong tập train.

## 5. Hướng cải tiến gợi ý (khung, không kết luận)
- **Fine-tune bổ sung trên 8kHz telephony** (chính data FCI + augment): ưu tiên câu readback số. Đây khớp hướng cả exp đang xây (xin data FCI).
- **Augment connected-digits**: sinh TTS/nối ghép dãy số 8kHz đủ độ dài + tốc độ đọc nhanh.
- **Chuẩn hoá số nhất quán** giữa train và inference (chốt đọc-rời hay số Ả Rập, không lẫn).
- **Rà vocab/tokenizer**: đảm bảo đủ token số; nếu `⁇` là token thật thì xử lý ở decode.
- So mốc: dùng Parakeet (sạch số) làm pseudo-label để đo mức cải thiện sau fine-tune.

> Con số + ví dụ ở trên tái lập bằng `tools/trace_stt_issues.py`. CSV đầy đủ mọi instance ở `out/issues/`.
