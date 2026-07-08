from __future__ import annotations

from pathlib import Path

from omegaconf import OmegaConf

from noise_gen import TARGET_SR

from .text_norm import normalize_text


def runtime_info() -> dict:
    import numpy as np
    import scipy
    import torch

    return {
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "torch": torch.__version__,
        "cuda": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
    }


def restore_nemo(path: str | Path):
    import torch
    try:
        import nemo.collections.asr as nemo_asr
    except Exception as exc:
        msg = str(exc)
        if "numba.cuda.types" in msg and "NPDatetime" in msg:
            raise RuntimeError(
                "NeMo ASR import failed because Kaggle pulled an incompatible numba-cuda package. "
                "In the install cell, uninstall numba-cuda after installing NeMo, restart the kernel, "
                "then rerun from section 2."
            ) from exc
        raise

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = nemo_asr.models.ASRModel.restore_from(str(path), map_location=device)
    if device == "cuda":
        model = model.cuda()
    model.eval()
    return model


def hyp_to_text(item) -> str:
    if isinstance(item, str):
        return item
    if hasattr(item, "text"):
        return item.text
    if isinstance(item, (list, tuple)) and item:
        return hyp_to_text(item[0])
    return str(item)


def transcribe_paths(model, paths: list[str], batch_size: int) -> list[str]:
    try:
        out = model.transcribe(paths, batch_size=batch_size, return_hypotheses=False)
    except TypeError:
        try:
            out = model.transcribe(audio=paths, batch_size=batch_size)
        except TypeError:
            out = model.transcribe(paths)
    return [normalize_text(hyp_to_text(x)) for x in out]


def setup_manifest_data(model, train_manifest: Path, dev_manifest: Path, batch_size: int) -> None:
    train_cfg = OmegaConf.to_container(model.cfg.train_ds, resolve=True)
    val_cfg = OmegaConf.to_container(model.cfg.validation_ds, resolve=True)

    # Lhotse ignores use_start_end_token and pretokenize=True can slow Kaggle runs.
    train_cfg.pop("use_start_end_token", None)
    val_cfg.pop("use_start_end_token", None)

    train_cfg.update(
        {
            "manifest_filepath": str(train_manifest),
            "sample_rate": TARGET_SR,
            "batch_size": batch_size,
            "shuffle": True,
            "num_workers": 2,
            "pin_memory": True,
            "pretokenize": False,
        }
    )
    val_cfg.update(
        {
            "manifest_filepath": str(dev_manifest),
            "sample_rate": TARGET_SR,
            "batch_size": batch_size,
            "shuffle": False,
            "num_workers": 2,
            "pin_memory": True,
            "pretokenize": False,
        }
    )
    model.setup_training_data(train_data_config=train_cfg)
    model.setup_validation_data(val_data_config=val_cfg)


def fine_tune(model_path: str | Path, train_manifest: Path, dev_manifest: Path, work_dir: str | Path, cfg) -> Path:
    import torch

    try:
        import lightning.pytorch as pl
    except Exception:
        import pytorch_lightning as pl

    work_dir = Path(work_dir)
    model = restore_nemo(model_path)
    setup_manifest_data(model, train_manifest, dev_manifest, cfg.batch_size)

    optim_cfg = OmegaConf.to_container(model.cfg.optim, resolve=True)
    optim_cfg["lr"] = cfg.lr
    if isinstance(optim_cfg.get("sched"), dict):
        optim_cfg["sched"]["warmup_steps"] = 100
    model.setup_optimization(optim_config=OmegaConf.create(optim_cfg))

    trainer = pl.Trainer(
        accelerator="gpu" if torch.cuda.is_available() else "cpu",
        devices=1,
        max_epochs=cfg.max_epochs,
        precision="16-mixed" if torch.cuda.is_available() else 32,
        accumulate_grad_batches=cfg.accum,
        log_every_n_steps=10,
        enable_checkpointing=False,
    )
    model.set_trainer(trainer)
    trainer.fit(model)

    ft_path = work_dir / "fastconformer_noisy_ft.nemo"
    model.save_to(str(ft_path))
    print("[train] saved", ft_path, flush=True)
    return ft_path
