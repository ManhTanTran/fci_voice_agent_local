---
marp: true
size: 16:9
paginate: true
theme: default
backgroundColor: '#f8fafc'
color: '#0f172a'
---
<!-- _class: title -->

<!-- _paginate: false -->

<style>
:root{
  --ink:#0f172a; --muted:#64748b; --line:#e2e8f0; --soft:#f8fafc; --slate:#334155; --slateS:#f1f5f9;
  --indigo:#4f46e5; --indigoS:#eef2ff;
  --blue:#2563eb;  --blueS:#eff6ff;
  --emerald:#059669; --emeraldS:#ecfdf5;
  --amber:#d97706; --amberS:#fffbeb;
  --red:#dc2626;   --redS:#fef2f2;
  --green:#16a34a; --greenS:#f0fdf4;
  --purple:#9333ea; --purpleS:#faf5ff;
}
section{
  font-family:"Segoe UI","Noto Sans",system-ui,sans-serif;
  font-size:25px; color:var(--ink); background:var(--soft);
  padding:52px 60px; line-height:1.42;
}
h1{font-size:46px; margin:0 0 10px; letter-spacing:-.5px;}
h2{font-size:33px; margin:0 0 20px; color:var(--slate);
   border-bottom:3px solid var(--blue); padding-bottom:9px;}
ul{margin:6px 0;} li{margin:4px 0;}
strong{color:var(--ink);}
a{color:var(--blue);}
small,.small{font-size:18px; color:var(--muted);}
.kicker{font-size:18px; letter-spacing:2px; text-transform:uppercase; color:var(--blue); font-weight:800;}
section::after{color:var(--muted); font-size:15px;}

section.title{background-color:#0f172a !important; background-image:linear-gradient(135deg,#0f172a,#1e3a8a 58%,#3730a3) !important; color:#fff !important; justify-content:center;}
section.title h1{color:#fff !important; font-size:52px;}
section.title h2{border:none; color:#c7d2fe !important; font-size:27px; margin-top:4px;}
section.title .brand{margin-top:26px; color:#93c5fd !important; font-weight:700; font-size:22px;}
section.title .kicker{color:#93c5fd !important;}

section.lead{background-color:#1e3a8a !important; background-image:linear-gradient(135deg,#1e3a8a,#4f46e5) !important; color:#fff !important; justify-content:center;}
section.lead h1{color:#fff !important; font-size:46px;}
section.lead .kicker{color:#c7d2fe !important;}
section.lead p{color:#dbeafe !important; font-size:23px; margin-top:12px;}

.row{display:flex; gap:20px; align-items:stretch;}
.col{flex:1;}
.take{margin-top:22px; background:#0f172a; color:#fff; padding:15px 20px; border-radius:12px; font-size:22px;}
.take b{color:#fbbf24;}

.card{background:#fff; border:1px solid var(--line); border-left:9px solid var(--blue);
  border-radius:12px; padding:16px 18px; box-shadow:0 2px 10px rgba(15,23,42,.06);}
.card h3{margin:6px 0 6px; font-size:24px;}
.card ul{padding-left:20px;} .card li{font-size:20px;}
.tag{display:inline-block; font-size:15px; font-weight:800; padding:3px 11px; border-radius:999px; background:var(--slateS); color:var(--slate);}
.indigo{border-left-color:var(--indigo);} .indigo.fill{background:var(--indigoS);}
.blue{border-left-color:var(--blue);} .blue.fill{background:var(--blueS);}
.emerald{border-left-color:var(--emerald);} .emerald.fill{background:var(--emeraldS);}
.amber{border-left-color:var(--amber);} .amber.fill{background:var(--amberS);}
.red{border-left-color:var(--red);} .red.fill{background:var(--redS);}
.green{border-left-color:var(--green);} .green.fill{background:var(--greenS);}
.purple{border-left-color:var(--purple);} .purple.fill{background:var(--purpleS);}

.cascade{display:flex; flex-direction:column; gap:4px; margin-top:4px;}
.layer{display:flex; align-items:center; gap:12px; color:#fff; border-radius:12px; padding:13px 20px; font-size:22px;}
.layer b{font-size:24px;}
.layer .to{margin-left:auto; font-size:17px; background:rgba(255,255,255,.20); padding:5px 12px; border-radius:999px;}
.L1{background:var(--indigo);} .L2{background:var(--blue);} .L3{background:var(--emerald);}
.L4{background:#fbbf24; color:#78350f;} .L4 .to{background:rgba(120,53,15,.14); color:#78350f;}
.down{align-self:center; color:var(--muted); font-size:20px; line-height:.5;}

.funnel{display:flex; flex-direction:column; gap:7px; align-items:center;}
.tier{color:#fff; border-radius:10px; padding:11px 16px; text-align:center; font-weight:700; font-size:21px;}
.tier small{color:rgba(255,255,255,.9); font-weight:400; display:block; font-size:15px;}
.t0{background:var(--green); width:100%;} .t1{background:var(--blue); width:82%;}
.t2{background:var(--indigo); width:64%;} .t3{background:var(--purple); width:48%;}

.pipe{display:flex; align-items:center; gap:8px; flex-wrap:wrap; justify-content:center; margin:8px 0;}
.chip{background:#fff; border:2px solid var(--line); border-radius:10px; padding:12px 18px; font-weight:800; font-size:22px;}
.chip.llm{background:var(--amberS); border-color:var(--amber); color:#92400e;}
.sep{color:var(--muted); font-size:26px; font-weight:800;}
.flows{margin:14px auto 0; text-align:center; background:var(--amberS); border:2px dashed var(--amber);
  border-radius:12px; padding:13px 18px; font-weight:700; max-width:86%; color:#92400e;}

.fsm{display:flex; align-items:center; gap:7px; flex-wrap:wrap; justify-content:center; margin-top:12px;}
.step{color:#fff; border-radius:10px; padding:14px 15px; font-weight:800; font-size:20px; text-align:center;}
.s1{background:#6366f1;} .s2{background:#4f46e5;} .s3{background:#4338ca;} .s4{background:#3730a3;} .s5{background:#312e81;}

.ngrid{display:grid; grid-template-columns:1fr 1.1fr 1fr; gap:14px; align-items:center; margin-top:6px;}
.core{grid-column:2; grid-row:1 / span 2; background:#0f172a; color:#fff; text-align:center;
  border-radius:16px; padding:26px 18px; font-weight:800; font-size:24px;}
.sat{background:#fff; border:1px solid var(--line); border-radius:12px; padding:13px 15px; font-size:19px;}
.state-bar{margin-top:14px; text-align:center; background:var(--indigoS); border:1px solid var(--indigo);
  border-radius:12px; padding:12px; font-weight:700; color:#3730a3;}
</style>

<p class="kicker">FCI · Voice AI Agent</p>

# Từ module của q-omni đến giá trị khách hàng

## Customer-first · bài toán và hướng cải tiến Voice AI Agent

<p class="brand">Lab QASI Multimodal (q-omni) × FCI · 2026-07-06</p>

---

## Chuỗi giá trị customer-first — 4 lớp

<div class="cascade">
  <div class="layer L1"><b>q-omni</b> — sản xuất các module của AI-Agent <span class="to">khách hàng → FCI</span></div>
  <div class="down">▼</div>
  <div class="layer L2"><b>FCI</b> — lắp module thành AI-Agent hoàn chỉnh <span class="to">khách hàng → Doanh nghiệp</span></div>
  <div class="down">▼</div>
  <div class="layer L3"><b>Doanh nghiệp</b> — tăng tỷ lệ chuyển đổi, giảm chi phí trong domain <span class="to">khách hàng → Người dùng cuối</span></div>
  <div class="down">▼</div>
  <div class="layer L4"><b>Người dùng cuối</b> — được phục vụ tốt và nhanh hơn</div>
</div>

<p class="take">Module của q-omni chỉ thực sự có giá trị khi góp phần <b>tăng tỷ lệ chuyển đổi</b> cho doanh nghiệp</p>

---

## Hai key-point cần cải tiến của Voice Agent

<div class="row">
  <div class="col card red fill">
    <span class="tag">Key-point #1</span>
    <h3>Turn-detection</h3>
    <p class="small">Module bắt nhịp lượt lời: khách nói xong chưa, có chen ngang không.</p>
    <ul>
      <li>Là module bị <b>noise</b> ảnh hưởng nặng nhất.</li>
      <li>Sai thì bot cắt lời hoặc đáp trễ, khách bỏ máy.</li>
      <li>Context: kênh 8kHz, người xung quanh, echo.</li>
    </ul>
  </div>
  <div class="col card red fill">
    <span class="tag">Key-point #2</span>
    <h3>Agent-reasoning</h3>
    <p class="small">Bộ não chọn bước tiếp theo, gọi tool, giữ đúng mục tiêu.</p>
    <ul>
      <li>Là module dễ <b>làm sai lệch luồng hội thoại</b>.</li>
      <li>Sai thì chọn nhầm bước, bịa số, lạc mục tiêu, không chốt được việc.</li>
      <li>Context: oriented conversation (not open-end conversation).</li>
    </ul>
  </div>
</div>

<p class="take">Chọn đúng key-point để dồn nguồn lực cải tiến trước.</p>

---

## Oriented vs Open-end — conversation

<div class="row">
  <div class="col card" style="border-left-color:#94a3b8;background:#f1f5f9">
    <h3>Open-end</h3>
    <ul>
      <li>Không có mục tiêu nghiệp vụ cố định.</li>
      <li>LLM tự do phản hồi theo ngữ cảnh.</li>
      <li>Dễ làm, nhưng khó kiểm soát chuyển đổi.</li>
    </ul>
  </div>
  <div class="col card green fill">
    <h3>Oriented</h3>
    <ul>
      <li>Mỗi bước đẩy hội thoại về mục tiêu nghiệp vụ.</li>
      <li>Phải giữ mục tiêu, kiểm soát từng bước.</li>
      <li>Gọi tool đúng lúc, đúng dữ liệu.</li>
    </ul>
  </div>
</div>

<p class="take"><b>Tỷ lệ chuyển đổi</b> sinh ra trong hội thoại <b>oriented</b>, không phải open-end.</p>

---

<!-- _class: lead -->

<p class="kicker">Phần 3</p>

# Hướng giải — xử lý phân tầng theo chi phí

<p>Tình huống dễ giải ở tầng rẻ; chỉ tình huống khó mới đẩy lên model đắt.<br>Hệ thống FCI đang chạy baseline — Q-omni sẽ nghiên cứu các giải pháp phức tạp tiếp theo</p>

---

## Turn-detection — xử lý phân tầng trên nền FCI

<div class="row">
  <div class="col card blue fill" style="max-width:32%">
    <h3>Tận dụng mọi nguồn dữ liệu</h3>
    <ul>
      <li>voice-audio (giọng khách)</li>
      <li>env-audio (nhiễu nền)</li>
      <li>context hội thoại (text)</li>
      <li>node đang đứng trong FSM</li>
    </ul>
  </div>
  <div class="col" style="display:flex;align-items:center">
    <div class="funnel" style="width:100%">
      <div class="tier t0">Tầng 0 · hệ thống FCI đang chạy<small>noise-detector · rule-based guardrail · rẽ nhánh tình huống ngoại lệ</small></div>
      <div class="tier t1">Tầng rẻ · classify model nhỏ</div>
      <div class="tier t2">Tầng giữa · zero-shot model</div>
      <div class="tier t3">Tầng đắt · LLM có ngữ cảnh</div>
    </div>
  </div>
</div>

<p class="take">q-omni ghép thêm <b>3 tầng ML</b> lên trên Tầng 0 của FCI, chỉ nhận các tình huống khó hoặc ngoại lệ do Tầng 0 chuyển lên.</p>

---

## Agent-reasoning — từ prompt nguyên khối sang flow-management

<div class="row">
  <div class="col card red fill">
    <span class="tag">hiện tại</span>
    <h3>FSM-based-LLM</h3>
    <ul>
      <li>Một prompt nguyên khối chứa cả kịch bản và mọi tool.</li>
      <li>LLM dễ lạc mục tiêu, chọn nhầm tool.</li>
      <li>Khó kiểm soát và khó debug.</li>
    </ul>
  </div>
  <div class="col card green fill">
    <span class="tag">hướng đi</span>
    <h3>Flow-management (Pipecat)</h3>
    <ul>
      <li>Chia kịch bản thành nhiều node, mỗi bước một mục tiêu.</li>
      <li>Giới hạn tool theo từng node.</li>
      <li>Giữ dữ liệu bằng shared state, hết phình prompt.</li>
    </ul>
  </div>
</div>

<p class="take">Đây là <b>bài toán ghép module đúng kiến trúc</b>, không phải cứ đổi sang model lớn hơn là xong.</p>

---

## Pipecat là gì

<p class="small">Framework open-source để xây voice-agent realtime. Ý tưởng lõi: tách 2 lớp độc lập.</p>

<div class="row">
  <div class="col card blue fill">
    <span class="tag">Lớp A</span>
    <h3>Data pipeline</h3>
    <p class="small">Cơ chế vận hành — cách dữ liệu chạy qua hệ thống.</p>
    <ul>
      <li>Luồng: Transport → STT → Context → LLM → TTS.</li>
      <li>Đổi provider (STT, TTS...) không đụng nghiệp vụ.</li>
    </ul>
  </div>
  <div class="col card amber fill">
    <span class="tag">Lớp B</span>
    <h3>Flows</h3>
    <p class="small">Logic hội thoại — cuộc gọi đi qua những bước nào.</p>
    <ul>
      <li>Graph các node, mỗi node một bước có mục tiêu.</li>
      <li>Điều khiển prompt và tool của LLM ngay giữa cuộc gọi.</li>
    </ul>
  </div>
</div>

<p class="take">Hai lớp tách biệt: đổi nghiệp vụ (Lớp B) không đụng audio (Lớp A), và ngược lại.</p>

---

## Pipecat — hai lớp phối hợp thế nào

<p class="small"><b>Lớp A · Data pipeline</b> — dữ liệu chạy tuần tự qua các module:</p>

<div class="pipe">
  <div class="chip">Transport</div><span class="sep">→</span>
  <div class="chip">STT</div><span class="sep">→</span>
  <div class="chip">Context</div><span class="sep">→</span>
  <div class="chip llm">LLM</div><span class="sep">→</span>
  <div class="chip">TTS</div><span class="sep">↺</span>
</div>

<div class="flows">↑ <b>Lớp B · Flows</b> — dùng graph node để đổi prompt và tool của LLM theo từng bước</div>

<p class="take">Lớp B chỉ tác động vào <b>LLM</b> (quyết mỗi lúc LLM thấy prompt và tool nào), không đụng phần audio.</p>

---

## Lớp B — cuộc gọi oriented thành FSM (ví dụ đòi nợ)

<div class="fsm">
  <div class="step s1">Chào và<br>xác minh</div><span class="sep">→</span>
  <div class="step s2">Tra<br>khoản nợ</div><span class="sep">→</span>
  <div class="step s3">Thương<br>lượng</div><span class="sep">→</span>
  <div class="step s4">Chốt<br>cam kết</div><span class="sep">→</span>
  <div class="step s5">Kết thúc<br>cuộc gọi</div>
</div>

<p class="take">Mỗi node xử lý đúng một tác vụ -> LLM gọi tool, xử lý -> trả kết quả -> chuyển sang node kế tiếp khi hoàn thành tác vụ đó. </p>
<p class="take">Cấu trúc hóa hội thoại <b>open-end → oriented</b>.</p>

---

## Bên trong một node

<div class="ngrid">
  <div class="sat">🎯 <b>Task goal</b><br>mục tiêu riêng của bước</div>
  <div class="core">1 NODE<br><span class="small" style="color:#cbd5e1">= 1 bước có mục tiêu</span></div>
  <div class="sat">🔧 <b>Tool riêng</b><br>chỉ mở tool bước này cần</div>
  <div class="sat">🪝 <b>Hook</b> trước / sau<br>thoại chờ, gọi API, kết thúc</div>
  <div class="sat">🔀 <b>Function</b><br>trả kết quả và node kế tiếp</div>
</div>

<div class="state-bar">🧠 Shared state — giữ dữ liệu xuyên suốt mọi node</div>

---

## FSM giúp gì cho guardrail và turn-detection

<p class="small">Chia hội thoại thành node không chỉ giúp reasoning — nó thu hẹp ngữ cảnh cho cả guardrail và turn-detection.</p>

<div class="row">
  <div class="col card green fill">
    <span class="tag">Guardrail</span>
    <h3>Khoanh vùng nội dung chặt hơn</h3>
    <ul>
      <li>Node biết bước hiện tại đang cần thông tin gì.</li>
      <li>Loại ngay câu thoại lan man, lạc tác vụ của node.</li>
      <li>Gom input của user về đúng chủ đề bước đó.</li>
    </ul>
  </div>
  <div class="col card blue fill">
    <span class="tag">Turn-detection</span>
    <h3>End-of-turn và barge-in có cơ sở hơn</h3>
    <ul>
      <li>EOU: chờ user trả lời đủ thông tin node cần mới chốt lượt.</li>
      <li>Node hỏi gọn, không dồn nhiều thông tin một lúc → user ít ngắt lời.</li>
      <li>Khi user ngắt: đoán thông tin theo context hẹp của node → chính xác hơn.</li>
    </ul>
  </div>
</div>

<p class="take">Node càng hẹp → guardrail và turn-detection càng có ngữ cảnh để quyết đúng.</p>

---

## Turn-detection — bản đồ các bài toán con

<p class="small"><b>Tiền xử lý âm thanh</b> — làm sạch tín hiệu trước khi quyết lượt lời:</p>

<div class="pipe">
  <div class="chip" style="text-align:center">VAD<br><small>có tiếng nói không</small></div>
  <div class="chip" style="text-align:center">Target-speaker<br><small>đúng giọng khách, khử echo</small></div>
  <div class="chip" style="text-align:center">Background-noise<br><small>lọc tiếng nền</small></div>
</div>

<div style="text-align:center;color:#64748b;font-size:22px;margin:6px 0">▼ quyết theo trạng thái bot</div>

<div class="row">
  <div class="col card blue fill">
    <span class="tag">bot đang im</span>
    <h3>EOU · end-of-turn</h3>
    <ul>
      <li>User đã nói xong chưa?</li>
      <li>Quyết thời điểm bot bắt đầu trả lời.</li>
    </ul>
  </div>
  <div class="col card amber fill">
    <span class="tag">bot đang nói</span>
    <h3>Barge-in · chen ngang</h3>
    <ul>
      <li>Có nên dừng TTS không?</li>
      <li><b>Backchannel</b>: "dạ/vâng/ừ" là đệm (nói tiếp) hay ý định ngắt thật (dừng).</li>
    </ul>
  </div>
</div>

<p class="take">Đã khảo sát kỹ ở <b>layer 05_turn_interruption</b> — taxonomy ngắt lời + phân tầng barge-in (deck kỹ thuật T6–T8).</p>

---

## Cách q-omni chủ động join sâu cùng FCI — đi lên từ data

<p class="small">Hệ thống hóa cách làm việc, bắt đầu từ dữ liệu — không nhảy ngay vào bài toán phức tạp.</p>

<div class="row">
  <div class="col card blue fill">
    <h3>1 · Hiểu dữ liệu</h3>
    <p class="small">join và query đúng dữ liệu cần từ FCI.</p>
  </div>
  <div class="col card indigo fill">
    <h3>2 · Data analysis</h3>
    <p class="small">chủ động bóc tách, tìm pattern và issue.</p>
  </div>
  <div class="col card purple fill">
    <h3>3 · Bộ monitor chất lượng</h3>
    <p class="small">chuẩn hóa thành công cụ giám sát hội thoại.</p>
  </div>
  <div class="col card emerald fill">
    <h3>4 · Nắm data + issue liên tục</h3>
    <p class="small">nền vững rồi mới tính bài toán phức tạp hơn.</p>
  </div>
</div>

<p class="take">Chủ động nắm chắc <b>data và issue</b> một cách liên tục trước; việc phức tạp hơn tính sau.</p>

---

## 4 nội dung muốn thống nhất với FCI

<div class="row">
  <div class="col card indigo fill"><h3>1 · Chuỗi giá trị</h3><p class="small">Ranh giới bàn giao giữa module (q-omni) và AI-Agent tích hợp (FCI) ở đâu.</p></div>
  <div class="col card blue fill"><h3>2 · Thứ tự ưu tiên</h3><p class="small">Cải tiến turn-detection (noise) hay agent-reasoning (oriented) trước.</p></div>
</div>

<div class="row" style="margin-top:14px">
  <div class="col card emerald fill"><h3>3 · Kiến trúc reasoning</h3><p class="small">FCI đã theo flow-management chưa, hay còn prompt nguyên khối.</p></div>
  <div class="col card amber fill"><h3>4 · Truy cập dữ liệu</h3><p class="small">Mở data để q-omni join, query và dựng monitor chất lượng.</p></div>
</div>

---

<!-- _class: title -->

<!-- _paginate: false -->

# Cảm ơn và thảo luận

<p class="brand">Nguyên tắc cốt lõi: module của q-omni được đo bằng tỷ lệ chuyển đổi thực tế của doanh nghiệp.</p>
