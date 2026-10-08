# 读 关系表_分类.csv，画人物关系图
#
# 【这个脚本产出什么】
#   1. 关系图_全图.png        全部类别画在一起（看整体结构）
#   2. 关系图_亲属.png        ┐
#   3. 关系图_主仆.png        │ 按关系类别分开画，
#   4. 关系图_社会.png        │ 解决"全图密密麻麻看不清"的问题
#   5. 关系图_冲突.png        │
#   6. 关系图_情感.png        ┘
#   7. 关系图_林黛玉.png      单个主角的关系网示例
#
# 【为什么要分开展示】
# 全图 426 条边里有 264 条（62%）都是亲属关系，把主仆/情感/冲突全盖住了。
# 拆开之后：亲属图虽然密，但密的都是同一种关系（家族谱系），
# 而冲突图只有 15 条边——正因为空，反而一眼能看清。
#
# 【为什么只画前 60 人】
# 全文抽出 497 个人物，全画上去中心会糊成一团、一个字看不清。
# 所以先读 人物表.csv，只保留出场次数最多的前 TOP_N 个人参与画图。

import csv
import networkx as nx
import matplotlib
matplotlib.use("Agg")                    # 不弹窗，直接存成图片
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

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

# 要单独出图的类别
CATEGORIES = ["亲属", "主仆", "社会", "冲突", "情感"]

# 主角示例图
主角 = "林黛玉"


def 算画布(pos, 基准=15.0):
    """按布局实际占的形状，算一个合适的画布大小（长宽比跟着布局走）。

    多做一步的原因：分块布局之后，图可能是"横向很长、竖向很矮"的形状。
    这时候如果还按固定的 (宽, 宽*0.76) 出图，两侧就会留下大片空白。
    """
    xs = [float(v[0]) for v in pos.values()]
    ys = [float(v[1]) for v in pos.values()]
    宽比 = (max(xs) - min(xs)) or 1.0
    高比 = (max(ys) - min(ys)) or 1.0

    if 宽比 >= 高比:
        画布宽 = 基准
        画布高 = max(6.0, 基准 * 高比 / 宽比)
    else:
        画布高 = 基准
        画布宽 = max(6.0, 基准 * 宽比 / 高比)
    return (画布宽, 画布高)


def 网格布局(g):
    """把节点排成方格阵，返回 {节点: (x, y)}。

    为什么不直接用 networkx 的布局：
    我们用到的 networkx 3.7 里没有 grid_2d_layout 这个函数（旧版本有，后来去掉了）。
    所以这里自己算：先根据节点数求出最接近正方形的行列数，
    再把节点按顺序一个个放进格子里。这样点与点之间永远不会重叠。
    """
    节点们 = list(g.nodes())
    n = len(节点们)

    # 求列数：从根号 n 附近找，找一个能整除的最小列数
    列数 = 1
    for c in range(1, n + 1):
        if c * c >= n:
            列数 = c
            break
    行数 = (n + 列数 - 1) // 列数

    pos = {}
    for i, 节点 in enumerate(节点们):
        列 = i % 列数
        行 = i // 列数
        # y 取负号，让第一行显示在最上面
        pos[节点] = (列, -行)
    return pos


def 分块布局(g, k):
    """把互不相连的几块分别布局，再横向拼起来。

    为什么需要这个：
    spring_layout 的规则是"有关系的互相拉近、没关系的互相推开"。
    当一张图里有好几块互不相连的部分时（亲属图就是这样：贾府一大块，
    林家三个人是另一块），它会把小块推到很远的地方，
    大块反而被压成一小团，画布大部分是空白 —— 图就白画了。

    这个函数把每一块单独摆好，再按块的大小从左到右并排铺开，
    这样画布上每一处都有内容。
    """
    各块 = sorted(nx.connected_components(g), key=len, reverse=True)

    if len(各块) == 1:                                   # 只有一块，正常布局
        return nx.spring_layout(g, k=k, seed=42, iterations=600)

    pos = {}
    累积宽度 = 0.0
    间距 = 1.2                                           # 块与块之间留一点空

    for 块 in 各块:
        子图 = g.subgraph(块)
        p = nx.spring_layout(子图, k=k, seed=42, iterations=600)

        # 算这一块现在占多大，好按比例缩放
        xs = [v[0] for v in p.values()] or [0]
        ys = [v[1] for v in p.values()] or [0]
        宽 = (max(xs) - min(xs)) or 1.0
        高 = (max(ys) - min(ys)) or 1.0

        # 块越大，分给它的宽度越大（按节点数的平方根来分，避免大块挤爆）
        目标宽 = max(1.5, (len(块) ** 0.5) * 1.9)
        比例 = 目标宽 / 宽

        for 节点, (x, y) in p.items():
            pos[节点] = ((x - min(xs)) * 比例 + 累积宽度,
                         (y - min(ys)) * 比例)

        累积宽度 += 目标宽 + 间距

    return pos


def 算布局参数(g):
    """按图的大小和疏密，自动决定用哪种布局、画布多大、字号多大。

    为什么不能只用一种布局：
    spring_layout（力学布局）的规则是"有关系的节点互相拉近、没关系的互相推开"。
    这在"一个连通的大网"上效果很好，但在"好几个互不相连的小簇"上会出问题：
    每个簇各自被推到一个角落，画布中央留一大片空白，图上却没多少内容。

    所以这里分三种情况：
      小图（<=20 人）   -> 网格布局：每个点占一格，永远不会重叠，一眼能数清
      中等（<=45 人）   -> 力学布局，参数按人数算
      大图（>45 人）    -> 力学布局 + 更大画布，否则标签会挤在一起
    """
    n = g.number_of_nodes()

    if n <= 20:
        布局 = "grid"
        画布 = (13, 10)
        字号 = 12
        k = None
    else:
        布局 = "spring"
        k = max(0.60, 2.6 - n * 0.030)          # 人越少 k 越大，把点铺开
        画布边长 = 13.0 + n * 0.16              # 人多就把画布放大，给标签留地方
        画布 = (画布边长, 画布边长 * 0.76)
        字号 = 10 if n <= 45 else 9

    return 布局, 画布, k, 字号


# ==================== 0. 读人物表，挑出"主要人物" ====================
def 读主要人物(top_n):
    """从 人物表.csv 取出场次数最多的前 top_n 个人的标准名"""
    人物 = set()
    with open("output/人物表.csv", encoding="utf-8-sig", newline="") as fi:
        for i, row in enumerate(csv.DictReader(fi)):
            if i >= top_n:
                break
            人物.add(row["标准名"])
    return 人物


# ==================== 1. 读关系表，按类别攒边 ====================
def 读边(主要人物):
    """返回 {类别: [(人物A, 人物B), ...]}，只保留两人都是主要人物的边"""
    按类别 = {c: [] for c in CATEGORIES}
    被过滤 = 0
    with open("output/关系表_分类.csv", encoding="utf-8-sig", newline="") as fi:
        for row in csv.DictReader(fi):
            if row["上图"] != "是":                    # 事件/称谓/未分类不画
                continue
            a, b, cat = row["人物A"], row["人物B"], row["类别"]
            if cat not in 按类别:                      # 只关心设定的 5 类
                continue
            if a not in 主要人物 or b not in 主要人物:   # 只画主要人物之间
                被过滤 += 1
                continue
            按类别[cat].append((a, b))
    return 按类别, 被过滤


def 建图(边列表):
    """把 [(a, b), ...] 变成一张无向图（同一对人物只留一条边）"""
    g = nx.Graph()
    for a, b in 边列表:
        if not g.has_edge(a, b):
            g.add_edge(a, b)
    return g


# ==================== 2. 画图的公共部分 ====================
def 画一张(g, 标题, 主色, 文件名, 高亮节点=None, 图例标签=None):
    """把图 g 画出来存成 文件名。布局参数由 算布局参数() 按图的疏密自动决定"""
    if g.number_of_nodes() == 0:
        print("  跳过", 标题, "——没有可画的关系")
        return

    布局, 画布, k, 字号 = 算布局参数(g)
    if 布局 == "grid":
        # 网格布局：每个点占一格，点与点之间永远不会重叠
        pos = 网格布局(g)
    else:
        pos = 分块布局(g, k)
        画布 = 算画布(pos, 基准=22.0)      # 画布长宽比跟着布局的实际形状走

    plt.figure(figsize=画布)

    边色 = [主色] * g.number_of_edges()

    度 = dict(g.degree())                                  # 每个人连了几条边
    点大小 = [220 + 度[n] * 55 for n in g.nodes()]
    if 高亮节点:
        点大小 = [700 if n == 高亮节点 else 300 for n in g.nodes()]

    nx.draw_networkx_edges(g, pos, edge_color=边色, width=1.4, alpha=0.6)
    nx.draw_networkx_nodes(
        g, pos, node_size=点大小,
        node_color=["#ffd54f" if n == 高亮节点 else "#fafafa" for n in g.nodes()],
        edgecolors="#333333", linewidths=1.2, alpha=0.85)
    nx.draw_networkx_labels(g, pos, font_size=字号)

    if 图例标签:
        图例 = [mlines.Line2D([], [], color=c, lw=2, label=k) for k, c in 图例标签.items()]
        plt.legend(handles=图例, loc="upper left", fontsize=13)

    plt.title(标题, fontsize=20)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(文件名, dpi=150)
    plt.close()
    print("  已保存 %s（%d 个节点，%d 条边）" % (文件名, g.number_of_nodes(), g.number_of_edges()))


# ==================== 主流程 ====================
主要人物 = 读主要人物(TOP_N)
print("主要人物（前", TOP_N, "名）:", len(主要人物), "人")

按类别边, 被过滤的边 = 读边(主要人物)

print("--- 出图 ---")

# --- 2a. 全图（所有类别画在一起，不同类别不同颜色）---
G = nx.Graph()
for cat, 边列表 in 按类别边.items():
    for a, b in 边列表:
        if G.has_edge(a, b):
            G[a][b]["类别"] = G[a][b]["类别"] + "/" + cat
        else:
            G.add_edge(a, b, 类别=cat)

if G.number_of_nodes():
    布局, 画布, k, 字号 = 算布局参数(G)
    if 布局 == "grid":
        pos = 网格布局(G)
    else:
        pos = 分块布局(G, k)
        画布 = 算画布(pos, 基准=24.0)
    plt.figure(figsize=画布)

    边色 = []
    for a, b in G.edges():
        cat = G[a][b]["类别"].split("/")[0]
        边色.append(COLOR.get(cat, "#999999"))

    度 = dict(G.degree())
    点大小 = [220 + 度[n] * 55 for n in G.nodes()]

    nx.draw_networkx_edges(G, pos, edge_color=边色, width=1.4, alpha=0.6)
    nx.draw_networkx_nodes(G, pos, node_size=点大小,
                           node_color="#fafafa", edgecolors="#333333",
                           linewidths=1.2, alpha=0.85)
    nx.draw_networkx_labels(G, pos, font_size=字号)

    图例 = [mlines.Line2D([], [], color=c, lw=2, label=k) for k, c in COLOR.items()]
    plt.legend(handles=图例, loc="upper left", fontsize=13)

    plt.title("红楼梦人物关系全图（%d 人 / %d 条关系）" % (G.number_of_nodes(), G.number_of_edges()), fontsize=20)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("output/关系图_全图.png", dpi=150)
    plt.close()
    print("  已保存 output/关系图_全图.png（%d 个节点，%d 条边）" % (G.number_of_nodes(), G.number_of_edges()))

# --- 2b~2f. 按类别各出一张 ---
for cat in CATEGORIES:
    子图 = 建图(按类别边[cat])
    画一张(
        子图,
        标题="%s关系图（%d 人 / %d 条关系）" % (cat, 子图.number_of_nodes(), 子图.number_of_edges()),
        主色=COLOR[cat],
        文件名="output/关系图_" + cat + ".png",
    )

# --- 3. 主角示例图（在全图上取他的一圈邻居）---
if 主角 in G:
    ego = nx.ego_graph(G, 主角, radius=1)          # 他 + 与他直接相连的人
    画一张(
        ego,
        标题="%s 的关系网（%d 人）" % (主角, ego.number_of_nodes()),
        主色="#555555",
        文件名="output/关系图_" + 主角 + ".png",
        高亮节点=主角,
    )
else:
    print("  图里没有", 主角, "——换成别人试试")

print("完成。提示：想看某个人的关系图，用 python scripts/query.py 人名")
