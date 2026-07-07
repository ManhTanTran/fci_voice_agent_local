# exp11 — Report so sánh WER bốn checkpoint ASR

Đo trên chín tập public tiếng Việt có ground-truth, cùng một chuẩn normalize và định nghĩa WER, xem [SPEC.md](SPEC.md).
Số WER phần trăm, thấp hơn tốt hơn; chi tiết máy sinh ở `out/results.json` và `out/table.md`.

## 1. Bảng WER

| Tập | fc_s3 | fc_s5 | parakeet | chunkformer |
|---|---|---|---|---|
| vivos | 8.46 | 7.98 | 6.59 | **2.76** |
| common_voice_vi | 17.20 | 16.22 | 10.73 | **6.77** |
| fleurs_vi | 16.45 | 15.52 | 12.15 | **10.25** |
| vlsp2020_100h | 24.81 | 24.10 | 16.06 | **9.30** |
| lsvsc | 13.12 | 12.56 | 10.24 | **7.81** |
| fosd | 19.95 | 19.16 | 8.91 | **5.19** |
| bud500 | 6.73 | 5.94 | 7.95 | **4.24** |
| vietmed | 26.38 | 25.76 | 23.28 | **19.42** |
| vietsuperspeech | 22.86 | **21.40** | 26.72 | 37.81 |
| **avg** | 17.33 | 16.52 | 13.63 | **11.51** |

## 2. Nhận định

- **ChunkFormer thấp WER nhất tổng thể (11.51)** và áp đảo trên giọng đọc-sạch:
  - vivos 2.76, fosd 5.19, bud500 4.24, vlsp 9.30, thấp hơn hẳn ba model kia,
  - nhưng **sập trên vietsuperspeech 37.81**, tệ nhất bảng, đây là giọng hội thoại tự nhiên.
- **Parakeet mạnh đều trên giọng đọc** (13.63), cũng yếu hơn trên vietsuperspeech 26.72.
- **fc_s5 của ta thắng đúng vietsuperspeech (21.40)** giọng hội thoại, domain gần callbot nhất:
  - trên giọng đọc thì thua hai model lớn, nhưng trên hội thoại lại bền nhất,
  - fc_s5 cũng vượt fc_s3 ở cả chín tập, xác nhận vòng mở rộng vocab cải thiện đều.
- **Trục đọc-sạch và trục hội thoại tách nhau:** model tối ưu giọng đọc thì đuối hội thoại và ngược lại.

## 3. Cảnh báo quan trọng khi chọn model cho FCI

- Bảng này đo trên **16kHz đọc-sạch**, KHÔNG bắt được lỗi chí mạng trên tổng đài:
  - trên data FCI 8kHz, fc_s5 sập chuỗi số readback thành ký tự unknown, còn ChunkFormer và Parakeet đọc được,
  - chi tiết ở [../10_conversation_analysis/ISSUES_FASTCONFORMER.md](../10_conversation_analysis/ISSUES_FASTCONFORMER.md) và chẩn đoán ở [nvidia_asr_nemo 09.01](../../../nvidia_asr_nemo/experiments/09_8khz_digit_robustness/01_diagnosis.md).
- Nên WER public chỉ là một mặt; chọn model cho callbot phải cân thêm chuỗi số 8kHz và giọng hội thoại.
- **Tốc độ không phải nút thắt:** cả bốn chạy GPU rất nhanh, RTF từ 0.003 tới 0.02, xem `out/results.json`.

## 4. Tái lập

- Chạy lại toàn bộ hoặc thêm checkpoint: xem [README.md](README.md) và [SPEC.md](SPEC.md).
- Thêm một model chỉ cần thêm một dòng trong `MODELS` của `run_bench.py`, phần đo giữ nguyên.
