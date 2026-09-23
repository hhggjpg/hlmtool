# 核对模型给出的"原文依据"是否真的出现在原文里
# 原理：把原文和依据里的"空格、换行、引号"全部去掉再比对
#       这样"换行不同""引号不同"就不算差异了
import json

def normalize(s):
    s = s.replace(" ", "").replace("\n", "").replace("\r", "")
    s = s.replace("\u3000", "")                                  # 全角空格
    for q in ["“", "”", "‘", "’", '"', "'"]:                     # 各种引号
        s = s.replace(q, "")
    return s

raw = open("data/clean/001.txt", encoding="utf-8").read()
stem = normalize(raw)

data = json.load(open("output/chapter_001_raw.json", encoding="utf-8"))

ok = 0
bad = 0
for i, rel in enumerate(data["关系"]):
    if normalize(rel["原文依据"]) in stem:
        ok = ok + 1
    else:
        bad = bad + 1
        print("未找到 第", i, "条：", rel["甲"], "—", rel["乙"])
        print("    依据开头：", rel["原文依据"][:40])

print("")
print("核对结果：找到", ok, "条，未找到", bad, "条")