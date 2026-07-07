# 14.04 — Cách review cảm nhận kết quả và cổng nghiệm thu

> **Vai trò:**
>
> Chốt cách người review nhìn và nghe kết quả turn-detection, không chỉ đọc một con số accuracy.
>
> Gắn mỗi bài con với metric đúng và một cổng nghiệm thu để biết khi nào coi là đạt.

---

## Glossary

- `EEPR` → **Early Endpoint Rate** → tỉ lệ cắt lời sớm khi khách chưa nói xong.
- `EP50` → **Endpoint latency P50** → độ trễ trung vị từ lúc khách dứt lời tới lúc chốt EOU.
- `stop-latency` → **stop latency** → độ trễ từ lúc khách ngắt tới lúc bot dừng TTS.
- `false-interrupt` → **false interrupt rate** → tỉ lệ bot dừng nhầm khi khách không thật sự ngắt.
- `missed-interrupt` → **missed interrupt rate** → tỉ lệ bot không dừng khi khách thật sự ngắt.
- `resume` → **resume success rate** → tỉ lệ bot nối lại đúng chỗ sau khi dừng nhầm.
- `SRCC` → **Spearman Rank Correlation** → tương quan thứ hạng giữa số trên sim và số thật.

---

## 1. Dẫn dắt bối cảnh

- Turn-detection là bài mà một con số tổng không nói đủ:
  - accuracy cao vẫn có thể đi kèm cắt lời sớm gây khó chịu,
  - độ trễ thấp vẫn có thể đi kèm ngắt nhầm liên tục.
- Người review cần cảm nhận trực tiếp hành vi trên trục thời gian:
  - nghe được chỗ bot dừng đúng hay sai,
  - nhìn được độ trễ và điểm bắn của decider so với mốc chuẩn.

> Doc này chia cách review làm ba tầng: nghe hai kênh audio, nhìn dòng thời gian có mốc, và đọc bảng phân rã theo tình huống có tên rõ; cuối cùng gắn cổng nghiệm thu cho từng bài con.

---

## 2. Tầng một là nghe hai kênh audio

- ⚙️ **Cơ chế:**
  - render mỗi kịch bản thành file hai kênh, một kênh là giọng khách, một kênh là TTS bot, đúng như thu âm tổng đài,
  - chèn một tiếng đánh dấu ngắn vào đúng thời điểm decider chốt quyết định.
- 🔍 **Cách nghe:**
  - nghe chỗ khách chen lời khi bot đang nói và kiểm bot có dừng đúng lúc không,
  - nghe các kịch bản âm tính như tiếng đế dạ vâng và tiếng tivi để chắc bot giữ lời chứ không dừng nhầm.
- 💡 **Ý nghĩa:**
  - tai người bắt được cảm giác cắt lời sớm và dừng trễ mà bảng số làm mờ,
  - nghe hai kênh cho thấy ngay chỗ echo hay giọng nền làm decider bắn sai.
- ⚠️ **Bẫy:**
  - nếu render một kênh trộn chung giọng bot và khách thì mất khả năng nghe tách, phải giữ hai kênh riêng.

---

## 3. Tầng hai là nhìn dòng thời gian có mốc

- ⚙️ **Cơ chế:**
  - vẽ một dải thời gian gồm khoảng bot đang nói, khoảng khách đang nói, mốc ngắt chuẩn và mốc decider chốt,
  - hiệu số giữa hai mốc là độ trễ thật của quyết định.
- 🔍 **Cách nhìn:**
  - mốc decider nằm trước mốc chuẩn nghĩa là cắt sớm, nằm sau nghĩa là phản xạ chậm,
  - đối chiếu cùng một kịch bản giữa các decider để thấy đánh đổi nhanh nhưng sai với đúng nhưng chậm.
- 💡 **Ý nghĩa:**
  - dòng thời gian biến độ trễ trừu tượng thành khoảng cách nhìn được, hợp để phản biện kỹ thuật,
  - đây cũng là chỗ thay số latency synthetic bằng số đo trên sóng âm thật.
- ⚠️ **Bẫy:**
  - độ trễ chỉ có nghĩa khi tính trên audio đã render, số latency ở chế độ text hiện tại là mô phỏng nên không trích như số cam kết.

---

## 4. Tầng ba là bảng phân rã theo tình huống

- ⚙️ **Cơ chế:**
  - mỗi tình huống có tên rõ nghĩa thay vì mã, ví dụ khách ngắt thật, tiếng đế dạ vâng, tivi nền, echo TTS,
  - mỗi tình huống ghi quyết định đúng mong đợi và quyết định thực tế của decider.
- 🔍 **Cách đọc:**
  - đọc theo cột dừng và giữ để thấy decider sai ở nhóm tình huống nào,
  - đối chiếu ma trận nhầm giữa dừng và giữ, chú ý cột dừng nhầm vì đó là cái khách ghét nhất.
- 💡 **Ý nghĩa:**
  - bảng theo tình huống có tên cho biết lỗi tập trung ở đâu để vá đúng chỗ, thay vì chỉ biết một con số tổng.
- ⚠️ **Bẫy:**
  - không đặt tên tình huống bằng mã khó hiểu, mỗi hàng phải nói rõ tình huống là gì và lỗi là gì.

| Tình huống | Quyết định đúng | Ý nghĩa nếu sai |
| --- | --- | --- |
| Khách ngắt thật giữa lời bot | dừng TTS | bỏ sót ngắt làm bot nói đè khách |
| Tiếng đế dạ vâng khi khách nghe | giữ lời | dừng nhầm làm hội thoại vụn |
| Tivi hoặc nhạc nền | giữ lời | dừng nhầm theo tiếng nền |
| Echo TTS dội về micro | giữ lời | bot tự ngắt chính mình |
| Khách nói xong chờ trả lời | chốt EOU | chốt sớm thì cắt lời, chốt trễ thì đơ |

---

## 5. Metric đúng cho từng bài con

- **B1 endpointing:**
  - EEPR cho cắt lời sớm, EP50 và EP90 cho độ trễ chốt, kèm phân bố P50 P90 P99.
- **B2 barge-in:**
  - false-interrupt và missed-interrupt cho độ chính xác, stop-latency cho phản xạ, resume cho khả năng nối lại.
- **B3 backchannel:**
  - tỉ lệ nhận đúng backchannel trong nhóm tiếng đế, đo riêng khỏi barge-in thật.
- **B4 target-speaker:**
  - EER nhận giọng trên 8kHz tiếng Việt, và delta WER khi bật tách so với không bật.

---

## 6. Cổng nghiệm thu theo nấc

- **Nấc luồng audio đạt khi:**
  - có renderer hai kênh chạy được, độ trễ turn-detection là số đo trên sóng âm thật chứ không synthetic.
- **Nấc English-first đạt khi:**
  - mỗi bài con có số baseline tiếng Anh tái lập được và có verifier tất định.
- **Nấc tiếng Việt đạt khi:**
  - có tập sim tiếng Việt có nhãn mili-giây đủ chạy bốn bài con,
  - số trên sim vượt baseline hiện tại của hệ, và tương quan thứ hạng SRCC với một lát cuộc gọi thật đủ cao để tin.
- **Điều kiện neo cuối:**
  - số tuyệt đối chỉ chốt khi có lát data thật, trước đó số trên sim chỉ để chọn cấu hình và chứng minh hướng.

---

## ✅ Tự kiểm nhanh

- **Vì sao không review bằng một con số accuracy?** → accuracy cao vẫn có thể đi kèm cắt lời sớm hoặc ngắt nhầm, phải nghe và nhìn trục thời gian.
- **Cột nào trong ma trận nhầm cần soi nhất?** → cột dừng nhầm, vì bot tự ngắt hoặc ngắt theo tiếng nền là cái khách ghét nhất.
- **Khi nào độ trễ mili-giây mới đáng trích?** → khi đã render audio thật, số ở chế độ text hiện tại là mô phỏng.
