# exp11 — Benchmark WER ASR: chuẩn đo và chuẩn env

> **Vai trò:**
>
> Chốt một cách đo WER thống nhất cho nhiều checkpoint ASR trên bộ manifest public tiếng Việt.
>
> Ghi lại chuẩn env để không lặp lại sự cố đo hỏng vì thư viện lệch, tách rõ code với hạ tầng.

---

## 1. Mục tiêu

- So sánh công bằng nhiều checkpoint trên cùng bộ test có ground-truth:
  - `fc_s3` FastConformer 114M bản s3 (nền cũ),
  - `fc_s5` FastConformer 114M bản s5 mở rộng vocab (nền mới),
  - `parakeet` nvidia parakeet-ctc-0.6b-Vietnamese,
  - `chunkformer` khanhld chunkformer-ctc-large-vie.
- Ra một bảng WER duy nhất, hàng là tập test, cột là model, cùng RTF để thấy đánh đổi tốc độ.

---

## 2. Cách đo, chốt để số so được với nhau

- **Chuẩn hóa text, áp CHUNG cho cả ref lẫn hyp:**
  - hạ thường, bỏ dấu câu theo `[^\w\s]`, giữ nguyên chữ có dấu tiếng Việt, chuẩn NFC,
  - đồng bộ đúng `deploy/asr_vi/_common.normalize_vi` nên số khớp eval lúc train,
  - lý do bắt buộc: Parakeet có dấu câu và viết hoa, không bỏ dấu câu thì WER của Parakeet bị phạt oan.
- **WER là mức corpus:**
  - tổng thay thế cộng xóa cộng chèn chia tổng từ tham chiếu, tính qua `jiwer`,
  - không lấy trung bình WER từng câu vì câu ngắn làm lệch.
- **RTF là thời gian transcribe chia tổng thời lượng audio của tập**, đo trên cùng máy để so tốc độ.
- **Cùng manifest, cùng normalize, cùng định nghĩa WER cho mọi model** là điều kiện để bảng so có nghĩa.

---

## 3. Chuẩn env, phần quan trọng nhất để không lặp lại sự cố

- **Sự cố đã gặp ngày 2026-07-07:**
  - env `nvidia_asr_nemo` bị tụt `torch` về `2.7.1+cpu` trong khi `torchvision 0.27.1+cu130` cần `torch 2.12.1`,
  - lệch ABI làm `torchvision::nms` không tồn tại, kéo theo mọi import qua nemo và lightning sập,
  - hệ quả kép là không đo được, và bản thân env train GPU cũng hỏng cho lần chạy sau.
- **Ba nguyên nhân gốc:**
  - lock của repo `nvidia_asr_nemo` pin `torch` bản CPU, nên GPU chỉ là bản cài đè tay rất mong manh,
  - mọi lệnh `uv run` hay `uv sync` tự đồng bộ venv về đúng lock, tức kéo torch ngược về CPU,
  - venv nằm trong ổ dùng chung dưới tài khoản chung, ai chạy uv cũng ghi đè lẫn nhau, không cô lập.
- **Bộ thư viện đúng, đã kiểm chứng chạy:**
  - `torch 2.12.1+cu130`, `torchaudio 2.11.0+cu130`, `torchvision 0.27.1+cu130`, cộng `chunkformer` và `jiwer`.
- **Luật chạy để khỏi hỏng lại:**
  - chạy bằng `.venv/bin/python` trực tiếp của `nvidia_asr_nemo`, KHÔNG dùng `uv run` hay `uv sync` trong repo đó,
  - vì lock còn pin CPU nên mỗi lần gọi uv sẽ revert GPU về CPU.
- **Hướng chữa gốc, để làm ở bước chuẩn hóa:**
  - đưa torch và torchvision cu130 vào chính lock để `uv sync` khôi phục đúng bản GPU,
  - trỏ `UV_PROJECT_ENVIRONMENT` ra venv riêng ngoài ổ chung để người khác không ghi đè.

---

## 4. Cách chạy

- **Lệnh chuẩn, chạy trên DGX:**
  - `cd /home/dgxadmin/fci_voice_agent/experiments/11_asr_wer_bench`,
  - `export HF_HOME=/srv/team-share/cache/hf`,
  - `/srv/team-share/projects/nvidia_asr_nemo/.venv/bin/python run_bench.py --models fc_s3,fc_s5,parakeet,chunkformer --sets vivos,common_voice_vi,fleurs_vi,vlsp2020_100h,lsvsc,fosd,bud500,vietmed,vietsuperspeech --out out`.
- **Cờ tiện dụng:**
  - `--limit N` chỉ lấy N clip đầu mỗi tập để smoke,
  - `--batch` chỉnh batch cho model NeMo.
- **Đầu ra trong `out/`:**
  - `results.json` số chi tiết WER và RTF mỗi cặp model và tập, ghi lại sau mỗi bước nên gián đoạn không mất,
  - `table.md` bảng WER hàng là tập cột là model.

---

## 5. Thêm một checkpoint mới

- Thêm một dòng vào `MODELS` trong `run_bench.py`:
  - `nemo` nếu là file `.nemo` local, `nemo_hf` nếu tải từ HuggingFace, `chunkformer` nếu là package chunkformer,
  - đặt tên key ngắn, tên này thành tên cột trong bảng.
- Không sửa phần đo, để mọi model đi qua đúng một đường normalize và WER.

---

## ✅ Tự kiểm nhanh

- **Vì sao phải bỏ dấu câu khi tính WER?** → để Parakeet có dấu câu không bị phạt oan so với model chỉ ra chữ thường.
- **Vì sao không chạy benchmark bằng `uv run`?** → lock repo pin torch CPU, `uv run` tự sync sẽ kéo torch về CPU và làm hỏng env GPU.
- **Bộ thư viện GPU đúng gồm gì?** → torch 2.12.1, torchaudio 2.11.0, torchvision 0.27.1, đều cu130.
