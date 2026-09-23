# 读 关系表_分类.csv，画人物关系图

import csv
import networkx as nx
import matplotlib
matplotlib.use("Agg")                    # 不弹窗，直接存成图片
import matplotlib.pyplot as plt

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

# ==================== 1. 建图 ====================
G = nx.Graph()

with open("output/关系表_分类.csv", encoding="utf-8-sig", newline="") as fi:
    for row in csv.DictReader(fi):
        if row["上图"] != "是":                       # 事件类不画
            continue
        a, b, cat = row["人物A"], row["人物B"], row["类别"]
        if G.has_edge(a, b):                          # 已经有边，就把类别追加
            G[a][b]["类别"] = G[a][b]["类别"] + "/" + cat
        else:
            G.add_edge(a, b, 类别=cat)

print("节点", G.number_of_nodes(), "个；边", G.number_of_edges(), "条")

# ==================== 2. 画全图 ====================
pos = nx.spring_layout(G, k=0.7, seed=42, iterations=300)   # seed 固定，每次布局一样

plt.figure(figsize=(20, 14))

边色 = []
for a, b in G.edges():
    cat = G[a][b]["类别"].split("/")[0]
    边色.append(COLOR.get(cat, "#999999"))

度 = dict(G.degree())                                 # 每个人连了几条边
点大小 = [200 + 度[n] * 150 for n in G.nodes()]

nx.draw_networkx_edges(G, pos, edge_color=边色, width=1.3, alpha=0.65)
nx.draw_networkx_nodes(G, pos, node_size=点大小,
                       node_color="#fafafa", edgecolors="#333333", linewidths=1.2)
nx.draw_networkx_labels(G, pos, font_size=10)

# 图例
import matplotlib.lines as mlines
图例 = [mlines.Line2D([], [], color=c, lw=2, label=k) for k, c in COLOR.items()]
plt.legend(handles=图例, loc="upper left", fontsize=12)

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

    plt.figure(figsize=(12, 10))
    边色2 = []
    for a, b in ego.edges():
        cat = ego[a][b]["类别"].split("/")[0]
        边色2.append(COLOR.get(cat, "#999999"))

    nx.draw_networkx_edges(ego, pos2, edge_color=边色2, width=2, alpha=0.7)
    nx.draw_networkx_nodes(ego, pos2, node_size=[500 if n == 主角 else 250 for n in ego.nodes()],
                           node_color=["#ffd54f" if n == 主角 else "#fafafa" for n in ego.nodes()],
                           edgecolors="#333333", linewidths=1.2)
    nx.draw_networkx_labels(ego, pos2, font_size=12)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("output/关系图_" + 主角 + ".png", dpi=150)
    plt.close()
    print("已保存 output/关系图_" + 主角 + ".png")
else:
    print("图里没有", 主角, "——换成别人试试")