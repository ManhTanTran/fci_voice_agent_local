# exp 03 — Full loop + hội thoại cơ bản (thông luồng HẾT)

> **Mục tiêu:** khép vòng voice-agent — cài **LLM nhỏ open-source** chạy trên DGX,
> test **hội thoại cơ bản**, rồi chạy **full loop audio → STT → LLM → TTS → audio**.
>
> ⚠️ STT vẫn English 16kHz; LLM/hội thoại đã tiếng Việt. Telephony 8kHz là bước sau.

## Lựa chọn (ít rủi ro, dùng đúng GPU)
- **LLM = Qwen2.5-1.5B-Instruct** qua `transformers` + **torch cu130** → chạy **GPU GB10**
  (đường native đã xác nhận trên máy này). Nhỏ, instruct tốt, biết tiếng Việt cơ bản.
- **TTS = Piper** (CPU/ONNX) nếu cài được; không thì **WAV placeholder** để vòng vẫn khép.
- **Hội thoại** = mini-dialogue CSKH tiếng Việt 3 lượt, kiểm tra **giữ ngữ cảnh**.

## Cách chạy
Ở máy local (sau `dgx-start`):
```bash
bash experiments/01_pipecat_dgx_smoke/sync_to_dgx.sh
ssh dgx 'cd fci_voice_agent && bash experiments/03_full_loop_conversation/setup_dgx.sh'
```
Có model Piper thật thì đặt `export FCI_PIPER_MODEL=/đường/dẫn/voice.onnx` trước khi chạy.

## Các mức (graceful)
| Mức | Kiểm |
|---|---|
| **C0** | load Qwen2.5-1.5B trên GPU (báo device/dtype) |
| **C1** | hội thoại CSKH tiếng Việt 3 lượt — giữ ngữ cảnh |
| **C2** | full loop tuần tự: audio → STT → LLM → TTS → WAV |
| **C3** | full chain qua **pipeline Pipecat**: audio → STT proc → LLM proc → TTS proc |

Cuối in **SCORECARD**. Báo cáo + WAV lưu `results/`.

## Đọc kết quả
- **C0 device = cuda** → torch cu130 dùng được GPU GB10 (không chỉ CPU).
- **C1** trả lời mạch lạc + lượt 2 ("cuối tuần") hiểu đang nói về giờ mở cửa = **giữ ngữ cảnh OK**.
- **C2/C3 ✅** = vòng khép, audio thật chảy hết chuỗi (qua orchestration ở C3).
- **TTS = placeholder** nghĩa là chưa phát tiếng thật (chỉ plumbing) — việc còn lại.

## Bước tiếp
TTS tiếng Việt thật · chuyển STT sang **vi + resample 8kHz** · LLM serving (vLLM/SGLang) thay
transformers cho đa phiên · ghép **Smart Turn v3 vi** vào turn-taking.
