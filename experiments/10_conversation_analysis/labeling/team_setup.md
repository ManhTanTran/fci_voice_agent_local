# Hướng dẫn cho team cài và dùng tool labeling hội thoại FPT

Tool chạy ở máy cá nhân, không cần GPU. Có hai cách chia việc, chọn theo tình huống:

- **Cách A, chung một server qua mạng:**
  - đơn giản nhất, không cần tải data,
  - dùng khi cả team cùng mạng LAN hoặc cùng Tailscale với máy Kỳ.
- **Cách B, mỗi người tự chạy máy riêng:**
  - dùng khi không chung mạng hoặc muốn chạy offline,
  - cần Kỳ gửi file data zip.

---

## Cách A, chung một server qua mạng

- **Kỳ chạy server một lần trên máy mình:**
  ```bash
  cd fci_voice_agent/experiments/10_conversation_analysis
  uv run --script labeling/label_server.py
  ```
  - server in ra sẵn link chia team, ví dụ `http://10.240.232.53:8010/?user=<tên>`,
  - nếu cả team dùng Tailscale thì lấy IP Tailscale `100.x` thay cho IP LAN.
- **Kỳ gửi mỗi người một link kèm TÊN RIÊNG, bắt buộc khác nhau:**
  - An mở `http://<ip>:8010/?user=an`,
  - Bình mở `http://<ip>:8010/?user=binh`,
  - tên riêng để nhãn mỗi người lưu tách thư mục, không đè nhau.
- **Chia cuộc cho từng người để tránh làm trùng:**
  - ví dụ An làm cuộc 1 tới 12, Bình 13 tới 24, Cường 25 tới 36.
- **Lưu ý:**
  - máy Kỳ phải bật và server chạy suốt lúc team làm,
  - audio phát từ máy Kỳ nên không phải gửi data,
  - chỉ share trong mạng tin cậy vì đây là cuộc gọi thật có thông tin cá nhân.

---

## Cách B, mỗi người tự chạy máy riêng

### B1. Lấy code

```bash
git clone <repo fci_voice_agent>        # hoặc git pull nếu đã có
cd fci_voice_agent/experiments/10_conversation_analysis
```

Cần `uv` để chạy. Nếu chưa có:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### B2. Ghép data vào tool

Kỳ gửi file **`fci_labeling_data.zip`** khoảng 25MB. Giải nén NGAY TẠI thư mục `10_conversation_analysis`:

```bash
unzip /đường/dẫn/fci_labeling_data.zip
```

Sau khi giải nén, cây thư mục phải như sau:

```
10_conversation_analysis/
├── data/audio_interrupt/*.wav     <- 36 cuộc gọi (từ zip)
├── out/parakeet/*.json            <- transcript 3 model (từ zip)
├── out/s5/*.json
├── out/s6/*.json
└── labeling/                      <- code tool (từ git)
```

- **Kiểm nhanh:** trong `data/audio_interrupt/` có file `.wav`, trong `out/parakeet/` có file `.json`.

### B3. Chạy tool

```bash
uv run --script labeling/label_server.py
# mở http://localhost:8010
```

Lần đầu uv tự cài `soundfile` và `numpy`, các lần sau chạy ngay.

---

## Cách gán nhãn dùng chung cho cả hai cách

- **Cột trái** là danh sách 36 cuộc; bấm một cuộc để mở.
- **Trên cùng** là trình phát cả cuộc, tua được; bật `chỉ hiện turn cần gõ` để giấu turn rác.
- **Mỗi turn có ba nút nghe:**
  - `▶` nghe riêng kênh người nói của turn đó, sạch nhất,
  - `+ khách` hoặc `+ bot` nghe riêng kênh còn lại,
  - `2 kênh` nghe cả hai.
- **Ba nút phân loại mỗi turn:**
  - `cần gõ` là có nội dung, gõ lại cho đúng, đây là phần đo năng lực,
  - `dạ/vâng` là tiếng đế, không cần gõ,
  - `bỏ` là nhiễu hoặc không nghe rõ, loại ra.
- **Ô transcript** điền sẵn bản parakeet làm nháp, bấm tên model để đổ bản đó vào, sửa lại cho đúng.
- **Auto-save** sau khi ngừng gõ, có chữ đã lưu, không cần bấm nút lưu.
- **Tick chốt** khi một turn đã xong, để tính tiến độ.
- **Ưu tiên** turn có badge `SỐ`, đó là chuỗi số readback cần đo kỹ.

---

## Gửi kết quả về, chỉ áp dụng Cách B

Với Cách A nhãn đã nằm sẵn trên máy Kỳ nên không cần gửi.
Với Cách B, nhãn ở `labeling/gold/`, zip gửi lại Kỳ:

```bash
cd labeling
zip -r gold_$(whoami).zip gold/
```

Kỳ gộp các gold rồi chạy `build_gold_manifest.py` để ra manifest đo WER và các nhãn khác.

---

## Hỏi nhanh

- **Không chạy được vì thiếu soundfile?** dùng đúng lệnh `uv run --script`, không phải `uv run` hay `python` thường.
- **Máy khác không vào được server Kỳ?** kiểm cùng mạng chưa, và firewall máy Kỳ có mở cổng 8010 không.
- **Trình duyệt trắng trơn ở Cách B?** kiểm lại đã giải nén data đúng chỗ chưa.
- **Sửa xong có mất không?** không, auto-save ghi ra đĩa ngay.
