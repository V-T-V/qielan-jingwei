/* ═══════════ 伽蓝经纬 · 左列纲目（卷 → 伽蓝 · 门 → 坊署） ═══════════ */

const QLRAIL = (() => {
  const host = () => document.getElementById("raillist");

  function build() {
    const el = host();
    let html = "";
    /* 序 */
    html += `<div class="rvol preface" data-vol="0"><span class="vlab">序</span>` +
      `<span class="vct">${QL_STATS.vol_chars["0"].toLocaleString()}字</span></div>`;
    for (let v = 1; v <= 5; v++) {
      const ts = QLZ.temples.filter(t => t.vol === v);
      html += `<div class="rvol" data-vol="${v}">` +
        `<span class="vdot" style="background:${VOL_COLORS[v]}"></span>` +
        `<span class="vlab">卷${v} · ${VOL_NAMES[v]}</span>` +
        `<span class="vct">${ts.length}寺 ${QL_STATS.vol_chars[String(v)].toLocaleString()}字</span></div>`;
      html += `<div class="vlist" data-for="${v}">` + ts.map(t =>
        `<div class="trow" data-id="${t.id}" data-name="${t.name}">` +
        `<span class="tn">${t.name}</span>` +
        `<span class="tc">${t.chars}</span></div>`).join("") + `</div>`;
    }
    /* 城市骨架组 */
    html += `<div class="rvol city"><span class="vlab">城市骨架</span>` +
      `<span class="vct">${QLZ.gates.length}门 ${QLZ.wards.length}坊署市</span></div>`;
    html += `<div class="vlist citylist">` +
      `<div class="trow gates"><span class="tn">城门十三</span><span class="tc">${QLZ.gates.length}</span></div>` +
      `<div class="trow wards"><span class="tn">里坊·市</span><span class="tc">${QLZ.wards.length}</span></div>` +
      `<div class="trow offices"><span class="tn">衙署·宫室</span><span class="tc">${QLZ.offices.length}</span></div>` +
      `</div>`;
    el.innerHTML = html;

    el.querySelectorAll(".rvol[data-vol]").forEach(r =>
      r.addEventListener("click", () => {
        const v = +r.dataset.vol;
        el.querySelectorAll(".vlist").forEach(l =>
          l.classList.toggle("open", +l.dataset.for === v && !l.classList.contains("open")));
      }));
    el.querySelectorAll(".trow[data-id]").forEach(r =>
      r.addEventListener("click", () => QLAPP.openTemple(r.dataset.id)));
    el.querySelectorAll(".trow.gates").forEach(r =>
      r.addEventListener("click", () => QLAPP.openDirectory("gates")));
    el.querySelectorAll(".trow.wards").forEach(r =>
      r.addEventListener("click", () => QLAPP.openDirectory("wards")));
    el.querySelectorAll(".trow.offices").forEach(r =>
      r.addEventListener("click", () => QLAPP.openDirectory("offices")));
  }

  function highlight(id) {
    host().querySelectorAll(".trow").forEach(r =>
      r.classList.toggle("cur", r.dataset.id === id));
    const row = host().querySelector(`.trow[data-id="${id}"]`);
    if (row) {
      const list = row.parentElement;
      list.classList.add("open");
      row.scrollIntoView({ block: "nearest" });
    }
  }

  function openVol(v) {
    host().querySelectorAll(".vlist").forEach(l =>
      l.classList.toggle("open", +l.dataset.for === v));
  }

  return { build, highlight, openVol };
})();
window.QLRAIL = QLRAIL;
