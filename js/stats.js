/* ═══════════ 伽蓝经纬 · 计量面板（数字全部出自 docs/stats.js 脚本产物） ═══════════
   两页签：文本计量（stats.py 产物） · 引水经注（水道经纬站际互查，data/xref_sjz.js 懒加载） */

const QLSTATS = (() => {
  const S = () => QL_STATS;   /* const 不上 window——直引 */
  let tab = "meter";
  let sjzOpen = null;

  function open(which) {
    if (which) tab = which;
    QLAPP.setMode("stats");
    document.getElementById("vname").textContent = tab === "sjz" ? "引水经注" : "文本计量";
    document.getElementById("vseal").textContent = tab === "sjz" ? "互查" : "计数";
    document.getElementById("pmeta").innerHTML = tab === "sjz"
      ? `<span>水道经纬站际桥 · data/xref_sjz.js（build_xref_sjz.py 生成）</span>`
      : `<span>全部数字出自 tools/stats.py → docs/stats.json</span>`;
    const host = document.getElementById("pbody");
    host.className = "";
    host.innerHTML =
      `<div class="dtabs">` +
      `<button class="dtab${tab === "meter" ? " cur" : ""}" data-t="meter">文本计量</button>` +
      `<button class="dtab${tab === "sjz" ? " cur" : ""}" data-t="sjz">引水经注</button></div>` +
      `<div id="stabbody"></div>`;
    host.querySelectorAll(".dtab").forEach(b =>
      b.addEventListener("click", () => open(b.dataset.t)));
    document.getElementById("panel").classList.add("open");
    location.hash = "#m=stats";
    if (tab === "sjz") xrefLoad();
    else renderMeter();
  }

  /* ── 页签一：文本计量 ── */
  function renderMeter() {
    const s = S();
    const host = document.getElementById("stabbody");

    const maxVol = Math.max(...Object.values(s.vol_chars));
    const volRows = Object.keys(s.vol_chars).map(v => {
      const w = Math.round(s.vol_chars[v] / maxVol * 100);
      const color = VOL_COLORS[v] || "#9a8f6d";
      return `<div class="strow"><span class="stl">${v === "0" ? "原序" : `卷${v}·${VOL_NAMES[v]}`}</span>` +
        `<span class="stbar"><i style="width:${w}%;background:${color}"></i></span>` +
        `<span class="stv">${s.vol_chars[v].toLocaleString()}字 · 伽蓝${s.temple_per_vol[v] || 0}</span></div>`;
    }).join("");

    const maxM = Math.max(...Object.values(s.gate_mentions).filter(x => typeof x === "number"));
    const gateRows = Object.entries(s.gate_mentions).filter(([, n]) => typeof n === "number")
      .sort((a, b) => b[1] - a[1]).map(([g, n]) =>
        `<div class="strow"><span class="stl">${g}</span>` +
        `<span class="stbar"><i style="width:${Math.round(n / maxM * 100)}%;background:#9a6b3f"></i></span>` +
        `<span class="stv">${n} 次</span></div>`).join("");

    const topT = s.temple_mentions.slice(0, 10);
    const maxT = topT[0][1];
    const templeRows = topT.map(([n, c]) =>
      `<div class="strow"><span class="stl">${n}</span>` +
        `<span class="stbar"><i style="width:${Math.round(c / maxT * 100)}%;background:#8e2b22"></i></span>` +
        `<span class="stv">${c} 次</span></div>`).join("");

    const w = s.words;
    host.innerHTML = `
<div class="sect"><h3>全书规模</h3><p class="kv">
总 ${s.total_chars.toLocaleString()} 字（序 ${s.vol_chars["0"].toLocaleString()} + 五卷）·
伽蓝 ${s.temple_entries} 条 · 宋云行纪 ${s.songyun_chars.toLocaleString()} 字<br>
寺 ${w["寺"]} · 尼寺 ${w["尼寺"]} · 浮图 ${w["浮图"]} · 塔 ${w["塔"]} · 御道 ${w["御道"]} ·
洛水 ${w["洛水"]} · 穀水 ${w["穀水"]} · 阳渠 ${w["阳渠"]}</p></div>
<div class="sect"><h3>卷篇幅 × 伽蓝条数</h3>${volRows}</div>
<div class="sect"><h3>佛寺出场频次（名气指数）</h3><p class="kv small">${s.mention_note}</p>${templeRows}</div>
<div class="sect"><h3>城门提及</h3><p class="kv small">城门是全书空间书写的锚点——「某门(内/外)N里御道某侧」</p>${gateRows}</div>
<div class="sect"><h3>详见</h3><p class="kv">docs/ANALYSIS.md（凡数字必出自脚本）· 论文 PDF 见 docs/</p></div>`;
  }

  /* ── 页签二：引水经注（站际互查）──
     数据 data/xref_sjz.js 懒加载（仿 reader.js 注入惯例）；
     深链 ../SDJW/#r=<水道id> 为相对兄弟路径——须父目录同根服务（README 注明）。 */
  function xrefLoad() {
    if (window.QL_SJZ) return renderXref();
    if (sjzOpen) return;
    const host0 = document.getElementById("stabbody");
    host0.innerHTML = `<div class="sect"><p class="kv">互查数据装载中…</p></div>`;
    sjzOpen = new Promise(ok => {
      const s = document.createElement("script");
      s.src = "data/xref_sjz.js?v=8";
      s.onload = ok;
      s.onerror = ok;
      document.head.appendChild(s);
    }).then(() => {
      sjzOpen = null;
      if (!window.QL_SJZ) {
        const h = document.getElementById("stabbody");
        if (h) h.innerHTML = `<div class="sect"><p class="kv">互查数据未载入（离线首访）——联网后重开即得。</p></div>`;
        return;
      }
      renderXref();
    });
  }

  function renderXref() {
    const d = window.QL_SJZ;
    const host = document.getElementById("stabbody");
    const t = d.totals;
    const maxW = Math.max(...d.waters.map(x => x.n));

    const waterRows = d.waters.map(w =>
      `<div class="strow"><span class="stl">${w.name}</span>` +
      `<span class="stbar"><i style="width:${Math.round(w.n / maxW * 100)}%;background:#4a7a9b"></i></span>` +
      `<span class="stv">${w.n} 次 · <a href="${w.href}" target="_blank" rel="noopener" ` +
      `class="xlink">↗循水</a></span></div>` +
      (w.note ? `<p class="kv small" style="margin:-2px 0 4px">${w.note}</p>` : "")).join("");

    const maxP = d.places[0] ? d.places[0].n : 1;
    const placeRows = d.places.map(p =>
      `<div class="strow"><span class="stl">${p.name}</span>` +
      `<span class="stbar"><i style="width:${Math.round(p.n / maxP * 100)}%;background:#9a6b3f"></i></span>` +
      `<span class="stv">${p.n} 次 · ${p.water}注 · ` +
      `<a href="../SDJW/#r=${p.waterId}" target="_blank" rel="noopener" class="xlink">↗</a></span></div>` +
      `<div class="xsamp" data-n="${p.name}">…${p.sample}…${p.note ? `（${p.note}）` : ""}</div>`).join("");

    const kindSum = Object.entries(t.placeKinds).map(([k, n]) => `${k} ${n}`).join(" · ");
    const noHitGates = d.noHit.filter(n => n.kind === "城门").map(n => n.name).join("、");

    const pairCards = d.pairs.map(p =>
      `<div class="xpair"><div class="xpname">${p.name}` +
      `<span class="xpk">${p.kind} · ${p.water}注</span>` +
      `<a href="${p.href}" target="_blank" rel="noopener" class="xlink">↗循水</a></div>` +
      `<div class="xpq"><span class="xptag">伽蓝记</span>${p.ql}</div>` +
      `<div class="xps"><span class="xptag">谷水注</span>${p.sjz}</div></div>`).join("");

    host.innerHTML = `
<div class="sect"><h3>同城异代 · 互查口径</h3>
<p class="kv small">${d.note}</p>
<p class="kv small">谷水注注文 ${t.waterTextChars["谷水"].toLocaleString()} 字 · 洛水注 ${t.waterTextChars["洛水"].toLocaleString()} 字（皆水道经纬快照）</p></div>
<div class="sect"><h3>本书提及水道（A→）</h3>${waterRows}
<p class="kv small">排除同名假阳性：${d.excluded.map(e => `${e.name}(${e.n})`).join("、")}——皆普通词序（「决水种麦」「渡一深水」等），非水道专名</p></div>
<div class="sect"><h3>谷水注/洛水注中的伽蓝记名物（→B）</h3>
<p class="kv small">命中 ${t.placesHit} / 无对应 ${t.placesNoHit}（${kindSum}）——城门仅 ${noHitGates} 无对应</p>
${placeRows}</div>
<div class="sect"><h3>样例对读（${t.pairs} 对，皆脚本截取）</h3>${pairCards}</div>`;
  }

  return { open };
})();
window.QLSTATS = QLSTATS;
