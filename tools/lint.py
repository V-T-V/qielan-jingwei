"""伽蓝经纬 · lint（确定性检查，失败即红）
用法: python tools/lint.py
类别（承姊妹站 lint 哲学——文字指令与 lint 冲突时 lint 是对的）：
  1  版本一致性   index.html/sw.js/js 的 ?v= 全等于 sw.js VERSION
  2  资源存在性   index.html 引用的 script/css 存在；sw SHELL_FILES 全部存在
  3  数据哨兵     伽蓝=43 · 城门=13 · 里坊≥20 · 衙署≥10 · 阅读块=53 · 总字数=stats.json
  4  坐标边界     伽蓝/城门/里坊/衙署全部落图界内；全部 src="derived"
  5  挂接完整     QLZ.temples 每条在 QL_SECTIONS 有原文；sections.js 与 entries.json 同块数
  6  语料口径     data/text/vN.js 与 data/vol/NNN.txt 逐字一致
  7  脚本产物一致 data/stats.js 的 total_chars 与 docs/stats.json 一致（前端只读脚本产物）
  8  禁用模式     map.fire("click") / innerHTML.indexOf 验证 / window._ftw / git mv -q / || true
  9  深链一致     app.js 深链语法（#m/#gl/#juan/#gate）
 10  manifest     icons 三枚存在，manifest 引用一致
 11  文档同步     ANALYSIS.md 新于论文 PDF 即红（改 md 必重排 build_paper_pdf.py）
 12  导出同口径   exports/ 四 CSV 行数=四表 · KML/GeoJSON 要素=94 · 皆含 derived 注记
 13  P2 数据哨兵  xref_sjz.js（桥双向计数/深链）· songyun.js（20 站书证）· 前端挂接
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails, checks = [], []


def ok(cond, msg):
    checks.append(cond)
    if not cond:
        fails.append(msg)


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def load_const(path, const):
    t = read(path)
    head = f"const {const} = "
    i = t.find(head)
    if i < 0:
        raise AssertionError(f"{path} 缺 const {const}")
    return json.loads(t[i + len(head):].rstrip().rstrip(";"))


def main():
    # ── 1 版本一致性 ──
    sw = read("sw.js")
    mver = re.search(r'VERSION = "v(\d+)"', sw)
    ok(mver, "sw.js 缺 VERSION 常量")
    ver = mver.group(1) if mver else ""
    for f in ["index.html", "sw.js"] + ["js/" + x for x in os.listdir(os.path.join(ROOT, "js"))
                                        if x.endswith(".js")]:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8").read()
        for bad in set(re.findall(r"\?v=(\d+)", t)):
            ok(bad == ver, f"{f} 含过期版本 ?v={bad}（当前 v{ver}）——请跑 tools/bump_version.py")

    # ── 2 资源存在性 ──
    idx = read("index.html")
    for src in re.findall(r'(?:src|href)="([^"#?]+)(?:\?[^"]*)?"', idx):
        if src.startswith(("http", "data:")):
            continue
        ok(os.path.exists(os.path.join(ROOT, src)), f"index.html 引用缺失: {src}")
    for m2 in re.finditer(r'"(\./[^"]+?)(?:\?[^"]*)?"', sw):
        rel = m2.group(1)[2:]
        ok(os.path.exists(os.path.join(ROOT, rel)), f"sw SHELL_FILES 缺失: {rel}")
    ok("data/stats.js" in idx, "index.html 须引 data/stats.js（rail/stats 面板依赖 QL_STATS）")
    ok("data/site_data.js" in idx, "index.html 须引 data/site_data.js")

    # ── 3 数据哨兵 ──
    qlz = load_const("data/site_data.js", "QLZ")
    m = qlz["meta"]
    ok(m["templeEntries"] == 43, f"伽蓝条数 {m['templeEntries']} ≠ 43")
    ok(len(qlz["gates"]) == 15, f"城门总数 {len(qlz['gates'])} ≠ 15（13 墙 + 2 宫）")
    ok(m["gatesWall"] == 13, f"城墙门 {m['gatesWall']} ≠ 13")
    ok(m["gatesPalace"] == 2, f"宫门 {m['gatesPalace']} ≠ 2")
    ok(len(qlz["wards"]) >= 20, f"里坊/市 {len(qlz['wards'])} < 20")
    ok(len(qlz["offices"]) >= 10, f"衙署 {len(qlz['offices'])} < 10")
    ok(len(qlz["temples"]) == 43, f"temples {len(qlz['temples'])} ≠ 43")
    ok(m["textConf"] + m["inferConf"] == 43, "text/infer 置信计数不齐")
    stats = json.load(open(os.path.join(ROOT, "docs", "stats.json"), encoding="utf-8"))
    ok(m["totalChars"] == stats["total_chars"], "site_data 与 stats.json 总字数不一致")
    ok(35000 <= stats["total_chars"] <= 40000, f"总字数 {stats['total_chars']} 越界")

    # ── 4 坐标边界与 src ──
    BX, BY = (-3400, 5900), (-2700, 5400)
    for kind in ["temples", "gates", "wards", "offices"]:
        for it in qlz[kind]:
            x, y = it["pos"]
            ok(BX[0] < x < BX[1] and BY[0] < y < BY[1],
               f"{kind}「{it['name']}」坐标越界 {it['pos']}")
    for it in qlz["temples"]:
        ok(it.get("src") == "derived", f"伽蓝「{it['name']}」缺 src:derived")
        ok(it["conf"] in ("text", "infer"), f"伽蓝「{it['name']}」conf 非法")
        ok(bool(it.get("loc")), f"伽蓝「{it['name']}」缺位置依据字段")
    for g in qlz["gates"]:
        ok(bool(g.get("att")), f"城门「{g['name']}」缺书证 att")

    # ── 5 挂接完整 ──
    secs = load_const("data/sections.js", "QL_SECTIONS")
    entries = json.load(open(os.path.join(ROOT, "data/intermediate/entries.json"),
                             encoding="utf-8"))
    ok(len(secs) == len(entries["blocks"]), f"sections {len(secs)} 块 ≠ entries {len(entries['blocks'])}")
    ords = sorted(b["ord"] for b in secs.values() if "ord" in b)
    ok(len(ords) == len(secs) and ords == list(range(len(secs))),
       "sections 缺 ord 或 ord 非连续（巡城排序依赖）")
    ok(all("id" in b and b["id"] for b in secs.values()), "sections 值缺 id 字段")
    for t in qlz["temples"]:
        ok(t["id"] in secs, f"伽蓝「{t['name']}」({t['id']}) 未挂原文块")
    kinds = {b["kind"] for b in entries["blocks"]}
    ok("songyun" in kinds and "preface" in kinds and "summary" in kinds,
       "特殊块（序/行纪/总述）缺失")

    # ── 6 语料口径 ──
    for v in range(0, 6):
        txt = read(f"data/vol/{v:03d}.txt")
        js = read(f"data/text/v{v}.js")
        head = f"(window.QLTEXT=window.QLTEXT||{{}})[{v}]="
        i = js.find(head)
        ok(i >= 0, f"data/text/v{v}.js 缺 {head.strip()}")
        if i >= 0:
            body = json.loads(js[i + len(head):].rstrip().rstrip(";"))
            ok(body == txt, f"data/text/v{v}.js 与 data/vol/{v:03d}.txt 语料不一致")

    # ── 7 脚本产物一致 ──
    qstats = load_const("data/stats.js", "QL_STATS")
    ok(qstats["total_chars"] == stats["total_chars"], "data/stats.js 与 docs/stats.json 不一致")
    ok(qstats["temple_entries"] == 43, "data/stats.js 伽蓝数 ≠ 43")

    # ── 8 禁用模式 ──
    banned = [
        (r'map\.fire\(\s*["\']click', "map.fire(click) 委托分发不可靠——用 canvas.dispatchEvent"),
        (r'innerHTML\.indexOf\(', "innerHTML.indexOf 验证会因 & 序列化失效——用 textContent"),
        (r'window\._ftw', "闭包 let 量不在 window 上——用存取函数"),
        (r'git mv -q', "git mv 无 -q flag"),
        (r'\|\|\s*true', "|| true 兜底吞错（教训 20）"),
    ]
    for f in ["js/" + x for x in os.listdir(os.path.join(ROOT, "js")) if x.endswith(".js")]:
        t = open(os.path.join(ROOT, f), encoding="utf-8").read()
        for pat, why in banned:
            ok(not re.search(pat, t), f"{f} 触禁：{why}")

    # ── 9 深链一致 ──
    app = read("js/app.js")
    for frag in ["#m=", "#gl=", "#juan=", "#gate="]:
        ok(frag in app, f"app.js 深链语法缺 {frag}")
    reader = read("js/reader.js")
    ok("#juan=" in reader, "reader.js 深链写回缺 #juan=")

    # ── 10 manifest ──
    mani = read("manifest.json")
    for icon in re.findall(r'"src":\s*"(icons/[^"]+)"', mani):
        ok(os.path.exists(os.path.join(ROOT, icon)), f"manifest 引用图标缺失: {icon}")

    # ── 11 文档同步（学 HHH check_docs_sync：md 改了 PDF 忘排即红） ──
    import time
    md = os.path.join(ROOT, "docs", "ANALYSIS.md")
    pdf = os.path.join(ROOT, "docs", "伽蓝经纬-数字人文.pdf")
    ok(os.path.exists(pdf), "docs/伽蓝经纬-数字人文.pdf 缺失——跑 tools/build_paper_pdf.py")
    if os.path.exists(pdf):
        mt, pt = os.path.getmtime(md), os.path.getmtime(pdf)
        ok(mt <= pt + 60,
           f"文档失同步：ANALYSIS.md（{time.strftime('%m-%d %H:%M', time.localtime(mt))}）"
           f"新于 PDF（{time.strftime('%m-%d %H:%M', time.localtime(pt))}）——重跑 tools/build_paper_pdf.py")

    # ── 12 导出同口径（前端 js/export.js 与 tools/export_data.py 同源） ──
    exp = os.path.join(ROOT, "exports")
    exp_files = ["伽蓝经纬-伽蓝.csv", "伽蓝经纬-城门.csv", "伽蓝经纬-里坊市.csv",
                 "伽蓝经纬-衙署宫室.csv", "伽蓝经纬-城图.kml", "伽蓝经纬-城图.geojson"]
    for fn in exp_files:
        ok(os.path.exists(os.path.join(exp, fn)), f"exports/{fn} 缺失——跑 tools/export_data.py")
    counts = {"伽蓝经纬-伽蓝.csv": len(qlz["temples"]),
              "伽蓝经纬-城门.csv": len(qlz["gates"]),
              "伽蓝经纬-里坊市.csv": len(qlz["wards"]),
              "伽蓝经纬-衙署宫室.csv": len(qlz["offices"])}
    for fn, n in counts.items():
        p = os.path.join(exp, fn)
        if os.path.exists(p):
            raw = open(p, "rb").read()
            ok(raw[:3] == b"\xef\xbb\xbf", f"exports/{fn} 缺 UTF-8 BOM")
            lines = raw.decode("utf-8-sig").rstrip("\n").split("\n")
            ok(len(lines) == n + 1, f"exports/{fn} {len(lines) - 1} 行 ≠ 表 {n} 行")
            ok("derived" in lines[1] if len(lines) > 1 else False,
               f"exports/{fn} 首数据行缺 src:derived 注记")
    n_pts = sum(counts.values())
    kml_p = os.path.join(exp, "伽蓝经纬-城图.kml")
    if os.path.exists(kml_p):
        kml = open(kml_p, encoding="utf-8").read()
        ok(kml.count("<Placemark>") == n_pts, f"KML 要素 {kml.count('<Placemark>')} ≠ {n_pts}")
        ok("derived" in kml, "KML 缺 derived 注记（示意坐标必须注明）")
    gj_p = os.path.join(exp, "伽蓝经纬-城图.geojson")
    if os.path.exists(gj_p):
        gj = json.load(open(gj_p, encoding="utf-8"))
        ok(len(gj["features"]) == n_pts, f"GeoJSON 要素 {len(gj['features'])} ≠ {n_pts}")
        ok(all(f["properties"].get("src") == "derived" for f in gj["features"]),
           "GeoJSON 存在未注 derived 的要素")
    ok("wgs" in qlz["temples"][0], "site_data 伽蓝缺 wgs（导出锚点字段）")
    ok("anchor" in qlz["city"], "site_data.city 缺 anchor（导出依据字段）")

    # ── 13 P2 数据哨兵（互查桥 + 宋云西行 + 前端挂接） ──
    ok(os.path.exists(os.path.join(ROOT, "data", "xref_sjz.js")),
       "data/xref_sjz.js 缺失——跑 tools/build_xref_sjz.py")
    ok(os.path.exists(os.path.join(ROOT, "data", "songyun.js")),
       "data/songyun.js 缺失——跑 tools/build_songyun.py")
    if os.path.exists(os.path.join(ROOT, "data", "xref_sjz.js")):
        xt = read("data/xref_sjz.js")
        head = "window.QL_SJZ = "
        xr = json.loads(xt[xt.find(head) + len(head):].rstrip().rstrip(";"))
        t13 = xr["totals"]
        ok(t13["placesHit"] >= 15, f"互查桥 B 侧命中 {t13['placesHit']} < 15")
        ok(t13["pairs"] >= 6, f"对读样例 {t13['pairs']} < 6")
        ok(t13["waterMentions"] >= 10, f"水道提及 {t13['waterMentions']} < 10")
        ok(all(w["href"].startswith("../SDJW/#r=") for w in xr["waters"]),
           "互查桥深链须为相对兄弟路径 ../SDJW/#r=<id>")
        ok(any("谷水" in w["forms"] for w in xr["waters"]), "谷水（穀水异体）须在桥内")
        ok(xr["excluded"], "同名假阳性排除表不得为空（消歧纪律）")
    if os.path.exists(os.path.join(ROOT, "data", "songyun.js")):
        st = read("data/songyun.js")
        head2 = "window.QL_SONGYUN = "
        sy = json.loads(st[st.find(head2) + len(head2):].rstrip().rstrip(";"))
        ok(sy["meta"]["stops"] == 20, f"西行 {sy['meta']['stops']} 站 ≠ 20")
        ok(sy["meta"]["chars"] == stats["songyun_chars"], "西行行纪字数与 stats 不一致")
        ok(all(s["cite"] for s in sy["stops"]), "西行站存在空书证")
        ok(all(s["src"] == "derived" and s["conf"] == "infer" for s in sy["stops"]),
           "西行站坐标须 src:derived·conf:infer")
        ok(any("存疑" in s["today"] for s in sy["stops"]), "波斯存疑注记须保留")
    for frag, why in [("js/export.js", "名录导出模块未挂 index.html"),
                      ("data/songyun.js", "宋云西行数据未挂 index.html")]:
        ok(frag in idx, why)
    stats_js = read("js/stats.js")
    ok("引水经注" in stats_js and "xref_sjz.js" in stats_js, "计量面板缺「引水经注」页签")
    ok("westOn" in app and "#m=west" in app, "西行场景/深链未接入 app.js")

    # ── 报告 ──
    n = len(checks)
    print(f"lint：{n} 项检查")
    if fails:
        print(f"✗ {len(fails)} 项失败：")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("✓ 全绿")


if __name__ == "__main__":
    main()
