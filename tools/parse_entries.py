# -*- coding: utf-8 -*-
"""伽蓝经纬 · Phase 1 条目解析
输入: data/vol/000..005.txt（fetch_text.py 产出，每行一段）
输出: data/intermediate/entries.json
  blocks: 按卷顺序的阅读块（伽蓝条目 / 叙事块 / 序 / 宋云行纪 / 京师总述）
  每块: {id, kind, name, vol, paras[], head, loc}
纪律: 条目头用「典校条目表」（周祖谟/范祥雍校本通行篇目，对照本文核验），
      解析器只认段落前缀——不猜、不模糊匹配；每条必命中一次，否则报错退出。
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL_DIR = os.path.join(ROOT, "data", "vol")
OUT = os.path.join(ROOT, "data", "intermediate", "entries.json")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

VOL_NAMES = {1: "城内", 2: "城东", 3: "城南", 4: "城西", 5: "城北"}

# ── 典校伽蓝条目表（卷 → [(寺名, 段首前缀)]）──────────────
# 前缀即原文段落开头；minor=True 表示条目头在他人段落之内（仍单列成条）。
TEMPLES = {
    1: [("永宁寺", "永宁寺，"), ("建中寺", "建中寺，"), ("长秋寺", "长秋寺，"),
        ("瑶光寺", "瑶光寺，"), ("景乐寺", "景乐寺，"), ("昭仪尼寺", "昭仪尼寺，"),
        ("胡统寺", "胡统寺，"), ("修梵寺", "修梵寺，"), ("景林寺", "景林寺，")],
    2: [("明悬尼寺", "明悬尼寺，"), ("龙华寺", "龙华寺，"),
        ("璎珞寺", "璎珞寺在建春门外御道北"), ("宗圣寺", "宗圣寺有像一躯"),
        ("崇真寺", "崇真寺比丘惠凝"), ("魏昌尼寺", "魏昌尼寺，"),
        ("庄严寺", "庄严寺在东阳门外"), ("秦太上君寺", "秦太上君寺，"),
        ("正始寺", "正始寺，"), ("平等寺", "平等寺，"), ("景宁寺", "景宁寺，")],
    3: [("景明寺", "景明寺，"), ("大统寺", "大统寺在景明寺西"),
        ("报德寺", "报德寺，"), ("菩提寺", "菩提寺，"),
        ("高阳王寺", "高阳王寺，"), ("崇虚寺", "崇虚寺在城西")],
    4: [("冲觉寺", "冲觉寺，"), ("宣忠寺", "宣忠寺，"),
        ("白马寺", "白马寺，"), ("宝光寺", "宝光寺，"),
        ("法云寺", "法云寺，"), ("追光寺", "追光寺，"),
        ("融觉寺", "融觉寺，"), ("大觉寺", "大觉寺，"),
        ("永明寺", "永明寺，")],
    5: [("禅虚寺", "禅虚寺在大夏门"), ("凝圆寺", "凝圆寺，")],
}

# 寺内附出的小条目（正文在他条段落内点名+「所立/在」；挂进条目表与阅读块）
MINOR = [
    (1, "愿会寺", "池西南有愿会寺"),
    (1, "嵩明寺", "嵩明寺复在修梵寺西"),
    (2, "景兴尼寺", "石桥南道有景兴尼寺"),
    (3, "龙华寺", "龙华寺，广陵王所立也"),
    (3, "追圣寺", "追圣寺，北海王所立也"),
    (4, "王典御寺", "宣忠寺东王典御寺，"),
]

# 阅读块特殊段（卷 → 段首前缀 → 块名/类别）
SPECIAL = [
    (1, "瑶光寺北有承明门", ("金墉城", "narrative")),
    (2, "出建春门外一里馀至东石桥", ("东石桥·马市", "narrative")),
    (2, "建阳里东有绥民里", ("绥民里·洛阳县", "narrative")),
    (2, "孝义里东即是洛阳小市", ("孝义里·小市", "narrative")),
    (2, "阳渠北有建阳里", ("建阳里·萧综", "narrative")),
    (2, "敬义里南有昭德里", ("昭德里", "narrative")),
    (5, "洛阳城东北有上商里", ("上商里·闻义里", "narrative")),
    (5, "闻义里有敦煌人宋云宅", ("宋云行纪", "songyun")),
    (5, "京师东西二十里", ("京师总述", "summary")),
]


def vol_lines(v):
    with open(os.path.join(VOL_DIR, f"{v:03d}.txt"), encoding="utf-8") as f:
        return [ln for ln in f.read().split("\n") if ln and not ln.startswith("◎")]


def extract_loc(head_para):
    """从头段提取位置描述：优先「在…」，次「所谓X里」。"""
    m = re.search(r"在[^。，；]{2,30}", head_para)
    if not m:
        m = re.search(r"(所谓[\u4e00-\u9fff]{2,6}里)", head_para)
    return (m.group(0) if m else "").strip()


def main():
    blocks, errors = [], []

    # 序（000）
    pre = vol_lines(0)
    blocks.append({"id": "p0", "kind": "preface", "name": "原序", "vol": 0,
                   "paras": pre, "loc": ""})

    for v in range(1, 6):
        lines = vol_lines(v)
        # 段落 → 块的分派表
        kinds = ["narrative"] * len(lines)   # 默认叙事（归入当前块）
        head_of = {}

        for name, prefix in TEMPLES[v]:
            idx = [i for i, ln in enumerate(lines) if ln.startswith(prefix)]
            if len(idx) != 1:
                errors.append(f"卷{v} 条目「{name}」前缀命中 {len(idx)} 次（前缀: {prefix}）")
                continue
            head_of[idx[0]] = name

        sp_heads = {}
        for sv, prefix, spec in SPECIAL:
            if sv != v or spec is None:
                continue
            idx = [i for i, ln in enumerate(lines) if ln.startswith(prefix)]
            if len(idx) != 1:
                errors.append(f"卷{v} 特殊块「{spec[0]}」前缀命中 {len(idx)} 次")
                continue
            sp_heads[idx[0]] = spec

        # 组块：条目头开新块；特殊块开新块；其余并入当前块
        cur = None
        for i, ln in enumerate(lines):
            if i in head_of:
                cur = {"id": f"t{v}-{len(blocks)+1:02d}", "kind": "temple",
                       "name": head_of[i], "vol": v, "paras": [ln], "head": ln}
                blocks.append(cur)
            elif i in sp_heads:
                nm, kd = sp_heads[i]
                cur = {"id": f"n{v}-{len(blocks)+1:02d}", "kind": kd, "name": nm,
                       "vol": v, "paras": [ln], "head": ln}
                blocks.append(cur)
            else:
                if cur is None:
                    cur = {"id": f"n{v}-{len(blocks)+1:02d}", "kind": "narrative",
                           "name": f"城{VOL_NAMES[v][1]}开篇", "vol": v, "paras": [ln], "head": ln}
                    blocks.append(cur)
                else:
                    cur["paras"].append(ln)

        # minor 条目：挂进所属段落所在块 + 单列条目表
        for mv, name, marker in MINOR:
            if mv != v:
                continue
            host = None
            for b in blocks:
                if b["vol"] == v and any(marker in p for p in b["paras"]):
                    host = b
                    break
            if host is None:
                errors.append(f"卷{v} 附条「{name}」未见宿主段落")
                continue
            host.setdefault("minors", []).append(name)

    # minor → 升格为独立阅读块（紧跟宿主块后，段落引用宿主段）
    out_blocks = []
    for b in blocks:
        out_blocks.append(b)
        for name in b.get("minors", []):
            paras = [p for p in b["paras"] if name in p]
            out_blocks.append({"id": f"m{b['vol']}-{len(out_blocks)+1:02d}",
                               "kind": "temple", "name": name, "vol": b["vol"],
                               "paras": paras, "head": paras[0] if paras else "",
                               "host": b["name"]})

    # 位置描述 + 字数
    for b in out_blocks:
        b.pop("minors", None)
        b["loc"] = extract_loc(b.get("head", "")) if b["kind"] == "temple" else ""
        b["chars"] = sum(len(p) for p in b["paras"])

    # 校验：条目总数
    temples = [b for b in out_blocks if b["kind"] == "temple"]
    expect = sum(len(x) for x in TEMPLES.values()) + len(MINOR)
    if len(temples) != expect:
        errors.append(f"伽蓝条目 {len(temples)} ≠ 预期 {expect}")

    if errors:
        print("✗ 解析失败：")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    order = {"preface": 0, "temple": 1, "narrative": 1, "songyun": 2, "summary": 3}
    meta = {
        "vols": 5,
        "temple_entries": len(temples),
        "per_vol": {v: sum(1 for b in temples if b["vol"] == v) for v in range(1, 6)},
        "blocks": len(out_blocks),
        "total_chars": sum(b["chars"] for b in out_blocks),
        "songyun_chars": next(b["chars"] for b in out_blocks if b["kind"] == "songyun"),
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "blocks": out_blocks}, f, ensure_ascii=False, indent=1)
    print(f"✓ {meta['blocks']} 块 · 伽蓝 {meta['temple_entries']} 条 · "
          f"{meta['total_chars']:,} 字（宋云行纪 {meta['songyun_chars']:,}）")
    print("  卷分布:", " ".join(f"卷{k}:{n}" for k, n in meta["per_vol"].items()))


if __name__ == "__main__":
    main()
