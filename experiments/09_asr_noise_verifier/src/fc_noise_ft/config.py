from __future__ import annotations

from dataclasses import asdict, dataclass, field


DEFAULT_MODEL_URI = "hf://buckets/MarkTT1/vi-asr-fastconformer-114m-bucket/s3-fc115m-full.nemo"


def default_train_grid() -> list[tuple[str, int | None]]:
    return [
        ("clean", None),
        ("white", 5),
        ("pink", 5),
        ("babble", 5),
        ("babble", 10),
    ]


def default_eval_grid() -> list[tuple[str, int | None]]:
    return [("clean", None)] + [
        (noise_type, snr)
        for noise_type in ["white", "pink", "babble"]
        for snr in [0, 5, 10, 20]
    ]


@dataclass
class RunConfig:
    vivos_root: str = "/kaggle/input"
    work_dir: str = "/kaggle/working/noise_ft"
    model_uri: str = DEFAULT_MODEL_URI
    model_path: str = "/kaggle/working/models/s3-fc115m-full.nemo"
    hf_secret_name: str = "HF_TOKEN"
    seed: int = 20260708

    max_train_base: int = 800
    max_dev_base: int = 120
    max_test_base: int = 200

    batch_size: int = 4
    accum: int = 4
    eval_batch_size: int = 8
    max_epochs: int = 1
    lr: float = 1e-4

    skip_train: bool = False
    skip_base_eval: bool = False

    train_grid: list[tuple[str, int | None]] = field(default_factory=default_train_grid)
    eval_grid: list[tuple[str, int | None]] = field(default_factory=default_eval_grid)

    def to_dict(self) -> dict:
        return asdict(self)
