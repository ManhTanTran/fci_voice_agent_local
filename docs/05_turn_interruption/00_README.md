# 05 — Turn & Semantic Interruption (bài đau #1)

> ⬜ Stub — chưa khảo sát. Mới chốt scope.

**Scope:** quyết định barge-in — khi user nói lúc bot đang nói, có nên dừng TTS không. Gồm 2 thành phần trong doc nội bộ: **Turn Interruption** (binary INTERRUPT/CONTINUE) + **Semantic Interruption Detection** (phân biệt backchannel vs ý định ngắt thật).

**Khoảng cách (CCU=100):** hiện Qwen-2.5-7B = **76% accuracy / ~280ms**; mục tiêu **≥85% / ≤150ms** → fail **cả hai** chiều.

**Hướng multi-solution-stack:**
- Rule-based: từ khóa backchannel ("ừ/ờ/dạ/rồi rồi") + ngưỡng VAD bắt phần dễ ở <10ms.
- DL nhỏ: classifier text/audio cho ca mơ hồ.
- LLM: chỉ giữ cho ca khó → giảm latency trung bình.

**Lead từ khảo sát ([02.01 FPT-vs-SOTA](../02_architecture/01_fpt_vs_sota.md)):** open-source ĐÃ đi xa hơn LLM-binary — semantic turn-detector nhỏ chạy CPU: **LiveKit turn-detector** (Qwen2.5-0.5B, trên transcript text, hybrid Silero VAD), **Pipecat Smart Turn v3** (Whisper-tiny trên waveform, ~12-65ms), **VAP** (CPU, 2 kênh liên tục). ⚠️ Tiếng Việt **chưa xác minh** → việc đầu tiên khi khoan sâu: kiểm `vi` trong các model này.

**Tài liệu mẫu:** prompt binary + 5 ví dụ (cả tiếng Việt) có trong doc nội bộ 02 §4; dataset `turn_interruption_test.json` → xem [`08_datasets`](../08_datasets/00_README.md).
