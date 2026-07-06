# 08 — Datasets: Hệ Thống Dữ Liệu Đánh Giá Cho Voice-Bot

> [!NOTE]
> Tài liệu này liệt kê và quản lý các tập dữ liệu (datasets) phục vụ quá trình đánh giá hiệu năng (benchmarking) và huấn luyện các mô hình thành phần trong hệ thống voice-bot.
>
> Ba tài liệu phương pháp đi kèm (bổ sung 2026-07): [01_eda_methodology.md](01_eda_methodology.md) (EDA 3 lớp audio → transcript → log hệ thống),
> [02_sim_to_real_data.md](02_sim_to_real_data.md) (tạo dữ liệu sim bổ trợ real-data theo kịch bản kiểm thử),
> và [03_training_recipes.md](03_training_recipes.md) (đặc thù training từng loại model trong hệ voice-agent).

---

## 1. Dẫn dắt bối cảnh

- **Vai trò của dữ liệu đánh giá chuẩn hóa**:
  - Để xây dựng các thành phần nhận dạng giọng nói (ASR), quản lý lượt lời (turn-taking) và mô hình ngôn ngữ (LLM) hoạt động tin cậy, hệ thống cần được đánh giá trên các tập dữ liệu mẫu chuẩn hóa.
  - Các tập dữ liệu này phải phản ánh chính xác các kịch bản đàm thoại thực tế trên kênh tổng đài viễn thông viễn thông.

- **Nghịch lý của kiểm thử chất lượng**:
  - Tại sao mô hình hoạt động rất tốt khi kiểm thử thủ công vài trường hợp riêng lẻ nhưng lại liên tục gặp lỗi nghiệp vụ khi đưa ra môi trường sản xuất?
  - Làm thế nào để tự động hóa việc chấm điểm và phát hiện sự sụt giảm hiệu năng (regression) của toàn hệ thống sau mỗi phiên bản cập nhật?

- **Mục tiêu của tài liệu**:
  
  Tài liệu này định hình cấu trúc các tập dữ liệu hiện có trong dự án và vạch ra lộ trình xây dựng dữ liệu phục vụ các đợt benchmark tiếp theo.

---

## 2. Glossary

Bảng Glossary dưới đây định nghĩa toàn bộ thuật ngữ viết tắt xuất hiện trong bài:

| Ký hiệu / Thuật ngữ | Tên đầy đủ tiếng Anh | Giải nghĩa tiếng Việt |
| :--- | :--- | :--- |
| `ASR` | **Automatic Speech Recognition** | Hệ thống tự động nhận dạng giọng nói. |
| `LLM` | **Large Language Model** | Mô hình ngôn ngữ lớn. |
| `JSONL` | **JSON Lines** | Định dạng tệp văn bản lưu trữ các chuỗi JSON độc lập trên mỗi dòng. |

---

## 3. Các Tập Dữ Liệu Hiện Có

Hệ thống hiện tại lưu trữ 2 tập dữ liệu phục vụ kiểm thử tích hợp và kiểm thử chen ngang:

- **Tập dữ liệu kiểm thử luồng nghiệp vụ (`voice_agent_trace_samples.jsonl`)**:
  - *Bản chất*: Lưu trữ các vết hội thoại (traces) theo từng lượt nói của người dùng và phản hồi dự kiến từ hệ thống.
  - *Cấu trúc một mẫu thử bao gồm*:
    - **System Prompt**: Chỉ dẫn nghiệp vụ của hệ thống tại thời điểm đó.
    - **Conversation History**: Lịch sử hội thoại trước đó.
    - **User Input**: Văn bản người dùng nói do ASR giải mã.
    - **Expected Response**: Phản hồi mong muốn từ bot.
    - **Expected Tool Calls**: Lời gọi hàm chính xác cần thực thi.

- **Tập dữ liệu kiểm thử chen ngang (`turn_interruption_test.json`)**:
  - *Bản chất*: Phục vụ đánh giá tính chính xác của mô hình quản lý lượt lời và phân biệt tiếng đệm.
  - *Cấu trúc một mẫu thử bao gồm*:
    - **Conversation History**: Ngữ cảnh hội thoại hiện tại.
    - **Partial Utterances**: Các phân đoạn âm thanh chen ngang ngắn của người dùng.
    - **Label**: Nhãn phân loại nghiệp vụ mong muốn (ví dụ: `INTERRUPT` - ngắt lời, hoặc `CONTINUE` - nói tiếp).

---

## 4. Các Nhiệm Vụ Dữ Liệu Cần Triển Khai

Để phục vụ các chặng phát triển tiếp theo, dự án cần hoàn thành 2 nhiệm vụ quản lý dữ liệu:

- **Đồng bộ hóa kho dữ liệu nội bộ**:
  - Thu thập các file dữ liệu gốc của `voice_agent_trace_samples.jsonl` và `turn_interruption_test.json` từ các thành viên dự án hoặc dịch vụ lưu trữ đám mây.
  - Tổ chức lưu trữ các tệp tin này trong thư mục dữ liệu cục bộ của dự án (ví dụ: `data/` - cấu hình loại trừ trong `.gitignore` và thiết lập cơ chế đồng bộ hóa an toàn).

- **Khảo sát dữ liệu thoại tiếng Việt chuyên dụng**:
  - Tiến hành thu thập và khảo sát các bộ dữ liệu thoại tiếng Việt narrowband (8kHz) phục vụ huấn luyện và đánh giá mô hình ASR tổng đài.
  - Thiết lập mối liên kết dữ liệu với phòng thí nghiệm fine-tune `nvidia_asr_nemo` để tận dụng chéo các tài nguyên dữ liệu sẵn có.

---

## 5. ✅ Tự Kiểm Nhanh

<details>
<summary><b>Câu hỏi 1: Tập dữ liệu `voice_agent_trace_samples.jsonl` được sử dụng để giải quyết bài toán nào trong dự án?</b></summary>

- **Ứng dụng thực tế**:
  - Tập dữ liệu này dùng để benchmark chất lượng của mô hình ngôn ngữ lớn (LLM) và cơ chế gọi hàm (tool-calling).
  - Bằng cách so sánh đầu ra thực tế của LLM với dữ liệu `Expected Response` và `Expected Tool Calls` trong tệp, kỹ sư có thể tự động đo lường tỷ lệ tuân thủ nghiệp vụ và tỷ lệ gọi hàm chính xác của agent.

</details>
