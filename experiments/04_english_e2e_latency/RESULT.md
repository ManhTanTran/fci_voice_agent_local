# Exp 04 — Full loop English trọn vẹn + đo latency từng step · RESULT

**Ngày chạy:** 2026-06-26 · **Máy:** DGX GB10 (STT/TTS CPU, LLM GPU) · **Trạng thái:** chưa commit · **Kết luận:** thông luồng English HẾT LƯỢT (audio → STT → LLM → TTS-thật → WAV)

---

## 1. Kết quả thật

- **TTS Piper THẬT ✅** — voice `en_US-lessac-medium` → `reply_0.wav` tiếng nói thật; piper-tts 1.4.2 synth OK arm64.
- **Latency từng step** (trung bình 3 case, đã warmup LLM, `max_new_tokens=64`):

| Step | Thiết bị | Latency |
|---|---|---|
| STT faster-whisper base.en | CPU | ~1536ms |
| LLM Qwen2.5-1.5B | GPU | ~578ms |
| TTS Piper | CPU | ~383ms |
| **Tổng tuần tự** | — | **~2496ms** |
| Qua Pipecat (STT+LLM) | — | 1841ms ✅ |

- **LLM output mạch lạc:** vd "The passage expresses gratitude for Mr. Quilter's appeal to middle-class values".
- Load (model đã cache): STT 3s / LLM 5.8s / TTS-Piper 5.5s.

## 2. Chênh lệch với kỳ vọng (SPEC §5)

| Tiêu chí | Kỳ vọng | Thực tế | Khớp? |
|---|---|---|---|
| TTS thật | WAV tiếng thật | ✅ reply_0.wav | ✅ |
| Vòng hết lượt | PASS (tuần tự + Pipecat) | PASS cả hai | ✅ |
| Latency tách step | đo được bottleneck | ✅ STT-CPU là bottleneck (~1.5s) | ✅ |
| LLM output | mạch lạc | ✅ | ✅ |
| latency tuyệt đối | (không phải mục tiêu) | ~2.5s offline | ⚠️ KHÔNG realtime — đúng cảnh báo SPEC |

## 3. Insight / bài học

- **Bottleneck = STT-CPU (~1536ms),** không phải LLM (~578ms GPU). ⇒ Ưu tiên tối ưu STT (GPU/streaming) trước khi đụng LLM.
- **Số 2.5s là OFFLINE tuần-tự cả-câu:** STT transcribe nguyên clip 5–12s SAU khi nói xong (RTF ~0.15–0.3). Kiến trúc realtime (STT streaming + token-streaming TTFT + barge-in) sẽ giảm mạnh — đừng đọc 2.5s như latency cảm nhận của người dùng.
- **Piper synth được arm64 không cần espeak ngoài** → TTS English self-host khả thi; voice tiếng Việt là việc riêng.

## 4. Việc còn lại

- Chuyển STT sang streaming / GPU để hạ bottleneck.
- Token-streaming + TTFT thật (đo latency cảm nhận, không phải tổng offline).
- Trục tiếng Việt + telephony 8kHz + Smart Turn v3 vi (barge-in).
