# -*- coding: utf-8 -*-
"""伽蓝经纬 · 文本计量（凡数字必出自脚本）
输入: data/vol/000..005.txt + data/intermediate/entries.json
输出: docs/stats.json + docs/ANALYSIS.md（前端 data/stats.js 由 build_data.py 转抄，不另算）
"""
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL_DIR = os.path.join(ROOT, "data", "vol")
DOCS = os.path.join(ROOT, "docs")
os.makedirs(DOCS, exist_ok=True)

VOL_NAMES = {0: "原序", 1: "城内", 2: "城东", 3: "城南", 4: "城西", 5: "城北"}


def corpus():
    """全书纯文本语料（同一口径：vol/*.txt 逐字）。"""
    return {v: open(os.path.join(VOL_DIR, f"{v:03d}.txt"), encoding="utf-8").read()
            for v in range(0, 6)}


def count_chars(t):
    """语料字数：不计空白与换行（与 fetch_report 同口径）。"""
    return len(re.sub(r"\s", "", t))


def main():
    texts = corpus()
    entries = json.load(open(os.path.join(ROOT, "data/intermediate/entries.json"),
                             encoding="utf-8"))
    blocks = entries["blocks"]
    temples = [b for b in blocks if b["kind"] == "temple"]
    whole = "\n".join(texts.values())

    # ── 卷篇幅 ──
    vol_chars = {str(v): count_chars(texts[v]) for v in range(0, 6)}

    # ── 伽蓝条目统计 ──
    per_vol = {str(v): sum(1 for b in temples if b["vol"] == v) for v in range(1, 6)}
    temple_chars = sorted(
        ((b["name"], b["vol"], b["chars"]) for b in temples),
        key=lambda x: -x[2])

    # ── 词汇频次（全书口径，含序） ──
    words = {w: whole.count(w) for w in
             ["寺", "尼寺", "浮图", "塔", "佛", "僧", "尼", "菩萨", "御道",
              "门", "里", "市", "洛水", "穀水", "阳渠", "洛阳", "京师",
              "永宁", "灵太后", "尔朱荣", "庄严", "金像", "幡"]}

    # ── 佛寺被引频次（名气指数：核心名=寺名去「寺」尾，全书出场；含自条头部） ──
    mentions = {}
    for b in temples:
        core = b["name"][:-1] if b["name"].endswith("寺") else b["name"]
        mentions[b["name"]] = whole.count(core)
    mentions_top = sorted(mentions.items(), key=lambda x: -x[1])

    # ── 城门提及 ──
    gate_names = ["建春门", "东阳门", "青阳门", "清阳门", "开阳门", "平昌门", "宣阳门",
                  "津阳门", "西阳门", "西明门", "承明门", "大夏门", "广莫门", "阊阖门",
                  "千秋门"]
    gate_mentions = {g: len(re.findall(g, whole)) for g in gate_names}
    gate_mentions["青阳门(合清阳门)"] = gate_mentions.pop("青阳门") + gate_mentions.pop("清阳门")

    # ── 里坊/市提及（典校名单） ──
    ward_names = ["建阳里", "绥民里", "崇义里", "东安里", "晖文里", "敬义里", "昭德里",
                  "孝敬里", "景宁里", "孝义里", "殖货里", "延年里", "永康里", "治粟里",
                  "利民里", "慕义里", "奉终里", "寿丘里", "闻义里", "永平里",
                  "大市", "小市", "四通市", "永桥",
                  # 大市十里（卷四，行当分坊）
                  "通商里", "达货里", "调音里", "乐律里", "退酤里",
                  "治觞里", "慈孝里", "准财里", "金肆里"]
    ward_mentions = {w: whole.count(w) for w in ward_names}

    stats = {
        "source": "国学导航《洛阳伽蓝记》（GB18030 抓取转存；维基文库本网络不可达，依 SPEC 数据源次序回退）",
        "mention_note": "名气指数=核心名（去「寺」尾）全书出场次数，含自条头部",
        "total_chars": sum(vol_chars.values()),
        "vol_chars": vol_chars,
        "vol_blocks": {str(v): sum(1 for b in blocks if b["vol"] == v) for v in range(0, 6)},
        "temple_entries": len(temples),
        "temple_per_vol": per_vol,
        "temple_chars_top": temple_chars[:12],
        "songyun_chars": next(b["chars"] for b in blocks if b["kind"] == "songyun"),
        "words": words,
        "temple_mentions": mentions_top,
        "gate_mentions": dict(sorted(gate_mentions.items(), key=lambda x: -x[1])),
        "ward_mentions": dict(sorted(ward_mentions.items(), key=lambda x: -x[1])),
    }
    with open(os.path.join(DOCS, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1)

    # ── ANALYSIS.md ──
    w = stats["words"]
    md = f"""# 伽蓝经纬 · 文本计量（ANALYSIS）

> 全部数字出自 `python tools/stats.py` → `docs/stats.json`；前端「计量」面板只读脚本产物（`data/stats.js` 转抄）。
> 语料口径：`data/vol/*.txt` 纯正文（不含 JS 键名/导航噪声），国学导航本。

## 一、覆盖

| 项 | 数 |
|---|---|
| 序 + 五卷总字数 | {stats['total_chars']:,} |
| 伽蓝条目 | {stats['temple_entries']} 条（{'/'.join(str(per_vol[str(v)]) for v in range(1,6))}，卷一至卷五） |
| 宋云行纪 | {stats['songyun_chars']:,} 字（卷五附出） |
| 阅读块 | {len(blocks)} 块（伽蓝 + 里坊叙事 + 行纪 + 京师总述） |

## 二、卷篇幅（字）

| 卷 | { ' | '.join(VOL_NAMES[v] for v in range(0,6)) } |
|---|{'---|' * 7}
| 字数 | { ' | '.join(f'{vol_chars[str(v)]:,}' for v in range(0,6)) } |

城东独厚（{vol_chars['2']:,} 字）：建春门—东阳门—青阳门外伽蓝与里坊交错，叙事最密。
城南最薄（{vol_chars['3']:,} 字）而景明寺一寺独大。

## 三、伽蓝条目篇幅 Top 12

| 伽蓝 | 卷 | 字数 |
|---|---|---|
{chr(10).join(f"| {n} | 卷{v} | {c:,} |" for n, v, c in stats['temple_chars_top'])}

永宁寺条 {temple_chars[0][2]:,} 字居全书之首——塔刹、装修、法事、火灾四段铺陈，是杨衒之的「序曲式」书写。

## 四、佛寺被引频次（{stats['mention_note']}）

| 寺 | 全书出场 |
|---|---|
{chr(10).join(f"| {n} | {c} |" for n, c in stats['temple_mentions'])}

## 五、城门提及

| 门 | 次 | 门 | 次 |
|---|---|---|---|
""" + "\n".join(
        f"| {k} | {v} | {k2} | {v2} |"
        for (k, v), (k2, v2) in zip(
            list(stats["gate_mentions"].items())[::2] + [("", "")],
            list(stats["gate_mentions"].items())[1::2] + [("", "")])
    ) + f"""

阊阖门（宫城正门）与建春门（东面首门）出场最频——前者是仪礼轴线起点，后者是城东伽蓝带的锚点。

## 六、里坊/市提及（Top）

{ ' · '.join(f'{k}({v})' for k, v in list(stats['ward_mentions'].items())[:14]) }

## 七、词汇

寺 {w['寺']} · 尼寺 {w['尼寺']} · 浮图 {w['浮图']} · 塔 {w['塔']} · 御道 {w['御道']} ·
洛水 {w['洛水']} · 穀水 {w['穀水']} · 阳渠 {w['阳渠']} · 洛阳 {w['洛阳']} · 永宁 {w['永宁']}

「御道」{w['御道']} 次：全书空间书写的骨架词——伽蓝、里坊、衙署皆以「某门(内/外)N里御道某侧」定位。
"""
    with open(os.path.join(DOCS, "ANALYSIS.md"), "w", encoding="utf-8") as f:
        f.write(md)

    print(f"✓ stats.json + ANALYSIS.md · 总 {stats['total_chars']:,} 字 · "
          f"伽蓝 {stats['temple_entries']} · 词「寺」{w['寺']} 御道{w['御道']}")


if __name__ == "__main__":
    main()
