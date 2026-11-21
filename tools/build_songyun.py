# -*- coding: utf-8 -*-
"""伽蓝经纬 · 宋云西行结构化（卷五行纪 5,651 字 → 20 站点名物）
输出: data/songyun.js —— window.QL_SONGYUN（js/map.js「西行」小比例尺示意场景用）
纪律：
  · 站名全部在行纪原文中验真（find 不到即报错退出，不硬凑）
  · 每站书证 = 行纪中含站名的首句（脚本截取）；今日地与坐标为整编考订（推）
  · 里程/历时凡可解析者出自脚本（「西行N里」句式），不可解析如实空缺
  · 全部坐标 src:"derived" conf:"infer"——丝路古道今地考订，量级示意
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (站名, 今地考订, lat, lng, 类别)——类：发/程/国/城/河/终
STOPS = [
    ("京师", "北魏洛阳城（今洛阳汉魏故城）", 34.731, 112.611, "发"),
    ("赤岭", "今青海日月山（唐蕃古道界山）", 36.383, 101.303, "程"),
    ("流沙", "柴达木荒漠带（赤岭—土谷浑间八百里流沙）", 36.9, 98.9, "程"),
    ("土谷浑", "吐谷浑国境·柴达木南道（今青海都兰一带）", 36.18, 98.43, "国"),
    ("鄯善", "古鄯善国都（今新疆若羌）", 38.868, 88.168, "城"),
    ("左末", "且末（今新疆且末县）", 38.136, 85.536, "城"),
    ("末城", "尼雅一带（今民丰县境，推）", 37.06, 82.75, "城"),
    ("捍麽", "于阗东八百七十八里（约387km，今和田东，推）", 37.05, 82.90, "城"),
    ("于阗", "于阗国（今新疆和田）", 37.112, 79.920, "国"),
    ("朱驹波", "子合（今叶城一带，推）", 37.88, 77.42, "国"),
    ("汉盘陀", "蒲犁国（今塔什库尔干石头城）", 37.772, 75.229, "国"),
    ("葱岭", "帕米尔高原（钵盂城—不可依山段）", 37.50, 74.50, "程"),
    ("钵和", "瓦罕谷地（今阿富汗瓦罕，推）", 37.05, 71.55, "国"),
    ("哒", "嚈哒国·吐火罗斯坦（今阿富汗巴尔赫一带）", 36.75, 66.90, "国"),
    ("波斯", "嚈哒—赊弥间政体（锡斯坦/法拉一带，推·存疑）", 33.50, 62.10, "国"),
    ("赊弥", "今奇特拉尔一带（巴基斯坦，推）", 35.85, 71.79, "国"),
    ("乌场", "乌苋国（今巴基斯坦斯瓦特 Swat）", 34.95, 72.36, "国"),
    ("辛头大河", "印度河（乾陀罗境渡口，推）", 34.05, 72.25, "河"),
    ("佛沙伏", "布色羯逻伐底（今恰尔萨达 Charsadda）", 34.145, 71.730, "城"),
    ("乾陀罗城", "犍陀罗都城（今白沙瓦 Peshawar）", 34.014, 71.545, "终"),
]
# 文中站名的匹配写法（哒=〈口歇〉哒）
FORMS = {"哒": ["哒"], "乾陀罗城": ["乾陀罗城"],
         "京师": ["京师"], "捍麽": ["捍麽"]}


def songyun_text():
    e = json.load(io.open(os.path.join(ROOT, "data", "intermediate", "entries.json"),
                          encoding="utf-8"))
    b = next(x for x in e["blocks"] if x["kind"] == "songyun")
    return b["id"], "\n".join(b["paras"]), b["chars"]


def main():
    bid, text, chars = songyun_text()
    # 全部写法（长名优先）——供「长名遮蔽」消歧：短名落在他站长名内者跳过
    all_forms = []
    for name, _, _, _, _ in STOPS:
        for f in FORMS.get(name, [name]):
            all_forms.append(f)
    stops = []
    for name, today, lat, lng, cat in STOPS:
        forms = FORMS.get(name, [name])
        idx = -1
        for f in forms:
            occ = []
            pos = text.find(f)
            while pos >= 0:
                # 遮蔽：该命中若是另一更长写法的尾部（如「末城」⊂「左末城」）则跳过
                covered = False
                for g in all_forms:
                    if g != f and len(g) > len(f) and g.endswith(f):
                        j = pos - (len(g) - len(f))
                        if j >= 0 and text[j:j + len(g)] == g:
                            covered = True
                            break
                if not covered:
                    occ.append(pos)
                pos = text.find(f, pos + 1)
            if occ:
                # 「入/至X」为其条目首现者优先（防落在他国朝贡句）
                entry = next((p for p in occ if p > 0 and text[max(0, p - 2):p] and
                              text[max(0, p - 2):p][-1] in "入至於"), None)
                idx = entry if entry is not None else occ[0]
                break
        if idx < 0:
            raise SystemExit(f"站名「{name}」在行纪原文中未命中——考订表有误，须修正")
        # 书证：含站名首句（。；切）
        seg = text[:idx]
        last = max(seg.rfind("。"), seg.rfind("；"))
        nxt = min([x for x in (text.find("。", idx), text.find("；", idx)) if x > 0])
        cite = text[last + 1:nxt].strip().replace("\n", "")[:90]
        # 里程：该句「(西|西南|西北)?行N里」或「N里」
        li = ""
        mli = re.search(r"([一二三四五六七八九十百千馀]+)里", cite)
        if mli:
            li = mli.group(0)
        stops.append({"name": name, "today": today, "cat": cat,
                      "wgs": [round(lat, 3), round(lng, 3)],
                      "cite": cite, "li": li,
                      "src": "derived", "conf": "infer"})

    out = {
        "meta": {
            "blockId": bid, "chars": chars,
            "stops": len(stops),
            "years": "神龟元年（518）冬发京师 — 正光二年（521）二月还",
            "note": "宋云、惠生使西域行纪（卷五附出）。站序依原文行进次序；"
                    "今地考订与坐标为量级示意（conf:infer, src:derived），"
                    "波斯一站地望存疑如实注记。里程凡原文可解析者记之（「N里」），余空缺。",
        },
        "stops": stops,
    }
    path = os.path.join(ROOT, "data", "songyun.js")
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("/* 伽蓝经纬 · 宋云西行结构化 · tools/build_songyun.py 生成，勿手改 */\n")
        f.write("window.QL_SONGYUN = " + json.dumps(out, ensure_ascii=False,
                                                   separators=(",", ":")) + ";\n")
    nli = sum(1 for s in stops if s["li"])
    print(f"✓ data/songyun.js：{len(stops)} 站 · 书证全量验真 · 明载里程 {nli} 段 · "
          f"行纪 {chars:,} 字（block {bid}）")
    print("  里程段：", "、".join(f"{s['name']}{s['li']}" for s in stops if s["li"]))


if __name__ == "__main__":
    main()
