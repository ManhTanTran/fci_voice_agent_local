# Exp 01 — Pipecat smoke trên DGX · RESULT

**Ngày chạy:** 2026-06-26 · **Máy:** DGX Spark GB10, `aarch64` kernel 6.17 nvidia, Python 3.12.3, `uv` ở /snap/bin · **Trạng thái:** chưa commit

---

## 1. Kết quả thật

- **L0 ✅** — máy `aarch64`, `import pipecat` OK, **pipecat 1.4.0**.
- **L1 ✅** — pipeline text tối thiểu chạy hết. API core khớp 1.4.0: `Pipeline / PipelineTask / PipelineRunner / queue_frames / EndFrame` + `FrameProcessor.process_frame / push_frame`.
- **L2 kiểm kê:**

| Thành phần | Kết quả |
|---|---|
| Silero VAD | ✅ có sẵn trong base `pipecat-ai` |
| module turn (Smart Turn) | ✅ import được (chưa chạy model) |
| onnxruntime | ✅ có sẵn |
| torch / faster-whisper / NeMo / Piper / Kokoro / vLLM | ❌ chưa có (base tối thiểu) |
| onnxruntime providers | `[Azure, CPU]` — **KHÔNG có CUDAExecutionProvider** |

## 2. Chênh lệch với kỳ vọng (SPEC §5)

| Tiêu chí | Kỳ vọng | Thực tế | Khớp? |
|---|---|---|---|
| L0/L1 | PASS | PASS | ✅ |
| model nặng ❌ lần đầu | phần lớn ❌ | đúng (torch/whisper/NeMo/TTS/vLLM ❌) | ✅ |
| VAD/turn | chưa rõ | **✅ đã bundle sẵn** trong base | 🟢 tốt hơn kỳ vọng |
| onnx GPU | chưa đặt kỳ vọng | **chỉ CPU provider** | ⚠️ phát hiện ngoài dự kiến |

## 3. Insight / bài học

- **Tin tốt:** VAD + turn-module nằm sẵn trong base `pipecat-ai` → dùng được ngay, không phải dựng riêng. Đúng triết lý "Pipecat lo slot điều phối, ta lo chất lượng tại adapter".
- **Bẫy hạ tầng:** onnxruntime trên DGX chỉ có provider `[Azure, CPU]` → Silero/Smart Turn ONNX chạy **CPU**. Chấp nhận được vì model turn-detector nhỏ (đúng triết lý turn-detector CPU); muốn GPU phải `onnxruntime-gpu`/build riêng.
- **Ranh giới phải nhớ:** "turn (pipecat) ✅" mới là *import được module*, CHƯA phải Smart Turn v3 tiếng Việt chạy ở 8kHz — đó là exp sau. Đừng nhầm "có slot" với "đạt chất lượng".

## 4. Việc còn lại

- Cắm model thật vào từng slot (exp 02+): `stt/` (NeMo-vi), `turn/` (Smart Turn v3 vi @8kHz), `agent/` (LLM self-host + tool-calling).
- Nếu cần turn-detector chạy GPU: xử lý `onnxruntime-gpu` cho aarch64.
