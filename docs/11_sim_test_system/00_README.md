# 11 — Hệ Thống Giả Lập & Kiểm Thử (Sim/Test System) của fci_voice_agent

> [!NOTE]
> - Tài liệu này giới thiệu tổng quan hệ thống giả lập hội thoại (Simulation) và các bộ khung kiểm thử (Harness),
> - **thiết lập cổng định hướng** để tự động kiểm thử hai module cốt lõi: turn-detection và tool-calling.
> - Tham chiếu chi tiết về thiết kế hệ thống giả lập xem tại [01_design.md](01_design.md),
> - và thiết kế chi tiết gym-env cùng mô hình 3 vai xem tại [02_gym_env_and_roles.md](02_gym_env_and_roles.md).

---

## 1. Dẫn dắt bối cảnh

- **Bối cảnh thực tế**:
  - Khi phát triển các module điều phối lượt thoại và gọi hàm nghiệp vụ cho trợ lý ảo giọng nói FCI,
  - việc thực hiện đánh giá chất lượng đòi hỏi một hệ thống giả lập môi trường hội thoại có khả năng tạo ra các kịch bản kiểm thử có nhãn và có độ tin cậy cao.
- **Nghịch lý đo lường**:
  - Các tài liệu nghiên cứu chất lượng mô hình chung của hệ thống thường mang tính lý thuyết vĩ mô và khó áp dụng trực tiếp cho các luồng nghiệp vụ đặc thù của FCI,
  - trong khi nếu không thiết kế các harness kiểm thử cụ thể dựa trên kịch bản thực tế thì chúng ta không thể định lượng được hiệu quả của từng thay đổi nhỏ trên mô hình trước khi đưa vào vận hành thật.

> Tài liệu này giới thiệu tổng quan hệ thống giả lập và kiểm thử của FCI,
> **xác định chỉ mục phân phối tài liệu thiết kế chi tiết**,
> giúp định hướng mối quan hệ giữa phần lý thuyết chung và hệ thống thực nghiệm tự động đang được xây dựng.

---

## 2. Glossary

- `adversarial test` -> **Kiểm thử đối kháng** ->
  - Phương pháp kiểm thử bằng cách cố tình đưa vào các tác nhân gây nhiễu hoặc kịch bản khó,
  - nhằm đánh giá độ bền và khả năng xử lý ngoại lệ của mô hình.
- `sim-to-real gap` -> **Khoảng cách giả lập - thực tế** ->
  - Sự sai lệch về phân phối dữ liệu và hiệu năng của mô hình,
  - khi đánh giá trên môi trường giả lập (simulation) so với khi vận hành trên môi trường thực tế (real telephony).
- `evaluation harness` -> **Khung kiểm thử tự động** ->
  - Hệ thống mã nguồn tự động nạp kịch bản, kích hoạt chạy thử nghiệm mô hình,
  - thực hiện đối chiếu kết quả đầu ra với nhãn chuẩn và xuất báo cáo chất lượng.

---

## 3. Phân biệt rõ Kiến thức nền và Hệ thống áp dụng

- **Thư mục tri thức chung (`.agent/skills/05_model_quality_engineering/`)**:
  - Đóng vai trò là nền tảng lý thuyết và các nghiên cứu khoa học:
    - tổng hợp các nghiên cứu về khoảng cách sim-to-real, kiểm thử đối kháng, cơ chế mô phỏng người dùng (user simulator),
    - và các phương pháp đánh giá chất lượng mô hình âm thanh.
    - Được thiết kế dưới dạng tri thức dùng chung cho mọi dự án liên quan đến giọng nói hoặc hình ảnh.
- **Thư mục hệ thống FCI (`docs/11_sim_test_system/` - Phân vùng hiện tại)**:
  - Là thiết kế kỹ thuật và đặc tả cụ thể áp dụng riêng cho dự án `fci_voice_agent`:
    - xây dựng các kịch bản hội thoại mẫu bám sát luồng nghiệp vụ của FCI (như khóa thẻ, xác thực danh tính),
    - thiết lập harness chạy trực tiếp trên các mô hình đã được thông luồng thực tế.

---

## 4. Chỉ mục Phân phối Tài liệu (Index)

- **00_README.md** (Tập tin hiện tại):
  - Điểm truy cập tổng quan và điều hướng hệ thống giả lập và kiểm thử.
- **[01_design.md](01_design.md)** (Thiết kế hệ thống):
  - Bản thiết kế tổng thể của hệ thống giả lập.
  - Phân tích quy trình kiểm thử thủ công qua file Excel, định nghĩa mô hình kịch bản (Scenario), mô tả đường ống xử lý dữ liệu và phương án giải quyết bài toán sim-to-real.
- **[02_gym_env_and_roles.md](02_gym_env_and_roles.md)** (Môi trường kiểm thử và vai trò):
  - Thiết kế chi tiết cấu trúc Gym-env và Bot-agent để phục vụ việc so sánh phiên bản một cách công bằng.
  - Định nghĩa mô hình 3 vai (Khách hàng, FCI-bot-dev, Solution-dev) để khép kín vòng lặp kiểm thử độc lập.
- **[03_structured_decoding.md](03_structured_decoding.md)** (Giải mã có ràng buộc):
  - Cơ chế ép tool-call vào JSON-schema bằng xgrammar và cách kiểm thử so sánh free-form với constrained.
  - Phân tích structured decoding vá được lớp lỗi định dạng nào và KHÔNG vá được lỗi ngữ nghĩa nào (đo trên bộ kịch bản khó exp 06).
- **Spec harness phát hiện lượt thoại (Kế hoạch)**:
  - Đặc tả kỹ thuật cho bộ sinh âm thanh giả lập và các cấp độ mô phỏng âm thanh (fidelity v1 đến v3).
- **Spec harness gọi hàm nghiệp vụ (Kế hoạch)**:
  - Đặc tả kỹ thuật cho bộ sinh kịch bản văn bản và cơ chế chấm điểm gọi hàm qua ba tầng chất lượng.
- **Scorecard và Metric (Kế hoạch)**:
  - Thiết kế cấu trúc báo cáo ma trận nhầm lẫn tự động và cơ chế tính toán độ tương quan sim-to-real.

---

## 5. Liên kết hệ thống

- **Dữ liệu kịch bản thủ công hiện tại**: `data/Testcase_Ngắt lời.xlsx`.
- **Cơ chế chấm điểm gọi hàm ba tầng**: [03_tool_calling_stages.md](../06_llm_agent/03_tool_calling_stages.md).
- **Mã nguồn hệ thống giả lập (Khi triển khai)**:
  - Thư mục thư viện dùng chung: `src/fci_voice/sim/`.
  - Thư mục thực nghiệm tương ứng: `experiments/05_sim_turn_detection/` và `experiments/06_sim_tool_calling/`.

---

## ✅ Tự kiểm nhanh

<details>
<summary>1. Tại sao cần phân biệt rõ ràng giữa tài liệu ở thư mục .agent/skills/05/ và thư mục docs/11/?</summary>

- **Phân tách lý thuyết và thực hành**:
  - Thư mục `.agent/skills/05/` chứa các nghiên cứu lý thuyết, phương pháp luận chung có thể tái sử dụng cho nhiều dự án khác nhau.
  - Thư mục `docs/11/` mô tả chi tiết thiết kế hệ thống và các harness cụ thể được xây dựng riêng cho dự án `fci_voice_agent`.
</details>

<details>
<summary>2. Hai module nghiệp vụ nào của fci_voice_agent được ưu tiên xây dựng hệ thống kiểm thử tự động?</summary>

- **Hạng mục kiểm thử trọng tâm**:
  - Module phát hiện lượt thoại và quản lý ngắt lời (turn-detection).
  - Module quyết định gọi hàm nghiệp vụ và trích xuất tham số (tool-calling).
</details>
