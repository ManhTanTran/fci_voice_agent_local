# Exp 03 — Full loop + hội thoại cơ bản (tiếng Việt) · RESULT

**Ngày chạy:** 2026-06-26 · **Máy:** DGX GB10 (LLM GPU) · **Trạng thái:** chưa commit · **Kết luận:** THÔNG LUỒNG HẾT

---

## 1. Kết quả thật

- **C0 ✅** — torch cu130 chạy **GPU OK**: `device cuda / float16`, GPU = NVIDIA GB10. Load Qwen2.5-1.5B = 49.5s.
- **C1 ✅** — hội thoại CSKH tiếng Việt 3 lượt PASS, **GIỮ NGỮ CẢNH**: lượt "cuối tuần có mở không" hiểu đang nói về giờ mở cửa. Latency **1.2–3.5s/lượt** (80 token, lượt đầu warmup chậm).
- **C2 ✅** — full loop tuần tự (audio → STT → LLM → TTS → WAV).
- **C3 ✅** — full chain qua Pipecat (STTProc → LLMProc → TTSProc → collect), audio thật chảy hết chuỗi qua orchestration.
- **TTS:** piper-tts 1.4.2 **cài được arm64** nhưng ra **placeholder** (chưa nạp voice .onnx). Set `FCI_PIPER_MODEL` + tải voice là ra tiếng thật.

## 2. Chênh lệch với kỳ vọng (SPEC §5)

| Tiêu chí | Kỳ vọng | Thực tế | Khớp? |
|---|---|---|---|
| C0 device | cuda | cuda/fp16 GB10 | ✅ |
| C1 giữ ngữ cảnh | có | có (lượt "cuối tuần") | ✅ |
| C2/C3 vòng khép | PASS | PASS | ✅ |
| TTS | thật hoặc placeholder | placeholder | ✅ (đúng dự phòng) |
| Latency | chưa đặt ngưỡng | 1.2–3.5s/lượt | ⚠️ vượt xa target realtime TTFT 800ms |

## 3. Insight / bài học

- **GPU GB10 dùng được qua torch cu130** — chốt được đường native cho LLM nhỏ, không phải fallback CPU.
- **Latency 1.2–3.5s/lượt >> target telephony (TTFT 800ms):** đây là sinh cả-câu bằng `transformers` (không streaming, không serving). Cần vLLM/SGLang + token-streaming + barge-in để chạm realtime. → định lượng kỹ ở exp04.
- **C2 LLM trả "not enough context" là ĐÚNG:** input C2 là câu kể LibriSpeech (không phải câu hỏi) → model từ chối hợp lý, không phải lỗi.
- **TTS placeholder = plumbing đã đúng, chỉ thiếu voice:** tách rõ "khung chảy đúng" vs "có tiếng thật" để không nhầm độ mature.

## 4. Việc còn lại

- TTS tiếng Việt thật (nạp voice .onnx) → đo ở exp04 (English) trước.
- Chuyển STT sang **vi + resample 8kHz**.
- LLM **serving** (vLLM/SGLang) thay `transformers` cho đa phiên + streaming giảm latency.
- Ghép **Smart Turn v3 vi** vào turn-taking.
