from __future__ import annotations

import subprocess
from pathlib import Path


DEFAULT_VIVOS_URL = "https://zenodo.org/records/7068130/files/vivos.tar.gz?download=1"
DEFAULT_VIVOS_TAR = Path("/kaggle/working/vivos.tar.gz")
DEFAULT_VIVOS_DIR = Path("/kaggle/working/vivos_raw")


def run_cmd(cmd: list[str]) -> None:
    print("$", " ".join(map(str, cmd)), flush=True)
    subprocess.run([str(x) for x in cmd], check=True)


def find_prompts(root: Path) -> list[Path]:
    return sorted(root.rglob("prompts.txt"))


def ensure_vivos(vivos_url: str, vivos_tar: Path, vivos_dir: Path, force_download: bool = False) -> Path:
    prompts = find_prompts(vivos_dir)
    if prompts and not force_download:
        print("[vivos] reuse existing extracted dataset", flush=True)
        print("[vivos] prompts:", [str(p) for p in prompts[:10]], flush=True)
        return vivos_dir

    vivos_dir.mkdir(parents=True, exist_ok=True)
    if force_download or not vivos_tar.exists():
        run_cmd(["wget", "-O", str(vivos_tar), vivos_url])
    run_cmd(["tar", "-xzf", str(vivos_tar), "-C", str(vivos_dir)])

    prompts = find_prompts(vivos_dir)
    if not prompts:
        raise RuntimeError(f"No prompts.txt found after extracting VIVOS under {vivos_dir}")

    print("[vivos] prompts:", [str(p) for p in prompts[:10]], flush=True)
    return vivos_dir
