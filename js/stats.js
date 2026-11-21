/* ═══════════ 伽蓝经纬 · 计量面板（数字全部出自 docs/stats.js 脚本产物） ═══════════ */

const QLSTATS = (() => {
  const S = () => QL_STATS;   /* const 不上 window——直引 */

  function open() {
    QLAPP.setMode("stats");
    const s = S();
    document.getElementById("vname").textContent = "文本计量";
    document.getElementById("vseal").textContent = "计数";
    document.getElementById("pmeta").innerHTML = `<span>全部数字出自 tools/stats.py → docs/stats.json</span>`;
    const host = document.getElementById("pbody");
    host.className = "";

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
<div class="sect"><h3>详见</h3><p class="kv">docs/ANALYSIS.md（凡数字必出自脚本）</p></div>`;
    document.getElementById("panel").classList.add("open");
    location.hash = "#m=stats";
  }

  return { open };
})();
window.QLSTATS = QLSTATS;
