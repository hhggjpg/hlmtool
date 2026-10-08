# 生成交互式网页关系图（一个自包含的 HTML 文件）
#
# 【为什么要做这个】
# PNG 图片是"拍死的照片"：
#   - 两个名字叠在一起，没法拉开
#   - 一条线是什么关系，看不见
#   - 想只看"冲突"，得重新生成一张图
# 网页图能拖动节点、缩放、悬停看详情、搜索、按类别开关。
#
# 【为什么不用 pyvis 之类的库】
# 那些库生成的 HTML 默认引用 CDN 网址（https://cdn.jsdelivr.net/...）。
# 一旦断网、或者对方网络受限，打开就是白屏，而且不报错。
# 所以这里把 vis-network 的 JS 整段内嵌进 HTML，
# 生成的文件是"自包含"的：拷给别人、断网双击，都能正常打开。
#
# 【为什么不额外装 Python 包】
# 全程只用标准库 + 项目里已有的东西，requirements.txt 一个字都不用改。

import csv
import json
import os
import sys

# ==================== 配置区 ====================
TOP_N = 80            # 网页里放前 N 个人物（太多会看不清）
OUT_HTML = "output/关系图_交互版.html"
LIB = "vendor/vis-network.min.js"      # vis-network 的 JS 库
# =================================================

人物表 = "output/人物表.csv"
分类表 = "output/关系表_分类.csv"

# 类别 → 颜色（和 draw_graph.py 保持一致，方便对照）
COLOR = {
    "亲属": "#e74c3c",
    "主仆": "#3498db",
    "社会": "#2ecc71",
    "冲突": "#f39c12",
    "情感": "#9b59b6",
}


def 读人物(top_n):
    """取前 top_n 个人物，返回 [(标准名, 出场次数), ...]"""
    结果 = []
    with open(人物表, encoding="utf-8-sig", newline="") as f:
        for i, row in enumerate(csv.DictReader(f)):
            if i >= top_n:
                break
            try:
                次数 = int(row["出场总次数"])
            except (KeyError, ValueError):
                次数 = 0
            结果.append((row["标准名"], 次数))
    return 结果


def 读关系(人物集):
    """只保留两个人都在这批人物里的关系（去重后）"""
    边 = {}
    跳过 = 0
    with open(分类表, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["上图"] != "是":          # 事件/称谓/未分类不上图
                continue
            a, b = row["人物A"], row["人物B"]
            if a not in 人物集 or b not in 人物集:
                跳过 += 1
                continue
            key = tuple(sorted([a, b]))      # 同一对只留一条
            if key in 边:
                # 已经有一条了：如果类别不同，记下来（用 / 连接）
                已有 = 边[key]["类别"]
                if row["类别"] not in 已有.split("/"):
                    边[key]["类别"] = 已有 + "/" + row["类别"]
                continue
            边[key] = {
                "甲": a, "乙": b,
                "类别": row["类别"],
                "标签": row["原标签"],
                "回": row["出现在第几回"],
                "依据": row["原文依据"],
            }
    return list(边.values()), 跳过


def 拼数据(人物, 边列表):
    """把人物和关系转成 vis-network 要的格式"""
    度数 = {}
    for e in 边列表:
        for n in (e["甲"], e["乙"]):
            度数[n] = 度数.get(n, 0) + 1

    节点 = []
    for 名, 次数 in 人物:
        d = 度数.get(名, 0)
        节点.append({
            "id": 名,
            "label": 名,
            "value": 次数,
            "title": "%s\n出场 %d 次\n图上连接 %d 条关系" % (名, 次数, d),
        })

    边 = []
    for e in 边列表:
        主类 = e["类别"].split("/")[0]
        边.append({
            "from": e["甲"],
            "to": e["乙"],
            "color": {"color": COLOR.get(主类, "#999999"), "opacity": 0.75},
            "title": "%s — %s\n类别：%s\n原标签：%s\n回目：%s\n依据：%s"
                     % (e["甲"], e["乙"], e["类别"], e["标签"], e["回"], e["依据"]),
        })
    return 节点, 边


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>红楼梦人物关系图（交互版）</title>
<style>
  html, body { margin: 0; padding: 0; height: 100%; overflow: hidden;
               font-family: "Microsoft YaHei", "SimHei", sans-serif; background: #1e1e24; }
  #bar { position: absolute; top: 0; left: 0; right: 0; z-index: 10;
         background: rgba(30,30,36,0.94); color: #eee; padding: 10px 14px;
         display: flex; flex-wrap: wrap; align-items: center; gap: 10px;
         border-bottom: 1px solid #3a3a44; }
  #bar input[type=text] { padding: 6px 10px; border-radius: 4px; border: 1px solid #555;
                          background: #2a2a32; color: #eee; width: 180px; font-size: 14px; }
  #bar button { padding: 6px 12px; border-radius: 4px; border: 1px solid #555;
                background: #2f2f38; color: #eee; cursor: pointer; font-size: 13px; }
  #bar button:hover { background: #3d3d48; }
  #net { width: 100%; height: 100%; }
  .cat { display: inline-flex; align-items: center; gap: 4px; font-size: 13px;
         cursor: pointer; user-select: none; }
  .cat input { cursor: pointer; }
  #info { position: absolute; right: 12px; bottom: 12px; z-index: 10;
          background: rgba(30,30,36,0.92); color: #ccc; padding: 8px 12px;
          border-radius: 6px; font-size: 12px; line-height: 1.6; max-width: 340px;
          border: 1px solid #3a3a44; display: none; }
  #stat { color: #999; font-size: 12px; margin-left: auto; }
</style>
</head>
<body>

<div id="bar">
  <strong style="font-size:15px">红楼梦 · 人物关系图</strong>
  <input type="text" id="search" placeholder="搜索人名，如 贾宝玉">
  <button id="btnSearch">定位</button>
  <button id="btnReset">重置视图</button>
  <span style="color:#666">|</span>
  <span id="cats"></span>
  <span id="stat"></span>
</div>

<div id="net"></div>
<div id="info"></div>

<script>
__VIS_LIB__
</script>

<script>
// ===== 数据（由 make_web.py 从 CSV 自动生成，不要手改）=====
var NODES = __NODES__;
var EDGES = __EDGES__;
var CATCOLOR = __CATCOLOR__;

// ===== 建图 =====
var nodes = new vis.DataSet(NODES.map(function (n) {
  return {
    id: n.id,
    label: n.label,
    title: n.title,
    value: n.value,
    shape: "dot",
    scaling: { min: 8, max: 34 },
    font: { size: 15, color: "#f0f0f0", strokeWidth: 3, strokeColor: "#1e1e24" },
    color: { background: "#fafafa", border: "#333", highlight: { background: "#ffd54f", border: "#333" } }
  };
}));

var edgeList = EDGES.map(function (e) {
  return {
    from: e.from, to: e.to, title: e.title, color: e.color,
    width: 1.5, selectionWidth: 3
  };
});
var edges = new vis.DataSet(edgeList);

var container = document.getElementById("net");
var data = { nodes: nodes, edges: edges };
var options = {
  physics: {
    solver: "forceAtlas2Based",
    forceAtlas2Based: { gravitationalConstant: -62, centralGravity: 0.008, springLength: 130, springConstant: 0.09 },
    stabilization: { iterations: 320 }
  },
  interaction: { hover: true, tooltipDelay: 120, navigationButtons: false, keyboard: false },
  edges: { smooth: { type: "continuous" } }
};
var network = new vis.Network(container, data, options);

// ===== 图例 + 类别开关 =====
var catsBox = document.getElementById("cats");
Object.keys(CATCOLOR).forEach(function (c) {
  var lab = document.createElement("label");
  lab.className = "cat";
  var cb = document.createElement("input");
  cb.type = "checkbox";
  cb.checked = true;
  cb.dataset.cat = c;
  cb.addEventListener("change", applyFilter);
  var dot = document.createElement("span");
  dot.style.cssText = "display:inline-block;width:10px;height:10px;border-radius:50%;background:" + CATCOLOR[c];
  lab.appendChild(cb);
  lab.appendChild(dot);
  lab.appendChild(document.createTextNode(c));
  catsBox.appendChild(lab);
});

function applyFilter() {
  var on = {};
  document.querySelectorAll("#cats input").forEach(function (cb) {
    on[cb.dataset.cat] = cb.checked;
  });
  var kept = edgeList.filter(function (e, i) {
    var main = EDGES[i].cat;
    return on[main];
  });
  edges.clear();
  edges.add(kept);
  document.getElementById("stat").textContent =
    "显示 " + nodes.length + " 人 / " + kept.length + " 条关系";
}

// ===== 搜索定位 =====
function doSearch() {
  var kw = document.getElementById("search").value.trim();
  if (!kw) return;
  var hit = NODES.filter(function (n) { return n.id.indexOf(kw) >= 0; });
  if (!hit.length) {
    document.getElementById("stat").textContent = "没找到「" + kw + "」";
    return;
  }
  // 选第一个匹配（出场次数最多的那个，因为数据已按次数排序）
  var target = hit[0].id;
  network.selectNodes([target]);
  network.focus(target, { scale: 1.15, animation: { duration: 600 } });
  var 度数 = EDGES.filter(function (e) { return e.from === target || e.to === target; }).length;
  document.getElementById("info").style.display = "block";
  document.getElementById("info").innerHTML =
    "<b>" + target + "</b><br>图上连接 " + 度数 + " 条关系" +
    (hit.length > 1 ? "<br><span style='color:#888'>（还匹配到：" + hit.slice(1, 6).map(function (n) { return n.id; }).join("、") + "）</span>" : "");
  if (hit.length > 1) {
    document.getElementById("stat").textContent = "匹配 " + hit.length + " 人，已定位到「" + target + "」";
  }
}

document.getElementById("btnSearch").addEventListener("click", doSearch);
document.getElementById("search").addEventListener("keydown", function (ev) {
  if (ev.key === "Enter") doSearch();
});
document.getElementById("btnReset").addEventListener("click", function () {
  network.fit({ animation: { duration: 500 } });
  document.getElementById("info").style.display = "none";
});

// ===== 点节点时显示它的关系列表 =====
network.on("click", function (params) {
  var box = document.getElementById("info");
  if (!params.nodes.length) { box.style.display = "none"; return; }
  var me = params.nodes[0];
  var mine = EDGES.filter(function (e) { return e.from === me || e.to === me; });
  var byCat = {};
  mine.forEach(function (e) {
    var other = (e.from === me) ? e.to : e.from;
    (byCat[e.cat] = byCat[e.cat] || []).push(other);
  });
  var html = "<b>" + me + "</b>：共 " + mine.length + " 条关系<br>";
  Object.keys(byCat).forEach(function (c) {
    html += "<span style='color:" + CATCOLOR[c] + "'>■</span> " + c + "：" + byCat[c].join("、") + "<br>";
  });
  box.innerHTML = html;
  box.style.display = "block";
});

// 初始化统计
document.getElementById("stat").textContent = "显示 " + nodes.length + " 人 / " + edges.length + " 条关系";
</script>
</body>
</html>
"""


def main():
    top_n = TOP_N
    if len(sys.argv) > 1:
        try:
            top_n = int(sys.argv[1])
        except ValueError:
            print("参数要是数字，例如：python scripts/make_web.py 120")
            return

    for p in (人物表, 分类表):
        if not os.path.exists(p):
            print("找不到", p)
            print("请先在项目根目录跑：python scripts/make_tables.py 和 python scripts/classify.py")
            return

    if not os.path.exists(LIB):
        print("找不到 JS 库：", LIB)
        print("它应该放在项目根目录的 vendor/ 文件夹里（约 670 KB）。")
        return

    人物 = 读人物(top_n)
    人物集 = set(n for n, _ in 人物)
    边列表, 跳过 = 读关系(人物集)

    节点, 边 = 拼数据(人物, 边列表)
    print("人物 %d 人，关系 %d 条（另有 %d 条涉及圈外人物，没画）" % (len(节点), len(边), 跳过))

    # 每条边加一个"主类别"，方便网页里做类别开关
    for i, e in enumerate(边):
        e["cat"] = 边列表[i]["类别"].split("/")[0]

    lib_js = open(LIB, encoding="utf-8").read()

    html = HTML_TEMPLATE
    # JS 库整段内嵌 —— 这是"离线可用"的关键
    html = html.replace("__VIS_LIB__", lib_js)
    html = html.replace("__NODES__", json.dumps(节点, ensure_ascii=False))
    html = html.replace("__EDGES__", json.dumps(边, ensure_ascii=False))
    html = html.replace("__CATCOLOR__", json.dumps(COLOR, ensure_ascii=False))

    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    大小 = os.path.getsize(OUT_HTML) / 1024 / 1024
    print("已生成 %s（%.2f MB）" % (OUT_HTML, 大小))
    print("用浏览器双击打开即可：可拖动节点、滚轮缩放、悬停看详情、搜索人名、按类别开关")
    print("这个文件是自包含的，断网也能打开")


if __name__ == "__main__":
    main()
