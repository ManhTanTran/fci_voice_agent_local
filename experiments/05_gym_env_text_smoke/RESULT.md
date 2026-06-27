# Exp 05 — Thông luồng gym-env (text mode / tool-calling) · RESULT

**Ngày chạy:** 2026-06-27 · **Máy:** DGX GB10 (Qwen2.5-1.5B cuda/fp16) + local (RuleBased) · **Trạng thái:** chưa commit

---

## 1. Kết quả thật — vòng ĐO → VÁ trên DGX

| Bước | micro turn_pass | goal | Vá gì (nguyên nhân thật) |
|---|---|---|---|
| LLM baseline | 75% | 3/4 | (chưa vá) |
| + prompt rules | 88% | 3/4 | cấm gọi tool khi chào/thiếu param; pin ISO date |
| + parser/history | 94% | 4/4 | parser lấy JSON đầu tiên (cân bằng ngoặc); history ghi JSON đúng format |
| + slot-grounding | **100%** | **4/4** | bỏ call nếu giá trị args không có trong lời user (chống bịa slot) |

- Baseline `RuleBasedPolicy` (LOCAL) trên cùng suite = **75% micro** — mốc đối chiếu rẻ.

## 2. Chênh lệch với kỳ vọng (SPEC §5)

| Tiêu chí | Kỳ vọng | Thực tế | Khớp? |
|---|---|---|---|
| Vòng lặp khép kín | chạy hết | ✅ 4/4 scenario | ✅ |
| Scorer bắt đúng tầng | phân biệt FN/FP/T2/T3 | ✅ — chính nhờ đó phát hiện 2 bug code | ✅ |
| LLMPolicy đẩy điểm | đo→vá lên được | 75% → **100%** | ✅ vượt kỳ vọng |

## 3. Insight / bài học

- **2/4 lỗi ban đầu là BUG CODE CỦA MÌNH, không phải model dốt:**
  - parser regex tham lam nuốt nhiều dòng JSON → đổi sang **quét cân-bằng-ngoặc** lấy object đầu tiên có key `tool`.
  - env ghi history tool-turn dạng `[tool:...]` → dạy model nhái sai format ở lượt sau → đổi ghi **JSON đúng**.
  - ⇒ Bài học: trước khi đổ lỗi model, trace lỗi thật (bật raw output) — scorer giúp khoanh đúng tầng.
- **slot-grounding guard:** bỏ tool-call nếu giá trị args không xuất hiện trong lời user → chặn model nhái giá trị trong few-shot example.
- **Trung thực:** 100% trên 4 scenario nhỏ KHÔNG phải "bot giỏi". Nó chỉ chứng minh (1) harness chạy đúng + bắt lỗi đúng tầng, (2) baseline sau vá vượt tập nhỏ. Giá trị thật đến khi: A/B phiên bản, bộ scenario lớn+khó, `pass^k` cho độ ổn định.

## 4. Việc còn lại (tech-debt, ưu tiên giảm dần)

1. **Sim-user agenda cố định** → v2 bọc LLM diễn đạt lại bề mặt, giữ nhãn (sim-to-real).
2. **Bộ scenario nhỏ** → mở rộng + `pass^k` (τ-bench). (Đã làm tiếp ở exp06/07.)
3. **Chỉ text mode** → audio/turn-detection là exp08.
4. **World-state tối giản** (chỉ ghi tool đã gọi) → mô phỏng hiệu ứng tool (verify fail → nhánh khác).
