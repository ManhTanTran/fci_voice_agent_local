# Kết quả chạy thật — lát mỏng Phase 0 (sinh nhiễu tất định + chấm PhoWhisper)

> Đây là số THẬT do pipeline trong thư mục này chạy ra, không phải ước lượng. Chạy trên CPU (máy không có GPU dùng được).
> Mục tiêu: chứng minh **verifier tất định** hoạt động — chấm được một ASR ra **đường cong WER theo loại nhiễu × SNR**, không cần xin data ai.

## a. Dữ liệu dùng

- **Nguồn sạch**: VIVOS test, tái dùng local ở `nvidia_asr_nemo/data/raw/vivos/test/` (KHÔNG tải mới).
- **Subset**: **30 clip** (câu ngắn tiếng Việt, có transcript chuẩn) — cố tình nhỏ để chạy xong nhanh trên CPU.
- **Sinh nhiễu tất định** (seed cố định): mỗi clip × {clean} ∪ {white, pink, babble} × {0, 5, 10, 20 dB} = **13 biến thể/clip** → **390 mẫu**, mỗi mẫu mang nhãn by-construction `(transcript, noise_type, snr_db)`. Manifest: `results/dataset_manifest.csv`.
  - **white**: nhiễu trắng (phổ phẳng).
  - **pink**: nhiễu hồng (lọc 1/f, gần nhiễu môi trường tự nhiên hơn).
  - **babble**: trộn nhiều clip speech khác chồng lên (giả "tiếng người ồn xung quanh" — sát tổng đài nhất).

## b. Model chấm

- **`vinai/PhoWhisper-small`** (244M), chạy `transformers` trên **CPU**.
- Chuẩn hóa text nhất quán hyp & ref trước khi tính WER bằng `jiwer` (lower + bỏ dấu câu, **giữ dấu tiếng Việt**, gộp khoảng trắng).

## c. Bảng WER (%) theo noise_type × SNR — số thật

| noise_type | SNR 0dB | SNR 5dB | SNR 10dB | SNR 20dB | clean |
|---|---|---|---|---|---|
| white | 9.4 | 7.1 | 5.5 | 0.8 | 0.8 |
| pink | 11.8 | 4.7 | 6.3 | 1.6 | 0.8 |
| **babble** | **59.1** | 12.6 | 6.3 | 3.1 | 0.8 |

(clean WER = **0.79%** — chung cho mọi hàng vì clean không phụ thuộc loại nhiễu.)

## d. Nhận xét

- **WER tăng đơn điệu khi SNR giảm** (nhiễu nặng hơn → nghe tệ hơn) — verifier phản ánh đúng vật lý, đường cong dùng được để so model.
- **Loại nhiễu quan trọng hơn mức nhiễu** — phát hiện đắt giá nhất:
  - Ở **SNR 0dB**, babble **59.1%** so với white 9.4% / pink 11.8% → **babble phá gấp ~5-6 lần** ở cùng mức ồn.
  - Lý do: white/pink là nhiễu tĩnh (model học lọc được); babble là **tiếng người cạnh tranh** — ASR khó tách đâu là giọng đích.
  - → Đúng tín hiệu voice-agent cần: **không chỉ hỏi "ồn bao nhiêu" mà "ồn LOẠI gì"** để quyết hành vi.
- **Vách rơi ở dải 0-5dB của babble** (59.1% → 12.6%): dưới ngưỡng SNR nào đó ASR sụp; đây là "điểm gãy" cần cảnh báo/nhờ nói lại.
- **SNR 20dB**: mọi loại nhiễu về gần clean (0.8-3.1%) → nhiễu nhẹ gần như vô hại.

## e. Thời gian chạy

- Sinh data: vài giây (numpy/scipy, CPU).
- Chấm điểm: **16.8 phút** cho 390 mẫu (**2.58s/mẫu**, PhoWhisper-small CPU).

## f. Hạn chế (đọc kỹ trước khi trích số)

- **Subset chỉ 30 clip câu ngắn** → clean WER 0.79% **lạc quan hơn benchmark thật** (paper: small trên VIVOS full = 6.33%). Bảng này là **stress-test tương đối** (so loại nhiễu / mức SNR với nhau), **KHÔNG** phải điểm benchmark tuyệt đối.
- **Nhiễu tổng hợp** (white/pink/babble tự sinh), **chưa dùng MUSAN thật**; **chưa có RIR/reverb**, **chưa có codec điện thoại 8kHz**, **không có Lombard**. → Đây là nhiễu *cộng*, còn cách nhiễu đời thật (xem bẫy synthetic→real ở doc 04 mục 5).
- **Chưa có mỏ-neo real** để đo gap synthetic→real (đó là bậc data xin FCI).
- **PhoWhisper-small**, chưa chạy medium/large.

## g. Chạy lại

Xem `README.md` cùng thư mục (`uv sync`, rồi `uv run python src/build_dataset.py` rồi `uv run python src/verify_asr.py`).

> **Ghi chú vị trí**: code này ban đầu chạy ở `.agent/research/03_research_direction/04_phase0_code/`, sau chuyển sang module `fci_voice_agent/experiments/09_asr_noise_verifier/`. `dataset_manifest.csv` + `noisy_wav/` đã regenerate theo path mới (tất định, wav y hệt). Riêng `predictions.csv` và `verify_run.log` là bản ghi của lần chấm gốc nên cột `audio_filepath` còn trỏ path cũ — nội dung số (WER, hyp/ref) vẫn đúng vì data tái lập theo seed.
