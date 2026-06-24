# 04 — ASR Telephony (8kHz / nhiễu)

> ⬜ Stub — chưa khảo sát. Mới chốt scope.

**Scope:** ASR trong điều kiện tổng đài thật — **8kHz**, nhiễu nền, chồng tiếng. Đây là **khoảng trống** doc nội bộ 02 chưa đo (mới benchmark LLM).

**Quan hệ lab:** layer này **trỏ sang** `nvidia_asr_nemo` (lab fine-tune STT tiếng Việt trên NeMo — đã có VIVOS/CommonVoice, WER ~11%). Không nuốt code vào đây; chỉ tham chiếu kết quả + đặt bài toán telephony.

**Câu hỏi cần trả lời:**
- Model STT hiện tại chịu 8kHz/nhiễu thế nào (WER giảm bao nhiêu so với audio sạch)?
- Cần fine-tune riêng cho 8kHz không, hay denoise (layer 03) là đủ?
- Confidence của ASR có dùng được làm tín hiệu cho ASR Fallback (hỏi lại) không?
