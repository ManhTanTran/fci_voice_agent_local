"""Bước 1+2: chọn subset VIVOS sạch -> sinh mẫu nhiễu tất định -> lưu manifest CSV.

Mỗi mẫu output mang nhãn by-construction: (path, transcript_goc, noise_type, snr_db).
Không tải gì: dùng manifest VIVOS test local đã có transcript.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from noise_gen import TARGET_SR, make_noise, mix_at_snr

# --- Đường dẫn cố định (data local, không tải) ---
VIVOS_MANIFEST = Path(
    "/home/kyle/work/startup/_0_iruka/_1_backend/nvidia_asr_nemo/data/manifests/vivos_test.jsonl"
)
CODE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = CODE_DIR / "results"
NOISY_DIR = OUT_DIR / "noisy_wav"          # audio nhiễu (nghe kiểm chứng)
MANIFEST_CSV = OUT_DIR / "dataset_manifest.csv"
SAMPLE_DIR = OUT_DIR / "samples"           # 2-3 wav mẫu để nghe

# --- Cấu hình thí nghiệm ---
N_CLIPS = 30                 # subset nhỏ để chạy CPU; giảm nếu quá chậm
NOISE_TYPES = ["white", "pink", "babble"]
SNR_LEVELS = [0, 5, 10, 20]  # dB; thêm điều kiện "clean" (không nhiễu)
GLOBAL_SEED = 20260702       # seed gốc để tái lập toàn bộ


def _stable_seed(*parts: str) -> int:
    """Seed tất định suy từ chuỗi (clip_id + noise_type + snr) -> nhiễu tái lập."""
    h = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return int(h[:8], 16)


def load_vivos_subset() -> list[dict]:
    """Chọn N_CLIPS clip NGẮN nhất (deterministic) -> chạy nhanh trên CPU.
    Sắp theo (duration, path) rồi lấy đầu; cùng manifest luôn ra cùng subset.
    """
    rows = []
    with VIVOS_MANIFEST.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    rows.sort(key=lambda r: (r["duration"], r["audio_filepath"]))
    subset = rows[:N_CLIPS]
    return subset


def load_clean(path: str) -> np.ndarray:
    """Đọc + resample 16kHz mono float32. Chuẩn hoá 1 lần cho cả pipeline."""
    wav, sr = librosa.load(path, sr=TARGET_SR, mono=True)
    return wav.astype(np.float32)


def build() -> None:
    NOISY_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    subset = load_vivos_subset()
    print(f"[build] VIVOS subset: {len(subset)} clip (ngắn nhất, deterministic)")

    # Nạp toàn bộ clip sạch 1 lần (để làm nguồn babble = các clip KHÁC)
    clips: list[np.ndarray] = []
    ids: list[str] = []
    texts: list[str] = []
    for r in subset:
        clips.append(load_clean(r["audio_filepath"]))
        ids.append(Path(r["audio_filepath"]).stem)
        texts.append(r["text"])

    manifest_rows: list[dict] = []
    n_samples_saved = 0

    for i, (cid, clean, text) in enumerate(zip(ids, clips, texts)):
        n = clean.size

        # 1) điều kiện clean: dùng thẳng file gốc (không copy để tiết kiệm)
        manifest_rows.append({
            "clip_id": cid,
            "audio_filepath": subset[i]["audio_filepath"],
            "transcript_goc": text,
            "noise_type": "clean",
            "snr_db": "",
        })

        # 2) các điều kiện nhiễu
        others = [c for j, c in enumerate(clips) if j != i]  # nguồn babble: clip khác
        for ntype in NOISE_TYPES:
            for snr in SNR_LEVELS:
                seed = _stable_seed(cid, ntype, str(snr))
                noise = make_noise(ntype, n, seed, others=others)
                mixed = mix_at_snr(clean, noise, float(snr))

                out_name = f"{cid}__{ntype}__snr{snr}.wav"
                out_path = NOISY_DIR / out_name
                sf.write(out_path, mixed, TARGET_SR)

                manifest_rows.append({
                    "clip_id": cid,
                    "audio_filepath": str(out_path),
                    "transcript_goc": text,
                    "noise_type": ntype,
                    "snr_db": snr,
                })

        # lưu 2-3 wav mẫu để nghe (clip đầu tiên): clean + babble 5dB + white 0dB
        if i == 0:
            sf.write(SAMPLE_DIR / f"{cid}__clean.wav", clean, TARGET_SR)
            for ntype, snr in [("babble", 5), ("white", 0)]:
                seed = _stable_seed(cid, ntype, str(snr))
                noise = make_noise(ntype, n, seed, others=others)
                mixed = mix_at_snr(clean, noise, float(snr))
                sf.write(SAMPLE_DIR / f"{cid}__{ntype}__snr{snr}.wav", mixed, TARGET_SR)
                n_samples_saved += 1
            n_samples_saved += 1

    with MANIFEST_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["clip_id", "audio_filepath",
                                          "transcript_goc", "noise_type", "snr_db"])
        w.writeheader()
        w.writerows(manifest_rows)

    print(f"[build] tổng mẫu: {len(manifest_rows)} dòng "
          f"({len(subset)} clean + {len(subset)*len(NOISE_TYPES)*len(SNR_LEVELS)} noisy)")
    print(f"[build] manifest: {MANIFEST_CSV}")
    print(f"[build] wav mẫu nghe: {SAMPLE_DIR} ({n_samples_saved} file)")


if __name__ == "__main__":
    build()
