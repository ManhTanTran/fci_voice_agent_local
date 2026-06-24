# 08 — Datasets

> ⬜ Stub — chưa khảo sát. Mới chốt scope.

**Scope:** dữ liệu đánh giá cho các bài toán con + dataset thoại tiếng Việt.

**Đã có (nêu trong doc nội bộ 02):**
- `voice_agent_trace_samples.jsonl` — mỗi sample = 1 trace 1 lượt: System Prompt + Conversation History + User Input + Expected Response + Expected Tool Calls.
- `turn_interruption_test.json` — Conversation History + Partial Utterances + label INTERRUPT/CONTINUE.

**Cần làm:**
- Lấy file gốc 2 dataset trên (hỏi team / Drive) → đặt vào `../../data/` (gitignore, mirror Drive).
- Khảo sát dataset thoại VN cho ASR telephony 8kHz (nối inventory bên `nvidia_asr_nemo`).
