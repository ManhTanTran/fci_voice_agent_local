# 01 — Survey: Hiện trạng, scope & đề bài Voice AI Agent

Layer khảo sát đầu tiên. Mục đích: chốt **bài toán thật**, **phạm vi**, và **khoảng cách so với mục tiêu** — trước khi khoan sâu kỹ thuật ở các layer sau.

Nguồn: 2 tài liệu nội bộ FCI trong [`../../_source/`](../../_source/README.md).

---

## Glossary (đọc trước)

- **Voice AI Agent** — trợ lý hội thoại bằng giọng nói, hoạt động trên kênh tổng đài điện thoại.
- **ASR** (Automatic Speech Recognition) — nhận dạng giọng nói → văn bản.
- **TTS** (Text-to-Speech) — tổng hợp văn bản → giọng nói.
- **VAD** (Voice Activity Detection) — phát hiện có tiếng nói hay không (lớp tín hiệu).
- **Barge-in / Turn Interruption** — user chen ngang khi bot đang nói; hệ thống cần biết có nên dừng TTS không.
- **Backchannel** — tiếng đệm xác nhận ("ừ", "ờ", "dạ") — KHÔNG phải ý định ngắt lời.
- **Orchestrator** — thành phần điều phối trung tâm, quyết định hướng xử lý hội thoại.
- **Rails / Guardrails** — lớp kiểm soát an toàn đầu vào (input rails) và đầu ra (output rails).
- **CCU** (Concurrent Users) — số phiên đồng thời; mốc đo mục tiêu là CCU=100.
- **TTFT / TTFS** — Time To First Token / Time To First Sentence (chỉ số độ trễ sinh phản hồi).

---

## 1. Hiện trạng tổ chức

- FCI (**FPT Smart Cloud**) có hạ tầng GPU lớn (~3000 GPU NVIDIA), đẩy mạnh **bán dịch vụ agent**: voice-bot tổng đài (đang vận hành) → video-bot cam giám sát (đang phát triển).
- Team là **team research**, vừa onboard; người cũ **chưa có mindset product** → chưa giao tiếp mạch lạc với team product FCI để nắm hạ tầng/code/data thật.
- **Hệ quả:** giai đoạn này chủ động **khảo sát thị trường + paper + open-source**, lấy 2 doc nội bộ làm tham chiếu lõi, để sau đối thoại được với team product bằng ngôn ngữ kỹ thuật chung.

## 2. Đề bài (theo định nghĩa của FCI)

**Intuition lõi:** tạo thế hệ voice-bot **giao tiếp tự nhiên, thân thiện hơn**.

"Tự nhiên" được định lượng thành các chức năng cụ thể:

- **Môi trường:** kênh tổng đài điện thoại — đường truyền **8kHz**, có nhiễu/ồn nền.
- **Nghe có chọn lọc, có chú ý:** trong môi trường nhiễu vẫn **duy trì được mục tiêu hội thoại**.
- **Phản hồi tự nhiên:**
  - **Dừng lại** khi user ngắt lời (barge-in).
  - **Hỏi lại** nếu nghe chưa rõ.
  - **Duy trì hướng mục tiêu** — không bị nhiễu dẫn nội dung lan man.
- **Hội thoại hướng mục tiêu:** làm rõ issue → giải quyết issue → đóng hội thoại; không bias theo nhiễu hoặc context.

## 3. Hai tài liệu nội bộ — vai trò

| Doc | Trả lời câu hỏi | Đầu ra chính |
|-----|-----------------|--------------|
| **01 — Kiến trúc hệ thống** | Hệ thống gồm những lớp nào, ghép ra sao? | 4 lớp xử lý (tiếp nhận → agent lõi → bổ trợ tool → kiểm soát ra) — xem [`02_architecture/`](../02_architecture/00_README.md) |
| **02 — Xây dựng LLM** | Cần huấn luyện/đo LLM cho tác vụ nào, đạt ngưỡng nào? | 2 tác vụ LLM (Agent + Turn Interruption) + metric + benchmark |

Hai doc là **hai góc nhìn của cùng một pipeline**: doc 01 mô tả *kiến trúc tĩnh*, doc 02 mô tả *thành phần học máy + tiêu chí nghiệm thu*.

## 4. Tiêu chí nghiệm thu & khoảng cách hiện tại (từ doc 02)

Benchmark hiện đo ở **CCU=5**; mục tiêu đặt ở **CCU=100**.

### 4.1 LLM Agent (hội thoại + tool calling)

| Metric | Mục tiêu (CCU=100) | gemma-3-27b-it | gpt-oss-120b | Qwen-3.5-35B-A3B |
|--------|--------------------|----------------|--------------|------------------|
| Mean TTFT | ≤ 800ms | ~700ms | ~1400ms | **~500ms** |
| P95 TTFT | ≤ 1200ms | ~1800ms | ~5000ms | **~1200ms** |
| Mean TTFS | ≤ 1200ms | ~900ms | ~6000ms | **~1000ms** |
| P95 TTFS | ≤ 2400ms | ~2300ms | ~10000ms | **~2100ms** |
| Prompt Compliance | ≥ 90% | 81.17% | 83.96% | **94.91% ✅** |
| Tool Calling | ≥ 90% | 53.09% | 52.14% | **61.79% ❌** |

### 4.2 Turn Interruption (binary INTERRUPT/CONTINUE)

| Metric | Mục tiêu (CCU=100) | Qwen-2.5-7B-Instruct |
|--------|--------------------|----------------------|
| Latency | ≤ 150ms | ~280ms ❌ |
| Accuracy | ≥ 85% | 76% ❌ |

## 5. Khoảng cách lớn nhất (định hướng nơi research có giá trị)

1. **Tool Calling accuracy** — tốt nhất mới **61.79%**, còn xa **90%**. Khoảng cách ~28 điểm.
2. **Turn Interruption** — fail **cả hai** chiều: accuracy 76% (cần 85%) **và** latency 280ms (cần 150ms). Đây là thứ quyết định trực tiếp cảm giác "tự nhiên".
3. **Khoảng trống chưa đo: ASR ở 8kHz + nhiễu tổng đài.** Doc 02 mới benchmark LLM, **chưa** đo robustness ASR trong điều kiện thật — dù đề bài nhấn mạnh môi trường 8kHz/nhiễu. Đây có thể là điểm mù lớn, nối thẳng với lab `nvidia_asr_nemo`.

> Điểm tích cực: latency TTFT và Prompt Compliance của Qwen-3.5-35B-A3B **đã đạt**. Tức kiến trúc + LLM nền không phải xây lại từ đầu; giá trị nằm ở **tinh chỉnh các bài toán con bị bỏ ngỏ**, đúng nhận định của team.

## 6. Scope đã chốt cho repo này

- **Trong scope:** khảo sát + định nghĩa bài toán con + đối chiếu SOTA/open-source + thiết kế multi-solution-stack + (khi có máy) thí nghiệm chọn lọc.
- **Ngoài scope (hiện tại):** dựng hệ thống production, tích hợp tổng đài thật, huấn luyện quy mô lớn (chờ GPU + nắm hạ tầng FCI).
- **Ủy thác sang lab khác:** huấn luyện model STT tiếng Việt → `nvidia_asr_nemo`.

---

## ✅ Tự kiểm nhanh

<details>
<summary>1. "Nghe có chọn lọc" trong đề bài được giải ở những thành phần nào?</summary>

Ở 2 chỗ: **Turn Interruption** (lúc bot đang nói — có nên dừng TTS không) và **Semantic Interruption Detection** (phân tích ngữ nghĩa câu nói để biết là backchannel hay ý định ngắt thật). Xem chi tiết ở layer 05.
</details>

<details>
<summary>2. Hai bài toán đang fail rõ nhất so với mục tiêu là gì?</summary>

(1) **Tool Calling** 61.79% vs mục tiêu 90%. (2) **Turn Interruption** 76% acc + 280ms, fail cả accuracy lẫn latency (mục tiêu 85% / 150ms).
</details>

<details>
<summary>3. Vì sao không gộp luôn vào repo nvidia_asr_nemo?</summary>

Vì ASR chỉ là **một lớp** của voice-agent; repo ASR đang có scope sạch (fine-tune STT có kết quả thật). Voice-agent rộng hơn nhiều (orchestrator, interruption, guardrail, TTS) → tách repo để không pha loãng, lớp ASR thì **trỏ sang** lab ASR.
</details>
