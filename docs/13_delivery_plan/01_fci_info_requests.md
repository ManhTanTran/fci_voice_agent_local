# 13.01 — Bản request thông tin gửi FCI

> **Vai trò:**
>
> Gom câu hỏi cần FCI làm rõ để thiết kế module, dạng gửi được sau khi biên tập lại.
>
> Nền: hiểu biết hiện tại về hệ FCI phần lớn từ sơ đồ khái niệm, chưa từ code thật, nên nhiều mục là xác nhận và đính chính.

---

## 1. Mục tiêu bản request

- **Ba việc cần từ FCI, theo thứ tự ưu tiên:**
  - xác nhận hoặc đính chính cách hiểu của mình về kiến trúc hệ họ,
  - làm rõ cách đo hai con số điểm đau, để mình đặt mục tiêu đúng nền,
  - mở đường thông tin về data và điểm tích hợp, chưa cần data khách thật.
- **Cập nhật 2026-07-06:** FCI đã chủ động chia sẻ một lát audio thật (`data/audio_interrupt`, 37 file telephony 2 kênh 8kHz).
  - lát này đã đo và cho thấy giá trị cao, chi tiết ở [../14_turn_detection_delivery/05_fci_shared_data_findings.md](../14_turn_detection_delivery/05_fci_shared_data_findings.md),
  - nên đợt này **có thể xin thêm data** theo mục 3.3, không còn phải chờ demo mới escalate.

---

## 2. Xác nhận cách hiểu kiến trúc hệ FCI

Trình bày cách mình đang hiểu để FCI gật hoặc sửa, gồm cascade bốn lớp:

- **Lớp nhận đầu vào:** nhận diện ngắt lời, input guardrail chống injection, cơ chế rails fallback trả câu mẫu an toàn.
- **Lớp orchestrator:** điều phối theo cấu hình Bot Builder, ASR fallback hỏi lại khi confidence thấp, cơ chế simulated tool-calling chèn hàm giả để ép model bám một bước kịch bản.
- **Lớp tool-calling:** tách luồng suy luận khỏi luồng gọi API, two-pass response viết lại câu theo số liệu thật, intent filter quyết định có gọi tool không.
- **Lớp kiểm soát đầu ra:** PII guardrail bọc thẻ quanh OTP và PIN, factual rail đối chiếu số với kết quả tool, chuẩn hóa văn bản cho TTS.

Câu hỏi xác nhận:
- Cách hiểu trên đúng tới đâu, chỗ nào sai hoặc đã thay đổi?
- Kênh thoại có phải 8kHz băng hẹp không, dùng transport hoặc telephony provider nào?
- ASR và TTS hiện tại FCI dùng engine nào, tự host hay dịch vụ ngoài?

---

## 3. Nhóm câu hỏi ưu tiên cao

### 3.1 Cách đo hai con số điểm đau

Mọi thiết kế module phụ thuộc hiểu đúng cách đo, nên hỏi trước tiên.

- **Tool-calling khoảng 62 phần trăm:**
  - đo trên tập nào, bao nhiêu mẫu, định nghĩa đúng là gì (đúng tên hàm, đúng tham số, hay đúng cả kết quả)?
  - lỗi phần lớn nằm ở chọn sai hàm, sai tham số, hay sai định dạng?
- **Turn-interruption 76 phần trăm ở 280ms:**
  - accuracy đo thế nào, tập nào, nhãn ngắt thật và backchannel do ai gán?
  - 280ms đo từ mốc nào tới mốc nào, gồm những chặng gì?
- **Có đo chất lượng cuộc gọi hay tỉ lệ chuyển đổi không, hay chỉ đo đúng sai kỹ thuật?**

### 3.2 Data mình có thể dùng để tự đo

- **Data adhoc test nội bộ:** FCI cấp được loại nào, format ra sao, bao nhiêu?
- **Log hội thoại:** có transcript turn-by-turn kèm timestamp per-turn không, domain nào (đòi nợ, chăm sóc, chốt sale)?
- **Audio thô:** có giữ file 8kHz gốc không, có tách kênh khách và bot không?
- **Trace tool-calling:** có tập câu thoại tới tool cộng tham số cộng kết quả để mình chạy harness đo tách lỗi không?
- **Nhãn sẵn:** có nhãn kết thúc lượt hoặc ngắt lời hoặc chất lượng cuộc gọi không, hay phải tự gán?

### 3.3 Lượng data cụ thể xin thêm cho turn-detection

Đặt số dựa trên đo thật lát `audio_interrupt`, không phải đoán; cách suy ở [../14_turn_detection_delivery/05_fci_shared_data_findings.md](../14_turn_detection_delivery/05_fci_shared_data_findings.md) mục 6.

- **Đơn vị xin là cuộc gọi:**
  - vì FCI lưu theo cuộc, và mỗi cuộc cho nhiều loại nhãn cùng lúc,
  - đo được mỗi cuộc khoảng 1,6 phút, cho ~2 tới 3 barge-in nội dung và ~10 tới 15 ranh giới lượt.
- **Xin làm hai đợt:**
  - **Đợt 1 pilot 300 tới 500 cuộc:**
    - đủ dựng tập test vàng và hiệu chỉnh pipeline auto-label,
    - xác nhận tách kênh và gán vai bot đúng trên nhiều loại cuộc trước khi xin lớn.
  - **Đợt 2 khoảng 10.000 cuộc:**
    - đây là mức đủ fine-tune cả ba bài con endpointing, barge-in, backchannel với tách train val test,
    - quy ra khoảng 265 giờ audio, ~20.000 tới 30.000 barge-in nội dung, ~100.000 ranh giới lượt.
- **Ba thứ xin kèm, quan trọng ngang số lượng:**
  - **Log trạng thái phiên bot:**
    - câu TTS kèm mốc thời gian, giả thuyết ASR kèm điểm tin cậy, sự kiện lượt,
    - đây là thứ biến nhãn suy đoán thành nhãn chính xác, một cuộc có log đáng giá bằng nhiều cuộc chỉ có audio.
  - **Đa dạng nghiệp vụ và giọng:**
    - trải đòi nợ, chăm sóc, chốt sale, khóa thẻ; trộn cuộc nhiều barge-in với cuộc bình thường; trải vùng miền và giới tính.
  - **Giữ nguyên tách hai kênh 8kHz:**
    - đúng như lát đã gửi, không trộn một kênh, vì trộn kênh làm mất nhãn người nói miễn phí.
- **Cách diễn đạt khi gửi FCI:**
  - nêu rõ pilot trước để hai bên thấy kết quả sớm, rồi mới xin đợt lớn,
  - nhấn rằng data ẩn danh vẫn dùng được vì bài toán cần biên tín hiệu và mốc lượt, không cần danh tính khách.

---

## 4. Nhóm câu hỏi về điểm tích hợp

- **Ranh giới bàn giao:** module của mình cắm vào đâu trong pipeline, nhận input gì và trả output gì?
- **I/O contract từng module:** schema request và response cho turn-detector, cho intent hoặc tool-selector, cho guardrail; đồng bộ hay bất đồng bộ, có streaming token không?
- **Ngân sách latency:** end-to-end FCI cho từng chặng bao nhiêu ms, mục tiêu thời gian tới tiếng nói đầu tiên là bao nhiêu?
- **Cơ chế rẽ nhánh:** luật nào để tầng rule của FCI chuyển ca khó lên module ML của mình, ai giữ state khi bàn giao?
- **Triển khai:** module chạy cùng runtime hay là service riêng, mục tiêu số cuộc đồng thời, hạ tầng phục vụ CPU hay GPU?
- **Framework runtime:** FCI tự viết orchestrator hay đã dùng LangGraph hoặc Pipecat, phiên bản API nào?

---

## 5. Nhóm câu hỏi về nội tại hệ thống

- **Tổ chức prompt, là điểm đau chính:**
  - simulated tool-calling định nghĩa ở mức prompt thuần hay có cấu trúc code điều khiển riêng?
  - prompt một bước gồm những gì, dài bao nhiêu, chia bước và sinh reasoning giả thế nào?
- **Bot Builder:** sơ đồ kịch bản cấu hình kiểu gì, một flow nghiệp vụ điển hình bao nhiêu bước?
- **State:** session state lưu gì và ở đâu, có checkpointer theo thread không?
- **Tool schema:** bao nhiêu tool mỗi domain, schema định nghĩa kiểu gì, đã dùng constrained decoding chưa?
- **Guardrails hiện thực bằng gì:** regex thuần, model NER, hay LLM judge, đã đo tỉ lệ chặn nhầm chưa?
- **Logging và trace:** có log chuỗi sự kiện per-turn và trace ID để debug một cuộc gọi không?

---

## 6. Điểm đau mình đã nhận diện, nêu để cùng xác nhận

- **Prompt phình to:** kiến trúc cũ nhồi cả kịch bản và mọi tool vào một prompt lớn, model dễ lạc mục tiêu; simulated tool-calling là cách vá tay, bản thân nó có rủi ro nhiễu suy luận.
- **Tool-calling:** phần lớn khoảng cách nằm ở logic chọn tool và grounding giá trị, không phải định dạng, nên cần harness đo tách lỗi trước khi tối ưu.
- **Turn-interruption:** dùng LLM 7B nặng để quyết ngắt lời vừa chậm vừa kém, trong khi bản chất là đa chiều, cần phễu nhẹ hơn.

---

## 7. Ghi chú dùng nội bộ

- Bản này là nháp nội bộ, biên tập lại giọng cho hợp kênh gửi trước khi chuyển FCI.
- Ưu tiên hỏi gọn theo mục 3 trước, các mục 4 và 5 có thể gửi thành đợt sau nếu sợ dài.
- Nguồn bóc câu hỏi: [../02_architecture/00_README.md](../02_architecture/00_README.md) và [../02_architecture/05_langgraph_reference_architecture.md](../02_architecture/05_langgraph_reference_architecture.md).
