# -*- coding: utf-8 -*-
"""伽蓝经纬 · 城图导出（与 js/export.js 前端按钮同口径，可复算）
四表：伽蓝 43 · 城门 15 · 里坊·市 24 · 衙署·宫室 12 →
  exports/伽蓝经纬-伽蓝.csv · -城门.csv · -里坊市.csv · -衙署宫室.csv（BOM）
  exports/伽蓝经纬-城图.kml（四 Folder 合一） · exports/伽蓝经纬-城图.geojson
坐标：一切 wgs 出自 build_data.py 管线（data/site_data.js QLZ.*.wgs），本脚本只读不另算；
      示意坐标在每一行/每个要素注明 src:derived + 坐标依据（SPEC P2 契约）。
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "exports")
VOL_NAMES = {0: "原序", 1: "城内", 2: "城东", 3: "城南", 4: "城西", 5: "城北"}
CRS_DESC = "坐标系：站内示意平面(米制)锚定WGS84·derived（量级推算）——非考古实测"


def load_qlz():
    t = io.open(os.path.join(ROOT, "data", "site_data.js"), encoding="utf-8").read()
    head = "const QLZ = "
    i = t.find(head)
    assert i >= 0, "site_data.js 缺 const QLZ"
    return json.loads(t[i + len(head):].rstrip().rstrip(";"))


def esc(s):
    s = "" if s is None else str(s)
    if any(c in s for c in '",\n'):
        return '"' + s.replace('"', '""') + '"'
    return s


def main():
    qlz = load_qlz()
    os.makedirs(OUT, exist_ok=True)

    tables = {
        "伽蓝经纬-伽蓝": (
            ["名", "类", "卷", "卷部", "位置句", "条目字数", "全书出场", "置信",
             "x_m", "y_m", "lat", "lng", "src", "坐标依据"],
            [[t["name"], "伽蓝", t["vol"], VOL_NAMES[t["vol"]], t["loc"], t["chars"],
              t["mention"], "原文明载方位" if t["conf"] == "text" else "区位示意",
              t["pos"][0], t["pos"][1], t["wgs"][0], t["wgs"][1], "derived",
              "原文方位句+汉魏洛阳故城考古常识布点；经纬为示意平面锚定换算（推）"]
             for t in qlz["temples"]]),
        "伽蓝经纬-城门": (
            ["名", "类", "墙", "书证", "全书提及", "x_m", "y_m", "lat", "lng",
             "src", "坐标依据"],
            [[g["disp"] or g["name"], "城门",
              "宫城门" if g["wall"] == "宫" else g["wall"] + "墙",
              g["att"], g["mention"], g["pos"][0], g["pos"][1],
              g["wgs"][0], g["wgs"][1], "derived",
              "序自载门谱+汉魏洛阳故城考古常识方位（示意）"] for g in qlz["gates"]]),
        "伽蓝经纬-里坊市": (
            ["名", "类", "卷", "书证", "x_m", "y_m", "lat", "lng", "src", "坐标依据"],
            [[w["name"], "里坊·市", w["vol"], w["att"], w["pos"][0], w["pos"][1],
              w["wgs"][0], w["wgs"][1], "derived", "书证锚定+示意布点"]
             for w in qlz["wards"]]),
        "伽蓝经纬-衙署宫室": (
            ["名", "类", "卷", "书证", "x_m", "y_m", "lat", "lng", "src", "坐标依据"],
            [[o["name"], "衙署·宫室", o["vol"], o["att"], o["pos"][0], o["pos"][1],
              o["wgs"][0], o["wgs"][1], "derived", "卷一轴线书证+示意布点"]
             for o in qlz["offices"]]),
    }

    for fname, (head, rows) in tables.items():
        with io.open(os.path.join(OUT, fname + ".csv"), "w", encoding="utf-8-sig",
                     newline="\n") as f:
            f.write(",".join(head) + "\n")
            for r in rows:
                f.write(",".join(esc(c) for c in r) + "\n")
        print(f"✓ {fname}.csv：{len(rows)} 行")

    # KML（四 Folder 合一）
    feats = []
    for t in qlz["temples"]:
        feats.append((t["name"], "伽蓝", "伽蓝",
                      f"卷{t['vol']}·{VOL_NAMES[t['vol']]} · 条目{t['chars']}字 · "
                      f"「{t['loc']}」· src:derived · {CRS_DESC}", t["wgs"]))
    for g in qlz["gates"]:
        feats.append((g["disp"] or g["name"], "城门", "城门",
                      f"{'宫城门' if g['wall'] == '宫' else g['wall'] + '墙'} · "
                      f"提及{g['mention']}次 · 「{g['att']}」· src:derived · {CRS_DESC}",
                      g["wgs"]))
    for w in qlz["wards"]:
        feats.append((w["name"], "里坊·市", "里坊市",
                      f"卷{w['vol']} · 「{w['att']}」· src:derived · {CRS_DESC}", w["wgs"]))
    for o in qlz["offices"]:
        feats.append((o["name"], "衙署·宫室", "衙署宫室",
                      f"卷{o['vol']} · 「{o['att']}」· src:derived · {CRS_DESC}", o["wgs"]))

    folders = {}
    for x in feats:
        folders.setdefault(x[2], []).append(x)
    pins = "".join(
        f'<Folder><name>{fn} {len(xs)}</name>' + "".join(
            f'<Placemark><name>{x[0]}</name><description>{x[3]}</description>'
            f'<Point><coordinates>{x[4][1]},{x[4][0]},0</coordinates></Point></Placemark>'
            for x in xs) + "</Folder>"
        for fn, xs in folders.items())
    kml = ('<?xml version="1.0" encoding="UTF-8"?>'
           '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'
           '<name>伽蓝经纬·北魏洛阳城示意点位</name>'
           f'<description>{CRS_DESC} · 内城2,800×3,700m 1里=440m · '
           f'{qlz["city"]["anchor"]["note"]}</description>'
           + pins + "</Document></kml>")
    with io.open(os.path.join(OUT, "伽蓝经纬-城图.kml"), "w", encoding="utf-8",
                 newline="\n") as f:
        f.write(kml)
    print(f"✓ 伽蓝经纬-城图.kml：{len(feats)} 要素")

    # GeoJSON
    gj = {
        "type": "FeatureCollection",
        "note": "伽蓝经纬 · 北魏洛阳示意点位 · tools/export_data.py 同口径可复算",
        "anchor": qlz["city"]["anchor"],
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [x[4][1], x[4][0]]},
            "properties": {"名": x[0], "类": x[1], "src": "derived",
                           "坐标系": "示意平面(米制)锚定WGS84（量级推算，非实测）",
                           "说明": x[3]},
        } for x in feats],
    }
    with io.open(os.path.join(OUT, "伽蓝经纬-城图.geojson"), "w", encoding="utf-8",
                 newline="\n") as f:
        json.dump(gj, f, ensure_ascii=False, indent=1)
    print(f"✓ 伽蓝经纬-城图.geojson：{len(feats)} 要素")
    print(f"合计：四表 {sum(len(r) for _, r in tables.values())} 行 CSV · "
          f"KML/GeoJSON 各 {len(feats)} 点（前端 js/export.js 同口径）")


if __name__ == "__main__":
    main()
