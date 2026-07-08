from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import soundfile as sf
from tqdm.auto import tqdm

from noise_gen import TARGET_SR

from .audio import load_audio, make_noisy


def write_manifest(
    rows_df: pd.DataFrame,
    split_name: str,
    grid: list[tuple[str, int | None]],
    pool_df: pd.DataFrame,
    work_dir: str | Path,
) -> tuple[Path, Path]:
    work_dir = Path(work_dir)
    out_dir = work_dir / split_name
    wav_dir = out_dir / "wav"
    wav_dir.mkdir(parents=True, exist_ok=True)

    manifest = out_dir / "manifest.jsonl"
    meta_csv = out_dir / "meta.csv"
    meta: list[dict] = []

    with manifest.open("w", encoding="utf-8") as f:
        for row in tqdm(list(rows_df.itertuples(index=False)), desc=split_name):
            clean = load_audio(row.audio_filepath)
            duration = float(clean.size / TARGET_SR)

            for noise_type, snr in grid:
                if noise_type == "clean":
                    audio_path = row.audio_filepath
                else:
                    noisy = make_noisy(clean, noise_type, snr, row, pool_df)
                    audio_path = wav_dir / f"{row.utt_id}__{noise_type}__snr{snr}.wav"
                    sf.write(str(audio_path), noisy, TARGET_SR)
                    audio_path = str(audio_path)

                rec = {"audio_filepath": audio_path, "duration": duration, "text": row.text}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                meta.append(
                    {
                        **rec,
                        "utt_id": row.utt_id,
                        "noise_type": noise_type,
                        "snr_db": "clean" if snr is None else snr,
                    }
                )

    pd.DataFrame(meta).to_csv(meta_csv, index=False)
    return manifest, meta_csv
