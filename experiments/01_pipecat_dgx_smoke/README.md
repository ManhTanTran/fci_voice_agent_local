# exp 01 — Pipecat smoke trên DGX

> **Mục tiêu:** chạy thử Pipecat lần đầu trên DGX để (1) xác nhận engine chạy nổi trên
> arm64/GB10, (2) **kiểm kê** thành phần nào self-host được — biến số "blog/vendor ⚠️
> chưa xác minh" trong `docs/` thành "đã tự chạy".
>
> ⚠️ Đây **KHÔNG** phải load-test CCU=100. DGX Spark là máy edge 1 con, không phải AI Factory.

## Câu hỏi đo được

1. Pipecat có cài + chạy một vòng tối thiểu trên GB10/arm64 không?
2. Các thành phần đã khảo sát (`03`–`06`) — cái nào import/chạy được trên máy này?

## Cách chạy

Ở **máy local** (sau khi `dgx-start` để có token Access):

```bash
# 1) đồng bộ code lên DGX (rsync, không cần git push)
bash experiments/01_pipecat_dgx_smoke/sync_to_dgx.sh

# 2) dựng env + chạy smoke trên DGX
ssh dgx 'cd fci_voice_agent && bash experiments/01_pipecat_dgx_smoke/setup_dgx.sh'
```

## Các mức (script tự bọc lỗi, in rõ thay vì crash)

| Mức | Kiểm | PASS khi |
|---|---|---|
| **L0** | python/arch + `import pipecat` | machine = aarch64, import OK, in version |
| **L1** | pipeline text tối thiểu chạy hết | text đi qua đủ chặng, kết thúc sạch |
| **L2** | probe import từng thành phần (Silero/turn/onnx/torch/whisper/NeMo/TTS/vLLM) | bảng ✅/❌ + providers onnx + torch CUDA |

Kết quả ghi vào `results/smoke_<timestamp>.txt` (gitignore — mirror Drive khi cần).

## Diễn giải kết quả

- **L0/L1 ✅** → engine OK trên GB10, có thể build tiếp pipeline thật.
- **L1 ❌** → lỗi in ra hé lộ API Pipecat thật của bản đã cài → khớp lại
  `src/fci_voice/pipeline/build.py` (vì Pipecat đổi API nhanh theo phiên bản).
- **L2** → mỗi `❌` là một việc cần làm: `uv add` extra/model tương ứng, hoặc
  xử lý wheel arm64. Hầu hết sẽ ❌ ở lần đầu (base cố ý tối thiểu) — đó chính là bản kiểm kê.

## Bước tiếp theo (exp 02+)

Theo [`docs/10_implementation/01_architecture.md`](../../docs/10_implementation/01_architecture.md) §3: cắm model thật vào từng slot — `stt/` (NeMo-vi),
`turn/` (Smart Turn v3 vi @8kHz), `agent/` (LLM self-host + tool-calling). Mỗi cái một exp riêng.
