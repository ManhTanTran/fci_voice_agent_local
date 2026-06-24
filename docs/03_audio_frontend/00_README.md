# 03 — Audio Frontend (lớp tín hiệu)

> ⬜ Stub — chưa khảo sát. Mới chốt scope.

**Scope:** lớp xử lý tín hiệu thô trước/song song ASR — VAD, voice-action segmenting, noise scoring / classify / filtering. Đây là tầng "phễu" rẻ nhất, giống lớp xử lý frame thô bên `nvidia_vlm_vss`.

**Câu hỏi cần trả lời (sẽ vỡ dần):**
- Đo "độ nhiễu" một đoạn 8kHz thế nào (noise scoring)? Phân loại loại nhiễu (noise classify)?
- Lọc nhiễu (noise filtering) trước ASR có cải thiện WER không, đánh đổi latency bao nhiêu?
- Segmenting hành vi thoại (im lặng / nói / chồng tiếng) phục vụ barge-in.

**Multi-solution-stack:** DSP cổ điển → model VAD/denoiser nhỏ. (Xem bảng ở [`02_architecture`](../02_architecture/00_README.md#3-bản-đồ-multi-solution-stack).)
