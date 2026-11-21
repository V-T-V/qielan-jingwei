# -*- coding: utf-8 -*-
"""伽蓝经纬 · 论文插图生成：python tools/build_paper_figs.py

数据源（口径纪律）：docs/stats.json（tools/stats.py 产物）——凡数字出自脚本。
输出：docs/figs/fig1_vols.png · fig2_gates.png（200dpi 绢面朱砂，学 HHH docs/build_paper_figs.py）
build_paper_pdf.py 于插图缺失时自动调用本脚本（管线可重入）。
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "figs")
os.makedirs(OUT, exist_ok=True)

STATS = json.load(open(os.path.join(ROOT, "docs", "stats.json"), encoding="utf-8"))

# ── 绢面朱砂版式（沿站点 CSS 与 PDF 配色） ──
SILK, INK, MUTED = "#f1ecda", "#2a2620", "#8d8474"
CINNABAR, GRIDC = "#7e2b1f", "#ddd3b8"
plt.rcParams.update({
    "font.family": "Microsoft YaHei", "axes.unicode_minus": False,
    "figure.facecolor": SILK, "axes.facecolor": SILK,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "text.color": INK,
})
KAI = FontProperties(fname=r"C:\Windows\Fonts\simkai.ttf", size=14)


def frame(ax, axis="x"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis=axis, color=GRIDC, lw=.7, alpha=.8)
    ax.set_axisbelow(True)


# ══ 图 1　卷帙篇幅：城东独厚 · 城南最薄 ══
VOL_LABELS = {"0": "原序", "1": "卷一·城内", "2": "卷二·城东", "3": "卷三·城南", "4": "卷四·城西", "5": "卷五·城北"}
vc = STATS["vol_chars"]                     # stats.json:vol_chars
fig, ax = plt.subplots(figsize=(7.2, 3.9), dpi=200)
frame(ax, "y")
xs = [VOL_LABELS[v] for v in ("0", "1", "2", "3", "4", "5")]
ys = [vc[v] for v in ("0", "1", "2", "3", "4", "5")]
cols = [CINNABAR if v == "2" else MUTED for v in ("0", "1", "2", "3", "4", "5")]
ax.bar(xs, ys, color=cols, width=.58, edgecolor=SILK, lw=.5)
for i, v in enumerate(ys):
    ax.text(i, v + 90, f"{v:,}", ha="center", fontsize=8.5, color=INK)
ax.set_ylabel("字数", fontsize=9.5)
ax.set_ylim(0, max(ys) * 1.15)
ax.set_title("卷帙篇幅：城东独厚（8,290 字）· 城南最薄（5,485 字）", fontproperties=KAI, pad=12)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_vols.png"))
plt.close(fig)

# ══ 图 2　城门提及频次：阊阖与建春双锚 ══
gm = sorted(STATS["gate_mentions"].items(), key=lambda kv: -kv[1])   # stats.json:gate_mentions
HILITE = {"阊阖门", "建春门"}
fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=200)
frame(ax)
names = [k for k, _ in gm][::-1]
vals = [v for _, v in gm][::-1]
cols = [CINNABAR if n in HILITE else MUTED for n in names]
ax.barh(names, vals, color=cols, height=.64, edgecolor=SILK, lw=.5)
for i, v in enumerate(vals):
    ax.text(v + .12, i, str(v), va="center", fontsize=8.5, color=INK)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=9)
ax.set_xlabel("全书提及次数", fontsize=9.5)
ax.set_xlim(0, max(vals) * 1.12)
ax.set_title("十三门（本站分列十四名）提及频次——阊阖与建春双锚", fontproperties=KAI, pad=12)
ax.legend(handles=[Patch(fc=CINNABAR, label="阊阖门（仪礼轴线起点）· 建春门（城东伽蓝带锚点）"),
                   Patch(fc=MUTED, label="其余诸门")],
          loc="lower right", fontsize=8.5, frameon=False)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_gates.png"))
plt.close(fig)

print("OK →", OUT, sorted(os.listdir(OUT)))
