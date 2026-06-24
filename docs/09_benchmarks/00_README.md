# 09 — Benchmarks

> ⬜ Stub — chưa khảo sát. Mới chốt scope.

**Scope:** đo lại metric các bài toán con, hướng tới mục tiêu **CCU=100**. Benchmark nội bộ hiện đo ở CCU=5.

**Bộ metric (từ doc nội bộ 02):**
- LLM Agent: TTFT/TTFS (Mean + P95) · Prompt Compliance ≥90% · Tool Calling ≥90%.
- Turn Interruption: Latency ≤150ms · Accuracy ≥85%.
- ASR telephony (cần bổ sung): WER ở 8kHz/nhiễu · RTF.

**Cách đo:** LLM-as-judge so phản hồi/tool-call của model với Human Annotator, chấm Pass/Fail. (Bảng số liệu hiện trạng đầy đủ ở [`01_survey §4`](../01_survey/00_README.md#4-tiêu-chí-nghiệm-thu--khoảng-cách-hiện-tại-từ-doc-02).)
