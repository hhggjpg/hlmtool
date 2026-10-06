# 找"关系随情节变化"的线索：同一对人物出现在多回，或有多条不同关系
# 输出：屏幕显示 + 写入 output/关系演变清单.txt
#
# 【改了什么】原版只 print 到屏幕，README 里承诺的 关系演变清单.txt 其实没生成。
# 现在把内容同时写进文件，README 和产出物就对得上了。

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

out = []

# 只输出有"多条记录"或"跨多回"的配对
for key in sorted(pairs):
    items = pairs[key]
    回集 = set()
    for it in items:
        for r in it["回"].split(","):
            回集.add(r)

    if len(items) >= 2 or len(回集) >= 2:
        out.append(key)
        for it in items:
            out.append("    " + it["回"] + " | " + it["类别"] + " / " + it["标签"])
            out.append("        " + it["依据"] + " ...")
        out.append("")

# 一起写进文件
with open("output/关系演变清单.txt", "w", encoding="utf-8") as fo:
    fo.write("关系演变清单\n")
    fo.write("说明：只列出「同一对人物出现多条记录」或「跨多回出现」的配对。\n")
    fo.write("      格式：人物A — 人物B / 然后是按回目排列的每条记录（含原文依据开头）。\n")
    fo.write("=" * 70 + "\n\n")
    for line in out:
        fo.write(line + "\n")

print("共找到", len([k for k in pairs if len(pairs[k]) >= 2 or
                    len(set(r for it in pairs[k] for r in it["回"].split(","))) >= 2]),
      "对「关系有变化」的人物")
print("已写出 output/关系演变清单.txt（", len(out), "行）")
