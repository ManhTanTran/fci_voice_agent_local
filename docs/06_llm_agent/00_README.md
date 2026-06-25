# 06 — LLM Agent + Simulated Tool-calling (bài đau #2)

> ⬜ Stub — chưa khảo sát. Mới chốt scope.

**Scope:** Agent lõi — Orchestrator điều phối, Conversation Checkpoint, và **simulated tool-calling** (`what_should_I_do_next`) để bám step nghiệp vụ. Bao gồm cả luồng bổ trợ gọi tool thật (lớp 3, đang research).

**Khoảng cách (CCU=100):** Tool Calling tốt nhất mới **61.79%** (Qwen-3.5-35B-A3B); mục tiêu **≥90%** → fail ~28 điểm. Prompt Compliance đã đạt (94.91%).

**Câu hỏi cần trả lời:**
- Vì sao tool-calling thấp: do model, do schema tool, hay do cách biểu diễn (filter phrase)?
- Luồng phụ "sinh cú pháp tool riêng + sinh lại phản hồi" cải thiện accuracy bao nhiêu, đánh đổi latency bao nhiêu?
- Đối chiếu kỹ thuật tool-calling SOTA (constrained decoding, function-calling fine-tune).

**Lead từ khảo sát ([02.01 FPT-vs-SOTA](../02_architecture/01_fpt_vs_sota.md)):** đo bằng **BFCL V4** (AST matching, hỗ trợ cả prompt-based = đúng "simulated tool-calling") để phân tách lỗi *format* vs *chọn-sai-tool*. **Constrained decoding (XGrammar)** chỉ vá lỗi format (không vượt được lỗi chọn-sai-tool) → làm BFCL harness TRƯỚC để biết XGrammar có đáng không.

**Tài liệu mẫu:** System Prompt template (Personality/Flow/Scenario/Guidelines/Tools) + `voice_agent_trace_samples.jsonl` → [`08_datasets`](../08_datasets/00_README.md).
