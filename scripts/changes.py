# 找"关系随情节变化"的线索：同一对人物出现在多回，或有多条不同关系
import csv

pairs = {}

with open("output/关系表_分类.csv", encoding="utf-8-sig", newline="") as fi:
    for row in csv.DictReader(fi):
        if row["上图"] != "是":
            continue
        a, b = row["人物A"], row["人物B"]
        key = " — ".join(sorted([a, b]))          # 配对顺序固定，A-B 和 B-A 归到一起
        if key not in pairs:
            pairs[key] = []
        pairs[key].append({
            "回": row["出现在第几回"],
            "类别": row["类别"],
            "标签": row["原标签"],
            "依据": row["原文依据"][:40],
        })

# 只打印有"多条记录"或"跨多回"的配对
for key in sorted(pairs):
    items = pairs[key]
    回集 = set()
    for it in items:
        for r in it["回"].split(","):
            回集.add(r)

    if len(items) >= 2 or len(回集) >= 2:
        print(key)
        for it in items:
            print("   ", it["回"], "|", it["类别"], "/", it["标签"])
            print("        ", it["依据"], "...")
        print("")