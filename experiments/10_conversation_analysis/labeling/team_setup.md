# Hướng dẫn cho team — cài và dùng tool labeling hội thoại FPT

Tool chạy 100% ở máy cá nhân, không cần GPU hay server.
Cần hai thứ: **code** lấy qua git, và **data** lấy qua file zip do Kỳ gửi.

---

## 1. Lấy code

```bash
git clone <repo fci_voice_agent>        # hoặc git pull nếu đã có
cd fci_voice_agent/experiments/10_conversation_analysis
```

Cần `uv` để chạy (không cần cài Python thủ công). Nếu chưa có uv:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

---

## 2. Ghép data vào tool

Kỳ gửi file **`fci_labeling_data.zip`** (khoảng 25MB). Giải nén NGAY TẠI thư mục `10_conversation_analysis`:

```bash
# đứng ở fci_voice_agent/experiments/10_conversation_analysis
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
    ├── label_server.py
    └── ...
```

- **Kiểm nhanh đã đúng chỗ chưa:** trong `data/audio_interrupt/` có các file `.wav`, và `out/parakeet/` có các file `.json`.
- Data là cuộc gọi thật có thông tin cá nhân, chỉ dùng nội bộ, không đưa lên git hay chia sẻ ra ngoài.

---

## 3. Chạy tool

```bash
uv run --script labeling/label_server.py
# mở trình duyệt: http://localhost:8010
```

Lần đầu uv tự cài `soundfile` và `numpy`, các lần sau chạy ngay.

---

## 4. Cách gán nhãn

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
- **Ô transcript** điền sẵn bản parakeet làm nháp, bấm tên model để đổ bản model đó vào, sửa lại cho đúng.
- **Auto-save** sau khi ngừng gõ, có chữ đã lưu, không cần bấm nút lưu.
- **Tick chốt** khi một turn đã xong, để tính tiến độ.
- Turn khách có thêm ô gắn barge-in và chọn nhóm nếu cần.

- **Ưu tiên:** turn có badge `SỐ` là quan trọng nhất, đó là chuỗi số readback cần đo kỹ.

---

## 5. Gửi kết quả về

Nhãn được lưu trong `labeling/gold/<call_id>.json`. Khi label xong, zip thư mục đó gửi lại Kỳ:

```bash
cd labeling
zip -r gold_$(whoami).zip gold/
# gửi file gold_<tên>.zip cho Kỳ
```

Kỳ gộp các gold rồi chạy `build_gold_manifest.py` để ra manifest đo WER và các nhãn khác.

---

## 6. Hỏi nhanh

- **Không chạy được vì thiếu soundfile?** dùng đúng lệnh `uv run --script`, không phải `uv run` hay `python` thường.
- **Mở trình duyệt trắng trơn?** kiểm lại đã giải nén data đúng chỗ chưa, xem lại cây thư mục mục 2.
- **Sửa xong có mất không?** không, auto-save ghi ra đĩa ngay, đóng trình duyệt vẫn còn.
