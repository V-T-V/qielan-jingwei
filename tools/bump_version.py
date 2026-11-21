"""伽蓝经纬 · 全站版本号一步到位（承姊妹站教训 13：忌手列清单）
用法: python tools/bump_version.py 1 2
覆盖: index.html · sw.js · js/*.js 内全部 ?v=OLD 与 sw VERSION 常量。
lint.py 校验一致性——改版本必须走本脚本。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def bump(old: str, new: str):
    targets = ["index.html", "sw.js"] + [
        os.path.join("js", f) for f in os.listdir(os.path.join(ROOT, "js"))
        if f.endswith(".js")] + [
        os.path.join("tests", f) for f in os.listdir(os.path.join(ROOT, "tests"))
        if f.endswith(".html")]
    n_files, n_hits = 0, 0
    for rel in targets:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            t = f.read()
        t2, k = re.subn(rf"\?v={old}\b", f"?v={new}", t)
        t2, k2 = re.subn(rf'VERSION = "v{old}"', f'VERSION = "v{new}"', t2)
        k += k2
        if k:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(t2)
            n_files += 1
            n_hits += k
    # sw SHELL_FILES 清单里的引用一并换
    p = os.path.join(ROOT, "sw.js")
    with open(p, encoding="utf-8") as f:
        t = f.read()
    print(f"bump v{old}→v{new}：{n_files} 文件 {n_hits} 处")
    if n_hits == 0:
        print("警告：无命中——检查 OLD 版本号")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    bump(sys.argv[1], sys.argv[2])
