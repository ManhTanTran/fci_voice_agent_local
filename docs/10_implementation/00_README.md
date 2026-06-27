# 10 — Triển Khai (Implementation Track)

> [!NOTE]
> - Tài liệu đóng vai trò là điểm truy cập tổng quan cho track triển khai (Implementation track),
> - **tập trung vào kết quả chạy mã nguồn thực tế** và thực nghiệm trên hạ tầng DGX,
> - phân biệt rõ ràng với các tài liệu khảo sát lý thuyết từ mục 01 đến 09.
> - Tham chiếu chi tiết về kiến trúc code xem tại [01_architecture.md](01_architecture.md),
> - và báo cáo đo lường hiệu năng xem tại [02_e2e_report.md](02_e2e_report.md).

---

## 1. Dẫn dắt bối cảnh

- **Bối cảnh thực tế**:
  - Khi phát triển và kiểm thử hệ thống trợ lý giọng nói (voice agent) trên các hạ tầng hiệu năng cao như DGX,
  - chúng ta cần phân tách rõ ràng giữa các giai đoạn khảo sát lý thuyết và quá trình triển khai mã nguồn thực tế.
- **Nghịch lý đo lường**:
  - Việc để các tài liệu tổng kết kiến trúc và mã nguồn thực nghiệm nằm rải rác mà không có một điểm kết nối tập trung,
  - thường gây khó khăn cho việc theo dõi tiến độ thực tế, đánh giá độ trưởng thành của hệ thống, và liên kết ngược về các kịch bản kiểm thử.

> Tài liệu này đóng vai trò là cổng tổng quan cho toàn bộ track triển khai,
> **giúp hệ thống hóa cấu trúc mã nguồn**,
> định hướng mối quan hệ giữa phần code tái sử dụng và các thư mục thực nghiệm tương ứng.

---

## 2. Glossary

- `implementation track` -> **Triển khai thực tế** ->
  - Các hoạt động xây dựng mã nguồn chạy được,
  - đo lường hiệu năng và tích hợp hệ thống trên hạ tầng thật.
- `as-built architecture` -> **Kiến trúc thực tế** ->
  - Sơ đồ và cách tổ chức mã nguồn,
  - phản ánh chính xác trạng thái vận hành hiện tại của hệ thống.
- `E2E report` -> **Báo cáo thông luồng** ->
  - Tài liệu tổng kết kết quả chạy thử nghiệm đầu cuối (End-to-End),
  - ghi nhận các chỉ số về độ trễ và độ chính xác của từng module.

---

## 3. Bản đồ phân phối tài liệu

- **Quy ước chung**:
  - Mọi tài liệu thuộc track triển khai bắt buộc phải được tổ chức trong các thư mục con được đánh số cụ thể.
  - Tuyệt đối không để các tập tin nằm rải rác ngoài thư mục gốc của repository.

### 3.1 Danh mục tài liệu trong Track 10

- **00_README.md** (Tập tin hiện tại):
  - Điểm truy cập tổng quan và điều hướng toàn bộ track triển khai.
- **[01_architecture.md](01_architecture.md)** (Kiến trúc thực tế):
  - Tổng kết cấu trúc tổ chức mã nguồn hiện tại chạy trên DGX.
  - Sử dụng Pipecat làm khung điều phối chính, ánh xạ chi tiết giữa cấu trúc thư mục code `src/` và tài liệu khảo sát `docs/`.
- **[02_e2e_report.md](02_e2e_report.md)** (Báo cáo đo lường):
  - Báo cáo kết quả thông luồng thử nghiệm từ exp01 đến exp04 trên hạ tầng DGX Spark.
  - Thống kê chi tiết sơ đồ đường ống, độ trễ xử lý của từng module, và đánh giá mức độ hoàn thiện của hệ thống (scorecard maturity).

---

## 4. Mối quan hệ với các phân vùng khác

- **Phần thực nghiệm (`experiments/NN_*/`)**:
  - Chứa toàn bộ các runbook hướng dẫn, script kích hoạt và kết quả thô của từng lượt chạy thực tế.
  - Ví dụ: thử nghiệm khói (smoke test), đo lường lỗi nhận dạng chữ (WER), khép vòng hội thoại, và đo độ trễ.
- **Phần tổng kết (`docs/10_implementation/`)**:
  - Đóng vai trò là tài liệu tổng hợp và báo cáo đọc một chỗ cho lập trình viên.
  - Thực hiện liên kết ngược về các kịch bản thực nghiệm tương ứng để đối chiếu số liệu.
- **Phần mã nguồn tái sử dụng (`src/fci_voice/`)**:
  - Chứa các lớp bọc (adapter) và logic nghiệp vụ nghiệp vụ chung,
  - được cài đặt dưới dạng thư viện để các thư mục thực nghiệm import trực tiếp khi chạy.
- **Hệ thống giả lập và kiểm thử (`docs/11_sim_test_system/`)**:
  - Được tách biệt hoàn toàn sang một phân vùng riêng biệt,
  - tập trung vào việc mô phỏng hành vi hội thoại để đánh giá chất lượng module.

---

## ✅ Tự kiểm nhanh

<details>
<summary>1. Mục tiêu cốt lõi của track triển khai (Track 10) là gì và khác gì so với các track trước?</summary>

- **Trọng tâm thực tế**:
  - Tập trung vào mã nguồn thực tế chạy được và đo lường trực tiếp trên hạ tầng DGX.
  - Đối lập với các nghiên cứu và khảo sát lý thuyết thuần túy của các track từ 01 đến 09.
</details>

<details>
<summary>2. Sự khác biệt giữa thư mục src/ và thư mục experiments/ trong quá trình phát triển là gì?</summary>

- **Mã nguồn tái sử dụng (`src/`)**:
  - Chứa các module, adapter và logic nghiệp vụ chung được sử dụng bởi nhiều thử nghiệm khác nhau.
- **Mã nguồn thực nghiệm (`experiments/`)**:
  - Chỉ chứa các script chạy một lần, runbook chi tiết và các tệp tin lưu kết quả thô của từng lượt thử nghiệm cụ thể.
</details>
