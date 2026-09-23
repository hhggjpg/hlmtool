# 合并 5 回的抽取结果 → 输出 output/人物表.csv 和 output/关系表.csv

import json
import os
import csv

# ==================== 1. 别名字典：叫法 → 标准名 ====================
# 原则：只写"确实指同一个人"的。有争议的宁可分开。
ALIAS = {
    "贾雨村": "贾雨村",
    "雨村": "贾雨村",

    "林黛玉": "林黛玉",
    "黛玉": "林黛玉",

    "贾宝玉": "贾宝玉",
    "宝玉": "贾宝玉",

    "薛宝钗": "薛宝钗",
    "宝钗": "薛宝钗",

    "王熙凤": "王熙凤",
    "凤姐": "王熙凤",

    "王夫人": "王夫人",
    "王氏": "王夫人",          # 注意：仅按抽取结果判断，见下方 NO_COUNT 说明

    "甄士隐": "甄士隐",
    "甄老爷": "甄士隐",

    "封氏": "封氏",
    "甄家娘子": "封氏",

    "娇杏": "娇杏",
    "甄家丫鬟": "娇杏",

    "薛姨妈": "薛姨妈",
    "薛家姨母": "薛姨妈",

    "贾敏": "贾敏",
    "贾氏": "贾敏",

    "秦可卿": "秦可卿",
    "秦氏": "秦可卿",
    "秦氏": "秦可卿",
    "可卿": "秦可卿",      # 第五回太虚幻境中"乳名兼美表字可卿"
}

# 这些叫法"指谁不唯一"，所以统计出场次数时不用它们，只用标准名本身
NO_COUNT = {"王氏"}     # 第四回的"寡母王氏"指的是薛姨妈，不是王夫人

# 不参与关系图谱的实体（神话框架、物件、已故先祖、现实作者）
EXCLUDE = {
    "女娲氏", "石头", "通灵宝玉", "绛珠仙草",
    "茫茫大士", "渺渺真人", "空空道人", "警幻仙子", "警幻仙姑", "情僧",
    "宁公", "荣公", "宁荣二公",
    "曹雪芹", "孔梅溪",
}

CH_DIR = "data/clean"
OUT_DIR = "output"


# ==================== 2. 工具函数 ====================
def std(name):
    """把各种叫法换成标准名；字典里没有的，原样返回"""
    return ALIAS.get(name, name)


# ==================== 3. 读入 5 回的 JSON，收集全部关系 ====================
relations = []

for f in sorted(os.listdir(OUT_DIR)):
    if not f.endswith(".json") or not f.startswith("chapter_"):
        continue
    tag = f[len("chapter_"):-len(".json")]
    if not (len(tag) == 3 and tag.isdigit()):        # 跳过 _raw、_v3test 这类变体
        continue

    data = json.load(open(OUT_DIR + "/" + f, encoding="utf-8"))
    for r in data["关系"]:
        a = std(r["甲"])
        b = std(r["乙"])
        if a in EXCLUDE or b in EXCLUDE:             # 排除神话框架等
            continue
        if a == b:                                   # 合并后变成"自己跟自己"
            continue
        relations.append({
            "甲": a, "乙": b,
            "类型": r["关系类型"],
            "依据": r["原文依据"],
            "回": tag,
        })

print("合并前：", len(relations), "条关系")

# ==================== 4. 去重 ====================
# A→B 和 B→A 算同一对：先把两个名字排序再拼 key
merged = {}
for r in relations:
    x, y = sorted([r["甲"], r["乙"]])          # 排序后，顺序就固定了
    key = x + "|" + y + "|" + r["类型"]
    if key in merged:
        if r["回"] not in merged[key]["回"]:
            merged[key]["回"] = merged[key]["回"] + "," + r["回"]
    else:
        r["甲"], r["乙"] = x, y                 # 输出也统一按排序后的顺序
        merged[key] = r.copy()

rows = list(merged.values())
print("去重后：", len(rows), "条关系")

# ==================== 5. 写 关系表.csv ====================
# encoding 用 utf-8-sig：这样用 Excel 打开不会中文乱码
with open(OUT_DIR + "/关系表.csv", "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["人物A", "人物B", "关系类型", "出现在第几回", "原文依据"])
    for r in sorted(rows, key=lambda x: x["甲"]):
        w.writerow([r["甲"], r["乙"], r["类型"], r["回"], r["依据"]])

print("已写出 关系表.csv")


# ==================== 6. 出场统计 → 人物表.csv ====================
# 6.1 把字典反过来：标准名 → 它的所有叫法
变体 = {}
for variant, standard in ALIAS.items():
    if variant in NO_COUNT:                          # 有歧义的叫法不参与统计
        continue
    变体.setdefault(standard, [])
    if variant not in 变体[standard]:
        变体[standard].append(variant)

# 6.2 把关系里出现、但别名字典没提的人补进来
for r in rows:
    for n in (r["甲"], r["乙"]):
        if n not in 变体:
            变体[n] = [n]

# 6.3 读入 5 回正文
texts = {}
for f in sorted(os.listdir(CH_DIR)):
    if f.endswith(".txt"):
        texts[f] = open(CH_DIR + "/" + f, encoding="utf-8").read()

# 6.4 逐人统计
people_rows = []
for standard, vs in 变体.items():
    if standard in EXCLUDE:
        continue
    total = 0
    detail = []
    for f in sorted(texts):
        tmp = texts[f]                               # 每个文件拿一份独立副本
        c = 0
        for v in sorted(vs, key=len, reverse=True):  # 长的叫法先数
            c = c + tmp.count(v)
            tmp = tmp.replace(v, "□" * len(v))       # 数完挖掉，避免"贾宝玉"里的"宝玉"被重复数
        if c > 0:
            total = total + c
            detail.append(f[0:3] + "(" + str(c) + ")")
    people_rows.append({
        "标准名": standard,
        "叫法": "、".join(vs),
        "总次数": total,
        "分布": " ".join(detail),
    })

# 6.5 写 人物表.csv（按次数从多到少排）
with open(OUT_DIR + "/人物表.csv", "w", encoding="utf-8-sig", newline="") as fo:
    w = csv.writer(fo)
    w.writerow(["标准名", "原文中的各种叫法", "出场总次数", "分布（回(次数)）"])
    for p in sorted(people_rows, key=lambda x: x["总次数"], reverse=True):
        w.writerow([p["标准名"], p["叫法"], p["总次数"], p["分布"]])

print("已写出 人物表.csv（共", len(people_rows), "人）")