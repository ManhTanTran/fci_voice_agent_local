# 10 — Triển khai (implementation track)

Track này tách khỏi các layer khảo sát (01–09, theo đường đi tín hiệu). Đây là phần
**code thật + thực nghiệm chạy được trên DGX**, đối lại với khảo sát lý thuyết.

> Quy ước: mọi tài liệu của track nằm trong folder con đánh số, KHÔNG để file loose ở root repo.

| # | File | Nội dung |
|---|------|----------|
| 00 | `00_README.md` | (file này) điểm vào track triển khai |
| 01 | [`01_architecture.md`](01_architecture.md) | **Tổng kết kiến trúc code** (as-built): Pipecat làm khung, `src/` adapter mỏng, ánh xạ `src/`↔`docs/` |
| 02 | [`02_e2e_report.md`](02_e2e_report.md) | **Report thông luồng** exp01→04 trên DGX: sơ đồ pipeline + latency từng step + scorecard maturity |

## Quan hệ với `experiments/`
- `experiments/NN_*/` = **runbook + script + kết quả** của từng lần chạy (01 smoke · 02 STT+WER · 03 full loop · 04 English latency).
- `docs/10_implementation/` = **tổng kết + report** đọc-một-chỗ, trỏ ngược về experiments.
- `src/fci_voice/` = **code tái dùng** (adapter), xem `01_architecture.md`.
