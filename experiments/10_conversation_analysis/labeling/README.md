# Tool labeling hội thoại FPT

Web-tool LOCAL để nghe và gắn nhãn 36 cuộc gọi FPT hai kênh.
KHÔNG phải artifact claude.ai — server http stdlib, mở trên trình duyệt máy Kỳ.

Gắn được **hai trục cùng lúc**:
- **transcript gold** — sửa bản đọc, mặc định lấy parakeet, đối chiếu s5 và s6 một click,
- **nhãn barge-in** — turn khách có phải ngắt lời thật không, thuộc nhóm nào trong sáu nhóm FCI.

## 1. Chạy

Chạy 100% ở LOCAL, không cần DGX hay GPU — tool chỉ đọc JSON model + audio đã sync sẵn.
Dep khai báo trong chính script (PEP 723) nên `uv run --script` tự cài, không cần nhớ flag:

```bash
uv run --script experiments/10_conversation_analysis/labeling/label_server.py
# mở http://localhost:8010
```

Cần audio local ở `experiments/10_conversation_analysis/data/audio_interrupt/*.wav`
và JSON model ở `experiments/10_conversation_analysis/out/{parakeet,s5,s6}/*.json` (cùng VAD, đã sync từ DGX).

## 2. Thao tác

- **Cột trái** — danh sách 36 cuộc, mỗi cuộc hiện số turn có số và tiến độ đã chốt.
- **Trên cùng** — trình phát cả cuộc, tua được; nút `[ ] chỉ turn có số` để lọc nhanh chỗ readback.
- **Mỗi turn** —
  - nút `▶` nghe riêng đoạn đó, cắt đúng kênh người nói kèm đệm,
  - ba dòng parakeet, s5, s6 để đối chiếu; bấm tên model để đổ bản đó vào ô sửa,
  - ô sửa transcript, **auto-save** sau khi ngừng gõ, có báo đã lưu,
  - turn khách thêm ô tick barge-in cộng chọn nhóm,
  - tick `✓ chốt` để tính vào tiến độ và đưa vào manifest.

## 3. Kết xuất để dùng

```bash
uv run --script experiments/10_conversation_analysis/labeling/build_gold_manifest.py
```

- `gold_manifest.jsonl` — turn đã chốt, cắt kênh người nói 16k, đo WER số thật cho s5/s6:
  - dùng lại `../../../../nvidia_asr_nemo/experiments/09_8khz_digit_robustness/tools/eval_public.py` hoặc harness tương tự trỏ vào manifest này.
- `gold_bargein.csv` — nhãn barge-in cho bài turn-detection.
- `gold/<cid>.json` — nhãn thô mỗi cuộc, key theo `spk@t0`.

## 4. Ghi chú

- VAD tất định nên turn khớp giữa parakeet, s5, s6; key `spk@t0` ổn định giữa các lần chạy.
- Auto-save ghi từng phím sau debounce, không cần bấm nút lưu; đóng trình duyệt không mất.
