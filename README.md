# 伽蓝经纬 · Qielan Jingwei

[![CI](https://github.com/V-T-V/qielan-jingwei/actions/workflows/ci.yml/badge.svg)](https://github.com/V-T-V/qielan-jingwei/actions/workflows/ci.yml)

北魏·杨衒之《洛阳伽蓝记》五卷数字人文平台——方舆经纬（[D:\W_A_W\HHH](../HHH)·点织明末版图）、
水道经纬（[D:\W_A_W\SDJW](../SDJW)·线溯北魏江河）的姊妹项目。
同一套方法论，第三种空间诗学：**以点（伽蓝）织一座城**——北魏洛阳，一城之内见一代之盛衰。

```
伽蓝经纬/
  index.html              # 入口（舆图 / 巡城 / 名录 / 计量 / 西行 / 关于）
  data/site_data.js       # 城市骨架 + 43 伽蓝 + 13 墙门 2 宫门 + 24 里坊市 + 12 衙署（管线生成）
  data/sections.js        # 巡城阅读块（53 块：伽蓝条目 + 里坊叙事 + 宋云行纪 + 京师总述）
  data/stats.js           # 计量（docs/stats.json 转抄——前端只读脚本产物）
  data/xref_sjz.js        # 水经互查桥（build_xref_sjz.py 生成，计量·引水经注页签懒加载）
  data/songyun.js         # 宋云西行 20 站结构化（build_songyun.py 生成）
  data/text/v0..v5.js     # 全文检索层（懒加载；序+五卷纯正文）
  exports/                # 城图导出产物（CSV×4·BOM / KML / GeoJSON，export_data.py 可复算）
  tools/                  # 管线：fetch_text → parse_entries → stats → build_xref_sjz
                          #        → build_songyun → build_data → build_paper_pdf → export_data → lint
  tests/                  # 断言页（数据 22 项 · 巡城 12 项 · P2 20 项）+ run_tests.py
  docs/ANALYSIS.md        # 文本计量（凡数字必出自脚本）
  docs/伽蓝经纬-数字人文.pdf  # 研究论文（build_paper_pdf.py 排印，数字全出自脚本产物）
```

## 快速开始

```bash
python -m http.server 9500 &      # 起本地服务（互查桥深链需父目录同根服务，见下）
python tools/fetch_text.py        # Phase 0 抓取（断点续抓，已缓存 raw 则重洗）
python tools/parse_entries.py     # Phase 1 条目切分（典校篇目表逐一前缀校验）
python tools/stats.py             # 计量 → docs/stats.json + ANALYSIS.md
python tools/build_xref_sjz.py    # 水经互查桥（读姊妹站 SDJW，只读不写）
python tools/build_songyun.py     # 宋云西行 20 站（站名在行纪原文逐一验真）
python tools/build_data.py        # 城市骨架 + 坐标 + WGS84 锚点 + 前端产物
python tools/build_paper_pdf.py   # 论文 PDF（ANALYSIS 改动后必重排，lint 哨兵联动）
python tools/export_data.py       # exports/ 四表 CSV·KML·GeoJSON（与前端按钮同口径）
python tools/lint.py              # 452 项确定性检查
python run_tests.py               # lint + 数据断言 + 断言页清单
```

## 核心体验

| # | 功能 | 入口 |
|---|---|---|
| 1 | **舆图**——自绘北魏洛阳示意平面（L.CRS.Simple）：城墙/宫城/金墉/河渠/邙山/外郭，43 伽蓝分卷五色点织（径=条目字数），13 墙门+2 宫门符号，里坊/衙署/桥市 | 默认 · `#m=map` |
| 2 | **按卷巡城**——右幅按卷滚读原文，滚到某伽蓝条目地图飞行高亮该点；宋云行纪/京师总述独立成块 | 「巡城」· `#m=read#juan=2` |
| 3 | **深链**——`#gl=永宁寺`（详情）`#juan=N`（卷）`#gate=建春门`（城门），刷新可复原 | 任意点击写回 |
| 4 | **伽蓝详情**——位置原文句 + 示意坐标（src:derived）+ 依据 + 原文全文 + 名气指数 | 点任一伽蓝 |
| 5 | **名录**——伽蓝/城门/里坊/衙署四表，皆带书证；**⤓ 导出** CSV(BOM)/KML/GeoJSON（示意坐标逐行注明 src:derived） | 「名录」 |
| 6 | **全文检索**——36KB 全书一次加载主线程扫描，命中定位巡城 | 顶栏 |
| 7 | **计量**——卷篇幅×条数、佛寺出场频次、城门提及（数字全出自 stats.py） | 「计量」 |
| 8 | **引水经注**——站际互查桥：本书提及水道（洛水/穀水/阳渠）↔ 谷水注/洛水注中的伽蓝记名物，双向计数 + 样例对读 + 「↗循水」深链姊妹站水道经纬 | 「计量」→「引水经注」 |
| 9 | **宋云西行**——卷五行纪 5,651 字结构化 20 站（赤岭—于阗—葱岭—乌场—乾陀罗），WGS84 小比例尺丝路示意（src:derived·infer）+ 站站书证 + 沿线巡读 | 底栏「◈ 西行」· `#m=west` |
| 10 | 书签（LocalStorage）· 夜读 · TTS 巡城听书 · PWA 两级缓存离线 · 漫游 | 底栏 |

## P2 契约（论文 · 导出 · 互查桥 · 西行）

- **论文 PDF**：`docs/伽蓝经纬-数字人文.pdf`（build_paper_pdf.py 排印）——数字运行时读自
  stats.json / site_data.js / xref_sjz.js，不手抄；**lint 哨兵联动**：ANALYSIS.md 新于 PDF 即红。
- **城图导出**：伽蓝 43 / 城门 15 / 里坊市 24 / 衙署宫室 12 四表——CSV（带 BOM）×4 +
  KML + GeoJSON（各 94 点）；**前端名录页按钮与 tools/export_data.py 同口径**（wgs 全出自
  build_data.py 管线锚点换算，单一事实源）；示意坐标在每一行/每个要素注明 `src:derived` 与依据；
  lint 校验行数与要素数一致。
- **水经互查桥**（伽蓝×水道经纬·谷水段）：`tools/build_xref_sjz.py` 读姊妹站
  `D:\W_A_W\SDJW` 的 rivers.json（**只读，绝不写入**），产 `data/xref_sjz.js`。
  A 侧本书提及水道 3 种 13 次（穀水≡谷水异体折算；决水/深水/若水/渠水四名假阳性如实排除）；
  B 侧谷水注 10,723 字/洛水注 6,433 字中命中伽蓝记名物 21 处（城门 12——津阳/承明无对应）、
  对读样例 10 对。**↗循水深链用相对兄弟路径 `../SDJW/#r=<水道id>`**——约定
  **父目录同根服务**：在 `D:\W_A_W` 起 `python -m http.server 8000` 后，
  `http://127.0.0.1:8000/LYGL/` 与 `/SDJW/` 同源可达（各站 9500/9300 独立服务下深链退化为站内提示）。
- **宋云西行**：`tools/build_songyun.py` 产 `data/songyun.js`——20 站站名在行纪原文逐一验真
  （命不中即报错退出），今地考订与坐标全量 `src:derived·conf:infer`（量级示意，非实测）；
  波斯一站地望存疑如实注记；底栏「◈ 西行」切换 WGS84 无瓦片示意场景，`#m=west` 深链。

## 数据边界（诚实口径）

- **文本**：国学导航本（GB18030 抓取转存）。**序+五卷共 35,999 字**——此为白文（无校注）口径；
  通行「约八万字」多为含范祥雍等校注之本，二者不可混同。本站语料或与四部丛刊影印底本存在排印差异，
  校勘不在范围。**维基文库本网络不可达（TLS 握手级阻断），依 SPEC 数据源次序（维基文库→国学导航）回退**，如实标注。
- **条目**：典校篇目表 43 条伽蓝（卷一至卷五 = 11/12/8/10/2，附出愿会/嵩明/景兴/追圣/王典御诸小条），
  解析器以段落前缀逐一命中校验，命不中即报错退出；宋云行纪（5,651 字）与京师总述独立成块。
- **城图**：示意城市平面（米制），内城 2,800×3,700m、1 里=440m，依汉魏洛阳故城考古常识布点；
  外郭范围依卷五「京师东西二十里，南北十五里」。**全部坐标 `src:"derived"`**。
- **城门 13**（序自载门谱：东3建春/东阳/青阳 · 南4开阳/平昌/宣阳/津阳 · 西4西明/西阳/阊阖/承明 ·
  北2大夏/广莫）+ 宫城门二（阊阖·宫前正门、千秋），每门附原文书证。
  阊阖门一名二实：西墙门（汉上西门，序）与宫城正门（卷一「宫前阊阖门」），本站分列。
- **伽蓝坐标**：40 条有原文方位句（conf:"text"——「某门(内/外)N里御道某侧」格式），3 条依卷部区位示意
  （conf:"infer"：宗圣寺/崇真寺/追光寺）；依据字段逐条可溯。

## 版本

`python tools/bump_version.py OLD NEW`——全站 `?v=` 一步到位（含 tests/），lint 校验一致性。

## 测试

`python run_tests.py` 全绿后，`tests/assert_data.html`（22 项）与 `tests/assert_reader.html`
（12 项，iframe 驱动主流程）于 9500 端口打开，title=PASS 即绿。截图证据：`docs/img/`。

学术引用：[CITATION.cff](CITATION.cff)（CFF 1.2.0 · dataset）——构建产物指纹账本另见 [SHA256SUMS](SHA256SUMS)，`python tools/build_sums.py` 重算、`run_tests.py` 对账。
