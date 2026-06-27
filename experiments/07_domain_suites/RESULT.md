# Exp 07 — Scale test-case ra 3 domain CSKH · RESULT

**Ngày chạy:** 2026-06-27 · **Máy:** DGX GB10 (Qwen2.5-1.5B) · **Trạng thái:** chưa commit

---

## 1. Kết quả thật

| Domain | free-form | **xgrammar** | Δ | Mốc RuleBased |
|---|---|---|---|---|
| booking | 92% | **100%** | +8 | 33% |
| sales | 38% | **62%** | +24 | 15% |
| debt | 38% | **69%** | +31 | 25% |

(micro turn_pass; RuleBased = baseline local không model.)

## 2. Chênh lệch với kỳ vọng (SPEC §5)

| Tiêu chí | Kỳ vọng | Thực tế | Khớp? |
|---|---|---|---|
| booking cao | gần trần | **100%** | ✅ |
| sales residual tăng | có | 62% — residual = chọn sai topic enum | ✅ |
| debt residual lớn nhất | có | 69% — residual = tình huống/compliance | ✅ |
| quy luật residual tăng theo thang | đúng | booking≈0 < sales < debt | ✅ |

## 3. Insight / bài học

- **booking → 100%:** chỉ cần tra cứu thông tin + trích slot (date/time/id) = thuần **định-dạng + trích-xuất** → grammar đưa lên trần.
- **sales → 62% (residual = định tuyến tri thức SAI NGHĨA):** lỗi còn lại đều là chọn sai `topic` enum (pricing thay vì promotion, coverage_area thay vì contract_terms) hoặc sai tool. Grammar đảm bảo `topic` đúng TẬP nhưng không đảm bảo đúng LỰA CHỌN — đây là tác vụ ngữ nghĩa.
- **debt → 69% (residual = tư duy tình huống + compliance):** lỗi còn lại là quyết định tình huống — gọi `get_debt_details` TRƯỚC khi xác thực (thủng cổng anti-IDOR), tiết lộ bên thứ ba, không escalate hardship/dispute. Grammar không thể ép logic "xác thực trước khi tiết lộ".
- **QUY LUẬT LÕI:** càng lên cao trên thang năng lực, **structured decoding càng để lại nhiều residual — và residual đó CHÍNH LÀ năng lực định nghĩa độ khó của domain**. Grammar trị dứt T3 (định-dạng/trích-xuất), trị một phần T2 (ép đúng tập enum), KHÔNG chạm T1 (quyết định) + T2 ngữ nghĩa.

## 4. Việc còn lại

- Vá residual: model lớn hơn · few-shot theo domain · tách bước "quyết định/định tuyến" khỏi "điền tham số".
- `pass^k` cho độ ổn định · BotV2 so A/B đúng mục đích gym-env.

> Phân tích đầy đủ: file này thay cho phần "Kết quả" trong README cũ.
