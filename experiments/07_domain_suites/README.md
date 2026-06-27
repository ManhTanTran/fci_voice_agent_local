# Exp 07 — Scale test-case ra 3 domain CSKH (thang năng lực tăng dần)

Mở rộng bộ kịch bản tool-calling sang 3 nhóm domain thật của FCI, **mỗi domain
kế thừa năng lực domain trước + thêm một lớp khó**. Dùng lại khung gym-env của
[exp 05](../05_gym_env_text_smoke/) + structured decoding của [exp 06](../06_gym_env_hard/);
mỗi domain là một thư mục suite riêng (chạy qua `FCI_SCEN_DIR`).

## Thang năng lực (đúng đề bài Kỳ)

| Domain | Năng lực tích lũy | Tool đặc trưng | Lớp khó MỚI |
|---|---|---|---|
| **booking** (đặt lịch) | tra cứu thông tin | check_availability, create/reschedule/cancel_booking | trích slot + action có xác nhận |
| **sales** (bán hàng) | + tra cứu **tri thức** | search_knowledge(topic enum), recommend_offer, mark_not_interested | định tuyến RAG theo topic + opt-out |
| **debt** (đòi nợ) | + **tư duy tình huống** | verify_debtor (gate), get_debt_details, search_policy, offer_payment_plan, escalate_to_human | cổng anti-IDOR + phán đoán escalate/plan + compliance |

- **Điểm thiết kế 1 — tri thức vẫn chấm được**: `search_knowledge`/`search_policy`
  nhận tham số `topic` dạng **enum** (không phải câu truy vấn tự do) → vừa chấm
  bằng scorer 3 tầng sẵn có, vừa ép được bằng grammar.
- **Điểm thiết kế 2 — compliance đặt trong `goal`**: luật nghiệp vụ (vd "phải
  xác thực trước khi tiết lộ nợ", "không tiết lộ cho bên thứ ba") nằm ở trường
  `goal` của scenario → chảy vào system prompt. Như vậy test đo việc model **tuân
  thủ** chính sách đã nêu, không phải đoán mò — đúng thực tế production.

## Kết quả đo trên DGX (Qwen2.5-1.5B, GB10)

| Domain | free-form | **xgrammar** | Δ | Mốc RuleBased |
|---|---|---|---|---|
| booking | 92% | **100%** | +8 | 33% |
| sales | 38% | **62%** | +24 | 15% |
| debt | 38% | **69%** | +31 | 25% |

(micro turn_pass; RuleBased = baseline local không model.)

## Đọc kết quả — structured decoding vá tới đâu, hụt ở đâu

- **booking → 100%**: domain chỉ cần tra cứu thông tin + trích slot (date/time/id).
  Đây thuần **định dạng + trích xuất** → grammar đưa lên trần.
- **sales → 62% (residual = định tuyến tri thức SAI NGHĨA)**:
  - Lỗi còn lại đều là chọn sai `topic` enum (pricing thay vì promotion,
    coverage_area thay vì contract_terms) hoặc chọn sai tool.
  - Grammar đảm bảo `topic` thuộc đúng tập, nhưng KHÔNG đảm bảo chọn đúng topic —
    đây là tác vụ ngữ nghĩa (hiểu câu hỏi thuộc chủ đề nào).
- **debt → 69% (residual = tư duy tình huống + compliance)**:
  - Lỗi còn lại đều là quyết định tình huống: gọi `get_debt_details` TRƯỚC khi
    xác thực (thủng cổng anti-IDOR), tiết lộ cho bên thứ ba, không nhận
    hardship → escalate, không escalate khi có tranh chấp.
  - Grammar không thể ép logic "xác thực trước khi tiết lộ" hay "tình huống này
    nên escalate" — đó là suy luận, không phải cú pháp.

> [!IMPORTANT]
> Quy luật rút ra: **càng lên cao trên thang năng lực, structured decoding càng
> để lại nhiều residual** — và residual đó CHÍNH LÀ năng lực định nghĩa độ khó
> của domain (định tuyến tri thức ở sales, tư duy tình huống ở debt). Grammar trị
> dứt tầng định-dạng/trích-xuất (T3), trị một phần chọn-enum (T2), KHÔNG chạm
> quyết-định/ngữ-nghĩa (T1 + T2 ngữ nghĩa). Hướng vá residual: model lớn hơn,
> few-shot theo domain, hoặc tách bước "quyết định/định tuyến" khỏi "điền tham số".

## Chạy

```bash
for d in booking sales debt; do
  for p in llm xgrammar; do
    ssh dgx "cd fci_voice_agent && FCI_SCEN_DIR=experiments/07_domain_suites/$d \
      FCI_POLICY=$p uv run python experiments/05_gym_env_text_smoke/run_gym_text.py"
  done
done
```

## Quy mô

17 scenario · ~41 lượt chấm (booking 5 · sales 6 · debt 6). Mỗi domain có file
tool riêng (`tools_<domain>.json`) tái dùng qua `tools_ref`.
