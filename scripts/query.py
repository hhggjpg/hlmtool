# 交互查询：想看什么，直接问它
#
# 【这个脚本干什么】
# 把"改代码才能换主角"变成"运行后输入名字就行"。支持两种用法：
#
#   用法一（菜单式）：python scripts/query.py
#       运行后列出选项，输入编号或人名，一路照着提示走。
#
#   用法二（直接传参，适合熟练用 / 写进批处理）：
#       python scripts/query.py 贾宝玉          看他的关系网图
#       python scripts/query.py 贾宝玉 演变      看他的关系随回目怎么变
#       python scripts/query.py 全部            重新生成全部预设图
#
# 【为什么不做"说人话"的自然语言查询】
# 那需要再调用一次大模型来"猜你想干什么"。而这会破坏项目最重要的一条设计：
# **全项目只有 extract_all.py 一个地方调用大模型** —— 这句话保证了便宜和可复现。
# 菜单式查询的体验已经够用，而且零成本、结果固定。

import csv
import os
import subprocess
import sys

OUT = "output"
人物表 = OUT + "/人物表.csv"
分类表 = OUT + "/关系表_分类.csv"
演变清单 = OUT + "/关系演变清单.txt"
绘图脚本 = "scripts/draw_graph.py"


# ==================== 读数据 ====================
def 读人物表():
    """返回 [(标准名, 出场次数), ...]，按出场次数从多到少"""
    结果 = []
    if not os.path.exists(人物表):
        return 结果
    with open(人物表, encoding="utf-8-sig", newline="") as fi:
        for row in csv.DictReader(fi):
            try:
                次数 = int(row["出场总次数"])
            except (KeyError, ValueError):
                次数 = 0
            结果.append((row["标准名"], 次数))
    return 结果


def 找人物(输入的名字, 人物列表):
    """支持模糊匹配：输"宝玉"能找到"贾宝玉"。

    返回 (标准名, 候选列表, 说明文字)
      标准名 有值 -> 直接用这个人；说明文字会告诉用户匹配到了谁
      标准名 为 None 且候选非空 -> 匹配到多个，需要用户写清楚一点

    匹配规则（好懂的顺序）：
      1. 名字完全一样 -> 就是它
      2. 只有一个人包含这个名字 -> 就是它（输"宝玉"但只有"贾宝玉"含"宝玉"）
      3. 有多个人包含 -> 取出场次数最多的那个。
         但如果第二名也有第一名的 1/3 以上（说明两个都是重要人物，容易搞混），
         就不猜了，把候选列出来让用户自己选。
         例如"宝玉"会匹配到 贾宝玉 / 甄宝玉 / 宝玉的奶母：
         贾宝玉 4498 次，甄宝玉只有几十次 -> 直接用贾宝玉，并告诉用户选了谁。
    """
    名字 = 输入的名字.strip()
    if not 名字:
        return None, [], ""

    标准名们 = [n for n, _ in 人物列表]
    if 名字 in 标准名们:                       # 1. 完全一样
        return 名字, [], ""

    候选 = [n for n in 标准名们 if 名字 in n]   # 2. 包含关系（人物列表已按次数排序）
    if len(候选) == 1:
        return 候选[0], [], "「%s」-> %s" % (名字, 候选[0])

    if len(候选) > 1:
        次数表 = dict(人物列表)
        第一, 第二 = 候选[0], 候选[1]
        if 次数表.get(第二, 0) * 3 < 次数表.get(第一, 1):     # 3. 第一名明显领先
            return 第一, [], "「%s」匹配到 %s，按出场次数选了「%s」" % (
                名字, "、".join(候选[:4]), 第一)
        return None, 候选, ""

    return None, [], ""


def 读某个人的关系(人名):
    """从分类表里挑出所有和这个人有关的关系，返回按类别分组的结果"""
    if not os.path.exists(分类表):
        return {}
    按类别 = {}
    with open(分类表, encoding="utf-8-sig", newline="") as fi:
        for row in csv.DictReader(fi):
            if row["人物A"] != 人名 and row["人物B"] != 人名:
                continue
            对方 = row["人物B"] if row["人物A"] == 人名 else row["人物A"]
            按类别.setdefault(row["类别"], []).append({
                "对方": 对方,
                "标签": row["原标签"],
                "回": row["出现在第几回"],
                "依据": row["原文依据"],
                "上图": row["上图"],
            })
    return 按类别


def 找演变段落(人名):
    """从 关系演变清单.txt 里找出和这个人有关的段落"""
    if not os.path.exists(演变清单):
        return []
    with open(演变清单, encoding="utf-8") as f:
        行们 = f.read().splitlines()

    段落 = []
    当前 = None
    for 行 in 行们:
        if 行 and not 行.startswith(" ") and " — " in 行:
            if 当前:
                段落.append(当前)
            当前 = {"标题": 行, "内容": []} if 人名 in 行 else None
        elif 当前 is not None:
            当前["内容"].append(行)
    if 当前:
        段落.append(当前)
    return 段落


# ==================== 三个功能 ====================
def 功能_关系图(人名):
    """在已经生成的图里找出这个人的关系网图；没有就现场生成一张"""
    路径 = OUT + "/关系图_" + 人名 + ".png"
    if os.path.exists(路径):
        print("\n  这张图已经存在：%s" % 路径)
        print("  （双击打开就能看；想重新画一遍就删掉它再运行）")
        return True

    print("\n  还没有 %s 的关系图，现在给你画一张..." % 人名)
    return 画一个人(人名)


def 画一个人(人名):
    """调用 draw_graph.py 里的函数，给某个人单独出一张关系网图"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), "scripts"))
        import draw_graph as dg          # 复用 draw_graph.py，不重复写画图代码
    except Exception as e:
        print("  画图失败：", e)
        return False

    import networkx as nx
    import matplotlib
    matplotlib.use("Agg")

    主要人物 = dg.读主要人物(dg.TOP_N)
    按类别边, _ = dg.读边(主要人物)

    G = nx.Graph()
    for cat, 边列表 in 按类别边.items():
        for a, b in 边列表:
            if G.has_edge(a, b):
                G[a][b]["类别"] = G[a][b]["类别"] + "/" + cat
            else:
                G.add_edge(a, b, 类别=cat)

    if 人名 not in G:
        print("  %s 不在关系图的主要人物里。" % 人名)
        print("  （图上只画出场次数最多的前 %d 人，他可能出场太少）" % dg.TOP_N)
        return False

    ego = nx.ego_graph(G, 人名, radius=1)      # 他 + 与他直接相连的人
    dg.画一张(
        ego,
        标题="%s 的关系网（%d 人）" % (人名, ego.number_of_nodes()),
        主色="#555555",
        文件名=OUT + "/关系图_" + 人名 + ".png",
        高亮节点=人名,
    )
    return True


def 功能_演变(人名):
    """打印这个人的关系演变文字清单"""
    段落 = 找演变段落(人名)
    if not 段落:
        print("\n  %s 没有出现在「关系演变清单」里。" % 人名)
        print("  （清单只收录了「同一对人物有多条记录」或「跨多回出现」的配对）")
        return

    print("\n  找到 %d 对与 %s 有关系变化的人物：\n" % (len(段落), 人名))
    for i, 段 in enumerate(段落, 1):
        print("  %d. %s" % (i, 段["标题"]))
        for 行 in 段["内容"]:
            if 行.strip():
                print("     " + 行.strip())
        print()


def 功能_某人的关系总览(人名):
    """打印这个人在各回出现过哪些关系（按类别分组）"""
    按类别 = 读某个人的关系(人名)
    if not 按类别:
        print("\n  没找到和 %s 有关的记录。" % 人名)
        return

    总数 = sum(len(v) for v in 按类别.values())
    print("\n  %s：共 %d 条关系记录" % (人名, 总数))
    print("  " + "-" * 50)
    for 类别 in ["亲属", "主仆", "情感", "冲突", "社会", "事件", "称谓", "未分类"]:
        if 类别 not in 按类别:
            continue
        条目 = 按类别[类别]
        print("\n  【%s】%d 条" % (类别, len(条目)))
        for it in 条目[:8]:                       # 每类最多显示 8 条
            print("     %s（%s回）｜%s" % (it["对方"], it["回"], it["标签"]))
        if len(条目) > 8:
            print("     ...还有 %d 条" % (len(条目) - 8))


def 需要的图都在吗():
    """检查预设的图是不是都已经生成过了"""
    需要 = ["关系图_全图.png", "关系图_林黛玉.png"] + \
           ["关系图_%s.png" % c for c in ("亲属", "主仆", "社会", "冲突", "情感")]
    return all(os.path.exists(OUT + "/" + f) for f in 需要)


def 功能_全部出图(强制=False):
    """重新生成全部预设图（调用 draw_graph.py）

    第一次运行会自动跑一遍；如果图已经都在了就直接跳过，
    省得你每次查询都等它重画 7 张图。想强制重画就选菜单里的 [4]。
    """
    if not 强制 and 需要的图都在吗():
        print("\n  预设的图已经生成过了，跳过。")
        print("  （想重新画一遍，选菜单里的 [4]）")
        return

    print("\n  正在重新生成全部关系图...")
    r = subprocess.run([sys.executable, 绘图脚本])
    if r.returncode == 0:
        print("  完成。图片都在 output/ 目录里。")
    else:
        print("  出错了，退出码：", r.returncode)


# ==================== 菜单 ====================
def 打印菜单():
    print()
    print("=" * 56)
    print("  红楼梦人物关系 —— 查询工具")
    print("=" * 56)
    print("  [1] 看某个人物的关系网图      例如：贾宝玉")
    print("  [2] 看某个人物的关系演变       例如：贾宝玉")
    print("  [3] 看某个人物的全部关系记录   按类别分组列出")
    print("  [4] 重新生成全部预设图（全图 + 5 张分类图）")
    print("  [5] 列出出场次数最多的人物")
    print("  [0] 退出")
    print("-" * 56)


def 主流程_菜单():
    人物列表 = 读人物表()
    if not 人物列表:
        print("找不到 output/人物表.csv")
        print("请先在项目根目录运行：python scripts/make_tables.py")
        return

    print("\n正在准备基础数据（第一次运行会自动生成全部图）...")
    功能_全部出图()

    while True:
        打印菜单()
        try:
            选择 = input("  请输入编号，或直接输入人名：").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  再见。")
            return

        if 选择 in ("0", "q", "quit", "exit"):
            print("  再见。")
            return

        if 选择 == "4":
            功能_全部出图(强制=True)      # 用户主动选的，就真的重画一遍
            continue

        if 选择 == "5":
            print("\n  出场次数最多的 20 人：")
            for i, (名, 次) in enumerate(人物列表[:20], 1):
                print("   %2d. %-10s %5d 次" % (i, 名, 次))
            continue

        if 选择 in ("1", "2", "3"):
            功能 = 选择
            名字 = input("  请输入人名（例如 贾宝玉）：").strip()
        else:
            功能 = "1"                      # 直接输人名 = 默认看关系图
            名字 = 选择

        标准名, 候选, 说明 = 找人物(名字, 人物列表)
        if 标准名 is None:
            if 候选:
                print("\n  「%s」匹配到多个人，你是指：" % 名字)
                for c in 候选[:10]:
                    print("     -", c)
                print("  请把名字写完整一点，重新输入。")
            else:
                print("\n  没找到「%s」这个人。想看看都有谁，可以选 [5]。" % 名字)
            continue

        if 说明:
            print("\n  提示：%s" % 说明)

        if 功能 == "1":
            功能_关系图(标准名)
        elif 功能 == "2":
            功能_演变(标准名)
        else:
            功能_某人的关系总览(标准名)


# ==================== 命令行直接调用 ====================
def 主流程_参数(参数):
    人物列表 = 读人物表()
    名字 = 参数[0]

    if 名字 in ("全部", "all"):
        功能_全部出图()
        return

    标准名, 候选, 说明 = 找人物(名字, 人物列表)
    if 标准名 is None:
        if 候选:
            print("「%s」匹配到多个人：%s" % (名字, "、".join(候选[:10])))
        else:
            print("没找到「%s」这个人。" % 名字)
            print("提示：运行 python scripts/query.py 会列出所有人名。")
        return

    if 说明:
        print("提示：%s" % 说明)

    动作 = 参数[1] if len(参数) > 1 else "图"
    if 动作 in ("图", "关系图", "graph"):
        功能_关系图(标准名)
    elif 动作 in ("演变", "变化", "change"):
        功能_演变(标准名)
    elif 动作 in ("全部关系", "列表", "list"):
        功能_某人的关系总览(标准名)
    else:
        print("不认识的指令：", 动作)
        print("可用的有：图 / 演变 / 全部关系")


def main():
    if not os.path.exists(人物表):
        print("找不到 output/人物表.csv")
        print("请先在项目根目录运行这几个脚本：")
        print("  python scripts/extract_all.py    （调模型抽取，要花钱）")
        print("  python scripts/make_tables.py    （生成人物表和关系表）")
        print("  python scripts/classify.py       （归类）")
        return

    参数 = sys.argv[1:]
    if 参数:
        主流程_参数(参数)
    else:
        主流程_菜单()


if __name__ == "__main__":
    main()
