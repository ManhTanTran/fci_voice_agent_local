# fci_voice_agent

Lab **khảo sát + thử nghiệm** bài toán **Voice AI Agent** (trợ lý thoại tổng đài) cho team Multimodal AI (FPT / FCI — FPT Smart Cloud).

> Giai đoạn hiện tại = **KHẢO SÁT + ĐỊNH NGHĨA BÀI TOÁN**, làm việc *layer by layer*.
> Đầu ra là **tài liệu + slide** rõ ràng để đồng bộ team và làm vật liệu trao đổi với team product FCI,
> KHÔNG phải chạy demo gấp.

## Bối cảnh

- FCI có hạ tầng GPU lớn (~3000 GPU NVIDIA), đang đẩy mạnh business **dịch vụ agent**: voice-bot tổng đài (đang bán) → video-bot cam giám sát (đang phát triển).
- Team là **team research**, vừa onboard, **chưa giao tiếp mạch lạc với team product** sẵn có để nắm hạ tầng/code/data cụ thể.
- Vì vậy: **chủ động khảo sát thị trường + paper + open-source trước**, dùng chính **2 tài liệu nội bộ FCI** (trong `_source/`) làm tham chiếu lõi.

## Mục tiêu

- Tạo thế hệ voice-bot **giao tiếp tự nhiên hơn** trong môi trường tổng đài điện thoại (đường truyền 8kHz, nhiễu, ồn):
  - **Nghe có chọn lọc** — duy trì mục tiêu hội thoại, không bị nhiễu dẫn dắt lan man.
  - **Phản hồi tự nhiên** — dừng khi user ngắt lời (barge-in), hỏi lại khi nghe chưa rõ.
  - **Hướng mục tiêu** — làm rõ issue → giải quyết → đóng hội thoại, không bias theo context nhiễu.
- **Thu hẹp scope** từ "voice-agent tổng quát" về các **bài toán con đo được**, rồi gom thành **hệ thống nhiều model phối hợp** (multi-solution-stack: rule-based → DL nhỏ → large model).

## Quan hệ với các lab khác

- `nvidia_vlm_vss` — repo **song sinh** (research video understanding). Cùng triết lý "phễu giảm tải" tín hiệu thô → ngữ nghĩa.
- `nvidia_asr_nemo` — **lab thành phần STT** (fine-tune ASR tiếng Việt trên NeMo). Layer `04_asr_telephony` của repo này **trỏ sang** đó, không nuốt vào.

## Cấu trúc

```
_source/        Tài liệu gốc nội bộ FCI (2 PDF) — chỉ đọc
present/        Slide đồng bộ team (Marp/markdown)
docs/           Khảo sát layer-by-layer (01–09) + triển khai (10), xem docs/00_INDEX.md
src/fci_voice/  Code tái dùng — adapter mỏng trên Pipecat (xem docs/10_implementation/01_architecture.md)
experiments/    Thí nghiệm chạy được trên DGX (01 smoke · 02 STT · 03 full loop · 04 English latency)
notebooks/      Notebook explore
data/           Audio/trace mẫu + eval (gitignore, mirror Drive)
```

Bắt đầu: đọc `docs/00_INDEX.md`. Hiện trạng triển khai: `docs/10_implementation/`.
