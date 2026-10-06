# 抓取《红楼梦》程高本（120 回）全文 → data/raw/NNN.txt
# 数据源：《红楼梦》程高本，公有领域。文本来自公开仓库 gitbook-hongloumeng
# 用法：python scripts/fetch_text.py            # 全部 120 回
#       python scripts/fetch_text.py 001        # 只抓第 1 回（用来抽查）
# 注意：已存在的文件默认不覆盖，想重抓要先删掉它

import os
import re
import sys
import time
import urllib.request

# ==================== 配置区 ====================
BASE_URL = ("https://raw.githubusercontent.com/AnLittleHong/"
            "gitbook-hongloumeng/master/ch_cgb/")   # 章节目录（cgb = 程高本）
OUT_DIR  = "data/raw"                               # 存到哪
TOTAL    = 120                                      # 一共几回
SLEEP    = 0.3                                      # 每回之间歇几秒（别把人家服务器打疼）
# ==================================================

# ---------- 1. 把网页格式的文本，洗成纯正文 ----------
def clean(md):
    """输入：一个 .md 文件的全部内容；输出：只有正文的多行文字"""
    lines = []

    for line in md.split("\n"):
        line = line.strip()

        # 1.1 跳过空的、分隔线、以及页面里没用的标签
        if line == "" or line.startswith("----") or line in ("<hr>", "<br>"):
            continue

        # 1.2 标题行：### 第一回 甄士隐梦幻识通灵 贾雨村风尘怀闺秀
        if line.startswith("#"):
            line = line.lstrip("#").strip()

        # 1.3 去掉 HTML 标签，只留标签中间的字
        #     先把没关的 <p> 补上 </p>，这样正则能一刀切干净
        line = line.replace("<blockquote>", "").replace("</blockquote>", "")
        line = re.sub(r"<p>(.*?)(</p>|$)", r"\1", line)
        line = re.sub(r"<[^>]+>", "", line)

        if line.strip():
            lines.append(line.strip())

    return "\n".join(lines) + "\n"


# ---------- 2. 抓一回 ----------
def fetch_one(num):
    """num 是 1~120 的整数；返回洗好的正文，失败返回 None"""
    name = "%03d" % num                       # 1 → "001"
    url = BASE_URL + name + ".md"
    out_path = os.path.join(OUT_DIR, name + ".txt")

    if os.path.exists(out_path):
        print(name, "已存在，跳过 →", out_path)
        return None

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        md = r.read().decode("utf-8")

    text = clean(md)

    with open(out_path, "w", encoding="utf-8") as fo:
        fo.write(text)

    print(name, "完成 |", len(text), "字符 |", text.count("\n"), "行")
    return text


# ---------- 3. 主流程 ----------
# 只有"直接运行这个文件"时才执行；被别的脚本 import 时不会执行
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)

    # 命令行给了编号就只抓那一回，没给就抓全部
    if len(sys.argv) > 1:
        targets = [int(sys.argv[1])]
    else:
        targets = range(1, TOTAL + 1)

    ok = 0
    fail = 0
    for n in targets:
        try:
            if fetch_one(n) is not None:
                ok += 1
            time.sleep(SLEEP)
        except Exception as e:
            fail += 1
            print(n, "失败：", e)

    print("")
    print("结束：新抓", ok, "回，失败", fail, "回")
