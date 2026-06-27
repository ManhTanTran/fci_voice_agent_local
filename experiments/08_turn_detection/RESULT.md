# Exp 08 — Harness phát hiện lượt thoại (turn-detection) · RESULT

**Ngày chạy:** 2026-06-27 · **Máy:** local (2 baseline; LLM trên DGX chưa chạy) · **Trạng thái:** chưa commit

---

## 1. Kết quả thật — A/B trên cùng 17 scenario

| Decider | accuracy | TP/FP/FN/TN | precision(INTR) | recall(INTR) |
|---|---|---|---|---|
| `energy_vad` (mù ngữ nghĩa) | **65%** | 9/**6**/0/2 | 60% | 100% |
| `semantic_rule` (lọc speaker + lexicon) | **100%** | 9/0/0/8 | 100% | 100% |

- Tách môi trường: quiet (11) energy 73% vs semantic 100%; noisy (6) energy ~50% vs semantic 100% (nhiễu nới rộng khoảng cách).

## 2. Chênh lệch với kỳ vọng (SPEC §5)

| Tiêu chí | Kỳ vọng | Thực tế | Khớp? |
|---|---|---|---|
| energy_vad thấp + FP cao | ~76%, FP nhiều | 65%, FP=6 | ✅ (sát mức đau) |
| semantic vá FP | cao hơn rõ | **100%**, FP=0 | ✅ |
| harness phân biệt 2 decider | có | 65% vs 100% | ✅ scorer không phải con dấu |
| latency | synthetic | energy 250ms / semantic 400ms (mô hình hóa) | ⚠️ chưa phải ms thật |

## 3. Insight / bài học

- **energy-VAD: recall 100% nhưng ngắt nhầm 6 ca** (âm-đệm-dài "dạ vâng", nói vấp, side-talk, nhạc, TV) → 65% ≈ đúng mức đau ~76%. Lỗi đặc trưng là **ngắt nhầm (FP)**, không phải sót.
- **semantic vá sạch FP** nhờ lọc theo người nói + nhận ra toàn tiếng đệm → đúng phát hiện SOTA: semantic turn-detection thắng energy-VAD ở chính lớp FP.
- **Trung thực về latency:** số ms là **synthetic** (text-mode chưa có audio) chỉ để lộ trục đánh đổi *nhanh-sai* (energy) vs *đúng-chậm* (semantic). Ở vài ca ồn, energy có latency "0ms" vì bắn theo TIẾNG NHẠC trước cả khi khách nói → minh chứng đo latency tách rời accuracy là vô nghĩa. Số ms thật cần Renderer audio v2/v3.
- **Chống chấm-vòng-tròn:** decider không đọc `tag`/`expected` → con số A/B đáng tin.

## 4. Việc còn lại

- `llm_semantic` trên DGX — xem LLM-1.5B đứng đâu giữa 2 baseline.
- **Renderer audio v1→v3** (ghép thời gian, trộn nhiễu MUSAN/DEMAND, hạ 8kHz μ-law) để đo **ms thật** thay synthetic.
- Neo SRCC với một tập nhỏ cuộc gọi thật trước khi tin kết luận.
