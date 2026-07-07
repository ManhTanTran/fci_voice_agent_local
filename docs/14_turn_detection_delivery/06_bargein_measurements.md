# 14.06 — Bảng số đo chi tiết lát audio FCI

> **Vai trò:**
>
> Chứa toàn bộ bảng số đo thô làm bằng chứng cho [05_fci_shared_data_findings.md](05_fci_shared_data_findings.md).
>
> Tách riêng phần số khỏi phần diễn giải để tiện đối chiếu và tái lập.

---

## Glossary

- `corr` → **correlation** → tương quan năng lượng hai kênh; âm nghĩa là hai bên nói luân phiên.
- `#Overlap` → **overlap count** → số vùng hai kênh cùng có tiếng, dài từ 0,25 giây.
- `#Barge-in` → **barge-in count** → số mốc kênh khách bật tiếng khi kênh bot đang bật.
- `CONTENT` → **content barge-in** → khách chen lời mang nội dung, bot phải dừng.
- `backchannel` → **backchannel** → tiếng đế xác nhận ngắn, không mang nội dung sửa.
- `rỗng` → **empty** → không có tiếng nói đọc được, tức VAD năng lượng bắt nhầm.

> Lưu ý bảo mật:
>
> mọi dãy số dài trong transcript đã được thay bằng `«[dãy số ẩn]»` để không đưa số điện thoại và số căn cước thật vào git.

---

## 1. Tổng hợp toàn corpus

- **Bộ đo:** 36 file (đã loại một bản trùng), tổng 56,9 phút audio telephony hai kênh 8kHz.
- **Ba con số chốt:**
  - **264** ứng viên barge-in đo bằng VAD năng lượng,
  - **247** vùng double-talk dài từ 0,25 giây,
  - `corr` trung bình **−0,19**, có **29/36 file** mang dấu âm rõ.
- **Phân loại bằng ASR trên file mẫu (39 mốc):**
  - **17** CONTENT, **5** backchannel, **17** rỗng,
  - tức chỉ **44%** mốc năng lượng là barge-in nội dung thật.

---

## 2. Bảng 36 file, xếp theo mật độ barge-in

| File (8 ký tự đầu) | Giây | Bot% | Khách% | corr | Chồng% | #Overlap | #Barge-in |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `5634d6eb` | 326 | 47 | 34 | -0.43 | 8.5 | 40 | 42 |
| `85fa33e2` | 224 | 45 | 32 | -0.38 | 7.5 | 22 | 31 |
| `fde2515f` | 231 | 52 | 22 | -0.28 | 4.0 | 20 | 21 |
| `dd95d9dd` | 183 | 42 | 23 | -0.16 | 6.8 | 17 | 18 |
| `86f6cc35` | 126 | 25 | 47 | -0.10 | 10.6 | 16 | 15 |
| `0718d87c` | 126 | 28 | 52 | -0.24 | 9.1 | 11 | 14 |
| `084bea35` | 180 | 48 | 20 | -0.20 | 6.3 | 16 | 14 |
| `115cfbb0` | 213 | 43 | 15 | -0.23 | 3.2 | 11 | 11 |
| `c6c00bcd` | 290 | 48 | 16 | -0.40 | 2.0 | 12 | 10 |
| `026be254` | 106 | 29 | 37 | -0.34 | 5.2 | 7 | 9 |
| `8acd01a9` | 116 | 24 | 39 | -0.18 | 6.3 | 7 | 9 |
| `62173ce1` | 111 | 42 | 20 | -0.20 | 5.6 | 7 | 8 |
| `7bdfd238` | 93 | 43 | 19 | -0.23 | 4.7 | 6 | 8 |
| `3a32c59c` | 99 | 33 | 18 | -0.12 | 2.4 | 3 | 6 |
| `e8c99462` | 50 | 53 | 21 | -0.13 | 8.4 | 8 | 6 |
| `3f1c7d62` | 42 | 31 | 32 | -0.08 | 9.0 | 7 | 5 |
| `5b16eff7` | 60 | 28 | 36 | -0.35 | 3.5 | 4 | 5 |
| `c341f057` | 58 | 22 | 42 | -0.06 | 9.4 | 7 | 5 |
| `845eea83` | 154 | 21 | 25 | -0.28 | 1.3 | 2 | 4 |
| `aaf60a07` | 35 | 32 | 24 | -0.20 | 3.5 | 2 | 4 |
| `b063037d` | 56 | 33 | 16 | -0.10 | 3.4 | 3 | 4 |
| `3d33fc8c` | 32 | 42 | 23 | -0.04 | 8.1 | 2 | 2 |
| `44ac42e1` | 38 | 40 | 6 | 0.08 | 2.7 | 3 | 2 |
| `6452f627` | 42 | 37 | 30 | -0.29 | 5.4 | 4 | 2 |
| `90a358c2` | 22 | 32 | 24 | -0.17 | 4.2 | 2 | 2 |
| `de16ee50` | 53 | 34 | 17 | -0.27 | 1.8 | 2 | 2 |
| `31420b0a` | 40 | 16 | 32 | -0.27 | 0.2 | 0 | 1 |
| `5af4f8b2` | 27 | 45 | 13 | -0.02 | 4.3 | 2 | 1 |
| `5b09f032` | 57 | 41 | 18 | -0.44 | 1.5 | 1 | 1 |
| `5e5d0508` | 16 | 23 | 36 | 0.01 | 7.9 | 1 | 1 |
| `9ebc636d` | 29 | 51 | 7 | -0.01 | 1.9 | 1 | 1 |
| `2392204d` | 40 | 17 | 8 | 0.00 | 0.2 | 0 | 0 |
| `3d32f5fa` | 48 | 38 | 26 | -0.47 | 0.8 | 0 | 0 |
| `79d01e9f` | 39 | 17 | 13 | -0.09 | 0.0 | 0 | 0 |
| `8dd7a009` | 18 | 12 | 67 | -0.26 | 2.3 | 1 | 0 |
| `eb8e7200` | 36 | 13 | 7 | 0.09 | 0.4 | 0 | 0 |

**Cách đọc bảng:**

- **Cột `corr`:**
  - gần như luôn âm, xác nhận hai kênh tách agent với khách,
  - bốn dòng dấu dương hoặc bằng không là các cuộc rất ngắn, một phía nói là chính, không phải mono nhân đôi.
- **Cột `#Barge-in` so `#Overlap`:**
  - hai cột bám nhau, cho thấy phần lớn vùng chồng lấn khởi phát từ phía khách chen vào,
  - dòng đầu `5634d6eb` là file mẫu, đậm đặc barge-in nhất vì ASR bot lỗi nặng.
- **Hàng cuối, bốn file `#Barge-in` bằng không:**
  - cuộc ngắn hoặc một phía im, đúng kỳ vọng, không phải lỗi đo.

---

## 3. Phân loại 39 mốc barge-in của file mẫu

- **File:** `5634d6eb-be46-4834-a819-1222e75c9936.wav`, cuộc gọi khóa thẻ tín dụng.
- **Bối cảnh:** ASR của bot FCI nghe nhầm mọi con số thành "4 năm", khách phải đọc lại liên tục.

| t (s) | Loại | Khách nói (ASR, đã ẩn dãy số) | Bot đang nói (bị chen) |
| ---: | --- | --- | --- |
| 25.6 | backchannel | mình | dạ em đã ghi nhận họ tên của chị là nguyễn thị ngọc hoa |
| 27.5 | backchannel | mình | tiếp theo chị vui lòng cung cấp cho em số căn cước công dân của chị nhé |
| 37.5 | rỗng | — | dạ em đã di nhận số căn cước công dân của chị là 4 năm |
| 41.9 | CONTENT | tôi không phải không phải một hai ba | dạ em đã di nhận số căn cước công dân của chị là 4 năm |
| 43.9 | CONTENT | tôi không phải không phải một hai ba | tiếp theo chị vui lòng cho em biết số điện thoại đang đăng ký với ngân hàng của chị nhé |
| 45.4 | CONTENT | sáu vậy | tiếp theo chị vui lòng cho em biết số điện thoại đang đăng ký với ngân hàng của chị nhé |
| 58.0 | CONTENT | không một hai | dạ em đã ghi nhận số điện thoại của chị là |
| 79.4 | CONTENT | ông «[dãy số ẩn]» | vậy số điện thoại đúng của chị là 4 năm sẽ không chị |
| 96.7 | rỗng | — | em nghĩ nhận lại số điện thoại của chị là «[dãy số ẩn]» mạng |
| 101.5 | CONTENT | số căn cước công dân là 4 năm | chị vui lòng cho em biết số căn cước công dân chính xác của chị nhé |
| 115.4 | CONTENT | nhằm thôi một | tiếp theo chị vui lòng cho em biết bốn số cuối của thầy tín dụng mà chị muốn khóa nhé |
| 117.0 | CONTENT | «[dãy số ẩn]» | tiếp theo chị vui lòng cho em biết bốn số cuối của thầy tín dụng mà chị muốn khóa nhé |
| 118.5 | CONTENT | «[dãy số ẩn]» | tiếp theo chị vui lòng cho em biết bốn số cuối của thầy tín dụng mà chị muốn khóa nhé |
| 126.8 | rỗng | — | dạ em đã ghi nhận 4 số cuối thẻ của chị là 4 năm |
| 133.0 | rỗng | — | bây giờ em sẽ kiểm tra lại toàn bộ thông tin chị vừa cung cấp để xác minh trước khi thực hiện khóa thể |
| 143.1 | CONTENT | số căn cước công dân lá 4 | số căn cước công dân «[dãy số ẩn]» |
| 156.3 | rỗng | — | em xin nghi nhận lại số căn cước công dân của chị là 4 năm |
| 158.9 | rỗng | — | em xin nghi nhận lại số căn cước công dân của chị là 4 năm |
| 160.5 | rỗng | — | vậy em xin sát nhận lại toàn bộ thông tin của chị như sau |
| 162.2 | CONTENT | cố canh cước không dơn là «[dãy số ẩn]» | vậy em xin sát nhận lại toàn bộ thông tin của chị như sau |
| 176.5 | rỗng | — | em đã cập nhật lại số căn cước công dân của chị là 4 năm |
| 178.0 | rỗng | — | để em xác nhận lại toàn bộ thông tin chị vừa cung cấp nhé |
| 184.6 | rỗng | — | số căn cước công dân 4 năm |
| 188.8 | CONTENT | tú canh cướp công dân sai lỗi tú canh cướp công dân là «[dãy số ẩn]» | số điện thoại |
| 202.4 | CONTENT | đó mời nó | dạ vâng |
| 208.7 | rỗng | — | em xin lỗi chị ạ |
| 214.9 | backchannel | đúng rồi | em đã ghi nhận lại số căn cước công dân chính xác của chị là 4 năm |
| 216.6 | backchannel | đúng rồi | để em xác nhận lại toàn bộ thông tin chị vừa cung cấp nhé |
| 226.8 | rỗng | — | số căn cước công dân 4 năm |
| 236.8 | CONTENT | 4 số cuối trẻ là 4 | chị vui lòng xác nhận xem các thông tin trên đã chính xác chưa ạ |
| 249.9 | CONTENT | ờ xác nhận hỗ trĩ luôn đi | để em xác nhận lại toàn bộ thông tin chính xác của chị trước khi kiểm tra với hệ thống nhé |
| 257.3 | rỗng | — | em xin sách nhận lại toàn bộ thông tin của chị như sau |
| 267.0 | rỗng | — | số điện thoại |
| 271.1 | backchannel | đó | bốn số cuối thẻ «[dãy số ẩn]» |
| 274.9 | rỗng | — | chị vui lòng cho em biết các thông tin trên đã chính xác chữa |
| 290.1 | rỗng | — | dạ vâng em đã xác thực thành công toàn bộ thông tin của chị với hệ thống ạ |
| 298.2 | CONTENT | «[dãy số ẩn]» | bây giờ em sẽ gửi mã otp đến số điện thoại «[dãy số ẩn]» của chị để xác minh cuối cùng trước khi khóa thẻ |
| 317.2 | rỗng | — | bây giờ em xin khách thực hiện khóa thể tín dụng của chị ngay nhé |
| 323.5 | CONTENT | chuyên cô ấy với đợt quy | chị có cần em hỗ trợ thêm gì nữa không ạ |

**Cách đọc bảng:**

- **Cột `t (s)`** chính là dòng thời gian barge-in, thay cho biểu đồ, đọc từ trên xuống là theo tiến trình cuộc gọi.
- **Nhóm CONTENT** là chỗ khách đọc lại số hoặc phản đối "không phải, sai", đây là mốc bot đáng lẽ phải dừng.
- **Nhóm rỗng** phần lớn rơi vào lúc bot đọc lại sai "4 năm", tiếng khách quá ngắn hoặc chỉ là phản ứng không thành lời.
- **Nhóm backchannel** như "đúng rồi", "mình", "đó" là khách giữ nhịp, không cần bot dừng hẳn.

---

## 4. Cách tái lập

- **Nguồn:** `fci_voice_agent/data/audio_interrupt/*.wav`, 37 file μ-law 8kHz hai kênh.
- **Model ASR:** `kyle/vi-asr-fastconformer-114m` bản `s3-fc115m-full.nemo`, chạy CPU qua `nvidia_asr_nemo/deploy/asr_vi/infer.py`.
- **Bước đo:**
  - giải mã μ-law sang PCM16 bằng ffmpeg, tách hai kênh,
  - tính năng lượng khung 20 mili-giây, lấy ngưỡng Otsu tách tiếng nói khỏi im lặng,
  - đánh dấu barge-in tại onset kênh khách khi kênh bot đang bật, gộp mốc cách nhau dưới 1,5 giây,
  - cắt clip khách tại mỗi mốc rồi transcribe, phân nhóm bằng luật từ vựng có chữ số và từ sửa.
- **Ghi chú độ tin:**
  - transcript là bản thô có lỗi nhỏ như "canh cước" thay "căn cước",
  - đủ để phân nhóm nhưng chưa phải nhãn vàng, còn cần nghe kiểm một lượt.

---

## ✅ Tự kiểm nhanh

- **Vì sao cột `t (s)` thay được biểu đồ dòng thời gian?**
  <details><summary>đáp án</summary>
  đọc cột thời gian từ trên xuống chính là trình tự các mốc barge-in trong cuộc gọi, kèm loại và nội dung hai phía.
  </details>
- **Vì sao nhiều mốc rơi vào nhóm rỗng?**
  <details><summary>đáp án</summary>
  VAD năng lượng bắt cả tiếng thở và phản ứng cực ngắn không thành lời; ASR trả rỗng nên lọc ra được, đúng vai trò của bước đọc nội dung.
  </details>
- **Dãy số trong transcript đi đâu?**
  <details><summary>đáp án</summary>
  đã thay bằng `«[dãy số ẩn]»` để không đưa số điện thoại và số căn cước thật vào git.
  </details>
