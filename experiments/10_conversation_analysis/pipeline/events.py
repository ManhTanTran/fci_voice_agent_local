"""Tang A3-A7 — dung luot, rut su kien barge-in, tinh dac trung, hanh vi bot, metrics.

Toan bo TAT DINH: khong phan doan barge-in hay khong (viec do de agent/human lam sau).
Chi cung cap dac trung de nguoi va agent quyet dinh nhanh, va do hanh vi that cua bot.
"""
from __future__ import annotations
import re
import numpy as np
from . import audio as A

# ---------- tu vung tat dinh (khong phai phan doan, chi khop chuoi) ----------
DIGITS = {"một","hai","ba","bốn","năm","sáu","bảy","tám","chín","không","mười"}
STOPWORDS = ["dừng lại","dừng","khoan đã","khoan","chờ chút","chờ đã","chờ đấy","chờ",
             "đợi","thôi","ngừng","stop","dừng đã"]
BACKCHANNEL = {"dạ","vâng","ừ","ừm","à","ờ","ạ","đúng","rồi","đúng rồi","dạ vâng",
               "vâng ạ","ok","okê","đó","uh","hm","ừa","ừm ừm"}


def segments_from_mask(mask, gap_s=0.3, min_dur_s=0.15):
    """mask frame bool -> list (start_s,end_s) da gop khoang gan va bo doan qua ngan."""
    segs = []
    i, n = 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            segs.append([A.frame_time(i), A.frame_time(j)])
            i = j
        else:
            i += 1
    if not segs:
        return []
    merged = [segs[0]]
    for s, e in segs[1:]:
        if s - merged[-1][1] <= gap_s:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged if e - s >= min_dur_s]


def assign_bot_channel(mask0, mask1, head_s=4.0):
    """Callbot chao truoc -> kenh active nhieu hon trong 4s dau la bot."""
    hf = int(head_s * 1000 / A.HOP_MS)
    return 0 if mask0[:hf].mean() > mask1[:hf].mean() else 1


def _active_at(mask, t):
    i = int(t * 1000 / A.HOP_MS)
    return 0 <= i < len(mask) and mask[i]


def _seg_containing(segs, t, tol=0.35):
    for s, e in segs:
        if s - tol <= t <= e + 0.05:
            return (s, e)
    return None


# ---------- dac trung noi dung (tat dinh) ----------
def content_features(text: str) -> dict:
    t = (text or "").strip().lower()
    words = t.split()
    return {
        "n_words": len(words),
        "has_digit": any(w in DIGITS for w in words),
        "has_stopword": any(sw in t for sw in STOPWORDS),
        "only_backchannel": bool(words) and all(w in BACKCHANNEL for w in words),
        "is_empty": len(words) == 0,
    }


# ---------- hanh vi bot: co dung TTS sau khi bi chen khong ----------
def bot_stop_behavior(mask_bot, onset_s, look_s=1.2, silence_need_s=0.2):
    """Sau onset khach, kenh bot co tat >=silence_need_s trong look_s khong.
    Tra (bot_stopped, stop_latency_ms|None)."""
    hop = A.HOP_MS / 1000.0
    i0 = int(onset_s / hop)
    end = min(len(mask_bot), int((onset_s + look_s) / hop))
    need = int(silence_need_s / hop)
    i = i0
    while i + need <= end:
        if not mask_bot[i:i+need].any():          # bot im lien tuc silence_need_s
            return True, round((A.frame_time(i) - onset_s) * 1000, 0)
        i += 1
    return False, None


# ---------- readback: bot doc lai co khop lai khach vua noi khong ----------
_NUM_RE = re.compile(r"(?:%s)(?:\s+(?:%s))*" % ("|".join(DIGITS), "|".join(DIGITS)))

def readback_mismatch(bot_text: str, prev_cust_text: str) -> dict:
    """Neu bot vua 'ghi nhan ... la X' ma X khong khop chuoi so khach vua doc -> nghi ASR loi.
    Tat dinh: so sanh chuoi so trich tu 2 cau."""
    def digits(s):
        s = (s or "").lower()
        return [m.group(0) for m in _NUM_RE.finditer(s)]
    bot_nums = digits(bot_text)
    cust_nums = digits(prev_cust_text)
    is_readback = any(k in (bot_text or "").lower()
                      for k in ["ghi nhận", "nhận lại", "cập nhật", "xác nhận"])
    mismatch = bool(is_readback and cust_nums and bot_nums and bot_nums[-1] != cust_nums[-1])
    return {"is_readback": is_readback, "readback_mismatch": mismatch}


def build_events(ch_cust, ch_bot, mask_cust, mask_bot, floor_cust,
                 seg_cust, seg_bot, cust_texts, bot_texts):
    """Sinh danh sach su kien barge-in ung vien + toan bo dac trung.
    cust_texts/bot_texts: list text cung thu tu seg_cust/seg_bot (co the rong)."""
    txt_cust = {tuple(round(v, 3) for v in s): t for s, t in zip(seg_cust, cust_texts)}
    txt_bot = {tuple(round(v, 3) for v in s): t for s, t in zip(seg_bot, bot_texts)}

    events = []
    for k, (cs, ce) in enumerate(seg_cust):
        # onset chi tinh la barge-in ung vien khi bot dang noi
        if not _active_at(mask_bot, cs):
            continue
        bot_seg = _seg_containing(seg_bot, cs, tol=6.0)
        prev_cust = seg_cust[k-1] if k > 0 else None
        # vung overlap = giao [cs,ce] voi bot_seg
        ov_a, ov_b = cs, min(ce, bot_seg[1]) if bot_seg else ce
        overlap = max(0.0, ov_b - ov_a)

        cust_text = txt_cust.get(tuple(round(v, 3) for v in (cs, ce)), "")
        bot_text = txt_bot.get(tuple(round(v, 3) for v in bot_seg), "") if bot_seg else ""
        prev_text = txt_cust.get(tuple(round(v, 3) for v in prev_cust), "") if prev_cust else ""

        cf = content_features(cust_text)
        stopped, lat = bot_stop_behavior(mask_bot, cs)
        rb = readback_mismatch(bot_text, prev_text)

        ev = {
            "event_id": k,
            "onset_s": round(cs, 2),
            # --- timing ---
            "cust_dur_s": round(ce - cs, 2),
            "overlap_dur_s": round(overlap, 2),
            "into_bot_s": round(cs - bot_seg[0], 2) if bot_seg else None,
            "gap_before_s": round(cs - prev_cust[1], 2) if prev_cust else None,
            # --- acoustic ---
            "cust_rms_db": round(A.rms_db(ch_cust, cs, ce), 1),
            "sir_db": round(A.rms_db(ch_cust, ov_a, ov_b) - A.rms_db(ch_bot, ov_a, ov_b), 1),
            "cust_snr_db": round(A.rms_db(ch_cust, cs, ce) - floor_cust, 1),
            "onset_slope_db": round(A.onset_slope_db(ch_cust, cs), 1),
            "zcr": round(A.zero_crossing_rate(ch_cust, cs, ce), 3),
            "spec_flatness": round(A.spectral_flatness(ch_cust, cs, ce), 3),
            # --- content (tat dinh) ---
            "cust_text": cust_text,
            **cf,
            # --- behavior that cua bot ---
            "bot_stopped": stopped,
            "stop_latency_ms": lat,
            "bot_text": bot_text,
            **rb,
            # --- nhan de trong cho human/agent dien sau ---
            "label_is_bargein": "",
            "label_group": "",
            "label_note": "",
        }
        events.append(ev)
    return events


def call_metrics(seg_cust, seg_bot, mask_cust, mask_bot, events, dur):
    """Chi so cap cuoc, bam theo cot danh gia cua FCI (sot ngat / cut nham suy tu hanh vi)."""
    stopped = [e for e in events if e["bot_stopped"]]
    lat = [e["stop_latency_ms"] for e in stopped if e["stop_latency_ms"] is not None]
    return {
        "dur_s": round(dur, 1),
        "n_turn_bot": len(seg_bot),
        "n_turn_cust": len(seg_cust),
        "n_bargein_cand": len(events),
        "n_bot_stopped": len(stopped),
        "n_bot_continued": len(events) - len(stopped),
        "stop_latency_p50_ms": round(float(np.median(lat)), 0) if lat else None,
        "n_readback_mismatch": sum(1 for e in events if e["readback_mismatch"]),
        "n_has_stopword": sum(1 for e in events if e["has_stopword"]),
        "n_empty_cand": sum(1 for e in events if e["is_empty"]),
    }
