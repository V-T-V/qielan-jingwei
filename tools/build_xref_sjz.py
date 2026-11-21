# -*- coding: utf-8 -*-
"""伽蓝经纬 · 《水经注》互查数据构建（水道经纬站际桥，承 HHH build_sjz_xref / SDJW build_crossref 模式）
双向互文（SDJW 只读，绝不写入）：
  A 本书→水经：伽蓝记语料提及的水道名（穀水≡谷水异体折算），含样例句 + ↗循水深链
  B 水经→本书：谷水注/洛水注（rivers.json blocks 全注文）中出现的伽蓝记名物
    （城门/伽蓝/里坊/衙署/地标）计数 + 样例句；命不中如实计「无对应」
消歧（如实记录，不硬凑）：
  · 深水/决水/若水/渠水 为普通词序（「决水种麦」「乘船渡一深水」「若水践泥」「临渠水」），排除并注明
  · 阳渠无独立分节（水经注以「渠水/阳渠」行于谷水注内），深链退到谷水
  · 辛头大河（宋云行纪·印度河）不属 SDJW 水道谱，不入计数，注明
输出: data/xref_sjz.js —— window.QL_SJZ（js/stats.js「引水经注」页签懒加载）
深链: ../SDJW/#r=<水道id>（相对兄弟路径——约定父目录 D:/W_A_W 同根服务）
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDJW = os.path.join(os.path.dirname(ROOT), "SDJW")   # D:/W_A_W/SDJW
SITE = "../SDJW/"

# ── A 侧：本书提及水道（异体/排除在此整编） ──
# (显示名, [伽蓝记中出现的写法], 排除说明 or None)
WATERS = [
    ("洛水", ["洛水"], None),
    ("谷水", ["谷水", "穀水"], "本书用「穀水」，水经注作「谷水」——异体同水"),
    ("阳渠", ["阳渠"], "无独立分节（行于谷水注内），深链退到谷水"),
]
EXCLUDED = [
    ("决水", "「决水种麦」「决水以种」动宾结构，非水道专名"),
    ("深水", "「乘船渡一深水」普通词序"),
    ("若水", "「若水践泥」普通词序（SDJW 之若水为雅砻江古名，与此无涉）"),
    ("渠水", "「临渠水」泛指渠中水，指阳渠，已归阳渠语境"),
]

# B 侧附加地标（不在四表，但两书皆及，互文价值高；先在语料中验真，验不中自动剔除）
EXTRA_LANDMARKS = ["铜驼", "翟泉", "华林园", "天渊池"]

# 全名→匹配别名（水经注用单名行文：太仓/太极殿；书证以 LYGL 表名为准）
ALIASES = {"太仓·导官署": ["太仓"], "宫城·太极殿": ["太极殿"]}

# 一名二实注记（同名条目合并计数，注在此）
NAME_NOTES = {"阊阖门": "西墙门（汉上西门）与宫城正门一名二实，本站分列、桥上合并计"}

# 样例对读名单（两句皆脚本截取，命不中即不入；铜驼语料零出现，不入）
PAIR_NAMES = ["永宁寺", "白马寺", "瑶光寺", "阊阖门", "建春门", "宣阳门",
              "金墉城", "翟泉", "太仓", "华林园"]


def load_const(path, const):
    t = io.open(os.path.join(ROOT, path), encoding="utf-8").read()
    head = f"const {const} = "
    i = t.find(head)
    assert i >= 0, f"{path} 缺 const {const}"
    return json.loads(t[i + len(head):].rstrip().rstrip(";"))


def sentences(text):
    """以句读切句（。；为界），保留较完整语境。"""
    return [s for s in re.split(r"[。；]", text) if len(s.strip()) >= 6]


def first_sent(text, name):
    for m in re.finditer(re.escape(name), text):
        s = text[max(0, m.start() - 60):m.start() + 90]
        return s.replace("\n", "")
    return ""


def main():
    if not os.path.isdir(SDJW):
        raise SystemExit("未找到姊妹站 D:/W_A_W/SDJW（互查桥需要其数据，只读）")
    riv = json.load(io.open(os.path.join(SDJW, "data", "intermediate", "rivers.json"),
                            encoding="utf-8"))
    # 同名跨卷分节取首节 id（承 HHH 消歧惯例：合并主键深链 #r=<首节id>）
    id_by_name = {}
    for r in riv["rivers"]:
        id_by_name.setdefault(r["name"], r["id"])
    by_id = {r["id"]: r for r in riv["rivers"]}

    # 伽蓝记语料（data/vol 纯正文口径）
    corpus = "".join(io.open(os.path.join(ROOT, "data", "vol", f"{v:03d}.txt"),
                             encoding="utf-8").read() for v in range(6))
    # 洛阳相关水道及其全注文（blocks）——按 SDJW 水道去重（阳渠行于谷水注内，不另立文本）
    water_texts = {}
    for disp, _, _ in WATERS:
        link = "谷水" if disp == "阳渠" else disp
        wid = id_by_name.get(link)
        if wid and link not in water_texts:
            water_texts[link] = "".join(b["text"] for b in by_id[wid].get("blocks", []))

    # ── A 侧：本书提及水道 ──
    waters_out = []
    for disp, forms, note in WATERS:
        n = sum(corpus.count(f) for f in forms)
        link_name = "谷水" if disp == "阳渠" else disp
        wid = id_by_name.get(link_name)
        samples = []
        for f in forms:
            for m in re.finditer(re.escape(f), corpus):
                if len(samples) < 3:
                    samples.append(corpus[max(0, m.start() - 45):m.start() + 60]
                                   .replace("\n", ""))
        waters_out.append({
            "name": disp, "forms": forms, "n": n, "note": note or "",
            "sjzId": wid or "", "href": f"{SITE}#r={wid}" if wid else SITE,
            "samples": samples,
        })
    excluded_out = [{"name": nm, "n": corpus.count(nm), "why": why}
                    for nm, why in EXCLUDED]

    # ── B 侧：谷水注/洛水注中的伽蓝记名物 ──
    qlz = load_const("data/site_data.js", "QLZ")
    raw_items = []
    raw_items += [{"name": g["name"].replace("宫阊阖门", "阊阖门"),
                   "disp": g["disp"], "kind": "城门", "att": g["att"]}
                  for g in qlz["gates"]]
    raw_items += [{"name": t["name"], "disp": t["name"], "kind": "伽蓝", "att": t["loc"]}
                  for t in qlz["temples"]]
    raw_items += [{"name": w["name"], "disp": w["name"], "kind": "里坊·市", "att": w["att"]}
                  for w in qlz["wards"]]
    raw_items += [{"name": o["name"], "disp": o["name"], "kind": "衙署·宫室", "att": o["att"]}
                  for o in qlz["offices"]]
    raw_items += [{"name": k["name"], "disp": k["name"], "kind": "地标", "att": k["att"]}
                  for k in qlz["landmarks"]]
    for nm in EXTRA_LANDMARKS:
        if nm in corpus:
            raw_items.append({"name": nm, "disp": nm, "kind": "地标", "att": ""})

    # 同名合并（一名二实如实注记；计数以名物名计，不重复）
    items = {}
    for it in raw_items:
        e = items.setdefault(it["name"], {"name": it["name"], "kinds": set(),
                                          "att": it["att"], "nEntries": 0})
        e["kinds"].add(it["kind"])
        e["nEntries"] += 1

    places, no_hit = [], []
    for nm, e in items.items():
        forms = [nm] + ALIASES.get(nm, [])
        hits = {}
        for wdisp, wtxt in water_texts.items():
            c = sum(wtxt.count(f) for f in forms)
            if c:
                hits[wdisp] = c
        kind = "/".join(sorted(e["kinds"]))
        if not hits:
            no_hit.append({"name": nm, "kind": kind})
            continue
        wtop = max(hits, key=lambda k: hits[k])
        sample = next((s for s in (first_sent(water_texts[wtop], f)
                                   for f in forms) if s), "")
        places.append({"name": nm, "disp": nm, "kind": kind,
                       "water": wtop, "waterId": id_by_name.get(wtop, ""),
                       "n": sum(hits.values()), "perWater": hits,
                       "sample": sample[:170], "att": e["att"],
                       "note": NAME_NOTES.get(nm, ""),
                       "nEntries": e["nEntries"]})
    places.sort(key=lambda p: (-p["n"], p["kind"], p["name"]))

    # ── 样例对读（伽蓝记句 × 谷水注句）──
    pairs = []
    for nm in PAIR_NAMES:
        cand = next((p for p in places
                     if p["name"] == nm or nm in ALIASES.get(p["name"], [])), None)
        if not cand:
            continue
        wdisp = cand["water"]
        wtxt = water_texts[wdisp]
        sjz_sent = ""
        for s in sentences(wtxt):
            if nm in s:
                sjz_sent = s.strip()
                break
        ql_sent = ""
        for s in sentences(corpus):
            if nm in s:
                s = re.sub(r"◎[\u4e00-\u9fff]{1,6}", "", s)   # 剥卷部标题残留
                ql_sent = s.strip()
                break
        if sjz_sent and ql_sent:
            pairs.append({"name": nm, "kind": cand["kind"], "water": wdisp,
                          "ql": ql_sent[:150], "sjz": sjz_sent[:150],
                          "href": f"{SITE}#r={cand['waterId']}"})

    by_kind = {}
    for p in places:
        by_kind[p["kind"]] = by_kind.get(p["kind"], 0) + 1
    nohit_by_kind = {}
    for p in no_hit:
        nohit_by_kind[p["kind"]] = nohit_by_kind.get(p["kind"], 0) + 1

    out = {
        "site": SITE,
        "generated": "tools/build_xref_sjz.py（SDJW 只读）",
        "note": "谷水注（水经注·卷十六）正是郦道元写洛阳城的段落——两书同城异代："
                "郦注北魏全盛（527 前），杨记武定重游（547）。深链为相对兄弟路径，"
                "须父目录同根服务（README 注明）。",
        "waters": waters_out,
        "excluded": excluded_out,
        "places": places,
        "noHit": no_hit,
        "pairs": pairs,
        "totals": {
            "waterKinds": len(waters_out),
            "waterMentions": sum(w["n"] for w in waters_out),
            "waterTextChars": {k: len(v) for k, v in water_texts.items()},
            "placeKinds": by_kind,
            "placesHit": len(places),
            "placesNoHit": len(no_hit),
            "noHitByKind": nohit_by_kind,
            "pairs": len(pairs),
        },
    }
    path = os.path.join(ROOT, "data", "xref_sjz.js")
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("/* 伽蓝经纬 · 引水经注互查数据 · tools/build_xref_sjz.py 生成，勿手改 */\n")
        f.write("window.QL_SJZ = " + json.dumps(out, ensure_ascii=False,
                                               separators=(",", ":")) + ";\n")

    t = out["totals"]
    print(f"✓ data/xref_sjz.js")
    print(f"  A 本书→水经：{t['waterKinds']} 水道 {t['waterMentions']} 次 · "
          f"排除 {len(excluded_out)} 名（{ '、'.join(e['name'] for e in excluded_out) }）")
    print(f"  B 水经→本书：命中 {t['placesHit']} 名物 / 无对应 {t['placesNoHit']} · "
          f"按类 {by_kind} · 对读样例 {t['pairs']} 对")
    print(f"  注文规模：{' · '.join(f'{k} {len(v):,} 字' for k, v in water_texts.items())}")
    print(f"  无对应（城门）：{'、'.join(n['name'] for n in no_hit if n['kind'] == '城门') or '无'}")


if __name__ == "__main__":
    main()
