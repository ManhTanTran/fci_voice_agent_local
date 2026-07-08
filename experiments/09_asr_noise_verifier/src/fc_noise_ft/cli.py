from __future__ import annotations

import argparse

from .config import DEFAULT_MODEL_URI, RunConfig
from .pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vivos-root", default="/kaggle/input")
    parser.add_argument("--work-dir", default="/kaggle/working/noise_ft")
    parser.add_argument("--model-uri", default=DEFAULT_MODEL_URI)
    parser.add_argument("--model-path", default="/kaggle/working/models/s3-fc115m-full.nemo")
    parser.add_argument("--hf-secret-name", default="HF_TOKEN")
    parser.add_argument("--max-train-base", type=int, default=800)
    parser.add_argument("--max-dev-base", type=int, default=120)
    parser.add_argument("--max-test-base", type=int, default=200)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--accum", type=int, default=4)
    parser.add_argument("--eval-batch-size", type=int, default=8)
    parser.add_argument("--max-epochs", type=int, default=1)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--skip-train", action="store_true")
    parser.add_argument("--skip-base-eval", action="store_true")
    return parser.parse_args()


def config_from_args(args: argparse.Namespace) -> RunConfig:
    return RunConfig(
        vivos_root=args.vivos_root,
        work_dir=args.work_dir,
        model_uri=args.model_uri,
        model_path=args.model_path,
        hf_secret_name=args.hf_secret_name,
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
    )


def main() -> None:
    run_pipeline(config_from_args(parse_args()))
