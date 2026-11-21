"""伽蓝经纬 · 回归入口
python run_tests.py
  1) tools/lint.py          确定性静态检查（450+ 项：含文档同步/导出同口径/P2 哨兵）
  2) 数据断言（python 版，与 tests/assert_data.html 同源 + P2：桥/导出/西行/PDF）
  3) 浏览器断言页提醒（tests/assert_*.html，http 服务下打开，title=PASS 即绿）
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
fails = []


def step(name, fn):
    print(f"—— {name} ——")
    try:
        fn()
        print(f"✓ {name} 通过\n")
    except AssertionError as e:
        fails.append(name)
        print(f"✗ {name} 失败：{e}\n")


def lint():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "lint.py")],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip())
    assert r.returncode == 0, "lint 未全绿"


def data_asserts():
    qlz = json.loads(open(os.path.join(ROOT, "data/intermediate/entries.json"),
                          encoding="utf-8").read())
    m = qlz["meta"]
    assert m["temple_entries"] == 43, f"伽蓝 {m['temple_entries']} ≠ 43"
    assert m["vols"] == 5, "五卷不齐"
    assert m["per_vol"] == {"1": 11, "2": 12, "3": 8, "4": 10, "5": 2}, \
        f"分卷分布异常 {m['per_vol']}"
    assert m["songyun_chars"] > 4000, "宋云行纪过短"
    stats = json.load(open(os.path.join(ROOT, "docs", "stats.json"), encoding="utf-8"))
    assert stats["total_chars"] == 35999, f"总字数 {stats['total_chars']} ≠ 35999"
    assert sum(stats["vol_chars"].values()) == stats["total_chars"], "卷字数与总字数不齐"
    assert stats["words"]["御道"] >= 30, f"御道词频 {stats['words']['御道']} < 30"
    assert len(stats["gate_mentions"]) >= 13, "城门提及表不足 13 门"
    fr = json.load(open(os.path.join(ROOT, "data", "fetch_report.json"), encoding="utf-8"))
    assert len(fr["vols"]) == 6 and fr["total_chars"] > 35000, "抓取报告异常"

    # ── P2：论文同步 · 互查桥 · 导出 · 西行 ──
    assert os.path.exists(os.path.join(ROOT, "docs", "伽蓝经纬-数字人文.pdf")), \
        "论文 PDF 缺失（tools/build_paper_pdf.py）"
    xt = open(os.path.join(ROOT, "data", "xref_sjz.js"), encoding="utf-8").read()
    head = "window.QL_SJZ = "
    xr = json.loads(xt[xt.find(head) + len(head):].rstrip().rstrip(";"))
    assert xr["totals"]["placesHit"] >= 15 and xr["totals"]["pairs"] >= 6, "互查桥计数不足"
    syt = open(os.path.join(ROOT, "data", "songyun.js"), encoding="utf-8").read()
    head2 = "window.QL_SONGYUN = "
    sy = json.loads(syt[syt.find(head2) + len(head2):].rstrip().rstrip(";"))
    assert sy["meta"]["stops"] == 20 and sy["meta"]["chars"] == m["songyun_chars"], "西行结构化异常"
    kml = open(os.path.join(ROOT, "exports", "伽蓝经纬-城图.kml"), encoding="utf-8").read()
    assert kml.count("<Placemark>") == 43 + 15 + 24 + 12, "KML 要素数与四表不齐"
    print(f"伽蓝 43（11/12/8/10/2）· 宋云行纪 {m['songyun_chars']:,} 字 · "
          f"总 {stats['total_chars']:,} 字 · 御道 {stats['words']['御道']} 次 · "
          f"城门提及 {len(stats['gate_mentions'])} 门")
    print(f"P2：桥命中 {xr['totals']['placesHit']}/对读 {xr['totals']['pairs']} 对 · "
          f"西行 {sy['meta']['stops']} 站 · 导出 94 点（CSV×4+KML+GeoJSON） · 论文 PDF 在账")


def account_sums():
    """账目对账（SHA256SUMS）：逐行指纹与磁盘实测（行尾无关）+ 行数与生成器一致，过期即红。"""
    import importlib.util
    import re as _re
    spec = importlib.util.spec_from_file_location(
        "build_sums", os.path.join(ROOT, "tools", "build_sums.py"))
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    want = bs.collect()
    path = os.path.join(ROOT, "SHA256SUMS")
    assert os.path.exists(path), "SHA256SUMS 缺失——先 python tools/build_sums.py"
    raw = open(path, "rb").read()
    assert b"\r" not in raw, "SHA256SUMS 行尾混入 CR——须纯 LF，重跑 tools/build_sums.py"
    lines = raw.decode("utf-8").splitlines()
    assert lines, "SHA256SUMS 为空"
    problems, seen = [], set()
    for i, line in enumerate(lines, 1):
        parts = line.split("  ", 1)
        rel = parts[1].strip().replace("\\", "/") if len(parts) == 2 else ""
        if len(parts) != 2 or not _re.fullmatch(r"[0-9a-f]{64}", parts[0]) or not rel:
            problems.append(f"第{i}行格式非法"); continue
        if rel in seen:
            problems.append(f"第{i}行重复 {rel}"); continue
        seen.add(rel)
        if not os.path.isfile(os.path.join(ROOT, rel)):
            problems.append(f"账上文件缺失 {rel}"); continue
        if bs.sha256(rel) != parts[0]:
            problems.append(f"指纹不符 {rel}")
    assert not problems, f"账目失真 {len(problems)} 处：{problems[:4]}——重跑 python tools/build_sums.py"
    assert len(lines) == len(want), \
        f"账目行数 {len(lines)} ≠ 生成器 {len(want)}（产物增删未记账）——重跑 python tools/build_sums.py"
    off = [r for r in want if r not in seen]
    assert not off, f"产物缺账 {off[:4]}——重跑 python tools/build_sums.py"
    print(f"SHA256SUMS 对账通过：{len(lines)} 行 · 指纹全符（纯 LF）")


def browser_pages():
    pages = [f for f in os.listdir(os.path.join(ROOT, "tests")) if f.startswith("assert_")]
    assert len(pages) >= 2, "断言页不足"
    print(f"浏览器断言页 {len(pages)} 枚：{', '.join(pages)}")
    print("（serve 后逐页打开，title=PASS 即绿——截图证据见 docs/img/）")


if __name__ == "__main__":
    step("lint", lint)
    step("数据断言", data_asserts)
    step("账目对账", account_sums)
    step("浏览器断言页", browser_pages)
    if fails:
        print(f"✗✗ 回归失败：{', '.join(fails)}")
        sys.exit(1)
    print("═══ 全绿 ═══")
