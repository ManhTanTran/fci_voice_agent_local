# 13.02 — Shortlist ưu tiên: model open-source và dataset public

> **Vai trò:**
>
> Chốt danh sách thử trước cho từng subsystem và dataset chủ động lấy được.
>
> Chi tiết landscape đầy đủ ở doc survey từng lớp; ở đây chỉ giữ lựa chọn thử trước cộng lý do ngắn.

---

## Glossary

- `TSE` → **Target-Speaker Extraction** → tách đúng giọng khách khỏi nhiễu và giọng khác.
- `EOU` → **End-Of-Utterance** → mốc người nói xong lượt.
- `VAD` → **Voice Activity Detection** → phát hiện có tiếng nói hay không.
- `MCT` → **Multi-Condition Training** → trộn nhiều điều kiện nhiễu khi train.
- `RIR` → **Room Impulse Response** → đáp ứng xung phòng để mô phỏng vọng.

---

## 1. Dẫn dắt bối cảnh

- Mỗi subsystem đã có bảng khảo sát rộng, nhưng chọn thử cái nào trước lại chưa gom một chỗ:
  - tiêu chí chọn thử trước là rẻ, có weights mở, license sạch, và có đường tới tiếng Việt,
  - mọi số WER hoặc accuracy trong tài liệu đều đo trên 16kHz sạch hoặc tiếng Anh, phải tự đo lại trên 8kHz tiếng Việt.

> Doc này rút mỗi subsystem một hai lựa chọn thử trước, kèm dataset để chạy được ngay, làm đầu vào cho pha 1 và pha 2.

---

## 2. Model ưu tiên thử trước theo subsystem

| Subsystem | Thử trước | License và tiếng Việt | Vì sao |
| --- | --- | --- | --- |
| ASR | FastConformer lab rồi fine-tune 8kHz VI | tài sản nội bộ, có VI | tái dùng ngay, bật entropy confidence |
| VAD | Silero VAD | MIT, 8kHz native | rẻ, dưới 1ms CPU, chuẩn ngành |
| EOU và turn | Smart Turn v3 rồi fine-tune VI | BSD-2, có VI khoảng 81 phần trăm | mở cả weights lẫn data train |
| Target-speaker | ECAPA-TDNN làm cờ enroll | checkpoint public | bền nhất trên 8kHz, chưa tách audio |
| Barge-in | kiến trúc pause-and-confirm hai pha | tự xây | OSS chưa chín, tham chiếu LiveKit |
| Tool-calling | XGrammar trên vLLM cộng Instructor | OSS | vá format rẻ, validator cho giá trị |
| Orchestration | Pipecat hoặc LiveKit cộng LangGraph | OSS | audio realtime cộng nền nghiệp vụ |
| Guardrails | rule tầng 0 cộng Presidio PhoBERT | Granite Guardian Apache | rule rẻ, model cho ca khó |

- **Đường ASR dài hạn:** Zipformer hoặc FastConformer-Transducer fine-tune VI 8kHz; PhoWhisper và Whisper làm baseline đối chứng; Parakeet và Canary loại vì không tiếng Việt.
- **EOU tự train tiếng Việt:** theo recipe endpoint tiếng Thái, dùng PhoBERT hoặc Qwen 0.6B text-first, gắn vào node kịch bản.
- **Cần xác minh thêm:** Namo Turn Detector v1 được ghi là có tiếng Việt, đáng thử riêng.
- Chi tiết: [../04_asr_telephony/00_README.md](../04_asr_telephony/00_README.md), [../05_turn_interruption/00_README.md](../05_turn_interruption/00_README.md), [../06_llm_agent/00_README.md](../06_llm_agent/00_README.md), [../07_guardrails/00_README.md](../07_guardrails/00_README.md).

---

## 3. Dataset public chủ động lấy được

### 3.1 Tiếng Anh và quốc tế, lấy ngay

| Bộ | Dùng cho | License |
| --- | --- | --- |
| Switchboard và Fisher | proxy turn-taking telephony 8kHz | LDC cấp phép |
| Libri2Mix 8kHz | benchmark target-speaker | CC BY 4.0 nguồn |
| smart-turn-data-v3 | train và test EOU, có tiếng Việt | HF public BSD-2 |
| Full-Duplex-Bench | benchmark hành vi turn-taking | theo challenge |
| MUSAN | nhiễu babble và nhạc để trộn | CC BY 4.0 |
| RIRS_NOISES | mô phỏng vọng loa ngoài | Apache 2.0 |

- Nhóm này đủ để chạy English-first cho renderer, turn-detection, TSE, ASR augmentation mà không xin phép ai.
- Cảnh báo license: WHAM và ESC-50 là CC BY-NC, tránh dùng nếu hướng thương mại.

### 3.2 Tiếng Việt, lấy được nhưng không phải telephony hội thoại

| Bộ | Dùng cho | License |
| --- | --- | --- |
| ViMD 63 tỉnh | kho reference voice cho TTS cloning | peer-reviewed, đọc license |
| VietSuperSpeech | giọng hội thoại thật, pool đối chứng | HF public |
| VIVOS và Common Voice VI và VLSP | nguồn sạch downsample 8kHz | public |

### 3.3 Lỗ hổng cứng phải ghi rõ

- **Không có corpus telephony hội thoại 8kHz tiếng Việt công khai** tương đương Switchboard.
- **Không có dataset nhiễu telephony nội địa** tích hợp hold-music cộng babble cộng phương ngữ cộng codec.
- Đây chính là lý do bắt buộc phải simulate và generate, xem [03_data_generation_plan.md](03_data_generation_plan.md).

---

## 4. Điểm mù phải tự đo trước khi chốt

- WER telephony tiếng Việt 8kHz, FP của Smart Turn trên 8kHz, EER của ECAPA trên tiếng Việt.
- Phân rã lỗi tool-calling trên data tiếng Việt, tỉ lệ chặn nhầm của guardrail tiếng Việt.
- Mọi số hiện có là 16kHz hoặc tiếng Anh hoặc vendor tự công bố, cần harness đo lại.

---

## ✅ Tự kiểm nhanh

- **Ba lựa chọn thử trước rẻ nhất cho audio là gì?** → Silero VAD, Smart Turn v3, ECAPA-TDNN.
- **Dataset nào cho phép chạy English-first ngay?** → Switchboard hoặc Fisher, Libri2Mix, smart-turn-data-v3, MUSAN, RIR.
- **Lỗ hổng dataset cứng nhất là gì?** → không có telephony hội thoại 8kHz tiếng Việt công khai.
