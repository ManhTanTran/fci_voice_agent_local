# 14.02 — Dataset public cho turn-detection và bắt đầu từ tập nào

> **Vai trò:**
>
> Liệt kê dataset public dùng được cho turn-taking, nói rõ mỗi tập là gì và bắt đầu từ tập nào.
>
> Chỉ giữ tập phục vụ turn-detection, barge-in, backchannel và target-speaker; tách rõ tiếng Anh dùng ngay với tiếng Việt còn thiếu.

---

## Glossary

- `EOU` → **End-Of-Utterance** → mốc người nói xong lượt.
- `TSE` → **Target-Speaker Extraction** → tách đúng giọng khách.
- `RIR` → **Room Impulse Response** → đáp ứng xung phòng để mô phỏng vọng.
- `MCT` → **Multi-Condition Training** → trộn nhiều điều kiện nhiễu khi train.
- `SIR` → **Signal-to-Interference Ratio** → tỉ lệ giọng target trên giọng chen.

---

## 1. Dẫn dắt bối cảnh

- Turn-taking cần loại data đặc thù mà ASR thường không có:
  - cần hội thoại hai chiều có chồng lấn để học ranh giới lượt và hành vi ngắt lời,
  - cần nhãn thời gian mức mili-giây cho điểm bắt đầu ngắt, thứ mà gán nhãn tay khó đạt.
- Tình hình tài nguyên lệch rõ giữa hai ngôn ngữ:
  - tiếng Anh có sẵn corpus telephony hội thoại chuẩn để chạy ngay,
  - tiếng Việt thiếu hẳn corpus telephony hội thoại 8kHz nên phải bắt đầu từ tập đọc và tập tổng hợp.

> Doc này xếp dataset thành ba nhóm theo mức sẵn sàng: tiếng Anh lấy ngay, tiếng Việt lấy được nhưng không phải telephony hội thoại, và lỗ hổng cứng bắt buộc phải tự sinh.

---

## 2. Bắt đầu từ tập nào

- **Điểm khởi động rẻ nhất là smart-turn-data-v3:**
  - đây là tập train và test cho EOU đã mở cả weights lẫn dữ liệu, có nhãn tiếng Việt,
  - cho phép đo lại và fine-tune EOU hợp pháp ngay từ ngày đầu.
- **Cặp đi kèm để dựng luồng audio là Libri2Mix 8kHz cộng MUSAN cộng RIR:**
  - Libri2Mix cho benchmark tách giọng target ở đúng 8kHz,
  - MUSAN và RIR cho nhiễu babble nhạc và vọng để trộn theo chuỗi kênh.
- **Corpus telephony hội thoại tiếng Anh là Switchboard hoặc Fisher:**
  - đóng vai proxy turn-taking telephony 8kHz thật khi chưa có data tiếng Việt tương đương.

---

## 3. Nhóm tiếng Anh và quốc tế lấy ngay

| Bộ | Dùng cho | License |
| --- | --- | --- |
| Switchboard và Fisher | proxy turn-taking telephony 8kHz | LDC cấp phép |
| Libri2Mix 8kHz | benchmark target-speaker | CC BY 4.0 nguồn |
| smart-turn-data-v3 | train và test EOU có tiếng Việt | HF public BSD-2 |
| Full-Duplex-Bench | benchmark hành vi turn-taking | theo challenge |
| MUSAN | nhiễu babble và nhạc để trộn | CC BY 4.0 |
| RIRS_NOISES | mô phỏng vọng loa ngoài | Apache 2.0 |

- Nhóm này đủ để chạy English-first cho renderer audio, EOU, barge-in và target-speaker mà không xin phép ai.
- Easy-Turn mở trainset khoảng 1145 giờ cho EOU nhưng chỉ tiếng Trung và tiếng Anh, dùng để đối chứng recipe.
- Cảnh báo license: tránh WHAM và ESC-50 vì là phi thương mại, không dùng nếu hướng sản phẩm.

---

## 4. Nhóm tiếng Việt lấy được nhưng không phải telephony hội thoại

| Bộ | Dùng cho | License |
| --- | --- | --- |
| VietSuperSpeech | giọng hội thoại thật, pool đối chứng | HF public |
| VieSpeaker | kho speaker cho target-speaker | đọc license nguồn |
| ViMD 63 tỉnh | reference voice cho sinh giọng vùng miền | đọc license nguồn |
| VIVOS và Common Voice VI và VLSP | nguồn sạch downsample 8kHz | public |

- VietSuperSpeech có khoảng 267 giờ giọng hội thoại, dùng làm pool đối chứng phân bố cho sim.
- VieSpeaker có khoảng 902 giờ và khoảng 4715 speaker, hợp làm kho enrollment cho target-speaker.
- Các tập này đều băng rộng và phần lớn là giọng đọc, phải tự downsample về 8kHz và tự sinh chồng lấn.

---

## 5. Lỗ hổng cứng phải ghi rõ

- **Không có corpus telephony hội thoại 8kHz tiếng Việt công khai** tương đương Switchboard.
- **Không có dataset nhiễu telephony nội địa** gồm nhạc chờ, babble, phương ngữ và codec trọn gói.
- **Không có tập barge-in tiếng Việt có nhãn mili-giây** cho điểm bắt đầu ngắt.
- Đây chính là lý do bắt buộc phải sinh kịch bản có nhãn bằng renderer, chi tiết ở [01_inference_flow_two_channel.md](01_inference_flow_two_channel.md) mục 6.

---

## 6. Điểm mù phải tự đo trước khi chốt

- Tỉ lệ báo nhầm của Smart Turn trên 8kHz tiếng Việt, vì con số 81 phần trăm là đo trên băng rộng 16kHz sạch.
- Tỉ lệ lỗi nhận giọng của bộ embedding target-speaker khi hạ về 8kHz tiếng Việt.
- Ngưỡng im lặng tối ưu cho endpointing tiếng Việt, vì thanh điệu làm tín hiệu ngữ điệu yếu đi.
- Mọi số hiện có là 16kHz hoặc tiếng Anh hoặc do hãng tự công bố, đều cần harness đo lại.

---

## ✅ Tự kiểm nhanh

- **Bắt đầu từ tập nào rẻ nhất?** → smart-turn-data-v3 cho EOU, kèm Libri2Mix 8kHz với MUSAN và RIR cho luồng audio.
- **Dataset tiếng Anh nào đóng vai telephony hội thoại?** → Switchboard hoặc Fisher.
- **Lỗ hổng cứng nhất của tiếng Việt là gì?** → không có telephony hội thoại 8kHz và không có barge-in có nhãn mili-giây.
