# exp 02 — Test thông luồng tự động (dataset tiếng Anh) → đo độ mature

> **Mục tiêu:** chạy tự động test case audio THẬT qua hệ thống, chấm điểm hệ thống
> mature đến đâu. Dùng dataset tiếng Anh sẵn (LibriSpeech dummy của HF) làm chuẩn để
> đo WER — số khách quan đầu tiên.
>
> ⚠️ Đây là **English 16kHz**, chưa phải tiếng Việt / telephony 8kHz (bước sau).

## Vì sao STT trước, LLM/TTS mock?
STT là viên gạch nền + cho **số đo khách quan (WER)**. Dùng **faster-whisper (CTranslate2)**
chạy **CPU int8** — không cần torch/CUDA (hợp GB10 lúc này). LLM cần serving, TTS cần model →
giữ **mock**, scorecard ghi rõ "chưa thật" để không tự huyễn hoặc về độ mature.

## Cách chạy
Ở máy local (sau `dgx-start`):
```bash
bash experiments/01_pipecat_dgx_smoke/sync_to_dgx.sh          # đồng bộ code
ssh dgx 'cd fci_voice_agent && bash experiments/02_e2e_flow_test/setup_dgx.sh'
```

## Các mức (graceful — lỗi in rõ, không crash)
| Mức | Kiểm | Ý nghĩa |
|---|---|---|
| **E0** | tải N=10 case (audio + transcript) | dataset + egress HF + decode ok? |
| **E1** | load faster-whisper base.en | model chạy được trên máy? |
| **E2** | transcribe thẳng → **WER + RTF** | ← con số mature của STT |
| **E3** | đẩy audio qua **pipeline Pipecat** → text | orchestration mang được frame audio thật? |

Cuối in **SCORECARD**: tầng nào thật / mock / chưa có. Báo cáo lưu `results/e2e_<ts>.txt`.

## Đọc kết quả
- **WER** thấp (vài %) trên LibriSpeech là kỳ vọng cho Whisper base.en → xác nhận STT nền ổn.
- **RTF** < 1 nghĩa là xử lý nhanh hơn thời gian thực (CPU); >1 là chậm hơn realtime.
- **E3 PASS** = audio thật chảy qua orchestration Pipecat ra text → khung lắp ráp đúng.
- Mọi `⬜ MOCK` = việc còn lại để hệ trưởng thành (LLM serving, TTS, rồi vi/8kHz).

## Bước tiếp
LLM serving thật (`agent/`, vLLM/SGLang OpenAI-compatible) · TTS local (`tts/`) ·
rồi chuyển trục sang **tiếng Việt + telephony 8kHz** (resample + model vi + Smart Turn v3 vi).
