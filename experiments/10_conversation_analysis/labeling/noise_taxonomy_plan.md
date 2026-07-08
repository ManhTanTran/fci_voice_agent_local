# Ghi chú phân loại noise và kế hoạch bóc tách để làm sau

> **Vai trò:**
>
> Ghi lại phân loại các dạng noise quan sát khi label FPT, và trục nào máy tự nhận được, trục nào người phải gán.
>
> Đây là note để làm sau; hiện tại chỉ gán gộp một nhãn `bỏ`, chi tiết hóa ở vòng sau.

---

## Glossary

- `VAD` → **Voice Activity Detection** → phát hiện có tiếng nói hay không trong một đoạn.
- `target-speaker` → **target speaker** → chỉ nhận đúng giọng người dùng đang nói với bot, bỏ giọng khác.
- `SIR` → **Signal-to-Interference Ratio** → tỉ lệ năng lượng tín hiệu chính so với tiếng chen.
- `SNR` → **Signal-to-Noise Ratio** → tỉ lệ tín hiệu so với nhiễu nền.
- `spec_flatness` → **spectral flatness** → độ phẳng phổ, cao thì giống nhiễu, thấp thì giống tiếng nói.
- `side conversation` → **side conversation** → người khác nói bên cạnh, không phải người dùng nói với bot.
- `backchannel` → **backchannel** → tiếng đế dạ vâng ừ, báo đang nghe, không mang nội dung.

---

## 1. Bối cảnh

- Khi gán nhãn FPT gặp nhiều turn không phải nội dung hội thoại thật, gộp chung một nhãn `bỏ` là đủ để không làm bẩn WER:
  - nhưng chính các turn `bỏ` này lại là data cho bài lọc nhiễu và turn-detection,
  - nên cần một phân loại tinh hơn ở vòng sau, tách rõ từng dạng noise.

> Ghi chú này cố định lại phân loại đã thống nhất, để khi quay lại làm chi tiết không phải nghĩ lại từ đầu; hiện tại vẫn label gộp một nhãn `bỏ`.

---

## 2. Các dạng noise quan sát từ phía người nghe

- **Loại 1, nền nhỏ không nghe rõ:**
  - năng lượng thấp, không rõ là gì.
- **Loại 2, nền to hơn nhưng nội dung vô nghĩa:**
  - nghe ra âm nhưng không thành nghĩa.
- **Loại 3, nền rõ nhưng không phải tiếng nói:**
  - tiếng động, nhạc, không phải giọng người.
- **Loại 4, nền rõ là tiếng nói nhưng side conversation:**
  - giọng người thật, nhưng của người khác, không phải người dùng đang nói với bot.
- **Loại 5, nội dung thật lẫn nhiễu, nhiễu lấn át:**
  - người dùng có nói nội dung có nghĩa nhưng nhiễu hoặc giọng khác đè lên, đây là case khó nhất.

---

## 3. Trục nào máy tự nhận, trục nào người phải gán

- **Ba detector độc lập, mỗi cái bắt một trục:**
  - trục tiếng-nói-hay-không bằng VAD model như Silero cộng spectral flatness,
  - trục có-nghĩa-hay-gibberish bằng độ tự tin ASR cộng bất đồng ba model cộng perplexity,
  - trục có-phải-giọng-user-chính bằng speaker embedding so với giọng khách chủ đạo.

- **Loại 1 nền nhỏ:**
  - máy nhận tốt bằng VAD năng lượng cộng ASR rỗng,
  - người gần như không cần gán.
- **Loại 3 không phải tiếng nói:**
  - máy nhận tốt bằng VAD model cộng spectral flatness,
  - người chỉ soi mẫu.
- **Loại 2 gibberish:**
  - máy bán tự động bằng ASR-confidence cộng bất đồng ba model cộng perplexity,
  - người xác nhận ca ranh giới.
- **Loại 4 side conversation:**
  - máy khó, cần speaker embedding thấy giọng lệch giọng chính,
  - người phải gán nhiều.
- **Loại 5 lẫn nhiễu lấn át:**
  - máy khó nhất, chỉ thấy SIR thấp mà vẫn còn nội dung,
  - người phải quyết còn cứu được nội dung hay không.

- **Kết luận:** loại 1 và 3 để máy lo; loại 2 máy chấm điểm người chốt; loại 4 và 5 người phải gán, và đó là data quý cho target-speaker và cho robustness.

---

## 4. Case khó nhất, nội dung thật lẫn nhiễu lấn át

- **Vì sao khó:**
  - không phải noise thuần để bỏ, cũng không phải content sạch để đo WER bình thường,
  - SIR thấp, người còn nghe được một phần nội dung user nhưng bị giọng khác hoặc nhiễu đè.
- **Quy ước xử lý khi label bây giờ:**
  - nếu người vẫn nghe ra nội dung user nói thật thì gán `cần gõ` và gõ phần nghe được, đây là hard sample quý,
  - nếu nhiễu lấn tới mức không cứu được nội dung thì gán `bỏ`.
- **Việc để sau:**
  - tách một nhãn riêng lẫn nhiễu để làm tập đo robustness, đo STT tụt bao nhiêu khi có nhiễu, tách khỏi WER sạch,
  - đây cũng là đầu vào cho tiền xử lý target-speaker và tách nguồn.

---

## 5. Quy ước tạm thời khi label vòng này

- **Gộp một nhãn `bỏ`** cho mọi noise không liên quan hội thoại, chưa tách loại 1 tới 4.
- **Loại 5 theo quy ước mục 4:** cứu được thì `cần gõ`, không cứu được thì `bỏ`.
- **Chi tiết hóa ở vòng sau**, cả code và người cùng bóc tách rõ từng dạng.

---

## 6. Việc để sau, theo thứ tự chi phí

- **Rẻ, làm trước:** hiện các đặc trưng có sẵn SNR SIR spec_flatness ZCR lên mỗi turn cộng auto-gợi-ý loại 1 và 3 từ số đó.
- **Vừa:** cắm Silero VAD tách speech và non-speech chắc hơn cho loại 3.
- **Nặng, tách session riêng:** speaker embedding cho loại 4 target-speaker và cho loại 5 tách nguồn.

---

## ✅ Tự kiểm nhanh

- **Loại nào máy tự nhận tốt nhất?** → loại 1 nền nhỏ và loại 3 không phải tiếng nói, bằng VAD.
- **Loại nào người phải gán và vì sao?** → loại 4 side conversation và loại 5 lẫn nhiễu, vì cần phân biệt giọng và cứu nội dung, embedding trên 8kHz chồng tiếng chưa đủ tin.
- **Bây giờ label thế nào?** → gộp một nhãn `bỏ` cho noise không liên quan, loại 5 thì cứu được gõ không cứu được bỏ.
