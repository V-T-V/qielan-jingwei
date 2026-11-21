/* ═══════════ 伽蓝经纬 · 按卷巡城（核心体验） ═══════════
   右幅 = 一卷的全部阅读块（伽蓝条目 + 里坊叙事 + 宋云行纪）
   滚动文本 → 当前伽蓝条目地图飞行+高亮；条目卡点击 → 地图跟随
   深链写回 #juan=N#gl=寺名 */

const QLREADER = (() => {
  let curVol = 1, curId = null;
  const pbody = () => document.getElementById("pbody");

  /* 全书 36KB：直接内联加载（懒加载保留结构位） */
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

  function blocksOf(v) {
    /* ord=build 插入序（t/n/m 混合前缀，字典序不可靠） */
    return Object.values(QL_SECTIONS)
      .filter(b => b.vol === v)
      .sort((a, b2) => a.ord - b2.ord);
  }

  async function open(vol, focusId = null) {
    try { await ensureSections(); } catch (e) { /* 骨架仍可展示 */ }
    curVol = vol;
    QLAPP.setMode("read");
    QLMAP.setVolFilter(null);
    document.getElementById("vname").textContent =
      (vol === 0 ? "原序" : `卷${vol} · ${VOL_NAMES[vol]}`);
    document.getElementById("vseal").textContent = "巡城";
    document.getElementById("pmeta").innerHTML = metaHTML(vol);
    renderBody(vol);
    document.getElementById("panel").classList.add("open");
    document.getElementById("readerbar").classList.remove("hidden");
    const sel = document.getElementById("rjvol");
    if (sel) sel.value = String(vol);
    gotoBlock(focusId || firstTempleId(vol), true);
    location.hash = `#m=read#juan=${vol}` + (focusId ? `#gl=${encodeURIComponent(nameOf(focusId))}` : "");
  }

  function firstTempleId(v) {
    const b = blocksOf(v).find(x => x.kind === "temple");
    return b ? b.id : blocksOf(v)[0].id;
  }

  function nameOf(id) {
    const b = QL_SECTIONS[id];
    if (!b) return "";
    const t = QLZ.temples.find(x => x.id === id);
    return t ? t.name : b.name;
  }

  function metaHTML(vol) {
    const bs = blocksOf(vol);
    const ts = bs.filter(b => b.kind === "temple").length;
    return `<span>${QL_STATS.vol_chars[String(vol)].toLocaleString()} 字</span>` +
      `<span>${bs.length} 阅读块</span>` +
      `<span>伽蓝 ${ts} 条</span>` +
      `<span>滚动文本 · 地图随行</span>`;
  }

  function blockCard(b) {
    const t = QLZ.temples.find(x => x.id === b.id);
    const kindTag = {
      temple: t ? `卷${t.vol}伽蓝` : "伽蓝",
      narrative: "里坊叙事", songyun: "行纪", summary: "总述", preface: "原序",
    }[b.kind];
    const meta = t
      ? `<div class="bmeta">${t.loc || "方位未明载"} · ${t.chars}字` +
        `${t.conf === "infer" ? " · <i>区位示意</i>" : ""}</div>`
      : `<div class="bmeta">${b.host ? "附于" + b.host + " · " : ""}${b.chars}字</div>`;
    const title = t ? t.name : b.name;
    return `<div class="entry${b.kind !== "temple" ? " narr" : ""}" data-id="${b.id}">` +
      `<div class="ehead"><span class="etag">${kindTag}</span>` +
      `<span class="ename">${title}</span>${b.kind === "temple" ? "" : ""}</div>` +
      meta +
      b.paras.map((p, i) =>
        `<p class="ctxt${i === 0 && b.kind === "temple" ? " first" : ""}">${p}</p>`).join("") +
      `</div>`;
  }

  function renderBody(vol) {
    const host = pbody();
    host.className = "reading";
    const bs = blocksOf(vol);
    host.innerHTML = bs.map(blockCard).join("");
    host.querySelectorAll(".entry").forEach(el =>
      el.addEventListener("click", () => gotoBlock(el.dataset.id, true)));
    host.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ── 锚导航 + 地图跟随 ── */
  function gotoBlock(id, scroll = true) {
    const host = pbody();
    const el = host.querySelector(`.entry[data-id="${id}"]`);
    if (!el) return;
    curId = id;
    host.querySelectorAll(".entry").forEach(x => x.classList.toggle("cur", x.dataset.id === id));
    if (scroll) el.scrollIntoView({ block: "start", behavior: "smooth" });
    const t = QLZ.temples.find(x => x.id === id);
    QLMAP.highlight(id, true);
    if (t) {
      QLMAP.selectTemple(id, { fly: true });
      QLMAP.highlight(id, true);
      QLRAIL.highlight(id);
    } else {
      const b = QL_SECTIONS[id];
      if (b && b.kind === "narrative") {
        /* 叙事块：飞到该卷伽蓝重心 */
        const near = QLZ.temples.filter(x => x.vol === b.vol);
        if (near.length) QLMAP.flyTo(near[0].pos, Math.max(QLMAP.map.getZoom(), -0.9));
      }
    }
    updateProg();
  }

  function updateProg() {
    const host = pbody();
    const els = [...host.querySelectorAll(".entry")];
    const i = els.findIndex(e => e.dataset.id === curId);
    const b = QL_SECTIONS[curId];
    const nm = nameOf(curId);
    document.getElementById("rprog").textContent =
      `${nm} · 卷${curVol} ${i + 1}/${els.length}`;
  }

  /* 滚动跟随：可视区顶部最近的 entry 即当前块（节流） */
  let timer = null;
  function onScroll() {
    if (timer) return;
    timer = setTimeout(() => {
      timer = null;
      const host = pbody();
      const top = host.scrollTop + 80;
      const els = [...host.querySelectorAll(".entry")];
      let best = 0;
      els.forEach((e, k) => { if (e.offsetTop <= top) best = k; });
      const id = els[best] && els[best].dataset.id;
      if (id && id !== curId) {
        curId = id;
        els.forEach(e => e.classList.toggle("cur", e.dataset.id === id));
        const t = QLZ.temples.find(x => x.id === id);
        QLMAP.highlight(id, true);
        if (t) {
          QLMAP.flyTo(t.pos);
          QLRAIL.highlight(id);
        }
        updateProg();
        const nm = nameOf(id);
        history.replaceState(null, "", `#m=read#juan=${curVol}` +
          (t ? `#gl=${encodeURIComponent(nm)}` : ""));
      }
    }, 260);
  }

  /* ── TTS 巡城听书 ── */
  const tts = { queue: [], idx: 0, on: false };
  function collectFrom(id) {
    const b = QL_SECTIONS[id];
    return b ? b.paras.slice(0, 6) : [];
  }
  function ttsNext() {
    if (!tts.on || tts.idx >= tts.queue.length) { ttsStop(); return; }
    const u = new SpeechSynthesisUtterance(tts.queue[tts.idx++]);
    u.lang = "zh-CN";
    u.rate = 0.95;
    const v = speechSynthesis.getVoices().find(x => x.lang && x.lang.startsWith("zh"));
    if (v) u.voice = v;
    u.onend = () => setTimeout(ttsNext, 240);
    speechSynthesis.speak(u);
  }
  function ttsToggle() {
    if (tts.on) { ttsStop(); return; }
    if (typeof speechSynthesis === "undefined") return;
    tts.queue = collectFrom(curId);
    if (!tts.queue.length) return;
    tts.on = true; tts.idx = 0;
    const b = document.getElementById("rtts");
    if (b) b.textContent = "■ 停读";
    ttsNext();
  }
  function ttsStop() {
    tts.on = false;
    try { speechSynthesis.cancel(); } catch (e) {}
    const b = document.getElementById("rtts");
    if (b) b.textContent = "▷ 朗读";
  }

  function close() {
    ttsStop();
    curId = null;
    document.getElementById("readerbar").classList.add("hidden");
  }

  return { open, close, gotoBlock, ttsToggle, get current() { return curId; },
           get vol() { return curVol; } };
})();
window.QLREADER = QLREADER;
