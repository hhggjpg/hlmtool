# 核对全部 5 回的"原文依据"
import json
import os

def normalize(s):
    s = s.replace(" ", "").replace("\n", "").replace("\r", "")
    s = s.replace("\u3000", "")
    for q in ["“", "”", "‘", "’", '"', "'"]:
        s = s.replace(q, "")
    return s

total_ok = 0
total_bad = 0

for f in sorted(os.listdir("data/clean")):
    if not f.endswith(".txt"):
        continue

    chapter = f[0:3]
    jf = "output/chapter_" + chapter + ".json"
    if not os.path.exists(jf):
        print(chapter, "：还没有 JSON，跳过")
        continue

    stem = normalize(open("data/clean/" + f, encoding="utf-8").read())
    data = json.load(open(jf, encoding="utf-8"))

    ok = 0
    bad = 0
    for r in data["关系"]:
        if normalize(r["原文依据"]) in stem:
            ok = ok + 1
        else:
            bad = bad + 1
            print("  ", chapter, "未找到：", r["甲"], "—", r["乙"], "｜", r["原文依据"][:30])

    print(chapter, "：找到", ok, "条，未找到", bad, "条")
    total_ok = total_ok + ok
    total_bad = total_bad + bad

print("")
print("合计：找到", total_ok, "条，未找到", total_bad, "条")
print("准确率：", round(total_ok * 100 / (total_ok + total_bad), 1), "%")