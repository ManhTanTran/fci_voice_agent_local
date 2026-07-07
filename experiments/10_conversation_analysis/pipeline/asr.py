"""Tang A2 — ASR hai kenh bang FastConformer 114M da train.

Nap model 1 lan, transcribe hang loat doan cat san. Chay CPU duoc (cham nhung on).
Model lay tu HF cache; neu chua co thi tu tai (repo private, can HF token da login).
"""
from __future__ import annotations
import os, tempfile
import numpy as np
import soundfile as sf

REPO = "kyle/vi-asr-fastconformer-114m"
NEMO_FILE = "s3-fc115m-full.nemo"
ASR_SR = 16000     # NeMo tu resample nhung cat san 16k cho gon


def resolve_model_path() -> str:
    env = os.environ.get("FCI_ASR_NEMO")
    if env and os.path.isfile(env):
        return env
    from huggingface_hub import hf_hub_download
    return hf_hub_download(REPO, NEMO_FILE)   # dung cache neu da tai


class ASR:
    def __init__(self):
        import torch
        import nemo.collections.asr as nemo_asr
        from nemo.utils import logging as nlog
        nlog.set_verbosity(nlog.ERROR)
        path = resolve_model_path()
        cuda = torch.cuda.is_available()
        self.model = nemo_asr.models.ASRModel.restore_from(
            path, map_location="cuda" if cuda else "cpu")
        if cuda:
            self.model = self.model.cuda()
        self.model.eval()
        self.device = "cuda" if cuda else "cpu"

    def transcribe_segments(self, wav_8k: np.ndarray, segs, batch=16):
        """wav_8k: mot kenh @8kHz. segs: list (start_s,end_s). Tra list text cung do dai segs."""
        if not segs:
            return []
        from scipy.signal import resample_poly
        with tempfile.TemporaryDirectory() as td:
            paths = []
            for i, (a, b) in enumerate(segs):
                clip = wav_8k[max(0, int(a*8000)):min(len(wav_8k), int(b*8000))]
                clip16 = resample_poly(clip, ASR_SR, 8000) if len(clip) else np.zeros(1600)
                p = os.path.join(td, f"{i:04d}.wav")
                sf.write(p, clip16.astype(np.float32), ASR_SR)
                paths.append(p)
            out = self.model.transcribe(paths, batch_size=batch, verbose=False)
        return [_text(x) for x in out]


def _text(x) -> str:
    if hasattr(x, "text"):
        return x.text
    if isinstance(x, (list, tuple)) and x:
        return _text(x[0])
    return str(x)
