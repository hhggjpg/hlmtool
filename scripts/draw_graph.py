# 读 关系表_分类.csv，画人物关系图
#
# 【5 回版 -> 120 回版 改了什么】
# 全文抽出来有 400 多个"人物"，全画上去中心区域会糊成一团、一个字都看不清。
# 所以加了 TOP_N 过滤：先读 output/人物表.csv，只保留出场次数最多的前 N 个人
# 参与画图。（出场次数 < MIN_COUNT 的小角色直接不画）

import csv
import networkx as nx
import matplotlib
matplotlib.use("Agg")                    # 不弹窗，直接存成图片
import matplotlib.pyplot as plt

# ==================== 配置区 ====================
TOP_N = 60          # 只画出场次数最多的前 N 个人
# =================================================

# 让中文能正常显示（不设这两行，图上全是方框）
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

# 类别 → 边的颜色
COLOR = {
    "亲属": "#e74c3c",   # 红
    "主仆": "#3498db",   # 蓝
    "社会": "#2ecc71",   # 绿
    "冲突": "#f39c12",   # 橙
    "情感": "#9b59b6",   # 紫
}

# ==================== 0. 读人物表，挑出"主要人物" ====================
主要人物 = set()
with open("output/人物表.csv", encoding="utf-8-sig", newline="") as fi:
    for i, row in enumerate(csv.DictReader(fi)):
        if i >= TOP_N:
            break
        主要人物.add(row["标准名"])

print("主要人物（前", TOP_N, "名）:", len(主要人物), "人")

# ==================== 1. 建图 ====================
G = nx.Graph()
被过滤的边 = 0

with open("output/关系表_分类.csv", encoding="utf-8-sig", newline="") as fi:
    for row in csv.DictReader(fi):
        if row["上图"] != "是":                       # 事件/称谓类不画
            continue
        a, b, cat = row["人物A"], row["人物B"], row["类别"]
        if a not in 主要人物 or b not in 主要人物:      # 只画主要人物之间的关系
            被过滤的边 += 1
            continue
        if G.has_edge(a, b):                          # 已经有边，就把类别追加
            G[a][b]["类别"] = G[a][b]["类别"] + "/" + cat
        else:
            G.add_edge(a, b, 类别=cat)

print("节点", G.number_of_nodes(), "个；边", G.number_of_edges(), "条（过滤掉", 被过滤的边, "条次要关系）")

# ==================== 2. 画全图 ====================
pos = nx.spring_layout(G, k=1.2, seed=42, iterations=400)   # seed 固定，每次布局一样

plt.figure(figsize=(22, 16))

边色 = []
for a, b in G.edges():
    cat = G[a][b]["类别"].split("/")[0]
    边色.append(COLOR.get(cat, "#999999"))

度 = dict(G.degree())                                 # 每个人连了几条边
点大小 = [300 + 度[n] * 120 for n in G.nodes()]

nx.draw_networkx_edges(G, pos, edge_color=边色, width=1.4, alpha=0.6)
nx.draw_networkx_nodes(G, pos, node_size=点大小,
                       node_color="#fafafa", edgecolors="#333333", linewidths=1.2)
nx.draw_networkx_labels(G, pos, font_size=11)

# 图例
import matplotlib.lines as mlines
图例 = [mlines.Line2D([], [], color=c, lw=2, label=k) for k, c in COLOR.items()]
plt.legend(handles=图例, loc="upper left", fontsize=13)

plt.axis("off")
plt.tight_layout()
plt.savefig("output/关系图_全图.png", dpi=150)
plt.close()
print("已保存 output/关系图_全图.png")

# ==================== 3. 画一个人物的关系网（改成你想看的人） ====================
主角 = "林黛玉"

if 主角 in G:
    ego = nx.ego_graph(G, 主角, radius=1)          # 他 + 与他直接相连的人
    pos2 = nx.spring_layout(ego, k=1.0, seed=42, iterations=300)

    plt.figure(figsize=(14, 11))
    边色2 = []
    for a, b in ego.edges():
        cat = ego[a][b]["类别"].split("/")[0]
        边色2.append(COLOR.get(cat, "#999999"))

    nx.draw_networkx_edges(ego, pos2, edge_color=边色2, width=2, alpha=0.7)
    nx.draw_networkx_nodes(ego, pos2, node_size=[700 if n == 主角 else 300 for n in ego.nodes()],
                           node_color=["#ffd54f" if n == 主角 else "#fafafa" for n in ego.nodes()],
                           edgecolors="#333333", linewidths=1.2)
    nx.draw_networkx_labels(ego, pos2, font_size=12)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("output/关系图_" + 主角 + ".png", dpi=150)
    plt.close()
    print("已保存 output/关系图_" + 主角 + ".png（", ego.number_of_nodes(), "个节点）")
else:
    print("图里没有", 主角, "——换成别人试试")
