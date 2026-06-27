# Exp 06 — Suite tool-calling KHÓ + Structured decoding (xgrammar)

Bộ ~20 case khó cố tình bẻ gãy free-form JSON của LLM nhỏ (Qwen2.5-1.5B), rồi
chứng minh **structured decoding** (xgrammar ép JSON-schema) vá đúng lớp lỗi nào.
Dùng chung khung gym-env của [exp 05](../05_gym_env_text_smoke/) — chỉ đổi
scenario (`FCI_SCEN_DIR`) và policy (`FCI_POLICY`).

## Bộ test-case (7 scenario · 22 lượt chấm)

Danh mục tool dùng chung [scenarios/tools_bank_hard.json](scenarios/tools_bank_hard.json)
có **enum** (reason, period, currency, category, country_code) và **pattern**
(`AC-\d{4}`, `TX\d{6}`, last4 `\d{4}`, ngày ISO) — đúng chỗ free-form hay sai.

| Scenario | Probe điểm khó |
|---|---|
| h1_block_reason_enum | enum reason từ paraphrase ("taken"→stolen); dob lẻ → ISO |
| h2_distractor_and_correction | số 16 chữ số gây nhiễu; thiếu slot → phải hỏi; sửa lại last4 |
| h3_transfer_currency_enum | enum currency ("euros"→EUR); 2 slot cùng kiểu; đổi enum |
| h4_dispute_pattern_enum | pattern txn; enum category từ paraphrase |
| h5_statement_vs_balance | chọn đúng tool gần giống nhau; nhớ account |
| h6_refuse_verify_and_oos | từ chối xác thực + yêu cầu ngoài phạm vi (bịa tool) |
| h7_travel_json_hostile | enum country ("France"→FR); input có dấu nháy/ngoặc nhọn |

## Kết quả đo trên DGX (Qwen2.5-1.5B, GB10 cuda/fp16)

| Policy | micro turn_pass | goal | Ghi chú |
|---|---|---|---|
| RuleBased (local) | 23% | 1/7 | mốc rẻ, không model |
| LLM free-form JSON | **50%** | 6/7 | lỗi dồn ở enum/cấu trúc/bịa-tool |
| **xgrammar (constrained)** | **86%** | **7/7** | grammar trị sạch lỗi format |
| xgrammar + reasoning | 86% | 7/7 | think-then-constrain: hòa ở 1.5B |

## Free-form sai cái gì (11 lỗi) → grammar trị được bao nhiêu

| Lỗi free-form | Loại | xgrammar |
|---|---|---|
| reason=`"unauthorized access"`, `"Ben Tran lost his card."` | enum ngoài tập | ✅ |
| amount=`"250 EUR"` (mất field currency) | sai cấu trúc | ✅ |
| category=`"duplicate charges"` | enum ngoài tập | ✅ |
| country_code=`"+33"` | enum ngoài tập | ✅ |
| tool=`"create_savings_account"` | bịa tên tool | ✅ |
| category=`"fraud"` (đúng enum, sai nghĩa) | ngữ nghĩa | ❌ |

3 lỗi còn lại của xgrammar (86%) đều **không phải format**:
- h1t2 reason=lost thay vì stolen — chọn **sai enum về nghĩa** (grammar chỉ ép đúng tập, không ép đúng lựa chọn).
- h2t1, h7t2 — **FP/quyết định**: gọi tool khi nên hỏi/xác nhận.

> [!IMPORTANT]
> Đây là giới hạn THẬT của model 1.5B (ngữ nghĩa + ranh giới quyết định), không
> phải lỗi cú pháp. Hướng vá tiếp KHÔNG phải grammar: model lớn hơn, few-shot
> theo enum-paraphrase, hoặc tách bước "có nên gọi tool" khỏi "điền tham số".

## Chạy

```bash
HARD=experiments/06_gym_env_hard/scenarios
# baseline free-form
ssh dgx "cd fci_voice_agent && FCI_SCEN_DIR=$HARD FCI_POLICY=llm  uv run python experiments/05_gym_env_text_smoke/run_gym_text.py"
# structured decoding
ssh dgx "cd fci_voice_agent && FCI_SCEN_DIR=$HARD FCI_POLICY=xgrammar uv run python experiments/05_gym_env_text_smoke/run_gym_text.py"
# + think-then-constrain
ssh dgx "cd fci_voice_agent && FCI_SCEN_DIR=$HARD FCI_POLICY=xgrammar FCI_REASONING=1 uv run python ..."
```

Cài deps DGX: `uv sync --extra exp03 --extra exp06` (xgrammar có wheel aarch64).
