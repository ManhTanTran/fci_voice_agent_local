# Exp 08 — Harness phát hiện lượt thoại (turn-detection, text/event-first)

Đăng ký + kết quả tách thành 2 file (chuẩn chung mọi exp):

- 📋 [SPEC.md](SPEC.md) — mục tiêu (điểm đau #2), flow event→decider→scorer, 3 bậc decider, cách chạy.
- 📊 [RESULT.md](RESULT.md) — energy-VAD 65% vs semantic 100%, lớp FP, caveat latency synthetic.

Mã nguồn: `src/fci_voice/sim/turn_*.py` · script `run_turn.py` · scenario `scenarios/{quiet,noisy}/`.
Lý thuyết: `docs/11_sim_test_system/04_turn_detection.md`.
