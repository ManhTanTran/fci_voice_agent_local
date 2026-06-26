# 02.01 — Đối Chiếu Hệ Thống FPT vs SOTA / Open-Source (Turn-Taking và Tool-Calling)

> [!NOTE]
> Tài liệu này tổng hợp kết quả khảo sát sâu rộng (21 nguồn tài liệu) đối chiếu kiến trúc 4 lớp nội bộ của FCI với các giải pháp công nghiệp dẫn đầu thị trường (SOTA) trong giai đoạn 2024-2026.
> Mục tiêu nhằm xác định các module bổ trợ khả thi để giải quyết triệt để hai điểm đau cốt lõi: Quản lý lượt lời (Turn Interruption) và Gọi hàm chính xác (Tool-calling).

---

## 1. Dẫn dắt bối cảnh

- **Xu thế phát triển của mô hình giọng nói**:
  - Sự xuất hiện của các mô hình Speech-to-Speech (S2S) tích hợp nghe-nói trực tiếp thời gian thực mở ra triển vọng cho các cuộc đàm thoại tự nhiên không độ trễ.
  - Các doanh nghiệp và đội ngũ phát triển tổng đài đứng trước sự lưỡng lự trong việc định hình kiến trúc hệ thống Voice Agent thế hệ mới.

- **Nghịch lý của tính năng doanh nghiệp**:
  - Tại sao mặc dù các mô hình S2S end-to-end cho độ trễ phản xạ cực kỳ ấn tượng, kiến trúc tách lớp truyền thống (Cascade ASR $\rightarrow$ LLM $\rightarrow$ TTS) vẫn đang là sự lựa chọn tối ưu và duy nhất đáp ứng được các ràng buộc an toàn giao dịch nghiêm ngặt của doanh nghiệp viễn thông tài chính?
  - Làm thế nào để giải quyết hai điểm đau nghiêm trọng của hệ cascade là độ trễ ngắt lời và tỷ lệ gọi hàm dựa trên các giải pháp open-source SOTA hiện nay?

- **Mục tiêu của tài liệu**:

  Tài liệu này sẽ phân tích ưu nhược điểm của hai trường phái kiến trúc Cascade và S2S, đặc tả hiệu năng của các dòng mô hình EOU nhỏ, và đề xuất lộ trình tích hợp tối ưu.

---

## 2. Glossary

Bảng Glossary dưới đây định nghĩa toàn bộ ký hiệu và thuật ngữ viết tắt xuất hiện trong bài:

| Ký hiệu / Thuật ngữ | Tên đầy đủ tiếng Anh                      | Giải nghĩa tiếng Việt                                                         |
| :------------------ | :---------------------------------------- | :---------------------------------------------------------------------------- |
| `S2S`               | **Speech-to-Speech**                      | Mô hình tích hợp xử lý âm thanh đầu vào sang âm thanh đầu ra trực tiếp.       |
| `ASR`               | **Automatic Speech Recognition**          | Nhận dạng giọng nói (Speech-to-Text).                                         |
| `TTS`               | **Text-to-Speech**                        | Tổng hợp giọng nói (Text-to-Speech).                                          |
| `LLM`               | **Large Language Model**                  | Mô hình ngôn ngữ lớn.                                                         |
| `VAD`               | **Voice Activity Detection**              | Bộ phát hiện hoạt động giọng nói (phân biệt khoảng lặng và tiếng nói).        |
| `EOU` / `EOT`       | **End-of-Utterance / End-of-Turn**        | Tín hiệu phát hiện điểm kết thúc lượt nói của người dùng.                     |
| `AST`               | **Abstract Syntax Tree**                  | Cây cú pháp trừu tượng (dùng để so khớp cấu trúc mã nguồn).                   |
| `BFCL`              | **Berkeley Function Calling Leaderboard** | Bảng xếp hạng năng lực gọi hàm của các mô hình ngôn ngữ.                      |
| `F1`                | **F1-Score**                              | Điểm trung bình điều hòa giữa Precision và Recall.                            |
| `RTF`               | **Real-Time Factor**                      | Chỉ số đo tốc độ xử lý âm thanh (RTF < 1.0 nghĩa là chạy kịp thời gian thực). |

---

## 3. S1 — So Sánh Kiến Trúc Cascade và Speech-to-Speech (S2S)

Bảng dưới đây đối chiếu hai trường phái kiến trúc dựa trên các tiêu chí vận hành tổng đài:

| Tiêu chí so sánh                       | Kiến trúc Cascade (ASR$\rightarrow$ LLM $\rightarrow$ TTS) | Kiến trúc S2S End-to-End                                    |
| :------------------------------------- | :--------------------------------------------------------- | :---------------------------------------------------------- |
| **Độ trễ (Latency)**                   | Cộng dồn qua từng chặng viễn thông.                        | Cực thấp (Bỏ qua các chặng dịch văn bản trung gian).        |
| **Kiểm soát nghiệp vụ & Tool-calling** | **Mạnh mẽ** (Dễ dàng can thiệp và chèn luật nghiệp vụ).    | Yếu (Logic tích hợp trực tiếp trong trọng số mô hình).      |
| **Bảo mật và Guardrails**              | **Dễ dàng tách lớp** (Can thiệp chốt chặn đầu vào/ra).     | Khó (Chưa có giải pháp kiểm soát an toàn đồng bộ triệt để). |
| **Quản lý lượt lời (Barge-in)**        | Đòi hỏi ghép nối các module VAD và turn-detector ngoài.    | Rất tốt (Tự động xử lý ở phía máy chủ của model).           |
| **Hỗ trợ tiếng Việt**                  | Phụ thuộc vào chất lượng mô hình ASR/TTS thành phần.       | ⚠️ Chưa có benchmark kiểm chứng hiệu năng thực tế.          |

- **Nhận định định hướng**:
  - Mô hình cascade phân lớp có guardrail tách biệt hiện tại vẫn là **kiến trúc chính thống** đáp ứng tốt nhất các yêu cầu nghiệp vụ doanh nghiệp.
  - S2S có tiềm năng lớn về độ trễ nhưng chưa giải quyết được bài toán an toàn thông tin (PII) và kiểm soát gọi hàm chính xác.

---

### 3.1 Sơ đồ dòng chảy tín hiệu: Cascade vs S2S

- **Kiến trúc S2S (Tích hợp một khối)**:
  ```mermaid
  graph TD
    AudioIn2["Audio 8kHz"] --> S2SModel["S2S Model (Black-box)"]
    S2SModel --> AudioOut2["Audio phản hồi"]
  ```

- **Kiến trúc Cascade (Phân lớp an toàn)**:

  ```mermaid
  graph TD
    AudioIn1["Audio 8kHz"] --> ASR1["ASR (STT)"]
    ASR1 --> GuardIn["Input Guardrail: Quét an toàn"]
    GuardIn --> LLM1["LLM Orchestrator: Gọi Tool & Logic"]
    LLM1 --> GuardOut["Output Guardrail: Lọc PII"]
    GuardOut --> TTS1["TTS (Synthesizer)"]
    TTS1 --> AudioOut1["Audio phản hồi"]
  ```

#### Khung đọc sơ đồ kiến trúc:

- **Đề bài cần giải**: So sánh cấu trúc dòng chảy tín hiệu và các chốt chặn an toàn giữa hai kiến trúc Cascade và S2S.
- **Giả định nền**: Cả hai hệ thống đều nhận luồng âm thanh đầu vào 8kHz thời gian thực.
- **Ý nghĩa các khối**:
  - `GuardIn` / `GuardOut`: Các middleware kiểm soát an toàn đồng bộ chỉ có ở kiến trúc Cascade.
  - `S2SModel`: Mô hình học sâu duy nhất xử lý tích hợp đầu-cuối.
- **Cách đọc và ứng dụng**: Hai sơ đồ được trình bày tách biệt; sơ đồ S2S tinh gọn theo chiều ngang cho thấy tính trực tiếp, trong khi sơ đồ Cascade đi theo chiều dọc thể hiện rõ các chốt chặn trung gian giúp kiểm soát nghiệp vụ an toàn.

---

## 4. S2 — Landscape Các Giải Pháp Quản Lý Lượt Lời (Turn-Taking)

Các tiến bộ công nghệ SOTA trong giai đoạn 2024-2026 tập trung giải quyết điểm nghẽn độ trễ phản xạ ngắt lời bằng các mô hình nhỏ:

| Tên giải pháp                       | Tín hiệu đầu vào     | Cơ chế cốt lõi                                             | Thời gian xử lý (Inference) | Môi trường chạy | Bản quyền                 |
| :---------------------------------- | :------------------- | :--------------------------------------------------------- | :-------------------------- | :-------------- | :------------------------ |
| **LiveKit Turn-Detector**           | Văn bản (Transcript) | Phân loại EOU ngữ nghĩa sử dụng mô hình Qwen2.5-0.5B.      | ⚠️ Chưa công bố             | CPU             | Custom License (Hạn chế). |
| **LiveKit Adaptive**                | Sóng âm (Waveform)   | Phân loại CNN phân biệt chen ngang thật và tiếng đệm.      | ~30ms                       | Cloud-only      | Bản thương mại có phí.    |
| **Pipecat Smart Turn v3**           | Sóng âm (Waveform)   | Phân tích ngữ điệu prosody bằng mô hình Whisper-tiny 8M.   | **12ms - 95ms**             | CPU             | BSD-2-Clause.             |
| **VAP (Voice Activity Projection)** | Sóng âm (Waveform)   | Dự đoán hoạt động âm thanh tương lai trên 2 kênh liên tục. | ~14.6ms                     | CPU-only        | MIT License.              |
| **EOT Classifier nhỏ**              | Văn bản (Transcript) | Mô hình Transformer nhỏ (Qwen3-0.6B) phân loại ngữ nghĩa.  | ~90ms - 110ms               | CPU             | Tùy thuộc base model.     |

- **Tiến bộ vượt trội so với VAD truyền thống**:
  - VAD năng lượng truyền thống sử dụng các ngưỡng im lặng cứng (ví dụ: timeout = 300ms) thường gây ra trễ phản xạ lớn hoặc ngắt lời sai khi người dùng ngập ngừng.
  - Các giải pháp SOTA sử dụng mô hình nhỏ (0.5B - 1B) chạy trực tiếp trên CPU giúp đưa thời gian phản xạ xuống mức **12ms - 110ms** với độ chính xác ngữ nghĩa cao.

---

## 5. S3 — Đối Chiếu Thực Tế và Hai Pain-Point Của Dự Án

### 5.1 Pain-Point #1: Độ trễ ngắt lời (Turn Interruption - 76% Accuracy / 280ms Latency)

- **Khoảng cách công nghệ**:
  - Hệ thống nội bộ đang sử dụng mô hình LLM 7B-binary để quyết định ngắt lời $\rightarrow$ Trễ quá lớn (280ms so với mục tiêu $\le$ 150ms) và độ chính xác thấp (76% so với mục tiêu $\ge$ 85%).
  - Open-source đã đi xa hơn với các mô hình nhỏ chạy trên waveform thô không phụ thuộc vào kết quả ASR (như Smart Turn hoặc VAP).
- **Lộ trình cải tiến**:
  - Thay thế mô hình LLM-7B bằng mô hình **semantic turn-detector nhỏ chạy CPU kết hợp hybrid VAD** (theo hướng thiết kế của LiveKit).

### 5.2 Pain-Point #2: Độ chính xác gọi hàm (Tool-Calling - 61.79% so với mục tiêu $\ge$ 90%)

- **Phạm vi tác động của Constrained Decoding (XGrammar)**:
  - Giúp cải thiện tỷ lệ định dạng JSON chính xác lên mức tiệm cận 100%. Tuy nhiên, nó chỉ giải quyết được lỗi định dạng (format), hoàn toàn không thể cứu được lỗi logic chọn sai tool hoặc điền sai tham số.
  - Phần lớn khoảng cách thiếu hụt 28% độ chính xác nằm ở năng lực ngữ nghĩa (prompt, mô hình, dữ liệu huấn luyện).
- **Lộ trình cải tiến**:
  - Tích hợp công cụ đo lường **BFCL V4 harness** sử dụng cơ chế so khớp cây cú pháp (AST matching).
  - Sử dụng BFCL để đo lường phân tách chính xác tỷ lệ lỗi định dạng và lỗi logic, làm cơ sở lựa chọn giải pháp tối ưu.

---

## 6. Lộ Trình Tích Hợp Module Bổ Trợ Đề Xuất

Lộ trình được sắp xếp theo thứ tự ưu tiên dựa trên tỷ lệ: Khả thi $\times$ Hiệu quả $\times$ Chi phí:

```
Ưu tiên 1: Tích hợp BFCL V4 Harness (Đo lường phân tách lỗi)
  │
  ├──► Ưu tiên 2: Triển khai Semantic Turn-Detector nhỏ (Thay thế LLM 7B)
  │      │
  │      └──► Ưu tiên 3: Tích hợp Constrained Decoding XGrammar (Vá lỗi format JSON)
```

- **Ưu tiên 1 — Triển khai BFCL V4 Harness (Đo lường phân tách lỗi)**:
  - _Đánh giá_: Khả thi rất cao (sử dụng thư viện sẵn có), hiệu quả cao để phá bỏ điểm mù, chi phí rất thấp.
  - _Hành động_: Chạy thử nghiệm BFCL trên tập dữ liệu gọi hàm nội bộ để xác định tỷ lệ lỗi format thực tế trước khi cấu hình XGrammar.

- **Ưu tiên 2 — Triển khai Semantic Turn-Detector nhỏ chạy CPU (Vá điểm đau Turn Interruption)**:
  - _Đánh giá_: Khả thi cao, hiệu quả cực kỳ lớn (giải quyết trực tiếp độ trễ phản xạ), chi phí thấp.
  - _Hạn chế rủi ro_: Hầu hết các mô hình open-source mạnh (LiveKit, VAP) không hỗ trợ tiếng Việt. Chỉ có **Smart Turn v3** hỗ trợ tiếng Việt (`✅ vi`) với độ chính xác 81.27% đo trên dải 16kHz sạch. Cần thực hiện kiểm thử độc lập và fine-tune trên dữ liệu tổng đài 8kHz nội bộ trước khi đưa vào sản xuất.

- **Ưu tiên 3 — Tích hợp Constrained Decoding XGrammar (Tối ưu hóa định dạng JSON)**:
  - _Đánh giá_: Khả thi cao (backend serving của vLLM đã tích hợp sẵn), hiệu quả trung bình (chỉ vá lỗi cú pháp JSON), chi phí thấp.
  - _Hành động_: Tích hợp sau khi có kết quả phân tách lỗi từ Ưu tiên 1.

---

## 7. ✅ Tự Kiểm Nhanh

<details>
<summary><b>Câu hỏi 1: Tại sao việc ứng dụng mô hình semantic turn-detector chạy trên dạng sóng thô (waveform-based) lại vượt trội hơn mô hình chạy trên văn bản (text-based) đối với tổng đài điện thoại?</b></summary>

- **Bản chất kỹ thuật**:
  - Mô hình dựa trên văn bản (text-based) bắt buộc phải chờ luồng âm thanh đi qua bộ giải mã ASR để có văn bản transcript mới tiến hành phân tích ngữ nghĩa câu thoại $\rightarrow$ Thời gian phản xạ bị cộng thêm toàn bộ độ trễ của ASR.
  - Mô hình dựa trên dạng sóng thô (waveform-based) phân tích trực tiếp các đặc trưng phi ngôn từ (ngữ điệu prosody, cao độ, nhịp điệu) ngay trên luồng âm thanh đầu vào, chạy song song với ASR và đưa ra quyết định hết lượt nói chỉ trong vòng **12ms - 60ms** từ CPU, đáp ứng hoàn hảo ngân sách latency $\le$ 150ms của kênh thoại tổng đài.

</details>

<details>
<summary><b>Câu hỏi 2: Tại sao kết luận "XGrammar có độ trễ (overhead) end-to-end gần bằng 0" lại bị bác bỏ trong các thử nghiệm thực tế?</b></summary>

- **Nguyên nhân kỹ thuật**:
  - Ở quy mô cuộc gọi lớn (CCU = 100), công nghệ serving (như vLLM) phải xử lý đồng thời nhiều luồng giải mã (batch size lớn).
  - Việc áp dụng các mặt nạ token (token masking) của FSM/CFG cho mỗi bước sinh của từng luồng tiêu tốn năng lượng tính toán đáng kể của CPU, làm giảm thông lượng (throughput) tổng thể của GPU phục vụ giải mã.
  - Ngoài ra, ở lần đầu tiên gặp một JSON schema mới, hệ thống mất từ 50ms đến 200ms để biên dịch đồ thị trạng thái FSM trước khi đưa vào bộ nhớ đệm cache. Do đó, overhead là có tồn tại và cần được đo lường thực tế dưới tải trọng cao.

</details>
