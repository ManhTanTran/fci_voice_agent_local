from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str]) -> None:
    print("$", " ".join(map(str, cmd)), flush=True)
    subprocess.run([str(x) for x in cmd], check=True)


def ensure_hf_token_from_kaggle(secret_name: str = "HF_TOKEN") -> None:
    if os.environ.get("HF_TOKEN"):
        return
    try:
        from kaggle_secrets import UserSecretsClient

        token = UserSecretsClient().get_secret(secret_name)
        if token:
            os.environ["HF_TOKEN"] = token
    except Exception:
        pass


def ensure_bucket_cli() -> None:
    proc = subprocess.run(["hf", "--help"], capture_output=True, text=True)
    help_text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if "buckets" in help_text:
        return

    print("[hf] current CLI has no bucket support; installing huggingface_hub from GitHub main", flush=True)
    run_cmd(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "--upgrade",
            "--no-cache-dir",
            "git+https://github.com/huggingface/huggingface_hub.git",
        ]
    )
    proc = subprocess.run(["hf", "--help"], capture_output=True, text=True)
    help_text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    if "buckets" not in help_text:
        raise RuntimeError("hf CLI still has no buckets support after upgrade; restart kernel and rerun.")


def download_model(model_uri: str, model_path: str | Path) -> Path:
    path = Path(model_path)
    if path.exists() and path.stat().st_size > 100_000_000:
        print(f"[model] reuse {path} ({path.stat().st_size / 1024**2:.1f} MB)", flush=True)
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_bucket_cli()
    run_cmd(["hf", "buckets", "cp", model_uri, str(path)])
    return path
