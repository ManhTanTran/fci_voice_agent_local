from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np

from .config import RunConfig
from .eval import eval_manifest
from .hf_io import download_model, ensure_hf_token_from_kaggle
from .manifests import write_manifest
from .nemo_runner import fine_tune, restore_nemo, runtime_info
from .vivos_data import find_vivos_rows, split_by_utt_id


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.set_float32_matmul_precision("medium")
    except Exception:
        pass


def run_pipeline(cfg: RunConfig) -> dict:
    set_seed(cfg.seed)
    ensure_hf_token_from_kaggle(cfg.hf_secret_name)

    work_dir = Path(cfg.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    print("[env]", runtime_info(), flush=True)
    model_path = download_model(cfg.model_uri, cfg.model_path)

    df = find_vivos_rows(cfg.vivos_root)
    train_df, dev_df, test_df = split_by_utt_id(
        df,
        cfg.max_train_base,
        cfg.max_dev_base,
        cfg.max_test_base,
        cfg.seed,
    )
    print("[data] base utterances", {"train": len(train_df), "dev": len(dev_df), "test": len(test_df)}, flush=True)

    train_manifest, _ = write_manifest(train_df, "train", cfg.train_grid, train_df, work_dir)
    dev_manifest, _ = write_manifest(dev_df, "dev", cfg.eval_grid, train_df, work_dir)
    _, test_meta = write_manifest(test_df, "test", cfg.eval_grid, train_df, work_dir)

    results: dict[str, object] = {
        "config": cfg.to_dict(),
        "model_path": str(model_path),
        "work_dir": str(work_dir),
        "n_base": {"train": len(train_df), "dev": len(dev_df), "test": len(test_df)},
    }

    base_wer = None
    if not cfg.skip_base_eval:
        base_model = restore_nemo(model_path)
        base_wer = eval_manifest(base_model, test_meta, "base", work_dir, cfg.eval_batch_size)
        results["base_wer"] = base_wer.to_dict(orient="records")
        del base_model
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass

    if not cfg.skip_train:
        ft_path = fine_tune(model_path, train_manifest, dev_manifest, work_dir, cfg)
        ft_model = restore_nemo(ft_path)
        ft_wer = eval_manifest(ft_model, test_meta, "finetuned", work_dir, cfg.eval_batch_size)
        results["ft_path"] = str(ft_path)
        results["finetuned_wer"] = ft_wer.to_dict(orient="records")

        if base_wer is not None:
            summary = base_wer.merge(ft_wer, on=["noise_type", "snr_db"], suffixes=("_base", "_finetuned"))
            summary["delta_abs"] = summary["wer_finetuned"] - summary["wer_base"]
            summary["delta_rel_pct"] = 100.0 * (
                summary["wer_finetuned"] - summary["wer_base"]
            ) / summary["wer_base"].replace(0, np.nan)
            summary = summary.sort_values(["noise_type", "snr_db"])
            summary_path = work_dir / "wer_base_vs_finetuned.csv"
            summary.to_csv(summary_path, index=False)
            results["summary_path"] = str(summary_path)

    results_path = work_dir / "results.json"
    results_path.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("[done] results:", results_path, flush=True)
    return results
