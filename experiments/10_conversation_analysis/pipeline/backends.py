"""Nhieu backend STT co the thay the nhau — moi backend cung interface transcribe_segments.

Tin hieu tat dinh (VAD/acoustic/behavior) GIONG nhau moi backend; chi khac phan TEXT.
Nen chay tung backend, luu dossier vao thu muc rieng out/<backend>/ (khong de nhau).

  fastconformer : model cua Ky (NeMo .nemo, 8kHz native)
  chunkformer   : khanhld/chunkformer-ctc-large-vie (CTC long-form, RTF ~0.06 CPU)
  parakeet      : nvidia/parakeet-ctc-0.6b-Vietnamese (NeMo CTC, co PnC, chay GPU)

CHOT BO PhoWhisper (2026-07-07): Whisper autoregressive -> RTF ~0.25 tren GPU GB10
(~2h cho 36 cuoc/114 phut audio), cham hon CTC ~50x. Parakeet da phu vai tro
"transformer co dau cau" ma nhanh gap 50x -> khong dung Whisper.
"""
from __future__ import annotations
import os
import numpy as np
import soundfile as sf

ASR_SR = 16000


def _resolve_device(device):
    """Device la THAM SO TUONG MINH (cpu|cuda) do nguoi van hanh truyen vao — default cpu.
    KHONG dung torch.cuda.is_available() lam CONG TAC chon device: may co the co GPU
    yeu/ban ma van muon chay CPU. is_available() chi de VALIDATE yeu cau 'cuda' (thieu GPU -> bao loi ro).
    Khi chon 'cpu', run.py da set CUDA_VISIBLE_DEVICES=-1 truoc khi import torch de lib khong tu vo GPU."""
    import torch
    dev = (device or "cpu").lower()
    if dev == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError(
                "Yeu cau --device cuda nhung torch.cuda.is_available()=False. "
                "Kiem: (1) may co GPU dung duoc khong; (2) da cai ban torch CUDA-build (torch+cuXXX) chua "
                "(ban torch+cpu khong the dung GPU).")
        return "cuda"
    if dev != "cpu":
        raise ValueError(f"device khong hop le: {device!r} (chi 'cpu' | 'cuda')")
    return "cpu"


def _clips_16k(wav_8k, segs):
    """Cat cac doan -> list array 16k float32 (Whisper/HF can 16k)."""
    from scipy.signal import resample_poly
    out = []
    for a, b in segs:
        c = wav_8k[max(0, int(a*8000)):min(len(wav_8k), int(b*8000))]
        out.append(resample_poly(c, ASR_SR, 8000).astype(np.float32) if len(c) else np.zeros(1600, np.float32))
    return out


# ---------------- FastConformer (model cua Ky) ----------------
class FastConformerASR:
    name = "fastconformer"
    REPO, FILE = "kyle/vi-asr-fastconformer-114m", "s3-fc115m-full.nemo"

    def __init__(self, device="cpu"):
        import nemo.collections.asr as nemo_asr
        from nemo.utils import logging as nlog
        nlog.set_verbosity(nlog.ERROR)
        dev = _resolve_device(device)   # device tuong minh, khong auto-detect
        path = os.environ.get("FCI_ASR_NEMO")
        if not (path and os.path.isfile(path)):
            from huggingface_hub import hf_hub_download
            path = hf_hub_download(self.REPO, self.FILE)
        self.model = nemo_asr.models.ASRModel.restore_from(path, map_location=dev)
        if dev == "cuda":
            self.model = self.model.cuda()
        self.model.eval()
        self.device = dev

    def transcribe_segments(self, wav_8k, segs, batch=16):
        if not segs:
            return []
        import tempfile
        clips = _clips_16k(wav_8k, segs)
        with tempfile.TemporaryDirectory() as td:
            paths = []
            for i, c in enumerate(clips):
                p = os.path.join(td, f"{i:04d}.wav")
                sf.write(p, c, ASR_SR)
                paths.append(p)
            out = self.model.transcribe(paths, batch_size=batch, verbose=False)
        return [_nemo_text(x) for x in out]


def _nemo_text(x):
    if hasattr(x, "text"):
        return x.text
    if isinstance(x, (list, tuple)) and x:
        return _nemo_text(x[0])
    return str(x)


# PhoWhisper (transformers Whisper) DA BO 2026-07-07 — xem docstring dau file.
# Whisper autoregressive cham hon CTC ~50x tren cung audio; Parakeet CTC thay the.


# ---------------- ChunkFormer CTC (package chunkformer) ----------------
def _parse_ts(s):
    """'00:00:03:680' (HH:MM:SS:mmm) -> giay float."""
    h, m, sec, ms = (int(x) for x in s.split(":"))
    return h*3600 + m*60 + sec + ms/1000.0


class ChunkFormerASR:
    name = "chunkformer"
    REPO = "khanhld/chunkformer-ctc-large-vie"   # ban CTC long-form, RTF ~0.06 tren CPU

    def __init__(self, device="cpu"):
        from chunkformer import ChunkFormerModel  # package chunkformer>=1.2
        dev = _resolve_device(device)   # device tuong minh; khi 'cpu' run.py da an GPU (CUDA_VISIBLE_DEVICES=-1)
        # nen package khong tu vo GPU. ChunkFormer CTC da RTF~0.06 tren CPU nen mac dinh cpu.
        self.model = ChunkFormerModel.from_pretrained(self.REPO)
        if dev == "cuda":
            self.model.model = self.model.model.cuda()   # best-effort: dat mang len GPU khi duoc yeu cau ro
        self.device = dev

    def transcribe_segments(self, wav_8k, segs, batch=1):
        """Long-form: decode CA KENH 1 lan (co timestamp) roi map ve tung VAD segment.
        Khong cat vun tung segment (khac Whisper) — CTC nhanh + on dinh tren full channel."""
        if not segs:
            return []
        import tempfile
        from scipy.signal import resample_poly
        full16 = resample_poly(wav_8k, ASR_SR, 8000).astype(np.float32)
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            sf.write(path, full16, ASR_SR)
            out = self.model.endless_decode(
                audio_path=path, chunk_size=64, left_context_size=128,
                right_context_size=128, total_batch_duration=1800, return_timestamps=True)
        finally:
            os.unlink(path)
        # out = list {decode, start, end}; doi ve (t0,t1,text) giay
        toks = [(_parse_ts(o["start"]), _parse_ts(o["end"]), o["decode"]) for o in out]
        # gan text vao tung VAD segment theo chong lan thoi gian
        texts = []
        for a, b in segs:
            words = [t[2] for t in toks if t[1] > a and t[0] < b]
            texts.append(" ".join(words).strip())
        return texts


# ---------------- Parakeet CTC 0.6B Vietnamese (NeMo, NVIDIA) ----------------
class ParakeetASR:
    name = "parakeet"
    REPO, FILE = "nvidia/parakeet-ctc-0.6b-Vietnamese", "parakeet-ctc-0.6b-vi.nemo"

    def __init__(self, device="cpu"):
        import nemo.collections.asr as nemo_asr
        from nemo.utils import logging as nlog
        nlog.set_verbosity(nlog.ERROR)
        dev = _resolve_device(device)   # device tuong minh (vd DGX: --device cuda)
        # Repo HF chi chua file .nemo -> tai roi restore_from (from_pretrained loi thieu model_config.yaml).
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(self.REPO, self.FILE)
        self.model = nemo_asr.models.ASRModel.restore_from(path, map_location=dev)
        if dev == "cuda":
            self.model = self.model.cuda()
        self.model.eval()
        self.device = dev

    def transcribe_segments(self, wav_8k, segs, batch=16):
        if not segs:
            return []
        import tempfile
        clips = _clips_16k(wav_8k, segs)
        with tempfile.TemporaryDirectory() as td:
            paths = []
            for i, c in enumerate(clips):
                p = os.path.join(td, f"{i:04d}.wav")
                sf.write(p, c, ASR_SR)
                paths.append(p)
            out = self.model.transcribe(paths, batch_size=batch, verbose=False)
        return [_nemo_text(x) for x in out]


def get_asr(name: str, device: str = "cpu"):
    """device tuong minh ('cpu'|'cuda') truyen xuong moi backend — KHONG auto-detect."""
    return {"fastconformer": FastConformerASR,
            "chunkformer": ChunkFormerASR,
            "parakeet": ParakeetASR}[name](device=device)
