"""Các bộ quyết định lượt thoại (turn decider) — "policy" của bài turn-detection.

3 bậc năng lực, song song với policy bên tool-calling (rule -> llm -> constrained):
  - EnergyVADDecider: mô phỏng VAD theo NĂNG LƯỢNG/độ dài, MÙ ngữ nghĩa & người nói.
    Recall cao (bắt được mọi lượt nói thật) nhưng precision thấp (ngắt nhầm
    side-talk, nhạc, backchannel dài). Đây là điểm yếu ta muốn phơi bày.
  - SemanticRuleDecider: nhận biết người nói + từ vựng (backchannel / stop-keyword /
    filler) → giảm mạnh FP. Chạy local, không cần GPU.
  - LLMTurnDecider: để DGX đo sau (dùng chính LLM của agent).

QUY ƯỚC QUAN TRỌNG: decider CHỈ đọc đặc trưng quan sát được của SpeechEvent
(speaker, text, t_start_s, duration_s). KHÔNG đọc `tag`/`expected` (đó là nhãn chấm).

LƯU Ý ĐỘ TRỄ: ở chế độ text, `decided_at_ms` là MÔ HÌNH HÓA (synthetic) để minh
họa đánh đổi nhanh/đúng, KHÔNG phải ms đo thật. Số ms thật cần audio (v2/v3).
"""

from __future__ import annotations

from typing import Protocol

from .turn_types import (
    HOLD,
    INTERRUPT,
    SPK_USER,
    SpeechEvent,
    TurnDecision,
    TurnScenario,
)

# Từ vựng quan sát được (tiếng Việt CSKH tổng đài + vài từ Anh hay gặp).
# Gộp âm đệm (backchannel) + tiếng đệm nói-vấp (filler) thành 1 tập từ-đơn: một sự
# kiện mà MỌI token đều thuộc tập này -> không mang ý định ngắt -> HOLD.
_HOLD_WORDS = {
    "dạ", "vâng", "ừ", "ừm", "ờ", "à", "ạ", "ok", "okê", "uh", "uhm", "thì", "hử", "hả",
}
_STOP_KEYWORD = ("dừng", "khoan", "thôi", "stop", "bỏ qua", "đợi đã", "đợi chút", "im", "ngừng")


def _norm(text: str) -> str:
    return text.strip().lower().rstrip(".!?,")


def _tok(word: str) -> str:
    # Bỏ dấu câu rìa token để "à...", "thì," khớp được từ đệm.
    return word.strip(".,!?…-:;\"'()")


def _has_digits_run(text: str, n: int = 3) -> bool:
    run = 0
    for ch in text:
        run = run + 1 if ch.isdigit() else 0
        if run >= n:
            return True
    return False


class TurnDecider(Protocol):
    name: str

    def decide(self, scn: TurnScenario) -> TurnDecision: ...


class EnergyVADDecider:
    """VAD năng lượng: thấy thoại đủ DÀI thì ngắt, bất kể nội dung hay người nói."""

    name = "energy_vad"

    def __init__(self, sustained_ms: float = 250.0):
        # Cần tích đủ ngần này năng lượng thoại liên tục mới coi là "có người nói".
        self.sustained_ms = sustained_ms

    def decide(self, scn: TurnScenario) -> TurnDecision:
        for ev in sorted(scn.events, key=lambda e: e.t_start_s):
            # Mù speaker: noise/other/user đều là năng lượng như nhau.
            if ev.duration_s * 1000.0 >= self.sustained_ms:
                decided = ev.t_start_s * 1000.0 + self.sustained_ms
                return TurnDecision(action=INTERRUPT, decided_at_ms=decided)
        return TurnDecision(action=HOLD)


class SemanticRuleDecider:
    """Nhận biết người nói + ngữ nghĩa bề mặt để lọc FP mà VAD năng lượng bỏ sót."""

    name = "semantic_rule"

    def __init__(self, semantic_window_ms: float = 400.0):
        # Để hiểu nghĩa, cần "nghe" lâu hơn VAD → chậm hơn nhưng đúng hơn (đánh đổi).
        self.semantic_window_ms = semantic_window_ms

    def _is_interrupt_event(self, ev: SpeechEvent) -> bool:
        # Chỉ giọng KHÁCH MỤC TIÊU mới được quyền ngắt; other/noise -> bỏ qua.
        if ev.speaker != SPK_USER:
            return False
        t = _norm(ev.text)
        if not t:
            return False
        # Từ khóa dừng dứt khoát -> ngắt ngay dù ngắn.
        if any(k in t for k in _STOP_KEYWORD):
            return True
        toks = [w for w in (_tok(x) for x in t.split()) if w]
        # MỌI token là âm đệm / tiếng đệm nói-vấp -> chưa thành ý -> KHÔNG ngắt.
        if toks and all(w in _HOLD_WORDS for w in toks):
            return False
        # Còn lại: có nội dung thực chất (đủ từ hoặc có số) -> lượt nói thật -> ngắt.
        return len(toks) >= 2 or _has_digits_run(ev.text)

    def decide(self, scn: TurnScenario) -> TurnDecision:
        for ev in sorted(scn.events, key=lambda e: e.t_start_s):
            if self._is_interrupt_event(ev):
                # Chốt sau khi nghe đủ cửa sổ ngữ nghĩa (hoặc hết sự kiện nếu ngắn hơn).
                listen = min(self.semantic_window_ms, max(ev.duration_s * 1000.0, 1.0))
                decided = ev.t_start_s * 1000.0 + listen
                return TurnDecision(action=INTERRUPT, decided_at_ms=decided)
        return TurnDecision(action=HOLD)


class LLMTurnDecider:
    """Bậc 3 — dùng LLM phán đoán ý định ngắt lời. Để DGX đo sau (không chạy local)."""

    name = "llm_semantic"
    _SYS = (
        "Bạn là bộ phát hiện lượt thoại cho trợ lý tổng đài. Bot đang nói câu sau:\n"
        '"{agent}"\n'
        "Người dùng/ngoại cảnh vừa phát ra các tín hiệu thoại (theo thứ tự thời gian):\n"
        "{events}\n"
        "Hãy quyết định bot có nên NGẮT LỜI (nhường lượt cho người dùng) hay GIỮ LỜI "
        "(nói tiếp). Chỉ ngắt khi CHÍNH người dùng mục tiêu thật sự muốn nói/chen ý "
        "(trả lời sớm, sửa thông tin, hỏi ngược, yêu cầu dừng, nói đè cả câu). KHÔNG "
        "ngắt với âm đệm (dạ/vâng/ừ), nói chuyện với người bên cạnh, nói vấp rồi thôi, "
        "hay tiếng nhạc/TV.\n"
        'Trả lời DUY NHẤT một từ: INTERRUPT hoặc HOLD.'
    )

    def __init__(self, llm, semantic_window_ms: float = 400.0):
        self.llm = llm
        self.semantic_window_ms = semantic_window_ms

    def decide(self, scn: TurnScenario) -> TurnDecision:
        ev_lines = "\n".join(
            f"- [{e.speaker}] \"{e.text}\" (t={e.t_start_s:.1f}s, dài {e.duration_s:.1f}s)"
            for e in sorted(scn.events, key=lambda e: e.t_start_s)
        )
        prompt = self._SYS.format(agent=scn.agent_utterance, events=ev_lines)
        out = self.llm.chat([{"role": "user", "content": prompt}], max_new_tokens=4)
        action = INTERRUPT if "INTERRUPT" in out.upper() else HOLD
        decided = None
        if action == INTERRUPT:
            users = [e for e in scn.events if e.speaker == SPK_USER]
            onset = min((e.t_start_s for e in users), default=0.0) * 1000.0
            decided = onset + self.semantic_window_ms
        return TurnDecision(action=action, decided_at_ms=decided)


def build_decider(name: str, llm=None) -> TurnDecider:
    if name == "energy_vad":
        return EnergyVADDecider()
    if name == "semantic_rule":
        return SemanticRuleDecider()
    if name == "llm_semantic":
        if llm is None:
            raise ValueError("llm_semantic cần truyền llm (chạy trên DGX)")
        return LLMTurnDecider(llm)
    raise ValueError(f"decider không rõ: {name}")
