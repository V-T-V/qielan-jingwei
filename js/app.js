/* ═══════════ 伽蓝经纬 · 应用装配（boot / 模式 / 深链 / 夜读） ═══════════
   深链语法：#m=map|read|directory|stats|about · #juan=0..5 · #gl=寺名|id · #gate=门名 */

const QLAPP = (() => {
  let mode = "map";
  const MODE_NOTE = {
    map: "四十三伽蓝 · 十三门 · 示意城市平面",
    read: "按卷巡城 · 滚动文本，地图随行",
    directory: "伽蓝名录 · 城市骨架名物",
    stats: "文本计量 · 数字出自脚本",
    about: "关于 · 数据与坐标边界",
  };

  function ensureSections() {
    if (typeof QL_SECTIONS !== "undefined") return Promise.resolve();
    if (ensureSections._p) return ensureSections._p;
    ensureSections._p = new Promise((ok, bad) => {
      const s = document.createElement("script");
      s.src = "data/sections.js?v=6";
      s.onload = ok;
      s.onerror = () => bad(new Error("sections.js 加载失败"));
      document.head.appendChild(s);
    });
    return ensureSections._p;
  }

  function boot() {
    QLMAP.init();
    QLMAP.onTemple = t => openTemple(t.id);
    QLMAP.onGate = g => openGate(g);
    QLMAP.onWard = w => openAux(w, "里坊·市");
    QLMAP.onOffice = o => openAux(o, "衙署·宫室");
    QLMAP.renderTemples();
    QLRAIL.build();
    QLSEARCH.init();
    bindUI();
    document.querySelector("#boot .go").addEventListener("click", () => {
      document.getElementById("boot").classList.add("off");
      setTimeout(() => document.getElementById("boot").remove(), 700);
    });
    const m = QLZ.meta;
    document.getElementById("bookstat").textContent =
      `五卷 ${m.totalChars.toLocaleString()} 字 · ${m.templeEntries} 伽蓝 · ${m.gates} 门`;
    applyHash();
    window.addEventListener("hashchange", applyHash);
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("sw.js").then(() => {
        const el = document.getElementById("swstate");
        el.style.display = ""; el.textContent = "离线就绪";
      }).catch(() => {});
    }
  }

  function bindUI() {
    document.querySelectorAll("#modes .mode").forEach(b =>
      b.addEventListener("click", () => act(b.dataset.mode)));
    document.getElementById("pclose").addEventListener("click", closePanel);
    document.getElementById("fitlink").addEventListener("click", () => QLMAP.fitAll());
    document.getElementById("wanderlink").addEventListener("click", () => {
      const ts = QLZ.temples;
      openTemple(ts[Math.floor(Math.random() * ts.length)].id);
    });
    document.getElementById("bmlink").addEventListener("click", () => QLBM.open());
    const nightBtn = document.getElementById("nightlink");
    const nightApply = on => {
      document.body.classList.toggle("night", on);
      nightBtn.textContent = on ? "☀ 昼" : "☾ 夜读";
      try { localStorage.setItem("qlgNight", on ? "1" : ""); } catch (e) {}
    };
    nightBtn.addEventListener("click", () =>
      nightApply(!document.body.classList.contains("night")));
    try { if (localStorage.getItem("qlgNight")) nightApply(true); } catch (e) {}
    /* 巡城条 */
    const sel = document.getElementById("rjvol");
    sel.innerHTML = `<option value="0">序</option>` +
      [1, 2, 3, 4, 5].map(v => `<option value="${v}">卷${v} · ${VOL_NAMES[v]}</option>`).join("");
    sel.addEventListener("change", () => QLREADER.open(+sel.value));
    document.getElementById("rprev").addEventListener("click", () => stepBlock(-1));
    document.getElementById("rnext").addEventListener("click", () => stepBlock(1));
    document.getElementById("rtts").addEventListener("click", () => QLREADER.ttsToggle());
    window.addEventListener("keydown", e => {
      if (e.key === "Escape") closePanel();
    });
  }

  function stepBlock(d) {
    if (QLREADER.current) {
      const host = document.getElementById("pbody");
      const els = [...host.querySelectorAll(".entry")];
      let i = els.findIndex(e => e.dataset.id === QLREADER.current);
      i = Math.max(0, Math.min(els.length - 1, i + d));
      if (els[i]) QLREADER.gotoBlock(els[i].dataset.id, true);
    } else {
      QLREADER.open(1);
    }
  }

  function setMode(m) {
    mode = m;
    document.querySelectorAll("#modes .mode").forEach(b =>
      b.classList.toggle("active", b.dataset.mode === m));
    document.getElementById("modelabel").textContent =
      document.querySelector(`#modes .mode[data-mode="${m}"]`).textContent;
    document.getElementById("modenote").textContent = MODE_NOTE[m] || "";
  }

  function act(m) {
    if (m === "stats") return QLSTATS.open();
    if (m === "about") return openAbout();
    if (m === "directory") return openDirectory("temples");
    if (m === "read") return QLREADER.open(QLREADER.vol || 1);
    setMode(m);
    QLMAP.setVolFilter(null);
    closePanel(false);
  }

  /* ── 伽蓝详情 ── */
  async function openTemple(id, inReader = false) {
    const t = QLZ.temples.find(x => x.id === id) ||
              QLZ.temples.find(x => x.name === id);
    if (!t) return;
    if (inReader || mode === "read") { QLREADER.open(t.vol, t.id); return; }
    setMode("map");
    try { await ensureSections(); } catch (e) {}
    QLMAP.selectTemple(t.id, { fly: true });
    QLMAP.highlight(t.id, true);
    QLRAIL.highlight(t.id);
    document.getElementById("vname").textContent = t.name;
    document.getElementById("vseal").textContent = "伽蓝";
    document.getElementById("pmeta").innerHTML =
      `<span>卷${t.vol} · ${VOL_NAMES[t.vol]}</span>` +
      `<span>条目 ${t.chars} 字</span>` +
      `<span>全书出场 ${t.mention} 次</span>` +
      `<span>坐标 ${t.conf === "text" ? "原文明载方位" : "区位示意"}</span>`;
    const sec = (typeof QL_SECTIONS !== "undefined") && QL_SECTIONS[t.id];
    const host = document.getElementById("pbody");
    host.className = "";
    host.innerHTML =
      `<div class="sect"><h3>位置</h3><p class="kv">「${t.loc || "方位未明载"}」</p>` +
      `<p class="kv small">示意平面坐标 ${t.pos[0]}, ${t.pos[1]} m · ` +
      `src:${t.src} · 依据：原文方位句 + 汉魏洛阳故城考古常识布点</p></div>` +
      `<div class="sect"><h3>原文</h3>` +
      (sec ? sec.paras.map((p, i) =>
        `<p class="ctxt${i === 0 ? " first" : ""}">${p}</p>`).join("")
        : `<p class="kv">正文加载失败</p>`) + `</div>` +
      `<div class="btnrow"><button class="ftool" id="goread">▸ 按卷巡城至此</button>` +
      `<button class="ftool" id="gobm"></button></div>`;
    document.getElementById("panel").classList.add("open");
    const gr = document.getElementById("goread");
    if (gr) gr.addEventListener("click", () => QLREADER.open(t.vol, t.id));
    QLBM.bindToggle(document.getElementById("gobm"), t.name, t.vol);
    location.hash = `#gl=${encodeURIComponent(t.name)}`;
  }

  /* ── 城门详情 ── */
  function openGate(g) {
    setMode("map");
    QLMAP.flyTo(g.pos, Math.max(QLMAP.map.getZoom(), 0.2));
    document.getElementById("vname").textContent = g.disp || g.name;
    document.getElementById("vseal").textContent = "城门";
    document.getElementById("pmeta").innerHTML =
      `<span>${g.wall === "宫" ? "宫城门" : g.wall + "墙"} · 示意方位</span>` +
      `<span>全书提及 ${g.mention} 次</span>`;
    document.getElementById("pbody").className = "";
    document.getElementById("pbody").innerHTML =
      `<div class="sect"><h3>书证</h3><p class="kv">「${g.att}」</p></div>` +
      `<div class="sect"><h3>说明</h3><p class="kv small">城门是《伽蓝记》空间书写的锚：` +
      `四十三伽蓝中三十七条的位置句以「某门(内/外)N里御道某侧」格式给出。` +
      `门位为汉魏洛阳故城考古常识示意（内城 2,800×3,700m，1里=440m），src:derived。</p></div>`;
    document.getElementById("panel").classList.add("open");
    location.hash = `#gate=${encodeURIComponent(g.name)}`;
  }

  /* ── 里坊/衙署 ── */
  function openAux(o, kind) {
    setMode("map");
    QLMAP.flyTo(o.pos, Math.max(QLMAP.map.getZoom(), 0.2));
    document.getElementById("vname").textContent = o.name;
    document.getElementById("vseal").textContent = kind.slice(0, 1);
    document.getElementById("pmeta").innerHTML = `<span>${kind} · 示意方位</span>`;
    document.getElementById("pbody").className = "";
    document.getElementById("pbody").innerHTML =
      `<div class="sect"><h3>书证</h3><p class="kv">「${o.att}」</p></div>` +
      (o.vol ? `<div class="btnrow"><button class="ftool" id="govol">▸ 巡城至卷${o.vol}</button></div>` : "");
    document.getElementById("panel").classList.add("open");
    const gb = document.getElementById("govol");
    if (gb) gb.addEventListener("click", () => QLREADER.open(o.vol));
    location.hash = "#m=map";
  }

  /* ── 名录 ── */
  function openDirectory(kind = "temples") {
    setMode("directory");
    document.getElementById("vname").textContent = "名物名录";
    document.getElementById("vseal").textContent = "名录";
    document.getElementById("pmeta").innerHTML =
      `<span>伽蓝 ${QLZ.temples.length} · 城门 ${QLZ.gates.length} · ` +
      `里坊/市 ${QLZ.wards.length} · 衙署 ${QLZ.offices.length}</span>`;
    const host = document.getElementById("pbody");
    host.className = "";
    const tabs = `<div class="dtabs">` +
      [["temples", "伽蓝"], ["gates", "城门"], ["wards", "里坊·市"], ["offices", "衙署"]]
        .map(([k, n]) => `<button class="dtab${k === kind ? " cur" : ""}" data-k="${k}">${n}</button>`).join("") +
      `</div>`;
    let body = "";
    if (kind === "temples") {
      for (let v = 1; v <= 5; v++) {
        body += `<div class="dvol"><span class="vdot" style="background:${VOL_COLORS[v]}"></span>` +
          `卷${v} · ${VOL_NAMES[v]}</div>` +
          QLZ.temples.filter(t => t.vol === v).map(t =>
            `<div class="drow" data-id="${t.id}"><span class="dn">${t.name}</span>` +
            `<span class="dl">${(t.loc || "").slice(0, 16)}</span>` +
            `<span class="dc">${t.chars}字</span></div>`).join("");
      }
    } else if (kind === "gates") {
      body = QLZ.gates.map(g =>
        `<div class="drow" data-gate="${g.name}"><span class="dn">${g.name}</span>` +
        `<span class="dl">${g.wall === "宫" ? "宫城门" : g.wall + "墙"}</span>` +
        `<span class="dc">${g.mention}次</span></div>`).join("");
    } else if (kind === "wards") {
      body = QLZ.wards.map(w =>
        `<div class="drow" data-ward="${w.name}"><span class="dn">${w.name}</span>` +
        `<span class="dl">卷${w.vol}</span><span class="dc"></span></div>`).join("");
    } else {
      body = QLZ.offices.map(o =>
        `<div class="drow" data-office="${o.name}"><span class="dn">${o.name}</span>` +
        `<span class="dl">卷${o.vol}</span><span class="dc"></span></div>`).join("");
    }
    host.innerHTML = tabs + `<div class="dlist">${body}</div>`;
    host.querySelectorAll(".dtab").forEach(b =>
      b.addEventListener("click", () => openDirectory(b.dataset.k)));
    host.querySelectorAll(".drow[data-id]").forEach(r =>
      r.addEventListener("click", () => openTemple(r.dataset.id)));
    host.querySelectorAll(".drow[data-gate]").forEach(r =>
      r.addEventListener("click", () => {
        const g = QLZ.gates.find(x => x.name === r.dataset.gate);
        if (g) openGate(g);
      }));
    host.querySelectorAll(".drow[data-ward]").forEach(r =>
      r.addEventListener("click", () => {
        const w = QLZ.wards.find(x => x.name === r.dataset.ward);
        if (w) openAux(w, "里坊·市");
      }));
    host.querySelectorAll(".drow[data-office]").forEach(r =>
      r.addEventListener("click", () => {
        const o = QLZ.offices.find(x => x.name === r.dataset.office);
        if (o) openAux(o, "衙署·宫室");
      }));
    document.getElementById("panel").classList.add("open");
    location.hash = "#m=directory";
  }

  function openAbout() {
    const m = QLZ.meta;
    setMode("about");
    document.getElementById("vname").textContent = "关于";
    document.getElementById("vseal").textContent = "叙";
    document.getElementById("pmeta").innerHTML = `<span>数据管线 · 方法与边界</span>`;
    document.getElementById("pbody").className = "";
    document.getElementById("pbody").innerHTML = `
<div class="sect"><h3>伽蓝经纬</h3>
<p class="kv">北魏杨衒之《洛阳伽蓝记》五卷数字人文平台。方舆经纬（点织版图）、
水道经纬（线溯江河）姊妹项目：此以<b>点</b>（伽蓝）织北魏洛阳——一城之内，见一代之盛衰。</p></div>
<div class="sect"><h3>数据与方法</h3><p class="kv">
· 文本：国学导航本（GB18030 抓取转存），序+五卷共 ${m.totalChars.toLocaleString()} 字，校勘不在范围<br>
　（维基文库本网络不可达，依 SPEC 数据源次序回退；如实标注，缺即是缺）<br>
· 条目：典校篇目表 ${m.templeEntries} 条伽蓝（卷一至卷五：${Object.values(m.templePerVol).join("/")}），解析器逐一前缀命中校验<br>
· 城图：自绘示意平面（Leaflet L.CRS.Simple）——内城 2,800×3,700m，1里=440m，<br>
　城墙/宫城/金墉/河渠依汉魏洛阳故城考古常识布点，全部坐标 <code>src:"derived"</code><br>
· 伽蓝坐标：${m.textConf} 条有原文方位句（text），${m.inferConf} 条依卷部区位示意（infer），依据字段附于各条<br>
· 城门 ${m.gatesWall} 墙门（序自载门谱：东3·南4·西4·北2，皆原文书证）+ 宫城门二（阊阖/千秋）；里坊/市 ${m.wards}、衙署 ${m.offices}<br>
· 计量：数字全部出自 python tools/stats.py → docs/stats.json</p></div>
<div class="sect"><h3>体例与致谢</h3><p class="kv">
基建承水道经纬/方舆经纬姊妹站：深链/夜读/TTS/书签/PWA。文本源：国学导航。底图：自绘（无外部瓦片）。</p></div>
<div class="sect"><h3>快速上手</h3><p class="kv">
左列纲目点寺名 → 详情；「巡城」按卷滚动读原文，地图随文飞行；顶栏检全书；
底栏「⚑ 漫游」随机巡礼一寺。</p></div>`;
    document.getElementById("panel").classList.add("open");
    location.hash = "#m=about";
  }

  function closePanel(clearHash = true) {
    document.getElementById("panel").classList.remove("open");
    if (QLREADER.current) QLREADER.close();
    if (clearHash) location.hash = "#m=map";
  }

  /* ── 深链：#m= #juan= #gl= #gate=（多段 # 并存） ── */
  function applyHash() {
    const segs = location.hash.split("#").filter(Boolean).map(s => s.split("="));
    const get = k => { const s = segs.find(x => x[0] === k); return s ? s[1] : null; };
    const gl = get("gl"), juan = get("juan"), gate = get("gate"), m = get("m");
    if (gl) {
      const dec = decodeURIComponent(gl);
      const t = QLZ.temples.find(x => x.name === dec) ||
                QLZ.temples.find(x => x.id === gl);
      if (t) {
        if (juan && +juan >= 0 && +juan <= 5) QLREADER.open(+juan, t.id);
        else openTemple(t.id);
        return;
      }
    }
    if (juan !== null && juan !== undefined && juan !== "") {
      const v = Math.max(0, Math.min(5, +juan));
      QLREADER.open(v);
      return;
    }
    if (gate) {
      const g = QLZ.gates.find(x => x.name === decodeURIComponent(gate));
      if (g) { openGate(g); return; }
    }
    if (m === "stats") return QLSTATS.open();
    if (m === "about") return openAbout();
    if (m === "directory") return openDirectory();
    if (m === "read") return QLREADER.open(1);
    setMode("map");
  }

  document.addEventListener("DOMContentLoaded", boot);
  return { openTemple, openDirectory, setMode, ensureSections, get mode() { return mode; } };
})();
window.QLAPP = QLAPP;
