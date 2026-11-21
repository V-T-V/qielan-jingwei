"""伽蓝经纬 · 回归入口
python run_tests.py
  1) tools/lint.py          确定性静态检查（60+ 项）
  2) 数据断言（python 版，与 tests/assert_data.html 同源）
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
    print(f"伽蓝 43（11/12/8/10/2）· 宋云行纪 {m['songyun_chars']:,} 字 · "
          f"总 {stats['total_chars']:,} 字 · 御道 {stats['words']['御道']} 次 · "
          f"城门提及 {len(stats['gate_mentions'])} 门")


def browser_pages():
    pages = [f for f in os.listdir(os.path.join(ROOT, "tests")) if f.startswith("assert_")]
    assert len(pages) >= 2, "断言页不足"
    print(f"浏览器断言页 {len(pages)} 枚：{', '.join(pages)}")
    print("（serve 后逐页打开，title=PASS 即绿——截图证据见 docs/img/）")


if __name__ == "__main__":
    step("lint", lint)
    step("数据断言", data_asserts)
    step("浏览器断言页", browser_pages)
    if fails:
        print(f"✗✗ 回归失败：{', '.join(fails)}")
        sys.exit(1)
    print("═══ 全绿 ═══")
