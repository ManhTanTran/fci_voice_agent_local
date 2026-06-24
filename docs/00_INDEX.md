# 00 — INDEX tài liệu fci_voice_agent

Điểm vào toàn bộ tài liệu khảo sát. Đọc theo thứ tự số. Làm việc *layer by layer*.

Thứ tự layer bám theo **đường đi của tín hiệu**: âm thanh thô → ngữ nghĩa → agent → an toàn → đo lường.

| # | Thư mục | Nội dung | Trạng thái |
|---|---------|----------|-----------|
| 01 | [`01_survey/`](01_survey/00_README.md) | Hiện trạng FCI + tổng hợp 2 doc nội bộ + chốt scope + đề bài + khoảng cách benchmark | 🟢 v1 |
| 02 | [`02_architecture/`](02_architecture/00_README.md) | Mổ kiến trúc 4 lớp nội bộ + tham chiếu ngoài + bản đồ multi-solution-stack | 🟢 v1 |
| 03 | [`03_audio_frontend/`](03_audio_frontend/00_README.md) | Lớp tín hiệu: VAD, voice-action segmenting, noise scoring/classify/filter (phễu giảm tải) | ⬜ chưa |
| 04 | [`04_asr_telephony/`](04_asr_telephony/00_README.md) | ASR môi trường 8kHz/nhiễu — nối lab `nvidia_asr_nemo` | ⬜ chưa |
| 05 | [`05_turn_interruption/`](05_turn_interruption/00_README.md) | Turn + Semantic Interruption (barge-in) — **bài đau #1** (76% acc / 280ms) | ⬜ chưa |
| 06 | [`06_llm_agent/`](06_llm_agent/00_README.md) | Orchestrator + simulated tool-calling — **bài đau #2** (tool 62% vs 90%) | ⬜ chưa |
| 07 | [`07_guardrails/`](07_guardrails/00_README.md) | Input rails (prompt injection, moderation) + PII + Output rail + Text-Norm | ⬜ chưa |
| 08 | [`08_datasets/`](08_datasets/00_README.md) | `voice_agent_trace_samples` + `turn_interruption_test` + dataset thoại VN | ⬜ chưa |
| 09 | [`09_benchmarks/`](09_benchmarks/00_README.md) | Đo lại metric + mục tiêu CCU=100 (latency + quality) | ⬜ chưa |

> Quy ước trạng thái: 🟢 có nội dung thật · 🟡 v1 chưa kiểm chứng · ⬜ mới có stub scope.

## Hai trục công việc

- **Trục A — Hiểu kiến trúc voice-agent (nội bộ + SOTA):** mổ 4 lớp trong doc nội bộ, đối chiếu hướng đi open-source / paper 2024-2026.
- **Trục B — Khai thác đặc thù tổng đài (8kHz, nhiễu, real-time):** phễu giảm tải audio (rule-based → micro model → ngữ nghĩa → LLM), tối ưu latency cho barge-in.

Hai trục gặp nhau ở: **định nghĩa các bài toán con đo được** → gom thành **hệ thống nhiều model phối hợp**.
