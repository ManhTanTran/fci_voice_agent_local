# 07 — Guardrails (input / PII / output)

> ⬜ Stub — chưa khảo sát. Mới chốt scope.

**Scope:** các lớp an toàn — Input Rails (Prompt Injection Detection + Content Moderation), Rails Fallback, PII Guardrails (chặn xin password/PIN/OTP), Output Rail (factual/anti-hallucination), Text Normalization.

**Câu hỏi cần trả lời:**
- Phân loại prompt injection / nội dung cấm bằng tầng nào (regex blocklist → NER nhỏ → LLM judge) cho đạt latency?
- Factual rail đối chiếu số liệu thế nào để bắt hallucination mà không chậm?
- Đối chiếu framework ngoài (vd NeMo Guardrails) với cơ chế rails + thẻ `<forbidden>` của doc nội bộ.

**Multi-solution-stack:** blocklist regex → NER PII → LLM judge. (Bảng ở [`02_architecture`](../02_architecture/00_README.md#3-bản-đồ-multi-solution-stack).)
