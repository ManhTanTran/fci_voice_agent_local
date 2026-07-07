#!/usr/bin/env python
"""Benchmark WER nhiều checkpoint ASR trên bộ manifest public tiếng Việt (có ground-truth).

CHẠY (trên DGX, KHÔNG qua `uv run` vì lock repo nvidia_asr_nemo pin torch CPU -> revert GPU):
  /srv/team-share/projects/nvidia_asr_nemo/.venv/bin/python run_bench.py \
      --models fc_s3,fc_s5,parakeet,chunkformer \
      --sets vivos,common_voice_vi,fleurs_vi,vlsp2020_100h,lsvsc,fosd,bud500,vietmed,vietsuperspeech \
      --out out

Cách đo (đồng bộ để so công bằng, xem SPEC.md):
  - text normalize GIỐNG deploy/asr_vi/_common.normalize_vi: hạ thường + bỏ dấu câu, giữ dấu tiếng Việt,
    áp CHUNG cho cả ref lẫn hyp -> triệt tiêu lợi thế/bất lợi dấu câu (Parakeet có PnC).
  - WER = corpus-level (tổng sub+del+ins / tổng từ ref), qua jiwer.
  - RTF = thời gian transcribe / tổng thời lượng audio của tập.
"""
from __future__ import annotations
import argparse
import gc
import json
import os
import re
import time
import unicodedata

MANIFEST_DIR = "/srv/team-share/datasets/asr_vi/_manifests"

# key -> (kind, spec). Thêm checkpoint mới = thêm 1 dòng.
MODELS = {
    "fc_s3":       ("nemo",    "/srv/team-share/models/asr_vi/s3-fc115m-full.nemo"),
    "fc_s5":       ("nemo",    "/srv/team-share/models/asr_vi/s5-vocabexp-full.nemo"),
    "parakeet":    ("nemo_hf", ("nvidia/parakeet-ctc-0.6b-Vietnamese", "parakeet-ctc-0.6b-vi.nemo")),
    "chunkformer": ("chunkformer", "khanhld/chunkformer-ctc-large-vie"),
}


def normalize_vi(text: str) -> str:
    # ĐỒNG BỘ deploy/asr_vi/_common.normalize_vi — WER công bằng cross-model.
    text = unicodedata.normalize("NFC", str(text)).lower()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def corpus_wer(refs, hyps) -> float:
    import jiwer
    r = [normalize_vi(x) for x in refs]
    h = [normalize_vi(x) for x in hyps]
    return float(jiwer.wer(r, h))


def read_manifest(path, limit=0):
    paths, refs, durs = [], [], []
    with open(path) as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            d = json.loads(line)
            paths.append(d["audio_filepath"])
            refs.append(d["text"])
            durs.append(float(d.get("duration", 0.0)))
    return paths, refs, durs


def load_model(kind, spec):
    import torch
    cuda = torch.cuda.is_available()
    if kind in ("nemo", "nemo_hf"):
        import nemo.collections.asr as na
        from nemo.utils import logging as nlog
        nlog.set_verbosity(nlog.ERROR)
        if kind == "nemo":
            path = spec
        else:
            from huggingface_hub import hf_hub_download
            path = hf_hub_download(*spec)
        cuda = torch.cuda.is_available()
        m = na.models.ASRModel.restore_from(path, map_location="cuda" if cuda else "cpu")
        if cuda:
            m = m.cuda()
        m.eval()
        return ("nemo", m)
    if kind == "chunkformer":
        from chunkformer import ChunkFormerModel
        m = ChunkFormerModel.from_pretrained(spec)
        if cuda:
            m = m.cuda()   # GB10 121GB: chạy GPU ~5x nhanh hơn CPU (224ms/clip vs ~1.25s)
        return ("chunkformer", m)
    raise ValueError(kind)


def _nemo_text(x):
    if hasattr(x, "text"):
        return x.text
    if isinstance(x, (list, tuple)) and x:
        return _nemo_text(x[0])
    return str(x)


def transcribe(handle, paths, batch=16):
    kind, m = handle
    if kind == "nemo":
        out = m.transcribe(paths, batch_size=batch, verbose=False)
        return [_nemo_text(x) for x in out]
    if kind == "chunkformer":
        texts = []
        for p in paths:
            out = m.endless_decode(
                audio_path=p, chunk_size=64, left_context_size=128,
                right_context_size=128, total_batch_duration=1800,
                return_timestamps=True)
            texts.append(" ".join(o["decode"] for o in out).strip() if isinstance(out, list) else str(out))
        return texts
    raise ValueError(kind)


def build_table(results, sets, models):
    # Bảng WER: hàng = tập, cột = model.
    hdr = "| Tập | " + " | ".join(models) + " |"
    sep = "|" + "---|" * (len(models) + 1)
    lines = [hdr, sep]
    for s in sets:
        row = [s]
        for mk in models:
            cell = results.get(mk, {}).get(s, {})
            row.append(f"{cell['wer']:.2f}" if "wer" in cell else "—")
        lines.append("| " + " | ".join(row) + " |")
    # dòng trung bình macro (bỏ tập lỗi)
    avg = ["**avg**"]
    for mk in models:
        vals = [results[mk][s]["wer"] for s in sets if "wer" in results.get(mk, {}).get(s, {})]
        avg.append(f"**{sum(vals)/len(vals):.2f}**" if vals else "—")
    lines.append("| " + " | ".join(avg) + " |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="fc_s3,fc_s5,parakeet,chunkformer")
    ap.add_argument("--sets", default="vivos,common_voice_vi,fleurs_vi,vlsp2020_100h,lsvsc,fosd,bud500,vietmed,vietsuperspeech")
    ap.add_argument("--manifest-dir", default=MANIFEST_DIR)
    ap.add_argument("--out", default="out")
    ap.add_argument("--limit", type=int, default=0, help=">0: N clip đầu mỗi tập (smoke)")
    ap.add_argument("--batch", type=int, default=16)
    args = ap.parse_args()

    import torch
    models = [m for m in args.models.split(",") if m]
    sets = [s for s in args.sets.split(",") if s]
    os.makedirs(args.out, exist_ok=True)
    print(f"# cuda={torch.cuda.is_available()} models={models} sets={sets} limit={args.limit}", flush=True)

    # Merge vào results.json có sẵn -> chạy bổ sung 1 model không mất model đã đo.
    results = {}
    rjson = os.path.join(args.out, "results.json")
    if os.path.isfile(rjson):
        try:
            with open(rjson) as f:
                results = json.load(f)
            print(f"# merge {len(results)} model có sẵn từ results.json", flush=True)
        except Exception:
            results = {}
    for mk in models:
        if mk not in MODELS:
            print(f"[skip] model không biết: {mk}", flush=True)
            continue
        kind, spec = MODELS[mk]
        t_load = time.time()
        try:
            handle = load_model(kind, spec)
        except Exception as e:
            print(f"[LOAD-ERR] {mk}: {type(e).__name__}: {e}", flush=True)
            results[mk] = {s: {"error": f"load: {e}"} for s in sets}
            continue
        print(f"[loaded] {mk} in {time.time()-t_load:.1f}s", flush=True)
        results.setdefault(mk, {})
        for s in sets:
            mpath = os.path.join(args.manifest_dir, f"{s}.test.jsonl")
            if not os.path.isfile(mpath):
                results[mk][s] = {"error": "manifest thiếu"}
                print(f"[skip] {mk}/{s}: manifest thiếu", flush=True)
                continue
            try:
                paths, refs, durs = read_manifest(mpath, args.limit)
                t0 = time.time()
                hyps = transcribe(handle, paths, args.batch)
                dt = time.time() - t0
                w = corpus_wer(refs, hyps)
                rtf = dt / max(sum(durs), 1e-9)
                results[mk][s] = {"wer": round(w * 100, 2), "rtf": round(rtf, 4),
                                  "n": len(paths), "sec": round(dt, 1)}
                print(f"[{mk}/{s}] WER={w*100:.2f} RTF={rtf:.4f} n={len(paths)} {dt:.0f}s", flush=True)
            except Exception as e:
                results[mk][s] = {"error": f"{type(e).__name__}: {e}"}
                print(f"[ERR] {mk}/{s}: {type(e).__name__}: {e}", flush=True)
            # dump tiến độ sau mỗi (model,set) để không mất khi gián đoạn
            with open(os.path.join(args.out, "results.json"), "w") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        del handle
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # Bảng cuối theo thứ tự cột chuẩn, gồm mọi model có trong results (kể cả đo ở lần trước).
    order = ["fc_s3", "fc_s5", "parakeet", "chunkformer"]
    all_models = [m for m in order if m in results] + [m for m in results if m not in order]
    table = build_table(results, sets, all_models)
    with open(os.path.join(args.out, "table.md"), "w") as f:
        f.write("# Bảng WER (%) — thấp hơn tốt hơn\n\n" + table + "\n")
    print("\n" + table, flush=True)
    print("RESULTS_DONE:", os.path.join(args.out, "results.json"), flush=True)


if __name__ == "__main__":
    main()
