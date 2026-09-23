# 人名点名：确认核心人物在前 5 回里都完好出现，并统计各自出现次数
import os

# 左边是"标准名"（你以后要用的正式名字），右边是"在文本里实际出现的那个叫法"
# 注意：每人只用一个叫法。如果同一人写成两种，短的会被长的包含，导致重复计数
people = {
    "甄士隐": "士隐",
    "贾雨村": "雨村",
    "林黛玉": "黛玉",
    "贾宝玉": "宝玉",
    "薛宝钗": "宝钗",
    "王熙凤": "凤姐",
    "贾母":   "贾母",
    "贾政":   "贾政",
    "王夫人": "王夫人",
    "秦可卿": "秦氏",
    "甄英莲": "英莲",
    "袭人":   "袭人",
    "贾琏":   "贾琏",
    "贾珍":   "贾珍",
    "薛蟠":   "薛蟠",
}

# 第一段：逐个点名
for name in people:
    keyword = people[name]                      # 取出这个人的搜索词
    total = 0
    parts = []                                  # 空列表，用来攒"第几回出现几次"
    for f in sorted(os.listdir("data/raw")):
        if not f.endswith(".txt"):
            continue
        text = open("data/raw/" + f, encoding="utf-8").read()
        c = text.count(keyword)                 # 数这个关键词在这份文件里出现几次
        if c > 0:
            parts.append(f[0:3] + "回:" + str(c))
        total = total + c
    print(name, "共", total, "次 |", " ".join(parts))

# 第二段：对照检查，看几个"容易误判"的词
print("")
print("=== 对照检查 ===")
for w in ["甄宝玉", "宝玉", "二爷", "太太"]:
    total = 0
    parts = []
    for f in sorted(os.listdir("data/raw")):
        if not f.endswith(".txt"):
            continue
        text = open("data/raw/" + f, encoding="utf-8").read()
        c = text.count(w)
        if c > 0:
            parts.append(f[0:3] + "回:" + str(c))
        total = total + c
    print(w, "共", total, "次 |", " ".join(parts))