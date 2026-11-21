/* ═══════════ 伽蓝经纬 · 书签（LocalStorage，浏览器本地） ═══════════ */

const QLBM = (() => {
  const KEY = "qlgBookmarks";
  const MAX = 40;

  function load() {
    try { return JSON.parse(localStorage.getItem(KEY) || "[]"); }
    catch (e) { return []; }
  }
  function save(list) {
    try { localStorage.setItem(KEY, JSON.stringify(list.slice(0, MAX))); }
    catch (e) {}
  }
  function add(name, vol) {
    const list = load();
    if (!list.some(x => x.name === name)) {
      list.unshift({ name, vol, t: Date.now() });
      save(list);
    }
  }
  function remove(name) {
    save(load().filter(x => x.name !== name));
  }
  function has(name) { return load().some(x => x.name === name); }

  /* 面板 */
  function open() {
    const list = load();
    QLAPP.setMode("map");
    document.getElementById("vname").textContent = "书签";
    document.getElementById("vseal").textContent = "夹页";
    document.getElementById("pmeta").innerHTML = `<span>LocalStorage · 本浏览器</span>`;
    const host = document.getElementById("pbody");
    host.className = "";
    host.innerHTML = list.length
      ? list.map(b => `<div class="bmrow"><span class="bmchip" data-n="${b.name}">` +
          `<i style="background:${VOL_COLORS[b.vol] || "#9a8f6d"}"></i>${b.name}` +
          `<span class="bmv">卷${b.vol}·${VOL_NAMES[b.vol] || "序"}</span></span>` +
          `<button class="bmdel" data-d="${b.name}" title="移除">✕</button></div>`).join("")
      : `<p class="kv">尚无书签。伽蓝详情面板「✿ 夹书签」即存此处。</p>`;
    host.querySelectorAll(".bmchip").forEach(c =>
      c.addEventListener("click", () => {
        const t = QLZ.temples.find(x => x.name === c.dataset.n);
        if (t) QLAPP.openTemple(t.id);
      }));
    host.querySelectorAll(".bmdel").forEach(b =>
      b.addEventListener("click", () => { remove(b.dataset.d); open(); }));
    document.getElementById("panel").classList.add("open");
  }

  /* 详情面板按钮状态 */
  function bindToggle(btn, name, vol) {
    const paint = () => {
      btn.textContent = has(name) ? "✿ 已夹" : "✿ 夹书签";
      btn.classList.toggle("on", has(name));
    };
    btn.addEventListener("click", () => {
      has(name) ? remove(name) : add(name, vol);
      paint();
    });
    paint();
  }

  return { open, bindToggle, has };
})();
window.QLBM = QLBM;
