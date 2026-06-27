# Exp 06 — Suite tool-calling KHÓ + structured decoding (xgrammar) · RESULT

**Ngày chạy:** 2026-06-27 · **Máy:** DGX GB10 (Qwen2.5-1.5B cuda/fp16) · **Trạng thái:** chưa commit

---

## 1. Kết quả thật

| Policy | micro turn_pass | goal | Ghi chú |
|---|---|---|---|
| RuleBased (local) | 23% | 1/7 | mốc rẻ, không model |
| LLM free-form JSON | **50%** | 6/7 | lỗi dồn ở enum/cấu trúc/bịa-tool |
| **xgrammar (constrained)** | **86%** | **7/7** | grammar trị sạch lỗi format |
| xgrammar + reasoning | 86% | 7/7 | think-then-constrain: HÒA ở 1.5B |

**11 lỗi free-form → grammar trị được:**

| Lỗi free-form | Loại | xgrammar |
|---|---|---|
| reason=`"unauthorized access"`, `"Ben Tran lost his card."` | enum ngoài tập | ✅ |
| amount=`"250 EUR"` (mất field currency) | sai cấu trúc | ✅ |
| category=`"duplicate charges"` | enum ngoài tập | ✅ |
| country_code=`"+33"` | enum ngoài tập | ✅ |
| tool=`"create_savings_account"` | bịa tên tool | ✅ |
| category=`"fraud"` (đúng enum, sai nghĩa) | ngữ nghĩa | ❌ |

**3 lỗi còn lại của xgrammar (86%) đều KHÔNG phải format:**
- h1t2 reason=lost thay vì stolen → chọn **sai enum về nghĩa** (grammar ép đúng tập, không ép đúng lựa chọn).
- h2t1, h7t2 → **FP/quyết định**: gọi tool khi nên hỏi/xác nhận.

## 2. Chênh lệch với kỳ vọng (SPEC §5)

| Tiêu chí | Kỳ vọng | Thực tế | Khớp? |
|---|---|---|---|
| Free-form thấp | thấp | 50% (goal 6/7) | ✅ |
| xgrammar vá format | tăng rõ | 50% → **86%**, goal 7/7 | ✅ |
| Residual = ngữ nghĩa | còn lỗi không-format | đúng (3 lỗi ngữ nghĩa/quyết định) | ✅ |
| reasoning cải thiện | giả thuyết | **HÒA** (vá 1 hồi quy 1) | ⚠️ không cải thiện ở 1.5B |

## 3. Insight / bài học

- **CHỐT lõi:** grammar **dời lỗi từ "cú pháp" sang "năng lực model"** — nó trị sạch format/enum-ngoài-tập/bịa-tool, nhưng KHÔNG chạm chọn-sai-enum-về-nghĩa hay FP-quyết-định.
- ⇒ **Hướng đầu tư đúng KHÔNG phải grammar** mà là: model lớn hơn, few-shot theo enum-paraphrase, hoặc tách bước "có nên gọi tool" khỏi "điền tham số".
- **think-then-constrain ở 1.5B = hòa** → khớp tranh luận "format tax": thêm reasoning không miễn phí, lợi/hại cân bằng ở model nhỏ.
- xgrammar có **wheel aarch64 chạy được trên GB10** → structured decoding self-host khả thi.

## 4. Việc còn lại

- Phân tách residual (ngữ nghĩa vs quyết định) → đo riêng từng lớp (link bài đo BFCL/HammerBench trong `docs/06`).
- Thử model lớn hơn / few-shot domain để vá residual (đã scale sang 3 domain ở exp07).
- `pass^k` cho độ ổn định.

> Lý thuyết structured decoding: `docs/11_sim_test_system/03_structured_decoding.md`.
