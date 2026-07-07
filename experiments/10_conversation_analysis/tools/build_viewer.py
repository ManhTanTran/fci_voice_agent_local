"""Sinh web-tool LOCAL so sanh NHIEU phien ban STT canh nhau.

Quet cac thu muc con out/<model>/ (moi model 1 STT). VAD tat dinh nen luot trung khop
theo (speaker, t_start) giua cac model -> ghep text cac model vao cung mot luot de so.

KHONG phai Artifact claude.ai — chi la file HTML tinh trong repo, mo bang trinh duyet.

Chay:
  python tools/build_viewer.py --out out --html out/viewer.html
"""
from __future__ import annotations
import argparse, glob, json, os, sys

HTML = r"""<!doctype html>
<html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>exp10 — So sanh STT</title>
<style>
:root{
  --bg:#f5f6f8; --panel:#fff; --ink:#1a2230; --muted:#6b7688; --line:#e2e6ec;
  --bot:#2b6cb0; --bot-bg:#e8f1fb; --cust:#b7791f; --cust-bg:#fcf3e3;
  --alert:#d64545; --alert-bg:#fdecec; --ok:#2f855a;
  --m0:#2b6cb0; --m1:#7b3fa0; --m2:#1c8a6a; --m3:#c05621;
  --mono:ui-monospace,Menlo,Consolas,monospace; --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}
@media(prefers-color-scheme:dark){:root{
  --bg:#0f151d; --panel:#161d27; --ink:#e6ecf3; --muted:#8b97a8; --line:#28313d;
  --bot:#5aa2e0; --bot-bg:#16263a; --cust:#e0b060; --cust-bg:#302510;
  --alert:#f06a6a; --alert-bg:#3a1c1c; --ok:#68d391;
  --m0:#5aa2e0; --m1:#c084e8; --m2:#4fd0a6; --m3:#f6a35c;
}}
*{box-sizing:border-box} html,body{margin:0;height:100%}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);display:flex;height:100vh;overflow:hidden}
#side{width:320px;flex:none;border-right:1px solid var(--line);background:var(--panel);display:flex;flex-direction:column}
#side h1{font-size:14px;margin:0;padding:14px 16px;border-bottom:1px solid var(--line)}
#side h1 small{color:var(--muted);font-weight:400}
#search{margin:10px 12px;padding:7px 10px;border:1px solid var(--line);border-radius:7px;background:var(--bg);color:var(--ink);font-size:13px}
#list{overflow-y:auto;flex:1}
.li{padding:10px 14px;border-bottom:1px solid var(--line);cursor:pointer;font-size:13px}
.li:hover{background:var(--bg)} .li.sel{background:var(--bot-bg)}
.li .cid{font-family:var(--mono);font-size:12px;font-weight:600}
.li .mini{color:var(--muted);font-size:11.5px;margin-top:3px;display:flex;gap:10px;flex-wrap:wrap}
.badge{font-family:var(--mono);padding:0 5px;border-radius:4px;background:var(--bg)}
.badge.bg{color:var(--alert)}
#main{flex:1;display:flex;flex-direction:column;overflow:hidden}
#head{padding:12px 20px;border-bottom:1px solid var(--line);background:var(--panel)}
#head .cid{font-family:var(--mono);font-weight:600;font-size:15px}
#head .m{display:flex;gap:16px;flex-wrap:wrap;margin-top:6px;font-size:12.5px;color:var(--muted)}
#head .m b{color:var(--ink);font-variant-numeric:tabular-nums}
#toolbar{display:flex;gap:14px;align-items:center;margin-top:8px;font-size:12.5px;flex-wrap:wrap}
#toolbar label{color:var(--muted);cursor:pointer;user-select:none}
.mtag{font-family:var(--mono);font-size:11px;padding:1px 6px;border-radius:9px;border:1px solid}
.mtag.m0{color:var(--m0);border-color:var(--m0)} .mtag.m1{color:var(--m1);border-color:var(--m1)}
.mtag.m2{color:var(--m2);border-color:var(--m2)} .mtag.m3{color:var(--m3);border-color:var(--m3)}
#chat{overflow-y:auto;flex:1;padding:18px 20px}
.row{display:flex;margin:4px 0}
.row.bot{justify-content:flex-start} .row.cust{justify-content:flex-end}
.bub{max-width:70%;padding:8px 12px;border-radius:12px;font-size:14px;line-height:1.4;position:relative}
.bot .bub{background:var(--bot-bg);border:1px solid var(--line);border-bottom-left-radius:3px}
.cust .bub{background:var(--cust-bg);border:1px solid var(--line);border-bottom-right-radius:3px}
.cust .bub.bg{border:1.5px solid var(--alert);background:var(--alert-bg)}
.t{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-bottom:3px}
.line{display:flex;gap:7px;align-items:baseline;margin:2px 0}
.line .lbl{flex:none;width:42px;font-family:var(--mono);font-size:10px;font-weight:600}
.line.m0 .lbl{color:var(--m0)} .line.m1 .lbl{color:var(--m1)} .line.m2 .lbl{color:var(--m2)} .line.m3 .lbl{color:var(--m3)}
.line .val{flex:1}
.line .nw{font-family:var(--mono);font-size:10px;color:var(--muted)}
.oov{color:var(--alert);opacity:.6}
.chips{display:flex;gap:5px;flex-wrap:wrap;margin-top:6px}
.chip{font-family:var(--mono);font-size:10.5px;padding:1px 6px;border-radius:10px;background:var(--panel);border:1px solid var(--line);color:var(--muted)}
.chip.on{color:var(--ink);border-color:var(--cust)} .chip.stop{color:var(--ok);border-color:var(--ok)} .chip.no{color:var(--alert);border-color:var(--alert)}
.hint{color:var(--muted);text-align:center;margin-top:40vh;font-size:14px}
#chat.hide{display:none}
</style></head>
<body>
<div id="side">
  <h1>So sánh STT <small id="count"></small></h1>
  <input id="search" placeholder="lọc theo call_id...">
  <div id="list"></div>
</div>
<div id="main">
  <div id="head" style="display:none">
    <div class="cid" id="hcid"></div>
    <div class="m" id="hm"></div>
    <div id="toolbar">
      <span id="mtoggles"></span>
      <label><input type="checkbox" id="onlyBg"> chỉ lượt barge-in</label>
      <label><input type="checkbox" id="showFeat" checked> hiện đặc trưng</label>
    </div>
  </div>
  <div id="empty" class="hint">Chọn một cuộc gọi bên trái để xem.</div>
  <div id="chat" class="hide"></div>
</div>
<script>
const DATA = __DATA__;
const MODELS = __MODELS__;
const byId = {}; DATA.forEach(d=>byId[d.call_id]=d);
let cur=null;
const shown = {}; MODELS.forEach(m=>shown[m]=true);

function esc(s){return (s||"").replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
function oov(s){return esc(s).replace(/⁇/g,'<span class="oov">⁇</span>')}
const mi = m => MODELS.indexOf(m);

function renderList(filter=""){
  const list=document.getElementById("list"); list.innerHTML="";
  const rows=DATA.filter(d=>d.call_id.includes(filter)).sort((a,b)=>b.n_cand-a.n_cand);
  document.getElementById("count").textContent="("+DATA.length+" cuộc · "+MODELS.length+" STT)";
  rows.forEach(d=>{
    const el=document.createElement("div");
    el.className="li"+(cur===d.call_id?" sel":"");
    el.innerHTML=`<div class="cid">${d.call_id.slice(0,8)}</div>
      <div class="mini"><span class="badge">${d.dur_s}s</span>
      <span class="badge bg">${d.n_cand} cand</span>
      <span class="badge">dừng ${d.n_stop}</span></div>`;
    el.onclick=()=>{cur=d.call_id;renderList(filter);renderCall(d)};
    list.appendChild(el);
  });
}

function renderToggles(){
  const box=document.getElementById("mtoggles"); box.innerHTML="STT: ";
  MODELS.forEach((m,i)=>{
    const id="tg_"+m;
    box.insertAdjacentHTML("beforeend",
      `<label class="mtag m${i}"><input type="checkbox" id="${id}" ${shown[m]?"checked":""}> ${m}</label> `);
  });
  MODELS.forEach(m=>{
    document.getElementById("tg_"+m).onchange=e=>{shown[m]=e.target.checked;cur&&renderCall(byId[cur])};
  });
}

function renderCall(d){
  document.getElementById("head").style.display="";
  document.getElementById("empty").style.display="none";
  const chat=document.getElementById("chat"); chat.classList.remove("hide");
  document.getElementById("hcid").textContent=d.call_id;
  document.getElementById("hm").innerHTML=
    `<span>bot=kênh <b>${d.bot_ch}</b></span><span>dài <b>${d.dur_s}s</b></span>
     <span>ứng viên barge-in <b>${d.n_cand}</b></span><span>bot dừng <b>${d.n_stop}</b></span>`;
  const onlyBg=document.getElementById("onlyBg").checked;
  const showFeat=document.getElementById("showFeat").checked;
  chat.innerHTML="";
  d.turns.forEach(r=>{
    if(onlyBg && !r.ev) return;
    const row=document.createElement("div"); row.className="row "+r.spk;
    let lines="";
    MODELS.forEach(m=>{
      if(!shown[m]) return;
      const txt=r.texts[m]; if(txt===undefined) return;
      const nw = r.ev && r.ev.nw && r.ev.nw[m]!==undefined ? `<span class="nw">nw ${r.ev.nw[m]}</span>` : "";
      lines+=`<div class="line m${mi(m)}"><span class="lbl">${m.slice(0,4)}</span>`
           +`<span class="val">${oov(txt)||'—'}</span>${nw}</div>`;
    });
    let chips="";
    if(r.ev && showFeat){
      const e=r.ev, c=[];
      c.push(`<span class="chip">sir ${e.sir}</span>`);
      c.push(`<span class="chip">dur ${e.dur}s</span>`);
      c.push(`<span class="chip">slope ${e.slope}</span>`);
      c.push(`<span class="chip">flat ${e.flat}</span>`);
      c.push(e.stop?`<span class="chip stop">bot DỪNG ${e.lat}ms</span>`:`<span class="chip no">bot TIẾP</span>`);
      chips=`<div class="chips">${c.join("")}</div>`;
    }
    row.innerHTML=`<div class="bub${r.ev?' bg':''}">
      <div class="t">${r.spk==="bot"?"BOT":"KHÁCH"} · ${r.t0.toFixed(1)}s${r.ev?' · BARGE-IN':''}</div>
      ${lines}${chips}</div>`;
    chat.appendChild(row);
  });
}

document.getElementById("search").oninput=e=>renderList(e.target.value.trim());
document.getElementById("onlyBg").onchange=()=>cur&&renderCall(byId[cur]);
document.getElementById("showFeat").onchange=()=>cur&&renderCall(byId[cur]);
renderToggles(); renderList();
</script></body></html>"""


def load_model(out, model):
    d = {}
    for jp in glob.glob(os.path.join(out, model, "*.json")):
        if os.path.basename(jp).startswith("_"):
            continue
        j = json.load(open(jp, encoding="utf-8"))
        d[j["call_id"]] = j
    return d


def merge(out, models):
    per = {m: load_model(out, m) for m in models}
    base_m = models[0]
    calls = sorted(per[base_m].keys())
    merged = []
    for cid in calls:
        base = per[base_m][cid]
        ev_by_onset = {round(e["onset_s"], 2): e for e in base["events"]}
        # gom nw moi model theo onset
        nw_by_onset = {}
        for m in models:
            bd = per[m].get(cid)
            if not bd:
                continue
            for e in bd["events"]:
                nw_by_onset.setdefault(round(e["onset_s"], 2), {})[m] = e["n_words"]
        turns = []
        for r in base["turns"]:
            key = (r["spk"], round(r["t0"], 2))
            texts = {}
            for m in models:
                bd = per[m].get(cid)
                if not bd:
                    continue
                match = next((t["text"] for t in bd["turns"]
                              if t["spk"] == r["spk"] and round(t["t0"], 2) == round(r["t0"], 2)), None)
                if match is not None:
                    texts[m] = match
            ev = None
            if r["spk"] == "cust" and round(r["t0"], 2) in ev_by_onset:
                e = ev_by_onset[round(r["t0"], 2)]
                ev = {"sir": e["sir_db"], "dur": e["cust_dur_s"], "slope": e["onset_slope_db"],
                      "flat": e["spec_flatness"], "stop": e["bot_stopped"],
                      "lat": e["stop_latency_ms"], "nw": nw_by_onset.get(round(r["t0"], 2), {})}
            turns.append({"spk": r["spk"], "t0": r["t0"], "texts": texts, "ev": ev})
        m0 = base["metrics"]
        merged.append({"call_id": cid, "bot_ch": base["bot_ch"], "dur_s": m0["dur_s"],
                       "n_cand": m0["n_bargein_cand"], "n_stop": m0["n_bot_stopped"], "turns": turns})
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="out")
    ap.add_argument("--html", default="out/viewer.html")
    args = ap.parse_args()
    models = sorted(os.path.basename(os.path.dirname(p))
                    for p in glob.glob(os.path.join(args.out, "*", "_index.json")))
    # dua fastconformer (model cua Ky) len dau
    if "fastconformer" in models:
        models = ["fastconformer"] + [m for m in models if m != "fastconformer"]
    if not models:
        sys.exit(f"khong thay model nao trong {args.out}/*/")
    data = merge(args.out, models)
    html = (HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False))
                .replace("__MODELS__", json.dumps(models, ensure_ascii=False)))
    open(args.html, "w", encoding="utf-8").write(html)
    print(f"[viewer] {len(data)} cuoc · models={models} -> {args.html}", file=sys.stderr)


if __name__ == "__main__":
    main()
