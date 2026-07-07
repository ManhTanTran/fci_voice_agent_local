# 00 — INDEX tài liệu fci_voice_agent

Điểm vào toàn bộ tài liệu khảo sát. Đọc theo thứ tự số. Làm việc *layer by layer*.

Thứ tự layer bám theo **đường đi của tín hiệu**: âm thanh thô → ngữ nghĩa → agent → an toàn → đo lường.

| # | Thư mục | Nội dung | Trạng thái |
|---|---------|----------|-----------|
| 01 | [`01_survey/`](01_survey/00_README.md) | Hiện trạng FCI + tổng hợp 2 doc nội bộ + chốt scope + đề bài + khoảng cách benchmark | 🟢 v1 |
| 02 | [`02_architecture/`](02_architecture/00_README.md) | Mổ kiến trúc 4 lớp nội bộ + bản đồ multi-solution-stack + [**so sánh FPT-vs-SOTA**](02_architecture/01_fpt_vs_sota.md) (deep-research, có citation) + [**Pipecat**](02_architecture/02_pipecat_reference_architecture.md)/[**LiveKit**](02_architecture/03_livekit_reference_architecture.md) (voice pipeline, Layer A) + [**LangGraph**](02_architecture/05_langgraph_reference_architecture.md) (bộ não agent = Layer 2-3, 7 axis, map FCI↔LangGraph) | 🟢 v2 |
| 03 | [`03_audio_frontend/`](03_audio_frontend/00_README.md) | **TAXONOMY nhiễu phân tầng (A acoustic / B codec-telephony / C người nói) + quy trình EDA/gắn nhãn (Brouhaha+PANNs+CLAP)** + bằng chứng tiếng Việt | 🟢 v2 (23 claim verified 3-0, 2 bị bác) |
| 04 | [`04_asr_telephony/`](04_asr_telephony/00_README.md) | ASR môi trường 8kHz/nhiễu (robust + streaming + confidence) — nối lab `nvidia_asr_nemo` + [**04.01 Confidence → hỏi lại/xác minh**](04_asr_telephony/01_confidence_clarification.md) (nhãn nhiễu runtime · calibration · máy trạng thái 3 vùng gắn FSM node) | 🟢 v1 (chưa verify 3-vote) |
| 05 | [`05_turn_interruption/`](05_turn_interruption/00_README.md) | **Quản lý lượt lời (turn-taking)**: turn-detection/endpointing (EOU) · barge-in & semantic interruption · backchannel — **bài đau #1** ở nhánh interruption (76% / 280ms) + đào sâu 3 bài con: [**05.05 target-speaker isolation**](05_turn_interruption/05_target_speaker_isolation.md) · [**05.06 EOU endpointing**](05_turn_interruption/06_eou_endpointing.md) · [**05.07 barge-in 2 pha + lớp echo**](05_turn_interruption/07_bargein_decision.md) | 🟢 v1 (chưa verify 3-vote) |
| 06 | [`06_llm_agent/`](06_llm_agent/00_README.md) | Tool-calling **bài đau #2** (62% vs 90%) + [**06.01 Orchestration & State**](06_llm_agent/01_orchestration_state.md) + [**06.02 Tool-call: tham số/state/goal**](06_llm_agent/02_tool_call_grounding.md) + [**06.03 Ba tầng chất lượng tool-call**](06_llm_agent/03_tool_calling_stages.md) (quyết-gọi/chọn-hàm · cú-pháp/tham-số · giá-trị) + [**06.04 Framework/lib hiện thực**](06_llm_agent/04_tool_call_frameworks.md) (constrained decoding · structured-output lib · agent framework) + [**06.05 Ba domain CSKH**](06_llm_agent/05_cskh_domains.md) (booking · customer-care · đòi nợ: kiến trúc mục tiêu + dữ liệu cần chuẩn bị + guardrail) + [**06.06 Lõi tri thức pháp luật tài chính**](06_llm_agent/06_financial_law_knowledge.md) (pháp lý grounding RAG/KG + tính toán bằng tool deterministic) | 🟢 v1 (chưa verify 3-vote) |
| 07 | [`07_guardrails/`](07_guardrails/00_README.md) | Input rails (prompt injection, moderation) + PII + Output rail + Text-Norm | 🟢 v1 (chưa verify 3-vote) |
| 08 | [`08_datasets/`](08_datasets/00_README.md) | `voice_agent_trace_samples` + `turn_interruption_test` + dataset thoại VN + hạ tầng dữ liệu: [**08.01 EDA 3 lớp**](08_datasets/01_eda_methodology.md) (audio → transcript → log, bảng utterance-level) · [**08.02 sim→real data**](08_datasets/02_sim_to_real_data.md) (codec-chain 8kHz · barge-in có nhãn miễn phí) · [**08.03 training recipes**](08_datasets/03_training_recipes.md) (đặc thù training 7 loại model) | 🟡 phương pháp 🟢 v1, data thật ⬜ |
| 09 | [`09_benchmarks/`](09_benchmarks/00_README.md) | Đo lại metric + mục tiêu CCU=100 (latency + quality) | ⬜ chưa |
| 10 | [`10_implementation/`](10_implementation/00_README.md) | **TRIỂN KHAI (thông luồng pipecat trên DGX):** [tổng kết kiến trúc as-built](10_implementation/01_architecture.md) + [report thông luồng exp01→04](10_implementation/02_e2e_report.md) (sơ đồ pipeline + latency từng step) | 🟢 full loop English chạy thật |
| 11 | [`11_sim_test_system/`](11_sim_test_system/00_README.md) | **HỆ THỐNG GIẢ LẬP + TEST module** (sim sinh hội thoại có nhãn để auto-test turn-detection + tool-calling): [thiết kế](11_sim_test_system/01_design.md). Tri thức nền + papers ở `.agent/skills/05_model_quality_engineering/` | 🟡 plan/khảo sát |
| 12 | [`12_presentation/`](12_presentation/00_deck_voice_agent.md) | **DECK TRÌNH BÀY team + FCI** (tổng thể → component → challenge): 11 topic, mỗi topic 1 sơ đồ + 1 bảng chú giải; dùng để thảo luận và **hiệu chỉnh lại thông tin hệ FCI** | 🟢 v1 |
| 13 | [`13_delivery_plan/`](13_delivery_plan/00_overview.md) | **KẾ HOẠCH DELIVERY** (roadmap 4 pha + cổng nghiệm thu): [request gửi FCI](13_delivery_plan/01_fci_info_requests.md) + [shortlist model/dataset](13_delivery_plan/02_priority_shortlist.md) + [lộ trình data English-first→VN](13_delivery_plan/03_data_generation_plan.md) | 🟢 v1 |
| 14 | [`14_turn_detection_delivery/`](14_turn_detection_delivery/00_overview.md) | **DELIVERY TURN-DETECTION tách riêng** (bàn giao sang phiên khác, KHÔNG tool-calling): [luồng infer 2 kênh khách/bot](14_turn_detection_delivery/01_inference_flow_two_channel.md) + [dataset public](14_turn_detection_delivery/02_public_datasets.md) + [bài con + model thử tuần tự](14_turn_detection_delivery/03_subproblems_and_models.md) + [cách review + cổng nghiệm thu](14_turn_detection_delivery/04_review_and_acceptance.md) | 🟢 v1 |

> Layer 01–09 = khảo sát theo đường đi tín hiệu; **layer 10 = thông luồng pipecat**, **layer 11 = hệ giả-lập+test** (trục triển khai: code + exp trên DGX).
>
> Quy ước trạng thái: 🟢 có nội dung thật · 🟡 đang khảo sát / chưa kiểm chứng đủ · ⬜ mới có stub scope.

### 🧭 Chuẩn hoá tên bài toán con (đọc trước khi dùng layer 05)

Tên doc nội bộ ("Turn Interruption") dễ gây hiểu hẹp. Tên **tổng quát đúng** là **quản lý lượt lời (turn-taking)**; "turn-interruption" (barge-in — user chen ngang lúc bot đang nói) chỉ là **một nhánh con**, dù là nhánh xuất hiện nhiều và đau nhất. Layer 05 phủ đủ 3 bài con:

1. **Turn-detection / endpointing (EOU)** — biết khi nào user nói *xong* để bot trả lời; phiên bản dùng ngữ nghĩa = **semantic turn detection**.
2. **Barge-in / interruption** — xử lý khi user chen ngang lúc bot đang nói; bên trong có **semantic interruption** phân biệt backchannel ("ừ/ờ/dạ") vs ý định ngắt thật. *(Đây là chỗ doc nội bộ đo 76% / 280ms.)*
3. **Backchannel** — bot phát tín hiệu "đang nghe" đúng lúc.

Giữ tên thư mục `05_turn_interruption` (đã commit) nhưng phạm vi layer là **cả turn-taking**.

## 🎯 Trọng tâm tuần này (sprint hiện tại): ĐÀO RỘNG (trục A)

Mục tiêu: **vẽ đầy đủ bức tranh toàn cảnh** trước khi khoan sâu xây module. Cụ thể:

1. **Khảo sát paper** — SOTA voice-agent / barge-in / streaming ASR-LLM / tool-calling (2024-2026).
2. **Khảo sát open-source** — framework voice-agent realtime, guardrail, interruption.
3. **So sánh hệ thống FPT (4 lớp nội bộ) vs open-source mới nhất** — chỗ nào FPT đã có, chỗ nào lệch, chỗ nào open-source đi xa hơn.

Đầu ra tuần: bức tranh + bảng so sánh đủ chất để chịu phản biện kỹ thuật → **chọn 1 module để khoan sâu**.

Tiêu chí chọn module (hội tụ cả 3): **khả thi × hiệu quả (add-on lên hệ thống sẵn có) × chi phí (thời gian × nhân sự trong scope)**.

> Nhịp làm việc FPT: không rush; cho đủ thời gian khảo sát chất lượng. Leader 80% từ kỹ thuật, phản biện sâu → số liệu phải có nguồn, chỗ chưa chắc đánh dấu "chưa xác minh".

## Hai trục công việc

- **Trục A — Hiểu kiến trúc voice-agent (nội bộ + SOTA):** mổ 4 lớp trong doc nội bộ, đối chiếu hướng đi open-source / paper 2024-2026.
- **Trục B — Khai thác đặc thù tổng đài (8kHz, nhiễu, real-time):** phễu giảm tải audio (rule-based → micro model → ngữ nghĩa → LLM), tối ưu latency cho barge-in.

Hai trục gặp nhau ở: **định nghĩa các bài toán con đo được** → gom thành **hệ thống nhiều model phối hợp**.
