# 体检 + 统一格式：读入全部 JSON，报告数量，再统一写成缩进格式
import json
import os

for f in sorted(os.listdir("output")):
    if not f.endswith(".json"):
        continue

    path = "output/" + f

    # ---------- 1. 能不能解析？ ----------
    try:
        data = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        print(f, "❌ 无法解析：", e)
        continue

    people = data.get("人物", [])
    rels = data.get("关系", [])

    print(f)
    print("   人物", len(people), "个；关系", len(rels), "条")

    # ---------- 2. 人名有没有重复 ----------
    if len(people) != len(set(people)):
        print("   ⚠️ 人物列表里有重复项")

    # ---------- 3. 每条关系的字段齐不齐 ----------
    missing = 0
    for r in rels:
        for k in ["甲", "乙", "关系类型", "原文依据"]:
            if k not in r:
                missing = missing + 1
                print("   ⚠️ 缺字段", k, "：", r)
    if missing == 0:
        print("   字段完整")

    # ---------- 4. 有没有完全重复的关系 ----------
    seen = []
    for r in rels:
        key = r["甲"] + "|" + r["乙"] + "|" + r["关系类型"]
        if key in seen:
            print("   ⚠️ 重复关系：", key)
        seen.append(key)

    # ---------- 5. 统一写成展开格式（内容不变，只改排版） ----------
    with open(path, "w", encoding="utf-8") as fo:
        json.dump(data, fo, ensure_ascii=False, indent=2)

print("")
print("完成：所有文件已统一为缩进格式")