from __future__ import annotations

from pathlib import Path

import jiwer
import pandas as pd

from .nemo_runner import transcribe_paths
from .text_norm import normalize_text


def eval_manifest(model, meta_csv: str | Path, name: str, work_dir: str | Path, batch_size: int) -> pd.DataFrame:
    work_dir = Path(work_dir)
    meta = pd.read_csv(meta_csv)
    hyps: list[str] = []
    print(f"[eval] {name} start: {len(meta)} samples", flush=True)

    for i in range(0, len(meta), batch_size):
        paths = meta.audio_filepath.iloc[i : i + batch_size].tolist()
        hyps.extend(transcribe_paths(model, paths, batch_size=batch_size))

    meta["hyp"] = hyps
    meta["ref"] = meta["text"].map(normalize_text)

    rows: list[dict] = []
    for (noise_type, snr), group in meta.groupby(["noise_type", "snr_db"]):
        rows.append(
            {
                "model": name,
                "noise_type": noise_type,
                "snr_db": snr,
                "n": len(group),
                "wer": jiwer.wer(group["ref"].tolist(), group["hyp"].tolist()),
            }
        )

    pred_path = work_dir / f"pred_{name}.csv"
    wer_path = work_dir / f"wer_{name}.csv"
    meta.to_csv(pred_path, index=False)
    wer_df = pd.DataFrame(rows).sort_values(["noise_type", "snr_db"])
    wer_df.to_csv(wer_path, index=False)
    print(f"[eval] {name} done: wrote {pred_path} and {wer_path}", flush=True)
    return wer_df
