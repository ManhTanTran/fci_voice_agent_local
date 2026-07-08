from __future__ import annotations

import random
from pathlib import Path

import pandas as pd
import soundfile as sf

from .text_norm import normalize_text


def find_vivos_rows(root: str | Path) -> pd.DataFrame:
    root = Path(root)
    prompt_files = sorted(root.rglob("prompts.txt"))
    if not prompt_files:
        raise RuntimeError("No prompts.txt found under VIVOS root. Attach a VIVOS dataset first.")

    rows: list[dict] = []
    for prompt_file in prompt_files:
        candidate_roots = [prompt_file.parent, prompt_file.parent.parent, root]
        wavs: dict[str, Path] = {}
        for candidate in candidate_roots:
            for wav in candidate.rglob("*.wav"):
                wavs.setdefault(wav.stem, wav)

        for line in prompt_file.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split(maxsplit=1)
            if len(parts) != 2:
                continue
            utt_id, text = parts
            wav = wavs.get(utt_id)
            if wav is None:
                continue
            info = sf.info(str(wav))
            rows.append(
                {
                    "utt_id": utt_id,
                    "audio_filepath": str(wav),
                    "duration": float(info.frames / info.samplerate),
                    "text": normalize_text(text),
                }
            )

    if not rows:
        raise RuntimeError("Found prompts.txt but no matching .wav files.")

    return pd.DataFrame(rows).drop_duplicates("utt_id").sort_values("utt_id").reset_index(drop=True)


def split_by_utt_id(
    df: pd.DataFrame,
    max_train: int,
    max_dev: int,
    max_test: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ids = df["utt_id"].tolist()
    random.Random(seed).shuffle(ids)

    n = len(ids)
    train_ids = ids[: int(0.8 * n)]
    dev_ids = ids[int(0.8 * n) : int(0.9 * n)]
    test_ids = ids[int(0.9 * n) :]

    by_id = df.set_index("utt_id", drop=False)
    train_df = by_id.loc[train_ids].head(max_train).reset_index(drop=True)
    dev_df = by_id.loc[dev_ids].head(max_dev).reset_index(drop=True)
    test_df = by_id.loc[test_ids].head(max_test).reset_index(drop=True)
    return train_df, dev_df, test_df
