"""伽蓝经纬 · Phase 0 文本抓取
数据源: http://www.guoxue123.com/shibu/0301/00lyjlj/  (国学导航 · 洛阳伽蓝记 魏杨衒之撰)
        —— 首选维基文库 zh.wikisource.org，但本网络不可达（连接重置），
           依 SPEC-NEW-SITES.md 数据源次序回退国学导航；两本均为通行整理本。
输出:   data_raw/NNN.html  原始页面（GB18030→UTF-8 转存，供复查）
        data/vol/NNN.txt   每卷纯净 UTF-8 文本（条目以 \n 分隔，◎ 为分节标记）
        data/fetch_report.json  字数/段落数盘点
用法:   python tools/fetch_text.py          # 断点续抓（已存在且非空则跳过）
        python tools/fetch_text.py --force # 全部重抓
纪律:   UA 自报家门 · 每页 ≥1s 限速 · 原始页留档
"""
import json
import os
import re
import sys
import time

import requests

# 本机 Windows 注册表残留死代理(127.0.0.1:58319 拒连)——直连可用，绕过系统代理。
SESSION = requests.Session()
SESSION.trust_env = False

BASE = "http://www.guoxue123.com/shibu/0301/00lyjlj"
HEADERS = {
    # UA 自报家门（HTTP 头仅 ASCII：LuoyangQielanji = 洛阳伽蓝记数字人文站建站抓取）
    "User-Agent": "JingweiDigitalHumanities/0.1 (LuoyangQielanji-DH-site build; "
                  "academic use; resumable fetch; one-shot batch)",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data_raw")
VOL_DIR = os.path.join(ROOT, "data", "vol")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(VOL_DIR, exist_ok=True)

# 000=原序 001..005=卷一..卷五
PAGES = {
    "000": "序",
    "001": "卷一·城内",
    "002": "卷二·城东",
    "003": "卷三·城南",
    "004": "卷四·城西",
    "005": "卷五·城北",
}

NOISE_EXACT = {
    "上一页", "目录页", "下一页", "首页", "国学导航", "经部", "史部", "子部", "集部",
    "专题", "今人新著", "", "www.guoxue123.com", "洛阳伽蓝记",
}
NOISE_RE = re.compile(
    r"^(卷[一二三四五]_?|洛阳伽蓝记（魏）杨衒之撰|国学导航|◎?\s*$|&copy;|《洛阳伽蓝记》|Powered by)"
)


def clean_html(html: str) -> str:
    """剥 HTML：留正文行。<BR> 断段；段首全角空格去除；◎ 分节标记保留。"""
    body = html
    # 只取正文 <p> 区（跳过导航 table）；正文在「卷X」标题行之后
    m = re.search(r"<span class=\"s3\">(卷[一二三四五]|序)</span>(.*?)(?:<p>\s*<a href=\"000\.htm\"|</body>)",
                  html, re.S)
    if m:
        body = m.group(2)
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", body, flags=re.S)
    body = re.sub(r"<img[^>]*>", "", body)          # 原书扫描图不入语料
    body = re.sub(r"<br\s*/?>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", "\n", body)
    lines = []
    for ln in body.split("\n"):
        ln = ln.replace("\u3000", "").replace("\xa0", "").replace("&nbsp;", "").strip()
        ln = re.sub(r"^◎\s*", "◎", ln)
        if ln in NOISE_EXACT or NOISE_RE.match(ln):
            continue
        if re.fullmatch(r"卷[一二三四五]", ln):
            continue
        if ln:
            lines.append(ln)
    return "\n".join(lines)


def fetch_one(num: str, force: bool) -> dict:
    txt_path = os.path.join(VOL_DIR, f"{num}.txt")
    raw_path = os.path.join(RAW_DIR, f"{num}.html")
    if not force and os.path.exists(txt_path) and os.path.getsize(txt_path) > 200:
        with open(txt_path, encoding="utf-8") as f:
            body = f.read()
        return {"num": num, "title": PAGES[num], "chars": len(body.replace("\n", "")),
                "paras": body.count("\n") + 1, "cached": True}
    url = f"{BASE}/{num}.htm"
    if os.path.exists(raw_path) and os.path.getsize(raw_path) > 2000:
        # 原始页已留档：直接重洗，不再打网
        with open(raw_path, encoding="utf-8") as f:
            html = f.read()
    else:
        for attempt in range(3):
            try:
                resp = SESSION.get(url, headers=HEADERS, timeout=30)
                resp.raise_for_status()
                break
            except Exception as e:
                if attempt == 2:
                    raise
                print(f"  重试 {num}: {e}")
                time.sleep(3 * (attempt + 1))
        resp.encoding = "gb18030"
        if "找不到文件" in resp.text or "404" in resp.text[:400]:
            raise RuntimeError(f"{url} 404")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(resp.text)      # 原始页面（转码后）留档供复查
        html = resp.text
    body = clean_html(html)
    if len(body) < 300:
        raise RuntimeError(f"{num}.htm 清洗后仅 {len(body)} 字，疑似版式变化，请人工检查 {raw_path}")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(body)
    return {"num": num, "title": PAGES[num], "chars": len(body.replace("\n", "")),
            "paras": body.count("\n") + 1, "cached": False}


def main():
    force = "--force" in sys.argv
    report = []
    for num in sorted(PAGES):
        info = fetch_one(num, force)
        tag = "缓存" if info["cached"] else "抓取"
        print(f"[{tag}] {num} {info['title']}  {info['chars']:>6} 字  {info['paras']:>3} 段")
        report.append(info)
        if not info["cached"]:
            time.sleep(1.2)   # 礼貌限速
    total = sum(r["chars"] for r in report)
    out = {"source": BASE, "source_note": "维基文库 zh.wikisource.org 本网络不可达，"
            "依 SPEC 数据源次序回退国学导航本（四部丛刊影印整理底本，GB18030）",
           "vols": report, "total_chars": total,
           "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(ROOT, "data", "fetch_report.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n合计 {total} 字（序 + 五卷）→ data/fetch_report.json")


if __name__ == "__main__":
    main()
