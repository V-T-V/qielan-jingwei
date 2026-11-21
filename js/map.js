/* ═══════════ 伽蓝经纬 · 城市舆图（L.CRS.Simple 示意平面） ═══════════
   城墙/宫城/金墉 · 城门符号 · 河渠 · 里坊/衙署 · 伽蓝点（分卷五色，径=条目字数）
   坐标=build_data.py 示意米制（x 东 y 北）；传 Leaflet 用 [y, x] */

const QLMAP = (() => {
  let map, selId = null, hlId = null, volFilter = null;
  let onTemple = null, onGate = null, onWard = null, onOffice = null, onWestStop = null;
  let scene = "city";
  const layers = {};
  let westLayers = null;

  const ll = p => [p[1], p[0]];                       /* [x,y] → latLng */
  const volColor = v => VOL_COLORS[v] || "#5a8368";
  const radiusOf = t => Math.max(5, Math.min(15, Math.sqrt(t.chars / 60)));

  function init() {
    initCity();
  }

  /* ── 场景切换：城图（CRS.Simple）⇄ 西行（WGS84 无瓦片示意） ── */
  function setScene(s) {
    if (s === scene) return;
    scene = s;
    if (map) { map.remove(); map = null; }
    westLayers = null;
    Object.keys(layers).forEach(k => { layers[k] = null; });
    if (s === "west") initWest();
    else initCity();
  }

  function toCity() {
    if (scene !== "city" && map) setScene("city");
  }

  function initCity() {
    scene = "city";
    map = L.map("map", {
      crs: L.CRS.Simple,
      attributionControl: false, zoomControl: true,
      minZoom: QL_CONF.minZoom, maxZoom: QL_CONF.maxZoom,
      zoomSnap: 0.25, zoomDelta: 0.5,
      center: ll(QL_CONF.homeView.center), zoom: QL_CONF.homeView.zoom,
      maxBounds: L.latLngBounds(ll([-3400, -2700]), ll([5900, 5400])),
      maxBoundsViscosity: .7,
    });
    ["guo", "mang", "river", "wall", "axis", "ward", "office", "landmark",
     "gate", "temple", "focus"].forEach(k => { layers[k] = L.layerGroup().addTo(map); });
    renderCity();
    renderGates();
    renderTemples();
    renderAux();
  }

  /* ── 西行场景：宋云行纪 20 站小比例尺示意（无外部瓦片，自绘底） ── */
  function initWest() {
    scene = "west";
    const stops = window.QL_SONGYUN ? window.QL_SONGYUN.stops : [];
    map = L.map("map", {
      attributionControl: false, zoomControl: true,
      minZoom: 3, maxZoom: 8, zoomSnap: 0.5,
      center: [36.5, 92], zoom: 4,
      maxBounds: L.latLngBounds([10, 50], [55, 130]), maxBoundsViscosity: .6,
    });
    westLayers = { route: L.layerGroup().addTo(map), stop: L.layerGroup().addTo(map) };
    if (!stops.length) return;
    const pts = stops.map(s => s.wgs);
    L.polyline(pts, { color: "#8e2b22", weight: 2.4, opacity: .85,
                      dashArray: "1 7", lineCap: "round" })
      .bindTooltip("宋云使西域 · 神龟元年—正光二年（518–521）", { sticky: true })
      .addTo(westLayers.route);
    stops.forEach((s, i) => {
      const edge = i === 0 || i === stops.length - 1;
      L.circleMarker(s.wgs, {
        radius: edge ? 6 : 4.5, color: "#f6f3e6", weight: 1.6,
        fillColor: edge ? "#7e2b1f" : "#a8874a", fillOpacity: .95, className: "westdot",
      }).bindTooltip(
        `<b style="font-family:KaiTi,serif;font-size:14px">${s.name}</b>` +
        ` <span style="color:#84929a">${s.cat}</span><br>` +
        `<span class="tipatt">今地：${s.today}</span><br>` +
        `${s.li ? "原文里程 " + s.li + " · " : ""}src:derived·infer` +
        `<br><span class="tipatt">「${s.cite.slice(0, 46)}…」</span>`,
        { direction: "top", opacity: .96, className: "ftip" })
        .on("click", () => onWestStop && onWestStop(s, i))
        .addTo(westLayers.stop);
      L.marker([s.wgs[0] + 0.25, s.wgs[1]], {
        icon: L.divIcon({ className: "", iconSize: null,
                          html: `<span class="westlab${edge ? " edge" : ""}">${s.name}</span>` }),
        interactive: false,
      }).addTo(westLayers.stop);
    });
    map.fitBounds(L.latLngBounds(pts).pad(0.18));
  }

  /* ── 城市骨架 ── */
  function renderCity() {
    const c = QLZ.city;
    /* 外郭（虚界） */
    L.polygon(c.guo.rect.map(ll), { className: "guoline", color: "#9a8f6d", weight: 1.2,
      dashArray: "6 8", fill: false, interactive: true })
      .bindTooltip(`外郭示意 · ${c.guo.att}`, { direction: "top" }).addTo(layers.guo);
    label((-2620 + 5460) / 2, -1560, "外郭（东西二十里 · 南北十五里）", "guolab", layers.guo);
    /* 邙山 */
    L.polygon(c.mangshan.band.map(ll), { className: "mangband", color: "#a79a72",
      weight: 1, fill: true, fillColor: "#c9bd93", fillOpacity: .3 })
      .bindTooltip(`邙山 · ${c.mangshan.att}`, { direction: "top" }).addTo(layers.mang);
    label((-2620 + 5460) / 2, 4620, "邙  山", "manglab", layers.mang);
    /* 河渠 */
    c.rivers.forEach(r => {
      L.polyline(r.pts.map(ll), { className: "riverline", color: "#4a7a9b", weight: 3,
        opacity: .75, smoothFactor: 1 })
        .bindTooltip(`${r.name} · ${r.att}`, { direction: "top", sticky: true })
        .addTo(layers.river);
      const mid = r.pts[Math.floor(r.pts.length / 2)];
      label(mid[0], mid[1] + 90, r.name, "riverlab", layers.river);
    });
    /* 内城城墙 */
    L.polygon(c.wall.map(ll), { className: "wallface", color: "#5c5138", weight: 4,
      fillColor: "#efe9d2", fillOpacity: .45 })
      .bindTooltip("北魏洛阳内城 · 示意轮廓 2,800×3,700m（考古常识量级）", { direction: "top" })
      .addTo(layers.wall);
    /* 宫城 + 金墉 */
    L.polygon(c.palace.map(ll), { color: "#8e2b22", weight: 2, fillColor: "#c8a06a",
      fillOpacity: .5 })
      .bindTooltip("宫城（太极殿—阊阖门轴线）· 示意", { direction: "top" }).addTo(layers.wall);
    L.polygon(c.jintang.map(ll), { color: "#6b5a8e", weight: 2, fillColor: "#b9aede",
      fillOpacity: .55 })
      .bindTooltip("金墉城 · 卷一「瑶光寺北有承明门，有金墉城，即魏氏所筑」", { direction: "top" })
      .addTo(layers.wall);
    label(1550, 3480, "宫城", "citylab", layers.wall);
    label(250, 3400, "金墉城", "citylab small", layers.wall);
    /* 铜驼中轴 */
    L.polyline(c.axis.map(ll), { color: "#a8874a", weight: 2.6, dashArray: "10 6",
      opacity: .9 }).bindTooltip("中轴御道（宣阳门—阊阖门）", { direction: "top" })
      .addTo(layers.axis);
    label(1400, 1100, "御  道", "axislab", layers.axis);
  }

  function label(x, y, text, cls, layer, dir = "center") {
    L.marker(ll([x, y]), {
      icon: L.divIcon({ className: "", html: `<span class="${cls}">${text}</span>`, iconSize: null }),
      interactive: false,
    }).addTo(layer);
  }

  /* ── 城门 ── */
  function renderGates() {
    layers.gate.clearLayers();
    QLZ.gates.forEach(g => {
      const m = L.marker(ll(g.pos), {
        icon: L.divIcon({
          className: "",
          html: `<span class="gatesym w${g.wall}">${g.disp || g.name}</span>`,
          iconSize: null, iconAnchor: [0, 0],
        }),
      });
      m.bindTooltip(`<b>${g.disp || g.name}</b> · ${g.wall === "宫" ? "宫城门" : g.wall + "墙"}<br>` +
        `<span class="tipatt">${g.att}</span><br>全书提及 ${g.mention} 次`,
        { direction: "top", opacity: .96, className: "ftip" });
      m.on("click", () => onGate && onGate(g));
      m.addTo(layers.gate);
    });
  }

  /* ── 伽蓝点 ── */
  function renderTemples() {
    if (scene !== "city" || !layers.temple) return;
    layers.temple.clearLayers();
    QLZ.temples.forEach(t => {
      if (volFilter && !volFilter.has(t.vol)) return;
      const sel = t.id === selId;
      const dot = L.circleMarker(ll(t.pos), {
        radius: radiusOf(t) + (sel ? 3 : 0),
        color: sel ? "#b23a2e" : "#f6f3e6",
        weight: sel ? 2.6 : 1.6,
        fillColor: volColor(t.vol), fillOpacity: .92,
        className: "galandot",
      });
      dot.bindTooltip(
        `<b style="font-family:KaiTi,serif;font-size:14px;letter-spacing:2px">${t.name}</b>` +
        ` <span style="color:#84929a">卷${t.vol}·${VOL_NAMES[t.vol]}</span><br>` +
        `<span class="tipatt">${t.loc || "方位未明载"}</span><br>` +
        `条目 ${t.chars} 字 · 全书出场 ${t.mention} 次` +
        (t.conf === "infer" ? " · <i>区位示意</i>" : ""),
        { direction: "top", opacity: .96, className: "ftip" });
      dot.on("click", () => onTemple && onTemple(t));
      dot.addTo(layers.temple);
      /* 寺名常显标签（高 zoom 时显示，避免远观拥挤——CSS 控制） */
      L.marker(ll([t.pos[0], t.pos[1] + 40]), {
        icon: L.divIcon({ className: "", iconSize: null,
          html: `<span class="galab v${t.vol}${t.id === hlId ? " hl" : ""}" data-tid="${t.id}">${t.name}</span>` }),
        interactive: false,
      }).addTo(layers.temple);
    });
  }

  /* ── 里坊 / 衙署 / 地标 ── */
  function renderAux() {
    QLZ.wards.forEach(w => {
      const m = L.rectangle(L.latLngBounds(ll([w.pos[0] - 55, w.pos[1] - 55]),
                                           ll([w.pos[0] + 55, w.pos[1] + 55])), {
        color: "#7d8a5a", weight: 1.2, fillColor: "#b5c08e", fillOpacity: .8, className: "wardsq",
      });
      m.bindTooltip(`<b>${w.name}</b> · 里坊/市<br><span class="tipatt">${w.att}</span>`,
        { direction: "top", opacity: .95 });
      m.on("click", () => onWard && onWard(w));
      m.addTo(layers.ward);
      L.marker(ll([w.pos[0], w.pos[1]]), {
        icon: L.divIcon({ className: "", iconSize: null, html: `<span class="wardlab">${w.name}</span>` }),
        interactive: false,
      }).addTo(layers.ward);
    });
    QLZ.offices.forEach(o => {
      const m = L.marker(ll(o.pos), {
        icon: L.divIcon({ className: "", iconSize: [10, 10],
          html: `<span class="offsym"></span>` }),
      });
      m.bindTooltip(`<b>${o.name}</b> · 衙署/宫室<br><span class="tipatt">${o.att}</span>`,
        { direction: "top", opacity: .95 });
      m.on("click", () => onOffice && onOffice(o));
      m.addTo(layers.office);
    });
    QLZ.landmarks.forEach(k => {
      L.marker(ll(k.pos), {
        icon: L.divIcon({ className: "", iconSize: null,
          html: `<span class="bridgesym">${k.name}</span>` }),
      }).bindTooltip(`<b>${k.name}</b><br><span class="tipatt">${k.att}</span>`,
        { direction: "top" }).addTo(layers.landmark);
    });
  }

  /* ── 选中 / 高亮 / 飞行 ── */
  function selectTemple(id, opt = {}) {
    toCity();
    selId = id;
    renderTemples();
    const t = QLZ.temples.find(x => x.id === id);
    if (t && opt.fly !== false && map) {
      map.flyTo(ll(t.pos), Math.max(map.getZoom(), -0.4), { duration: .9 });
    }
    focusRing(t);
  }

  function focusRing(t) {
    if (scene !== "city" || !layers.focus) return;
    layers.focus.clearLayers();
    if (!t) return;
    L.circleMarker(ll(t.pos), {
      radius: radiusOf(t) + 9, color: "#b23a2e", weight: 1.6,
      fill: false, dashArray: "4 4", className: "focusring",
    }).addTo(layers.focus);
  }

  function highlight(id, on) {
    hlId = on ? id : null;
    renderTemples();
  }

  function flyTo(pos, zoom) {
    toCity();
    if (!map) return;
    map.flyTo(ll(pos), zoom != null ? zoom : Math.max(map.getZoom(), -0.4), { duration: .9 });
  }

  function fitAll() {
    if (scene === "west" && map) {                    /* 西行场景：全程视图 */
      const pts = (window.QL_SONGYUN ? window.QL_SONGYUN.stops : []).map(s => s.wgs);
      if (pts.length) map.fitBounds(L.latLngBounds(pts).pad(0.18));
      return;
    }
    if (!map) return;
    map.fitBounds(L.latLngBounds(ll([-2700, -2400]), ll([5500, 5100])), { padding: [20, 20] });
  }

  function home() {
    toCity();
    if (!map) return;
    map.flyTo(ll(QL_CONF.homeView.center), QL_CONF.homeView.zoom, { duration: .8 });
  }

  return {
    init, selectTemple, highlight, flyTo, fitAll, home, renderTemples,
    setScene, get scene() { return scene; },
    get map() { return map; },
    set onTemple(fn) { onTemple = fn; },
    set onGate(fn) { onGate = fn; },
    set onWard(fn) { onWard = fn; },
    set onOffice(fn) { onOffice = fn; },
    set onWestStop(fn) { onWestStop = fn; },
    setVolFilter(vols) {
      /* vols: null=全部；Set(卷号) 则只显所选 */
      volFilter = vols;
      renderTemples();
    },
  };
})();
window.QLMAP = QLMAP;
