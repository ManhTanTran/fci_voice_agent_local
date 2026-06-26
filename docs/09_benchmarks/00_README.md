# 09 — Benchmarks: Chỉ Số và Quy Trình Đo Lường Hiệu Năng

> [!NOTE]
> Tài liệu này thiết lập khung chỉ số đánh giá (metrics suite) và quy trình kiểm thử hiệu năng (benchmarking) cho toàn bộ hệ thống voice-bot tổng đài, hướng tới tối ưu hóa hạ tầng dưới tải trọng lớn.

---

## 1. Dẫn dắt bối cảnh

- **Yêu cầu khắt khe của hệ thống thời gian thực**:
  - Đối với các ứng dụng thoại tự động trên mạng viễn thông, tốc độ phản hồi và độ chính xác của bot quyết định trực tiếp tới sự hài lòng của khách hàng.
  - Hệ thống cần phải hoạt động ổn định và giữ vững chất lượng ngay cả trong các khung giờ cao điểm có lượng người gọi đồng thời tăng vọt.

- **Nghịch lý của đo lường hiệu năng**:
  - Tại sao một mô hình vượt qua tất cả các bài kiểm tra tốc độ trong môi trường thử nghiệm đơn lẻ (CCU = 5) lại gặp hiện tượng nghẽn cổ chai và sụt giảm hiệu năng nghiêm trọng khi đưa vào môi trường sản xuất thực tế?
  - Làm thế nào để định lượng chính xác sự đánh đổi (trade-off) giữa chất lượng xử lý của mô hình học sâu và độ trễ chấp nhận được của luồng đàm thoại?

- **Mục tiêu của tài liệu**:
  
  Tài liệu này định nghĩa hệ chỉ số đo lường chuẩn hóa cho các thành phần (ASR, LLM, Turn-Taking) và thiết lập kịch bản thử nghiệm hướng tới mục tiêu chịu tải CCU = 100.

---

## 2. Glossary

Bảng Glossary dưới đây định nghĩa toàn bộ ký hiệu và thuật ngữ viết tắt xuất hiện trong bài:

| Ký hiệu / Thuật ngữ | Tên đầy đủ tiếng Anh | Giải nghĩa tiếng Việt |
| :--- | :--- | :--- |
| `CCU` | **Concurrent Users** | Số lượng cuộc gọi đồng thời chạy trong hệ thống. |
| `TTFT` | **Time to First Token** | Thời gian phản hồi ra token đầu tiên của mô hình ngôn ngữ (LLM). |
| `TTFS` | **Time to First Sound / Speech** | Thời gian tính từ lúc người dùng nói xong đến khi bot phát ra âm thanh đầu tiên. |
| `WER` | **Word Error Rate** | Tỷ lệ lỗi từ trong giải mã nhận dạng giọng nói. |
| `RTF` | **Real-Time Factor** | Chỉ số đo tốc độ xử lý âm thanh (RTF < 1.0 nghĩa là xử lý kịp thời gian thực). |
| `ASR` | **Automatic Speech Recognition** | Hệ thống tự động nhận dạng giọng nói. |
| `LLM` | **Large Language Model** | Mô hình ngôn ngữ lớn. |

---

## 3. Khung Chỉ Số Đo Lường Theo Thành Phần

Quy trình benchmark đo lường hiệu năng trên cả 3 tầng cốt lõi của kiến trúc:

- **Tầng LLM Agent (Bộ não điều phối)**:
  - **TTFT / TTFS**: Đo lường thời gian trung bình (Mean) và phân vị thứ 95 (P95) của hệ thống.
  - **Prompt Compliance (Tỷ lệ tuân thủ Prompt)**: Cam kết đạt mức **$\ge$ 94.91%** (đáp ứng mục tiêu thiết kế $\ge$ 90%).
  - **Tool Calling Accuracy (Tỷ lệ gọi hàm chính xác)**: Đang ở mức **61.79%** và cần tối ưu hóa để đạt mục tiêu **$\ge$ 90%**.

- **Tầng Turn Interruption / Turn-Taking (Quản lý lượt lời)**:
  - **Latency (Độ trễ quyết định ngắt)**: Cam kết phản xạ đạt mức **$\le$ 150ms** kể từ khi người dùng phát tiếng.
  - **Accuracy (Độ chính xác quyết định)**: Đặt mục tiêu đạt tỷ lệ chính xác **$\ge$ 85%**.

- **Tầng ASR Telephony (Nhận dạng giọng nói tổng đài)**:
  - **WER / CER**: Đo lường tỷ lệ lỗi trên dải tần narrowband 8kHz và dưới ảnh hưởng của các loại nhiễu.
  - **RTF**: Đo lường tốc độ xử lý của mô hình giải mã tín hiệu.

---

## 4. Phương Pháp Đánh Giá và Kiểm Thử Tải

- **Phương pháp đánh giá chất lượng (LLM-as-Judge)**:
  - Sử dụng mô hình ngôn ngữ lớn đóng vai trò là giám khảo (Judge LLM) để tự động so sánh phản hồi và các lời gọi hàm do bot sinh ra với đáp án chuẩn của chuyên gia (Human Annotator).
  - Trả về kết quả phân loại nhị phân Pass/Fail làm cơ sở tính toán tỷ lệ chính xác tổng thể.

- **Mục tiêu tải trọng hạ tầng (CCU Target)**:
  - Các chỉ số hiệu năng hiện tại của dự án mới chỉ được đo đạc trong điều kiện tải tĩnh cực thấp (**CCU = 5**).
  - Trọng tâm của đợt benchmark tiếp theo là đo lường sự biến động của độ trễ (TTFT/TTFS) khi nâng tải hệ thống đồng thời lên mức **CCU = 100** trên cùng một hạ tầng phần cứng.

---

## 5. ✅ Tự Kiểm Nhanh

<details>
<summary><b>Câu hỏi 1: Tại sao chỉ số P95 Latency lại quan trọng hơn chỉ số Mean Latency đối với trải nghiệm voice-bot tổng đài?</b></summary>

- **Ý nghĩa thực tế**:
  - Chỉ số trung bình (Mean Latency) có thể bị che giấu bởi phần lớn các cuộc gọi phản hồi rất nhanh, tạo ra ảo giác rằng hệ thống hoạt động mượt mà.
  - Chỉ số P95 Latency thể hiện ngưỡng thời gian phản hồi của 5% số lượng cuộc gọi chậm nhất hệ thống (những cuộc gọi bị nghẽn mạng hoặc quá tải tính toán).
  - Nếu P95 Latency quá cao (ví dụ: > 3 giây), 5% khách hàng tương ứng sẽ phải chịu đựng trải nghiệm ngắt quãng cực kỳ tồi tệ, gây ảnh hưởng tiêu cực đến chất lượng dịch vụ tổng thể.

</details>
