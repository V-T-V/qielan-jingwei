/* ═══════════ 伽蓝经纬 · 城图导出（CSV·BOM / KML / GeoJSON） ═══════════
   四表：伽蓝 43 · 城门 15 · 里坊·市 24 · 衙署·宫室 12。
   坐标口径与 tools/export_data.py 同源——一切 wgs 出自 build_data.py 管线
   （QLZ.*.wgs），前端只读不另算；示意坐标在每一行/每个要素注明 src:derived。
   经纬=示意平面锚定 WGS84（QLZ.city.anchor，量级推算），非考古实测。 */

const QLEXPORT = (() => {
  const CRSDesc = "坐标系：站内示意平面(米制)锚定WGS84·derived（量级推算）——非考古实测";

  function esc(s) {
    s = String(s == null ? "" : s);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  }

  function dl(content, mime, filename) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([content], { type: mime }));
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 3000);
  }

  /* ── 表结构（列名 + 行函数）；wgs/pos/依据全出自 QLZ ── */
  const TABLES = {
    temples: {
      label: "伽蓝", file: "伽蓝经纬-伽蓝",
      head: ["名", "类", "卷", "卷部", "位置句", "条目字数", "全书出场", "置信",
             "x_m", "y_m", "lat", "lng", "src", "坐标依据"],
      rows: () => QLZ.temples.map(t => [
        t.name, "伽蓝", t.vol, VOL_NAMES[t.vol], t.loc, t.chars, t.mention,
        t.conf === "text" ? "原文明载方位" : "区位示意",
        t.pos[0], t.pos[1], t.wgs[0], t.wgs[1], "derived",
        "原文方位句+汉魏洛阳故城考古常识布点；经纬为示意平面锚定换算（推）"]),
    },
    gates: {
      label: "城门", file: "伽蓝经纬-城门",
      head: ["名", "类", "墙", "书证", "全书提及", "x_m", "y_m", "lat", "lng",
             "src", "坐标依据"],
      rows: () => QLZ.gates.map(g => [
        g.disp || g.name, "城门", g.wall === "宫" ? "宫城门" : g.wall + "墙",
        g.att, g.mention, g.pos[0], g.pos[1], g.wgs[0], g.wgs[1], "derived",
        "序自载门谱+汉魏洛阳故城考古常识方位（示意）"]),
    },
    wards: {
      label: "里坊·市", file: "伽蓝经纬-里坊市",
      head: ["名", "类", "卷", "书证", "x_m", "y_m", "lat", "lng", "src", "坐标依据"],
      rows: () => QLZ.wards.map(w => [
        w.name, "里坊·市", w.vol, w.att, w.pos[0], w.pos[1], w.wgs[0], w.wgs[1],
        "derived", "书证锚定+示意布点"]),
    },
    offices: {
      label: "衙署·宫室", file: "伽蓝经纬-衙署宫室",
      head: ["名", "类", "卷", "书证", "x_m", "y_m", "lat", "lng", "src", "坐标依据"],
      rows: () => QLZ.offices.map(o => [
        o.name, "衙署·宫室", o.vol, o.att, o.pos[0], o.pos[1], o.wgs[0], o.wgs[1],
        "derived", "卷一轴线书证+示意布点"]),
    },
  };

  function csv(kind) {
    const t = TABLES[kind];
    const NL = String.fromCharCode(10);
    const BOM = String.fromCharCode(0xFEFF);
    const body = [t.head.join(",")].concat(
      t.rows().map(r => r.map(esc).join(","))).join(NL);
    dl(BOM + body, "text/csv;charset=utf-8", t.file + ".csv");
  }

  /* ── KML / GeoJSON：四表合一（Folder 分组） ── */
  function allFeatures() {
    const f = [];
    QLZ.temples.forEach(t => f.push({
      name: t.name, kind: "伽蓝", folder: "伽蓝",
      desc: `卷${t.vol}·${VOL_NAMES[t.vol]} · 条目${t.chars}字 · ` +
        `「${t.loc}」· src:derived · ` + CRSDesc,
      wgs: t.wgs }));
    QLZ.gates.forEach(g => f.push({
      name: g.disp || g.name, kind: "城门", folder: "城门",
      desc: `${g.wall === "宫" ? "宫城门" : g.wall + "墙"} · 提及${g.mention}次 · 「${g.att}」· src:derived · ` + CRSDesc,
      wgs: g.wgs }));
    QLZ.wards.forEach(w => f.push({
      name: w.name, kind: "里坊·市", folder: "里坊市",
      desc: `卷${w.vol} · 「${w.att}」· src:derived · ` + CRSDesc, wgs: w.wgs }));
    QLZ.offices.forEach(o => f.push({
      name: o.name, kind: "衙署·宫室", folder: "衙署宫室",
      desc: `卷${o.vol} · 「${o.att}」· src:derived · ` + CRSDesc, wgs: o.wgs }));
    return f;
  }

  function kml() {
    const folders = {};
    allFeatures().forEach(x => (folders[x.folder] = folders[x.folder] || []).push(x));
    const pins = Object.entries(folders).map(([fn, xs]) =>
      `<Folder><name>${fn} ${xs.length}</name>` + xs.map(x =>
        `<Placemark><name>${x.name}</name><description>${x.desc}</description>` +
        `<Point><coordinates>${x.wgs[1]},${x.wgs[0]},0</coordinates></Point></Placemark>`
      ).join("") + `</Folder>`).join("");
    const kml = `<?xml version="1.0" encoding="UTF-8"?>` +
      `<kml xmlns="http://www.opengis.net/kml/2.2"><Document>` +
      `<name>伽蓝经纬·北魏洛阳城示意点位</name>` +
      `<description>${CRSDesc} · 内城2,800×3,700m 1里=440m · ${QLZ.city.anchor.note}</description>` +
      pins + `</Document></kml>`;
    dl(kml, "application/vnd.google-earth.kml+xml", "伽蓝经纬-城图.kml");
  }

  function geojson() {
    const feats = allFeatures().map(x => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [x.wgs[1], x.wgs[0]] },
      properties: { 名: x.name, 类: x.kind, src: "derived",
        坐标系: "示意平面(米制)锚定WGS84（量级推算，非实测）",
        说明: x.desc },
    }));
    dl(JSON.stringify({ type: "FeatureCollection",
      note: "伽蓝经纬 · 北魏洛阳示意点位 · tools/export_data.py 同口径可复算",
      anchor: QLZ.city.anchor, features: feats }, null, 1),
      "application/geo+json", "伽蓝经纬-城图.geojson");
  }

  return { csv, kml, geojson, tables: TABLES };
})();
window.QLEXPORT = QLEXPORT;
