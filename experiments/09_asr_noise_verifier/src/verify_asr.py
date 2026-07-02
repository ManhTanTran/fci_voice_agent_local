"""Bước 3+4: Verifier - chấm PhoWhisper trên dataset nhiễu -> WER theo (noise_type x SNR).

Chạy CPU. Model mặc định PhoWhisper-small; fallback tiny nếu quá chậm (set env
PHOWHISPER_MODEL). Chuẩn hoá text nhất quán hyp & ref trước khi tính WER (jiwer).
"""
from __future__ import annotations

import csv
import os
import re
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

import jiwer
import librosa
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor

CODE_DIR = Path(__file__).resolve().parent.parent
OUT_DIR = CODE_DIR / "results"
MANIFEST_CSV = OUT_DIR / "dataset_manifest.csv"
PRED_CSV = OUT_DIR / "predictions.csv"
WER_CSV = OUT_DIR / "wer_by_snr.csv"

MODEL_NAME = os.environ.get("PHOWHISPER_MODEL", "vinai/PhoWhisper-small")
TARGET_SR = 16_000
CACHE_DIR = os.environ.get(
    "HF_HOME",
    "/tmp/claude-1000/-home-kyle-work-startup--0-iruka--1-backend/"
    "1d5ad618-87ed-4c17-9736-665ac1f1f0d6/scratchpad/hf_cache",
)


# --- chuẩn hoá text: lower + bỏ dấu câu, giữ dấu tiếng Việt, gộp khoảng trắng ---
_PUNCT = re.compile(r"[^\w\sÀ-ỹ]", flags=re.UNICODE)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    text = _PUNCT.sub(" ", text)          # bỏ dấu câu, giữ chữ (kể cả có dấu)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_manifest() -> list[dict]:
    with MANIFEST_CSV.open() as f:
        return list(csv.DictReader(f))


def main() -> None:
    torch.set_num_threads(os.cpu_count() or 4)  # tận dụng đa nhân CPU
    rows = load_manifest()
    print(f"[verify] model={MODEL_NAME} | mẫu={len(rows)} | device=cpu")

    t0 = time.time()
    processor = WhisperProcessor.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
    model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
    model.eval()
    # ép ngôn ngữ tiếng Việt + task transcribe (PhoWhisper là whisper vi)
    forced = processor.get_decoder_prompt_ids(language="vi", task="transcribe")
    print(f"[verify] nạp model xong sau {time.time()-t0:.1f}s")

    preds: list[dict] = []
    # gom hyp/ref theo nhóm (noise_type, snr) để tính WER cấp nhóm bằng jiwer
    grp_hyp: dict[tuple, list[str]] = defaultdict(list)
    grp_ref: dict[tuple, list[str]] = defaultdict(list)

    t_infer = time.time()
    for k, r in enumerate(rows):
        wav, _ = librosa.load(r["audio_filepath"], sr=TARGET_SR, mono=True)
        feats = processor(wav, sampling_rate=TARGET_SR, return_tensors="pt").input_features
        with torch.no_grad():
            ids = model.generate(feats, forced_decoder_ids=forced, max_new_tokens=128)
        hyp_raw = processor.batch_decode(ids, skip_special_tokens=True)[0]

        ref = normalize(r["transcript_goc"])
        hyp = normalize(hyp_raw)
        key = (r["noise_type"], r["snr_db"])
        grp_hyp[key].append(hyp)
        grp_ref[key].append(ref)

        preds.append({**r, "hyp_raw": hyp_raw, "ref_norm": ref, "hyp_norm": hyp})

        if (k + 1) % 20 == 0 or k == 0:
            el = time.time() - t_infer
            rate = el / (k + 1)
            eta = rate * (len(rows) - k - 1)
            print(f"[verify] {k+1}/{len(rows)} | {rate:.2f}s/mẫu | ETA {eta/60:.1f} phút")

    infer_secs = time.time() - t_infer

    # lưu predictions chi tiết
    with PRED_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(preds[0].keys()))
        w.writeheader()
        w.writerows(preds)

    # WER theo từng nhóm (noise_type x snr). clean có snr rỗng.
    wer_rows = []
    for key in sorted(grp_hyp.keys(), key=lambda x: (x[0], x[1])):
        ntype, snr = key
        wer = jiwer.wer(grp_ref[key], grp_hyp[key])
        wer_rows.append({
            "noise_type": ntype,
            "snr_db": snr if snr != "" else "clean",
            "n": len(grp_hyp[key]),
            "wer": round(wer, 4),
        })
    with WER_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["noise_type", "snr_db", "n", "wer"])
        w.writeheader()
        w.writerows(wer_rows)

    print(f"\n[verify] inference xong: {infer_secs/60:.1f} phút "
          f"({infer_secs/len(rows):.2f}s/mẫu)")
    print(f"[verify] predictions: {PRED_CSV}")
    print(f"[verify] wer_by_snr:  {WER_CSV}")

    # in bảng markdown WER-theo-nhiễu (hàng=noise_type, cột=SNR + clean)
    print_markdown_table(wer_rows)


def print_markdown_table(wer_rows: list[dict]) -> None:
    snr_cols = ["0", "5", "10", "20"]
    header_cols = snr_cols + ["clean"]
    lookup = {(r["noise_type"], str(r["snr_db"])): r["wer"] for r in wer_rows}
    ntypes = ["white", "pink", "babble"]

    print("\n### Bảng WER (%) theo noise_type × SNR\n")
    print("| noise_type | " + " | ".join(f"SNR {c}dB" for c in snr_cols) + " | clean |")
    print("|" + "---|" * (len(header_cols) + 1))
    # clean là 1 điều kiện chung (noise_type=clean); in ở cột clean cho mọi hàng
    clean_wer = lookup.get(("clean", "clean"))
    for nt in ntypes:
        cells = []
        for c in snr_cols:
            v = lookup.get((nt, c))
            cells.append(f"{v*100:.1f}" if v is not None else "-")
        cw = f"{clean_wer*100:.1f}" if clean_wer is not None else "-"
        print(f"| {nt} | " + " | ".join(cells) + f" | {cw} |")


if __name__ == "__main__":
    main()
