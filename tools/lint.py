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
