from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fc_noise_ft.config import RunConfig
from fc_noise_ft.datasets import (
    DEFAULT_VIVOS_DIR,
    DEFAULT_VIVOS_TAR,
    DEFAULT_VIVOS_URL,
    ensure_vivos,
)
from fc_noise_ft.pipeline import run_pipeline



def balanced_train_grid() -> list[tuple[str, int | None]]:
    return [
        ("clean", None),
        ("white", 10),
        ("pink", 10),
        ("babble", 5),
    ]


def balanced_eval_grid() -> list[tuple[str, int | None]]:
    return [("clean", None)] + [
        (noise_type, snr)
        for noise_type in ["white", "pink", "babble"]
        for snr in [0, 5, 10, 20]
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivos-url", default=DEFAULT_VIVOS_URL)
    parser.add_argument("--vivos-tar", default=str(DEFAULT_VIVOS_TAR))
    parser.add_argument("--vivos-dir", default=str(DEFAULT_VIVOS_DIR))
    parser.add_argument("--work-dir", default="/kaggle/working/noise_ft")
    parser.add_argument("--model-uri", default="hf://buckets/MarkTT1/vi-asr-fastconformer-114m-bucket/s3-fc115m-full.nemo")
    parser.add_argument("--model-path", default="/kaggle/working/models/s3-fc115m-full.nemo")
    parser.add_argument("--hf-secret-name", default="HF_TOKEN")
    parser.add_argument("--max-train-base", type=int, default=5000)
    parser.add_argument("--max-dev-base", type=int, default=500)
    parser.add_argument("--max-test-base", type=int, default=760)
    parser.add_argument("--max-epochs", type=int, default=22)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--accum", type=int, default=4)
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=20260708)
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-base-eval", action="store_true")
    parser.add_argument("--force-download-vivos", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    vivos_dir = ensure_vivos(
        vivos_url=args.vivos_url,
        vivos_tar=Path(args.vivos_tar),
        vivos_dir=Path(args.vivos_dir),
        force_download=args.force_download_vivos,
    )

    cfg = RunConfig(
        vivos_root=str(vivos_dir),
        work_dir=args.work_dir,
        model_uri=args.model_uri,
        model_path=args.model_path,
        hf_secret_name=args.hf_secret_name,
        seed=args.seed,
        max_train_base=args.max_train_base,
        max_dev_base=args.max_dev_base,
        max_test_base=args.max_test_base,
        batch_size=args.batch_size,
        accum=args.accum,
        eval_batch_size=args.eval_batch_size,
        max_epochs=args.max_epochs,
        lr=args.lr,
        skip_train=args.skip_train,
        skip_base_eval=args.skip_base_eval,
        train_grid=balanced_train_grid(),
        eval_grid=balanced_eval_grid(),
    )

    Path(cfg.work_dir).mkdir(parents=True, exist_ok=True)
    print("[config]", json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2, default=str), flush=True)
    results = run_pipeline(cfg)
    print("[results]", json.dumps(results, ensure_ascii=False, indent=2, default=str)[:4000], flush=True)


if __name__ == "__main__":
    main()
