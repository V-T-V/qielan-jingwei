/* ═══════════ 伽蓝经纬 · 应用装配（boot / 模式 / 深链 / 夜读） ═══════════
   深链语法：#m=map|read|directory|stats|about · #juan=0..5 · #gl=寺名|id · #gate=门名 */

const QLAPP = (() => {
  let mode = "map";
  const MODE_NOTE = {
    map: "四十三伽蓝 · 十三门 · 示意城市平面",
    read: "按卷巡城 · 滚动文本，地图随行",
    directory: "伽蓝名录 · 城市骨架名物 · 可导出",
    stats: "文本计量 · 引水经注互查",
    west: "宋云西行 · 行纪二十站示意（src:derived）",
    about: "关于 · 数据与坐标边界",
  };

  function ensureSections() {
    if (typeof QL_SECTIONS !== "undefined") return Promise.resolve();
    if (ensureSections._p) return ensureSections._p;
    ensureSections._p = new Promise((ok, bad) => {
      const s = document.createElement("script");
      s.src = "data/sections.js?v=9";
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
    QLMAP.onWestStop = (s, i) => openWestStop(s, i);
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
    const westBtn = document.getElementById("westlink");
    if (westBtn) westBtn.addEventListener("click", () =>
      QLMAP.scene === "west" ? westOff() : westOn());
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
    const btn = document.querySelector(`#modes .mode[data-mode="${m}"]`);
    document.getElementById("modelabel").textContent =
      btn ? btn.textContent : (m === "west" ? "西行" : m);
    document.getElementById("modenote").textContent = MODE_NOTE[m] || "";
  }

  function act(m) {
    if (m === "stats") return QLSTATS.open();
    if (m === "about") return openAbout();
    if (m === "directory") return openDirectory("temples");
    if (m === "read") return QLREADER.open(QLREADER.vol || 1);
    setMode(m);
    if (QLMAP.scene !== "city") QLMAP.setScene("city");
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

  /* ── 宋云西行（小比例尺示意场景 · data/songyun.js 管线产物） ── */
  function westOn() {
    const SY = window.QL_SONGYUN;
    if (!SY) return;
    setMode("west");
    QLMAP.setScene("west");
    document.getElementById("vname").textContent = "宋云西行";
    document.getElementById("vseal").textContent = "行纪";
    document.getElementById("pmeta").innerHTML =
      `<span>${SY.meta.stops} 站 · ${SY.meta.chars.toLocaleString()} 字行纪</span>` +
      `<span>${SY.meta.years}</span>`;
    const host = document.getElementById("pbody");
    host.className = "";
    host.innerHTML =
      `<div class="sect"><h3>驼铃出京师</h3><p class="kv">神龟元年（518）冬，太后遣惠生向西域取经，` +
      `宋云同行——洛阳的城市书写由此伸向丝路。行纪以里程范式（「从X西行N里至Y」）` +
      `与城内门锚范式同卷并置。</p>` +
      `<p class="kv small">${SY.meta.note}</p></div>` +
      `<div class="sect"><h3>二十站 · 沿线巡读</h3>` +
      SY.stops.map((s, i) =>
        `<div class="drow" data-st="${i}"><span class="dn">${i + 1}. ${s.name}</span>` +
        `<span class="dl">${s.today.slice(0, 14)}</span>` +
        `<span class="dc">${s.li || ""}</span></div>`).join("") + `</div>`;
    host.querySelectorAll(".drow[data-st]").forEach(r =>
      r.addEventListener("click", () => openWestStop(SY.stops[+r.dataset.st], +r.dataset.st)));
    document.getElementById("panel").classList.add("open");
    location.hash = "#m=west";
  }

  function westOff() {
    QLMAP.setScene("city");
    setMode("map");
    closePanel(false);
    location.hash = "#m=map";
  }

  function openWestStop(s, i) {
    const SY = window.QL_SONGYUN;
    if (!s || !SY) return;
    setMode("west");
    if (QLMAP.scene !== "west") QLMAP.setScene("west");
    if (QLMAP.map) QLMAP.map.flyTo(s.wgs, Math.max(QLMAP.map.getZoom(), 4.5), { duration: .8 });
    document.getElementById("vname").textContent = s.name;
    document.getElementById("vseal").textContent = "行纪";
    document.getElementById("pmeta").innerHTML =
      `<span>第 ${i + 1}/${SY.meta.stops} 站 · ${s.cat}</span>` +
      `<span>坐标 ${s.wgs[0]}, ${s.wgs[1]} · src:${s.src} · ${s.conf}</span>`;
    const host = document.getElementById("pbody");
    host.className = "";
    host.innerHTML =
      `<div class="sect"><h3>今地考订</h3><p class="kv">${s.today}` +
      `${s.li ? ` · 原文明载里程「${s.li}」` : " · 里程未明载"}</p>` +
      `<p class="kv small">量级示意坐标（build_songyun.py 整编考订），非考古实测</p></div>` +
      `<div class="sect"><h3>行纪书证</h3><p class="ctxt first">「${s.cite}」</p></div>` +
      `<div class="btnrow"><button class="ftool" id="gostopread">▸ 巡读行纪全篇（卷五）</button>` +
      `<button class="ftool" id="gowestback">◂ 回西行总览</button></div>`;
    document.getElementById("panel").classList.add("open");
    const gr = document.getElementById("gostopread");
    if (gr) gr.addEventListener("click", () => QLREADER.open(5, SY.meta.blockId));
    const gb = document.getElementById("gowestback");
    if (gb) gb.addEventListener("click", westOn);
    location.hash = "#m=west";
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
      `<span class="dspacer"></span>` +
      `<button class="dtab exp" id="csvdl" title="当前表 CSV（带 BOM，Excel 直开）· tools/export_data.py 同口径">⤓ CSV</button>` +
      `<button class="dtab exp" id="kmldl" title="四表合一 · Google Earth · 示意坐标已注明">⤓ KML</button>` +
      `<button class="dtab exp" id="gjdl" title="四表合一 · 通用 GIS · src:derived">⤓ GeoJSON</button>` +
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
    host.querySelectorAll(".dtab[data-k]").forEach(b =>
      b.addEventListener("click", () => openDirectory(b.dataset.k)));
    const bc = document.getElementById("csvdl");
    if (bc) bc.addEventListener("click", () => QLEXPORT.csv(kind));
    const bk = document.getElementById("kmldl");
    if (bk) bk.addEventListener("click", () => QLEXPORT.kml());
    const bg = document.getElementById("gjdl");
    if (bg) bg.addEventListener("click", () => QLEXPORT.geojson());
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
<div class="sect"><h3>P2 · 论文 / 导出 / 互查 / 西行</h3><p class="kv">
· 论文：docs/伽蓝经纬-数字人文.pdf（数字全出自脚本；改 ANALYSIS.md 必重排，lint 哨兵联动）<br>
· 导出：名录页 ⤓ CSV(BOM)/KML/GeoJSON 与 tools/export_data.py 同口径；示意坐标逐行注明 src:derived<br>
· 互查：「计量 → 引水经注」——谷水注/洛水注 ↔ 本书名物双向计数 + 对读样例；<br>
　↗循水深链 ../SDJW/#r=&lt;水道id&gt;（相对兄弟路径，须父目录同根服务，README 注明）<br>
· 西行：底栏「◈ 西行」——宋云行纪 20 站 WGS84 小比例尺示意（src:derived·infer，非实测）</p></div>
<div class="sect"><h3>快速上手</h3><p class="kv">
左列纲目点寺名 → 详情；「巡城」按卷滚动读原文，地图随文飞行；顶栏检全书；
底栏「⚑ 漫游」随机巡礼一寺、「◈ 西行」出塞。</p></div>`;
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
    if (m === "west") return westOn();
    if (m === "about") return openAbout();
    if (m === "directory") return openDirectory();
    if (m === "read") return QLREADER.open(1);
    setMode("map");
    if (QLMAP.scene !== "city") QLMAP.setScene("city");
  }

  document.addEventListener("DOMContentLoaded", boot);
  return { openTemple, openDirectory, setMode, ensureSections, get mode() { return mode; } };
})();
window.QLAPP = QLAPP;
