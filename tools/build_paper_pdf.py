# -*- coding: utf-8 -*-
"""伽蓝经纬 · 研究论文排印 → docs/伽蓝经纬-数字人文.pdf
   学 HHH docs/build_paper_pdf.py 模式（BaseDocTemplate + 楷体/雅黑 + 中表）。
   数字纪律：一切统计数字运行时读自 docs/stats.json · data/site_data.js(QLZ) ·
   data/xref_sjz.js(桥)——脚本产物，不手抄；lint 哨兵联动（ANALYSIS.md 新于 PDF 即红）。"""
import io
import json
import math
import os
import subprocess
import sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, Image, KeepTogether,
                                PageTemplate, Paragraph, Spacer, Table, TableStyle)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "伽蓝经纬-数字人文.pdf")

# 插图缺失时自动重建（管线可重入：stats.json → build_paper_figs.py，学 HHH）
FIGS_DIR = os.path.join(ROOT, "docs", "figs")
NEED_FIGS = ["fig1_vols.png", "fig2_gates.png"]
if not all(os.path.isfile(os.path.join(FIGS_DIR, f)) for f in NEED_FIGS):
    subprocess.run([sys.executable, "-I", os.path.join(ROOT, "tools", "build_paper_figs.py")],
                   check=True)

pdfmetrics.registerFont(TTFont("KaiTi", r"C:\Windows\Fonts\STKAITI.TTF"))
pdfmetrics.registerFont(TTFont("YaHei", r"C:\Windows\Fonts\msyh.ttc", subfontIndex=0))

# 配色承站点 CSS（绢面·朱砂·赭）
ACCENT = colors.HexColor('#7e2b1f')
TEXT_PRIMARY = colors.HexColor('#2a2620')
TEXT_MUTED = colors.HexColor('#8d8474')
BG_SURFACE = colors.HexColor('#e9e2c9')
BG_PAGE = colors.HexColor('#f1ecda')

W, H = A4
M = 20 * mm
AW = W - 2 * M

S = {
    "title": ParagraphStyle("t", fontName="KaiTi", fontSize=23, leading=33,
                            alignment=TA_CENTER, textColor=TEXT_PRIMARY, wordWrap="CJK"),
    "sub": ParagraphStyle("s", fontName="KaiTi", fontSize=12.5, leading=19,
                          alignment=TA_CENTER, textColor=TEXT_MUTED, wordWrap="CJK"),
    "h1": ParagraphStyle("h1", fontName="KaiTi", fontSize=15.5, leading=23,
                         textColor=ACCENT, spaceBefore=14, spaceAfter=6, wordWrap="CJK"),
    "h2": ParagraphStyle("h2", fontName="KaiTi", fontSize=12.5, leading=19,
                         textColor=TEXT_PRIMARY, spaceBefore=9, spaceAfter=4, wordWrap="CJK"),
    "body": ParagraphStyle("b", fontName="YaHei", fontSize=10.5, leading=17.5,
                           alignment=TA_JUSTIFY, textColor=TEXT_PRIMARY,
                           spaceAfter=5, wordWrap="CJK", firstLineIndent=21),
    "body0": ParagraphStyle("b0", fontName="YaHei", fontSize=10.5, leading=17.5,
                            alignment=TA_JUSTIFY, textColor=TEXT_PRIMARY,
                            spaceAfter=5, wordWrap="CJK"),
    "abs": ParagraphStyle("a", fontName="YaHei", fontSize=9.8, leading=16.5,
                          alignment=TA_JUSTIFY, textColor=TEXT_PRIMARY,
                          wordWrap="CJK", firstLineIndent=19.6),
    "cap": ParagraphStyle("c", fontName="KaiTi", fontSize=9.5, leading=14,
                          alignment=TA_CENTER, textColor=TEXT_MUTED,
                          spaceBefore=2, spaceAfter=8, wordWrap="CJK"),
    "th": ParagraphStyle("th", fontName="YaHei", fontSize=9.5, leading=13.5,
                         alignment=TA_CENTER, textColor=colors.white, wordWrap="CJK"),
    "td": ParagraphStyle("td", fontName="YaHei", fontSize=9.5, leading=13.5,
                         alignment=TA_CENTER, textColor=TEXT_PRIMARY, wordWrap="CJK"),
    "tdl": ParagraphStyle("tdl", fontName="YaHei", fontSize=9.5, leading=13.5,
                          alignment=TA_JUSTIFY, textColor=TEXT_PRIMARY, wordWrap="CJK"),
}


def P(t, st="body"):
    return Paragraph(t, S[st])


def tbl(headers, rows, widths, caption=None, left_cols=()):
    data = [[Paragraph(h, S["th"]) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), S["tdl"] if i in left_cols else S["td"])
                     for i, c in enumerate(r)])
    t = Table(data, colWidths=[w * AW for w in widths], hAlign="CENTER", repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BG_SURFACE]),
        ("GRID", (0, 0), (-1, -1), .4, colors.HexColor('#c9bfa5')),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    out = [t]
    if caption:
        out.append(Paragraph(caption, S["cap"]))
    return KeepTogether(out)


def fig(fname, h_mm, caption):
    img = Image(os.path.join(FIGS_DIR, fname), width=AW, height=h_mm * mm, hAlign="CENTER")
    return KeepTogether([Spacer(1, 2 * mm), img, Paragraph(caption, S["cap"])])


def footer(cv, doc):
    cv.saveState()
    cv.setFont("KaiTi", 8.5)
    cv.setFillColor(TEXT_MUTED)
    cv.drawCentredString(W / 2, 12 * mm, f"— {doc.page} —")
    cv.setFont("KaiTi", 7.5)
    cv.drawString(M, 12 * mm, "伽蓝经纬 · 数字人文研究")
    cv.drawRightString(W - M, 12 * mm, "docs/build_paper_pdf.py 可复核重排")
    cv.restoreState()


def load_const(path, const):
    t = io.open(os.path.join(ROOT, path), encoding="utf-8").read()
    head = f"const {const} = " if not path.endswith("xref_sjz.js") else f"window.{const} = "
    i = t.find(head)
    assert i >= 0, f"{path} 缺 {head.strip()}"
    return json.loads(t[i + len(head):].rstrip().rstrip(";"))


def main():
    stats = json.load(io.open(os.path.join(ROOT, "docs", "stats.json"), encoding="utf-8"))
    qlz = load_const("data/site_data.js", "QLZ")
    xref = load_const("data/xref_sjz.js", "QL_SJZ") if os.path.exists(
        os.path.join(ROOT, "data", "xref_sjz.js")) else None

    m = qlz["meta"]
    vc = stats["vol_chars"]
    tt = xref["totals"] if xref else {}
    pairs = xref["pairs"][:3] if xref else []
    gates_hit = [p for p in xref["places"] if p["kind"] == "城门"] if xref else []
    no_hit_gates = [n["name"] for n in xref["noHit"] if n["kind"] == "城门"] if xref else []
    wm = stats["words"]

    doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=M, rightMargin=M,
                          topMargin=18 * mm, bottomMargin=20 * mm,
                          title="《洛阳伽蓝记》的城市空间与文本计量研究",
                          author="伽蓝经纬项目组", subject="数字人文·北魏洛阳·城市史",
                          creator="伽蓝经纬")
    frame = Frame(M, 20 * mm, AW, H - 38 * mm, id="f")
    doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=footer)])

    E = []
    # ── 题页块 ──
    E += [Spacer(1, 10 * mm),
          Paragraph("《洛阳伽蓝记》的城市空间与文本计量研究", S["title"]),
          Spacer(1, 3 * mm),
          Paragraph("——基于四十三伽蓝点织的北魏洛阳数字人文平台", S["sub"]),
          Spacer(1, 8 * mm),
          Paragraph("伽蓝经纬项目组", S["sub"]),
          Paragraph("2026 年 11 月 · 全部数字由脚本可复核（stats.py / build_data.py / build_xref_sjz.py）", S["sub"]),
          Spacer(1, 5 * mm),
          HRFlowable(width="34%", thickness=.7, color=ACCENT, hAlign="CENTER"),
          Spacer(1, 5 * mm)]

    abs_txt = (
        f"<b>摘　要</b>　本文对北魏杨衒之《洛阳伽蓝记》五卷进行城市尺度数字化：以典校篇目表校验的 "
        f"{stats['temple_entries']} 条伽蓝条目（卷一至卷五 "
        f"{'/'.join(str(stats['temple_per_vol'][str(v)]) for v in range(1, 6))}）为点集，"
        f"以序载十三门谱为空间锚，构建「某门(内/外)N里御道某侧」句式的定位体系——"
        f"{m['textConf']} 条得原文明载方位（text），{m['inferConf']} 条依卷部区位示意（infer），"
        f"在自绘示意平面（内城 2,800×3,700m，1 里=440m）上点织北魏洛阳。语料为国学导航白文本，"
        f"序并五卷共 {stats['total_chars']:,} 字。主要发现：(1) 空间书写高度门锚化——"
        f"「御道」{wm['御道']} 次、城门提及 {len(stats['gate_mentions'])} 门，"
        f"永宁寺条 {stats['temple_chars_top'][0][2]:,} 字居全书之首；"
        f"(2) 卷部即城市象限——城东卷 {vc['2']:,} 字最厚而城南卷 {vc['3']:,} 字最薄，"
        f"叙事密度随城门外伽蓝带分布；(3) 与《水经注》谷水注互查：两书同城异代"
        f"（郦注成于 527 前、杨记成于 547），谷水注 {tt.get('waterTextChars', {}).get('谷水', 0):,} 字"
        f"注文与本书互文名物 {tt.get('placesHit', 0)} 处、对读样例 {tt.get('pairs', 0)} 对，"
        f"城门系统仅 {'、'.join(no_hit_gates) if no_hit_gates else '无'} 无对应——"
        f"北魏洛阳的双文献地理由此可并读。")
    abs_tbl = Table([[Paragraph(abs_txt, S["abs"])],
                     [P("<b>关键词</b>　洛阳伽蓝记；北魏洛阳；数字人文；城市空间结构；水经注；文本计量", "abs")]],
                    colWidths=[AW])
    abs_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BG_PAGE),
        ("LINEBELOW", (0, 0), (-1, 0), .4, colors.HexColor('#d5ccb2')),
        ("BOX", (0, 0), (-1, -1), .6, colors.HexColor('#c9bfa5')),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    E += [abs_tbl, Spacer(1, 6 * mm)]

    # ── 一、引言 ──
    E += [P("一、引言", "h1"),
          P("《洛阳伽蓝记》五卷，北魏杨衒之重览洛阳废寺后所撰（武定五年，547 年），"
            "是中国古代城市书写的高峰：以伽蓝为目，以城门御道为经纬，一城之内见一代之盛衰。"
            "本平台「伽蓝经纬」承方舆经纬（读史方舆纪要·点织版图）与水道经纬（水经注·线溯江河）"
            "的方法论，作第三种空间范式——以点织城：条目解析、门锚定位、示意成图、全文可检、"
            "站际互查。本文报告其材料、方法与主要发现；交互验证见配套站点（舆图/巡城/计量/引水经注）。")]

    # ── 二、材料与方法 ──
    E += [P("二、材料与方法", "h1"),
          P("2.1 语料与口径", "h2"),
          P(f"语料取国学导航本（GB18030 抓取转存）。维基文库本网络不可达（TLS 握手级阻断），"
            f"依数据源次序回退，如实标注。序并五卷白文共 {stats['total_chars']:,} 字"
            f"（序 {vc['0']:,} · 卷一 {vc['1']:,} · 卷二 {vc['2']:,} · 卷三 {vc['3']:,} · "
            f"卷四 {vc['4']:,} · 卷五 {vc['5']:,}）；通行「约八万字」多为含校注之本，与本站白文口径"
            f"不可混同。宋云行纪 {stats['songyun_chars']:,} 字独立成块（卷五附出）。"),
          P("2.2 条目解析：典校篇目表逐一校验", "h2"),
          P(f"以典校篇目表 {stats['temple_entries']} 条为纲，解析器对每卷段落以前缀逐一命中校验，"
            f"命不中即报错退出——条目不贪多，宁缺毋假。分卷 "
            f"{'/'.join(str(stats['temple_per_vol'][str(v)]) for v in range(1, 6))}"
            f"（卷一至卷五），另整编里坊/市 {m['wards']}、衙署/宫室 {m['offices']}、"
            f"墙门 {m['gatesWall']} 并宫门 {m['gatesPalace']}。"),
          P("2.3 门锚定位法与示意平面", "h2"),
          P(f"全书空间句式的骨架是「某门(内/外)N里御道某侧」——城门即坐标原点，御道即轴线。"
            f"据此对 {m['templeEntries']} 条伽蓝定位：{m['textConf']} 条有原文明载方位句（conf:text），"
            f"{m['inferConf']} 条依卷部区位示意（conf:infer，宗圣/崇真/追光）。示意平面取 "
            f"L.CRS.Simple 米制：内城 2,800×3,700m（汉魏洛阳故城考古常识量级），1 北魏里=440m；"
            f"外郭依卷五「京师东西二十里，南北十五里」。全部坐标 src:derived，依据字段逐条可溯。"),
          P("2.4 数字复核制度", "h2"),
          P("凡进入本文的数字均出自仓库脚本（tools/stats.py → docs/stats.json；build_data.py → "
            "site_data.js；build_xref_sjz.py → xref_sjz.js），前端只读转抄；改 ANALYSIS.md 必须重排"
            "本 PDF，lint 哨兵联动（ANALYSIS.md 新于 PDF 即红）。")]

    # ── 三、卷帙 ──
    rows = [[v == "0" and "原序" or f"卷{v}·{qlz['meta']['volNames'][int(v)-1]}",
             f"{vc[v]:,}", str(stats["temple_per_vol"].get(v, 0) or 0),
             str(stats["vol_blocks"][v])] for v in map(str, range(0, 6))]
    E += [P("三、卷帙：卷部即城市象限", "h1"),
          tbl(["卷", "字数", "伽蓝条", "阅读块"], rows, [.34, .26, .18, .22],
              "表 1　卷帙与条目分布（stats.py 产物）"),
          P("城东卷独厚（%s 字）：建春门—东阳门—青阳门外伽蓝与里坊交错，叙事最密；"
            "城南卷最薄（%s 字）而景明寺一寺独大。卷部不只是分目，更是城市象限——"
            "这为「按卷巡城」的阅读体验提供了数据根据。" % (f"{vc['2']:,}", f"{vc['3']:,}")),
          fig("fig1_vols.png", 92.1,
              f"图 1　卷帙篇幅——城东独厚（{vc['2']:,} 字）· 城南最薄（{vc['3']:,} 字）"
              f"（docs/stats.json: vol_chars）")]

    # ── 四、空间结构 ──
    gate_rows = [[g, str(n)] for g, n in
                 list(dict(list(stats["gate_mentions"].items())).items())[:8]]
    E += [P("四、空间结构：门锚与御道", "h1"),
          P(f"「御道」{wm['御道']} 次，为全书空间书写骨架词；「寺」{wm['寺']} 次、"
            f"「浮图」{wm['浮图']}、「塔」{wm['塔']}。城门提及 {len(stats['gate_mentions'])} 门，"
            f"阊阖门（宫城正门，仪礼轴线起点）与建春门（东面首门，城东伽蓝带锚点）最频。"),
          tbl(["门", "次", "门", "次"],
              [[gate_rows[i][0], gate_rows[i][1],
                gate_rows[i + 1][0] if i + 1 < len(gate_rows) else "",
                gate_rows[i + 1][1] if i + 1 < len(gate_rows) else ""]
               for i in range(0, len(gate_rows), 2)],
              [.28, .22, .28, .22], "表 2　城门提及（前八，stats.py）"),
          P(f"十三门谱系序文自载（东3建春/东阳/青阳 · 南4开阳/平昌/宣阳/津阳 · 西4西明/西阳/阊阖/承明 · "
            f"北2大夏/广莫），每门附原文书证；阊阖门一名二实（西墙汉上西门与宫城正门）本站分列。"
            f"里坊/市提及以建阳里、孝义里、永桥为最——城东里坊带与洛水永桥市是次级空间骨架。"),
          fig("fig2_gates.png", 118.1,
              "图 2　城门提及频次（十四名全谱）——阊阖门（仪礼轴线起点）与建春门（城东伽蓝带锚点）双锚"
              "（docs/stats.json: gate_mentions）")]

    # ── 五、文本计量 ──
    E += [P("五、文本计量", "h1"),
          P("5.1 条目篇幅", "h2"),
          tbl(["伽蓝", "卷", "字数"],
              [[n, f"卷{v}", f"{c:,}"] for n, v, c in stats["temple_chars_top"][:10]],
              [.46, .20, .34], "表 3　伽蓝条目篇幅 Top 10（parse_entries.py）"),
          P(f"永宁寺条 {stats['temple_chars_top'][0][2]:,} 字居全书之首——塔刹、装修、法事、火灾四段铺陈，"
            f"是杨衒之的「序曲式」书写。名气指数（核心名全书出场）以 "
            f"{stats['temple_mentions'][0][0]}（{stats['temple_mentions'][0][1]} 次）居首。"),
          P("5.2 词汇层", "h2"),
          P(f"寺 {wm['寺']} · 尼寺 {wm['尼寺']} · 浮图 {wm['浮图']} · 塔 {wm['塔']} · "
            f"御道 {wm['御道']} · 洛水 {wm['洛水']} · 穀水 {wm['穀水']} · 阳渠 {wm['阳渠']} · "
            f"洛阳 {wm['洛阳']} · 永宁 {wm['永宁']}——水文词（洛水/穀水/阳渠）与仪礼词（御道）"
            f"构成城市书写的经纬。")]

    # ── 六、宋云行纪 ──
    E += [P("六、宋云行纪：从城到路", "h1"),
          P(f"卷五附宋云、惠生使西域行纪 {stats['songyun_chars']:,} 字，神龟元年（518）冬发京师、"
            f"正光二年（521）还——洛阳的书写由城内伸向丝路：赤岭—流沙—鄯善—左末—捍麽—于阗—"
            f"朱驹波—汉盘陀（葱岭）—钵和—嚈哒—波斯—赊弥—乌场—乾陀罗。城的空间范式（门锚御道）"
            f"在行纪中转为里程范式（「从X西行N里至Y」），两种范式同卷并置，是全书空间书写"
            f"的自觉实验。")]

    # ── 七、站际互查：谷水注 ──
    if xref:
        pair_rows = [[p["name"], p["ql"][:38] + "…", p["sjz"][:38] + "…"] for p in pairs]
        E += [P("七、站际互查：与《水经注》谷水注并读", "h1"),
              P(f"《水经注》卷十六谷水注正是郦道元写洛阳城的段落（注文 "
                f"{tt['waterTextChars']['谷水']:,} 字，取姊妹站水道经纬快照）。两书同城异代："
                f"郦注成于北魏全盛（527 年前），杨记成于武定重游（547 年）——盛衰两帧。"
                f"互查桥（tools/build_xref_sjz.py，SDJW 只读）双向计数：本书提及水道 "
                f"{tt['waterKinds']} 种 {tt['waterMentions']} 次（洛水 "
                f"{xref['waters'][0]['n']} · 穀水/谷水 {xref['waters'][1]['n']} · 阳渠 "
                f"{xref['waters'][2]['n']}；排除决水/深水/若水/渠水假阳性四名）；"
                f"谷水注/洛水注中出现本书名物 {tt['placesHit']} 处"
                f"（城门 {tt['placeKinds'].get('城门', 0)} · 伽蓝 {tt['placeKinds'].get('伽蓝', 0)} · "
                f"衙署·宫室 {tt['placeKinds'].get('衙署·宫室', 0)} · 地标 {tt['placeKinds'].get('地标', 0)}），"
                f"城门仅 {'、'.join(no_hit_gates)} 无对应——郦杨两家的城门系统高度可并读。"),
              tbl(["名物", "《洛阳伽蓝记》", "《水经注》谷水注"], pair_rows,
                  [.16, .42, .42], "表 4　样例对读（脚本截取，全文见站内「引水经注」页签）",
                  left_cols=(1, 2))]

    # ── 八、局限 ──
    E += [P("八、方法局限", "h1"),
          P("(1) 示意坐标非考古实测——依原文明载方位句与汉魏洛阳故城考古常识量级布点，"
            "导出文件（CSV/KML/GeoJSON）逐行注明 src:derived 与依据；(2) 语料为国学导航白文本，"
            "与四部丛刊影印底本或存在排印差异，校勘不在范围；「八万字」之说是含注本口径；"
            "(3) 水经互查以字面匹配为界，穀/谷异体已折算、决水/深水/若水/渠水假阳性已排除，"
            "但非同名异实与异写仍可能漏计——无对应者如实计无对应，不强配。")]

    E += [P("参考文献", "h1"),
          P("［1］杨衒之．洛阳伽蓝记［M］．周祖谟，校释．北京：中华书局，2010（校释本供参酌，"
            "站用白文另据国学导航本）．", "body0"),
          P("［2］范祥雍．洛阳伽蓝记校注［M］．上海：上海古籍出版社，1978．", "body0"),
          P("［3］郦道元．水经注［M］．陈桥驿，点校．北京：中华书局，2007．（互查对端：水道经纬站）", "body0"),
          P("［4］中国社会科学院考古研究所．汉魏洛阳故城——1962—1992 年考古发掘报告［R］．北京：文物出版社，2009．"
            "（示意坐标量级依据）", "body0"),
          Spacer(1, 4 * mm),
          HRFlowable(width="100%", thickness=.5, color=BG_SURFACE),
          Paragraph("本文一切数字可由仓库脚本复现；交互验证：站点「舆图」「巡城」「计量·引水经注」。"
                    "导出：名录页 ⤓ CSV/KML/GeoJSON 或 tools/export_data.py。", S["cap"])]

    doc.build(E)
    print("OK →", OUT, os.path.getsize(OUT) // 1024, "KB")


if __name__ == "__main__":
    main()
