# 02.01 — Đối chiếu hệ thống FPT vs SOTA / open-source (S1+S2+S3)

Kết quả khảo sát rộng (deep-research, 21 nguồn → 25 claim kiểm chứng đối nghịch → 22 xác nhận / 3 bác). Mục đích: định vị kiến trúc 4 lớp nội bộ so với SOTA 2024-2026, tìm **module add-on khả thi** vá 2 điểm đau (turn-interruption, tool-calling).

> ⚠️ **Cách đọc:** mỗi claim quan trọng đều dẫn nguồn ở mục [§5 Nguồn](#5-nguồn-tổ-chức-theo-loại). Số liệu vendor (LiveKit/Daily blog) ghi rõ "(vendor)". Chỗ chưa chắc ghi "**chưa xác minh**". Latency của model turn-detection là **phần inference**, KHÔNG phải toàn vòng barge-in end-to-end.

---

## Glossary

- **Cascade** — kiến trúc ghép rời ASR → LLM → TTS (hệ nội bộ thuộc nhóm này).
- **Speech-to-speech (S2S) end-to-end** — model nghe-nói trực tiếp, không tách ASR/TTS (vd OpenAI Realtime, Gemini Live).
- **Turn-detection / EOU / EOT** — phát hiện hết-lượt-nói (End-of-Utterance / End-of-Turn).
- **Semantic turn-detection** — quyết định hết lượt dựa trên *nội dung/ngữ nghĩa* câu nói, khác **VAD năng-lượng** (chỉ đo có tiếng/im lặng).
- **Constrained / guided decoding** — ép LLM sinh output đúng một văn phạm/schema (vd JSON) ở mức token.
- **CFG** — context-free grammar. **AST** — abstract syntax tree.
- **BFCL** — Berkeley Function Calling Leaderboard (benchmark tool-calling).

---

## 1. S1 — Cascade vs Speech-to-speech (kiến trúc tổng thể)

Hai hướng kiến trúc, các framework hiện đại **hỗ trợ cả hai** (thay LLM bằng Realtime API):

| Trục | Cascade (ASR→LLM→TTS) | Speech-to-speech end-to-end |
|------|----------------------|------------------------------|
| Latency | Cộng dồn qua từng chặng | Thấp hơn (bỏ chặng trung gian) |
| Kiểm soát nghiệp vụ + tool-calling | **Mạnh** (dùng LLM frontier + chèn module) | Yếu hơn, khó kiểm soát |
| Guardrail / an toàn | **Dễ tách lớp** (rails riêng) | Khó (logic nằm trong model) |
| Barge-in / turn-taking | Cần ghép turn-detector + VAD | Tốt ở server-side (built-in) |
| Tiếng Việt | Tùy ASR/TTS thành phần | **Chưa xác minh** |

- **Hệ nội bộ 4 lớp = cascade có guardrail tách lớp** → đây là lựa chọn **chính thống**, không lạc hướng. Điểm mạnh cascade (kiểm soát nghiệp vụ + guardrail + dễ chèn module) đúng là thứ một voice-bot tổng đài cần.
- Đánh đổi: cascade cộng dồn latency → áp lực dồn vào từng module phải nhanh.
- Nguồn S1 ở mức kiến trúc; **chưa có benchmark head-to-head sống sót** đo trực tiếp guardrail/tool-calling/tiếng Việt của riêng realtime model → chưa kết luận S2S "thay được" cascade cho nghiệp vụ tổng đài.

## 2. S2 — Landscape open-source (turn-taking là điểm nóng)

Điểm quan trọng nhất: **turn-detection đã có lời giải open-source trưởng thành**, đi xa hơn VAD năng-lượng thuần.

| Giải pháp | Bản chất | Latency (inference) | Chạy ở đâu | Nguồn |
|-----------|----------|---------------------|-----------|-------|
| **LiveKit turn-detector** | semantic EOU, fine-tune **Qwen2.5-0.5B**, chạy trên **transcript text**, hybrid với Silero VAD | — | CPU khả thi | [a4][b2][c1] |
| **LiveKit adaptive interruption** | phân biệt interrupt thật vs backchannel, truncate history tới phần user đã nghe | ~30ms; **86%P/100%R** @500ms (vendor) | **chỉ full trên Cloud**, self-host giới hạn quota | [b5][b6] |
| **Pipecat Smart Turn v3** | semantic turn (Whisper-tiny ~8M trên **waveform** bắt prosody) | ~12ms (c7a) → 65ms (phổ biến) → 94.8ms (t3.medium) | CPU | [c2][b7] |
| **VAP (Voice Activity Projection)** | dự đoán voice-activity tương lai **cả 2 kênh** liên tục (không nhị phân) | ~14.6ms/frame, RTF<1.0 | **CPU-only** | [a1][c3] |
| **Semantic EOT small model** | transformer nhỏ fine-tune, quyết định gần-tức-thời | Qwen3-0.6B 0.866 F1 @90ms; Typhoon2-1B @110ms (CPU server) | CPU | [a2] |

- **LiveKit** = framework đầy đủ nhất cho cascade: 5 chế độ turn-detection (turn-detector model / realtime / VAD-only / STT-endpointing / manual), hybrid VAD + semantic.
- **NeMo Guardrails** [a4-guard][c4]: toolkit rail lập trình được, tách rời LLM, 5 loại rail (input / dialog / retrieval / execution / output) — **input/output rails khớp gần 1-1** với 2 lớp guardrail nội bộ.

## 3. S3 — Đối chiếu trực tiếp & 2 điểm đau

### 3.1 Turn-interruption (đau #1: 76% / 280ms)

- **Open-source ĐÃ ĐI XA HƠN.** Hệ nội bộ hiện giải bằng LLM 7B (76%/280ms) — chậm và chưa chính xác. SOTA open-source dùng **semantic turn-detection model nhỏ (0.5B-1B) chạy CPU** với inference 12-110ms. Energy-based end-pointer truyền thống cộng *hàng trăm ms* và fail khi người nói ngập ngừng → đúng lý do khó đạt ≤150ms.
- **Hướng vá:** thay LLM-7B-binary bằng **semantic turn-detector nhỏ + hybrid VAD** (mô hình LiveKit). Vừa giảm latency, vừa tăng accuracy.

### 3.2 Tool-calling (đau #2: 62% → cần ≥90%)

- **Constrained decoding (XGrammar)** [a3][b8][c5] ép output đúng JSON schema/CFG, là default backend của vLLM/SGLang/TensorRT-LLM. Một nguồn đo: không guided decoding correctness **không vượt 72%**, có guided decoding đạt 100% trên schema lặp lại [d4].
- **⚠️ Giới hạn then chốt:** constrained decoding chỉ guarantee **HỢP LỆ ĐỊNH DẠNG**, KHÔNG fix lỗi *chọn sai tool* hay *sai giá trị tham số*. Phần lớn khoảng cách 62%→90% có thể nằm ở lớp ngữ nghĩa (prompt/model/few-shot). Claim "XGrammar overhead end-to-end gần 0" đã **bị bác** (3 phiếu refute).
- **Cách đo:** **BFCL V4** [b-bfcl][a-bfcl] dùng AST matching, hỗ trợ cả native lẫn **prompt-based** function-calling — đúng kiểu "simulated tool-calling" của hệ nội bộ → là công cụ chuẩn để đo 62%→90% và **phân tách** lỗi format vs lỗi chọn-tool.

### 3.3 Chỗ cách tiếp cận nội bộ hợp lý / độc đáo

- **Simulated tool-calling** (fake `what_should_I_do_next`) là nhánh prompt-based — không lạ, BFCL đo được nhánh này. Hợp lý cho việc bám step.
- **Rails tách lớp** trùng hướng với NeMo Guardrails (kiến trúc chính thống). Lưu ý: tác giả NeMo nói rails **không nên dùng stand-alone** cho safety, nên bổ trợ thêm model alignment.

## 4. Kết luận — 3 module add-on ưu tiên (khả thi × hiệu quả × chi phí)

| Ưu tiên | Module | Khả thi | Hiệu quả | Chi phí | Rủi ro chính |
|---------|--------|---------|----------|---------|--------------|
| **1** | **Semantic turn-detector** thay LLM-binary (layer 05) | Cao — model nhỏ CPU, open-source sẵn | Cao — vá thẳng đau #1 (latency + acc) | Thấp | **Tiếng Việt chưa xác minh** → cần kiểm/fine-tune |
| **2** | **BFCL V4 harness** đo tool-calling | Cao — pip cài, reproducible | Trung bình — không phải sản phẩm, là thước đo để phân tách nguyên nhân | Rất thấp | — |
| **3** | **Constrained decoding (XGrammar)** cho tool-calling (layer 06) | Cao — backend serving có sẵn | Trung bình — chỉ vá lỗi format, không vá chọn-sai-tool | Thấp | Dễ kỳ vọng quá mức; cần (2) trước để biết bao nhiêu lỗi là format |

> Thứ tự đề xuất: làm **(2) BFCL harness** trước để biết bao nhiêu % lỗi tool-calling là do format → mới quyết (3) XGrammar có đáng không. Module **(1) semantic turn-detector** là ứng viên giá trị nhất nhưng phải giải bài toán tiếng Việt trước.

## 4b. Câu hỏi mở then chốt (cần giải trước khi cam kết)

1. **Tiếng Việt** (rủi ro lớn nhất): LiveKit turn-detector / Smart Turn / VAP có hỗ trợ `vi` production không? Bằng chứng semantic EOT hiện là **tiếng Thái** (suy luận sang SEA, **chưa xác minh** cho Việt).
2. **Full-loop latency**: các số 12-110ms chỉ là inference đơn lẻ — cần đo trọn vòng barge-in (VAD trigger + buffer + inference + TTS-stop) ở CCU=100.
3. **Phân tách lỗi tool-calling**: bao nhiêu % do format (XGrammar fix được) vs chọn-sai-tool (cần prompt/model)? → chạy BFCL prompt-mode.
4. **S2S head-to-head**: realtime model kiểm soát nghiệp vụ/guardrail/tiếng Việt tới đâu so với cascade — chưa có số sống sót.

---

## 5. Nguồn (tổ chức theo loại — tự kiểm chứng được)

### (a) Paper arXiv / hội nghị

| ID | Link | Chứng minh điều gì |
|----|------|--------------------|
| a1 | https://arxiv.org/abs/2401.04868 | VAP (IWSDS 2024) — turn-taking liên tục 2 kênh, chạy realtime **CPU-only** (RTF<1.0) |
| a2 | https://arxiv.org/abs/2510.04016 | Semantic EOT small model ~90-110ms CPU; energy end-pointer cộng *hàng trăm ms* (baseline **tiếng Thái**) |
| a3 | https://arxiv.org/pdf/2411.15100 | XGrammar (MLSys 2025) — constrained decoding CFG/JSON, tăng tốc tới ~100x |
| a-guard | https://arxiv.org/abs/2310.10501 | NeMo Guardrails (EMNLP 2023) — rails lập trình được, tách rời LLM |
| a-bfcl | https://proceedings.mlr.press/v267/patil25a.html | BFCL (ICML 2025) — AST matching là method lõi |
| a-vn1 | https://arxiv.org/abs/2603.01894 | VietSuperSpeech — dataset hội thoại tiếng Việt kiểu call-center (lead cho layer 04) |
| a-vn2 | https://arxiv.org/html/2508.04721v1 | Nguồn angle ASR/TTS telephony tiếng Việt (cần đọc kỹ ở layer 04) |
| a-easyturn | arXiv 2509.23938 (EASY TURN) | Phê phán linear-classifier khó bắt semantic phong phú (đối trọng Smart Turn) — **chưa fetch trực tiếp** |

### (b) Doc / blog chính thức của framework

| ID | Link | Chứng minh điều gì |
|----|------|--------------------|
| b2 | https://docs.livekit.io/agents/build/turns/ | 5 chế độ turn-detection; hybrid VAD + semantic |
| b3 | https://docs.livekit.io/agents/models/realtime/ | Hỗ trợ realtime model (S2S) |
| b4 | https://docs.livekit.io/agents/start/voice-ai/ | Hỗ trợ cả cascade lẫn realtime, unified interface |
| b5 | https://docs.livekit.io/agents/logic/turns/adaptive-interruption-handling/ | Phân biệt interrupt vs backchannel, truncate history |
| b6 | https://livekit.com/blog/adaptive-interruption-handling | 86%P/100%R, ~30ms (**vendor**, 19/03/2026) |
| b-eot | https://livekit.com/blog/solving-end-of-turn-detection | Giải thích turn-detector (**vendor**) |
| b7 | https://www.daily.co/blog/announcing-smart-turn-v3-with-cpu-inference-in-just-12ms/ | Smart Turn v3 latency 12-95ms (**vendor**) |
| b-st2 | https://www.daily.co/blog/smart-turn-v2-faster-inference-and-13-new-languages-for-voice-ai/ | Smart Turn v2 (**vendor**) |
| b8 | https://blog.mlc.ai/2024/11/22/achieving-efficient-flexible-portable-structured-generation-with-xgrammar | XGrammar 3.5x JSON / 10x CFG |
| b-bfcl | https://gorilla.cs.berkeley.edu/leaderboard.html | BFCL: native vs prompt-based, AST, reproducible |
| b-oai | https://openai.com/index/introducing-gpt-realtime/ | gpt-realtime (S2S đại diện) |

### (c) Repo GitHub

| ID | Link | Chứng minh điều gì |
|----|------|--------------------|
| c1 | https://github.com/livekit/agents | Framework voice-agent cascade + realtime |
| c2 | https://github.com/pipecat-ai/smart-turn | Smart Turn — semantic turn trên waveform |
| c3 | https://github.com/inokoj/VAP-Realtime | VAP realtime CPU (repo chính chủ) |
| c4 | https://github.com/NVIDIA-NeMo/Guardrails | NeMo Guardrails — 5 loại rail |
| c5 | https://github.com/mlc-ai/xgrammar | XGrammar — thư viện constrained decoding |
| c6 | https://github.com/QwenLM/Qwen3-Omni | Qwen3-Omni (multimodal audio, lead S2S/tiếng Việt) |
| c-livekit-model | https://huggingface.co/livekit/turn-detector | Model card: fine-tune Qwen2.5-0.5B, chạy trên transcript text |

### (d) Blog / bài viết khác

| ID | Link | Chứng minh điều gì |
|----|------|--------------------|
| d1 | https://hamming.ai/blog/are-speech-to-speech-models-ready-to-replace-cascade-models | So sánh cascade vs S2S (điểm mạnh/yếu) |
| d2 | https://artificialanalysis.ai/speech-to-speech | Leaderboard S2S (secondary) |
| d3 | https://medium.com/@ggarciabernardo/realtime-ai-agents-frameworks-bb466ccb2a09 | Tổng quan framework realtime |
| d4 | https://blog.squeezebits.com/guided-decoding-performance-vllm-sglang | Không guided decoding correctness ≤72%, có thì đạt 100% schema lặp |

---

## ✅ Tự kiểm nhanh

<details>
<summary>1. Open-source đã đi xa hơn hệ nội bộ ở điểm đau nào, bằng cách nào?</summary>

Turn-interruption. Hệ nội bộ dùng LLM-7B-binary (76%/280ms); open-source dùng **semantic turn-detection model nhỏ 0.5-1B chạy CPU** (LiveKit turn-detector, Smart Turn, VAP) inference 12-110ms + hybrid VAD — nhanh hơn và chính xác hơn.
</details>

<details>
<summary>2. Vì sao constrained decoding KHÔNG đủ để đưa tool-calling lên 90%?</summary>

Vì nó chỉ đảm bảo output **đúng định dạng** (parse được JSON schema), không sửa lỗi *chọn sai tool* hay *sai tham số*. Phần ngữ nghĩa vẫn cần prompt/model tốt hơn. Phải đo BFCL V4 prompt-mode trước để biết bao nhiêu % lỗi là do format.
</details>

<details>
<summary>3. Rủi ro lớn nhất chưa giải quyết là gì?</summary>

**Tiếng Việt.** Không nguồn nào xác minh trực tiếp các module turn-detection hỗ trợ tiếng Việt production (claim Smart Turn hỗ trợ tiếng Việt đã bị bác). Bằng chứng semantic EOT là tiếng Thái, chỉ suy luận sang SEA.
</details>
