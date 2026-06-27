# Exp 02 — Test thông luồng tự động (English STT + WER) · RESULT

**Ngày chạy:** 2026-06-26 · **Máy:** DGX GB10 (STT chạy CPU) · **Trạng thái:** chưa commit

---

## 1. Kết quả thật

- **Cài đặt ✅** — `uv sync --extra exp02` OK trên arm64: ctranslate2 4.8 / faster-whisper 1.2.1 / datasets 2.21.
- **E0/E1 ✅** — tải 10 case + decode soundfile + load base.en OK.
- **E2:** **WER corpus = 9.65% · RTF = 0.175** (10 câu) → CPU nhanh ~6× realtime.
- **E3 ✅** — audio thật chảy qua pipeline Pipecat ra text (`InputAudioRawFrame → STT processor tự viết → TextFrame`, KHÔNG đụng internals của `WhisperSTTService`).
- **Scorecard:** VAD/turn ✅ · STT ✅ (EN) · orchestration ✅ · LLM/TTS = ⬜ MOCK · vi/8kHz = ⬜ chưa.

## 2. Chênh lệch với kỳ vọng (SPEC §5)

| Tiêu chí | Kỳ vọng | Thực tế | Khớp? |
|---|---|---|---|
| WER | ~4-5% | **9.65%** | ⚠️ cao hơn — nhưng do NORMALIZE thô, không phải acoustic |
| RTF | < 1 | 0.175 | ✅ tốt |
| E0/E1/E2/E3 | PASS | PASS | ✅ |
| LLM/TTS mock | ⬜ | ⬜ | ✅ đúng chủ ý |

## 3. Insight / bài học

- **WER 9.65% là CẬN TRÊN, không phản ánh acoustic thật:** lỗi đến từ chuẩn hóa formatting — ref "MISTER"/"CLASS" vs hyp "Mr."/"classes". Acoustic thật thấp hơn (base.en test-clean thường ~4-5%). ⇒ Bài học: tách *lỗi chuẩn-hóa* khỏi *lỗi nghe* trước khi kết luận chất lượng STT.
- **Né được bẫy arm64:** dùng `soundfile` decode thay datasets-auto-decode → tránh librosa/numba không có wheel arm64 ngon.
- **Trung thực về độ mature:** giữ LLM/TTS mock + ghi rõ scorecard để con số mature không bị thổi phồng — đúng tinh thần đo đúng cái đang có.

## 4. Việc còn lại

- LLM serving thật (`agent/`, vLLM/SGLang OpenAI-compatible) · TTS local (`tts/`).
- Chuẩn lại metric WER (tách normalization) trước khi dùng làm mốc so sánh model.
- Chuyển trục sang **tiếng Việt + telephony 8kHz** (resample + model vi + Smart Turn v3 vi).
