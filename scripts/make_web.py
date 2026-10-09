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
OUT_TAG = ""          # 文件名后缀，留空即可；调试时设成 "_v2" 之类可绕开浏览器缓存
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
  #hint { position: absolute; top: 58px; left: 14px; z-index: 10; color: #8a8a96;
          font-size: 12px; background: rgba(30,30,36,0.75); padding: 5px 10px;
          border-radius: 4px; pointer-events: none; }
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
  <span style="color:#666">|</span>
  <label class="cat" title="打开后：点哪个人物，就只显示和他有关的关系线；点空白处恢复全部">
    <input type="checkbox" id="onlySel"> 只看选中的人
  </label>
  <span id="stat"></span>
</div>
<div id="hint">拖动节点后它会停在原地 ｜ 点人物看他的关系 ｜ 悬停线条看原文依据</div>

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
    // 所有节点一样大：size 固定，并且不给 value（value 会让大人物自动变大）
    shape: "dot",
    size: 15,
    font: { size: 14, color: "#f0f0f0", strokeWidth: 3, strokeColor: "#1e1e24" },
    color: { background: "#fafafa", border: "#333", highlight: { background: "#ffd54f", border: "#333" } }
  };
}));

var edgeList = EDGES.map(function (e, i) {
  return {
    id: i,                     // 给每条线一个固定编号，筛选时按编号更新
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
    // 这几行决定了节点散不散开：排斥力越大、弹簧越长，节点之间离得越远
    forceAtlas2Based: {
      gravitationalConstant: -82,    // 小球之间的排斥力（负数 = 互相推开；绝对值越大越散）
      centralGravity: 0.012,         // 往中心拉的力（越大越往中间挤）
      springLength: 125,             // 有关系的两个人之间的理想距离（像素）
      springConstant: 0.08,
      avoidOverlap: 0.3              // 不许节点和别人的名字重叠
    },
    stabilization: { iterations: 400 },
    // 这两行治"打开后一直转圈、轻微晃"：阻尼越大，晃动越快停下来；限速防止甩过头
    damping: 0.45,
    maxVelocity: 20
  },
  interaction: { hover: true, tooltipDelay: 120, navigationButtons: false, keyboard: false },
  edges: { smooth: { type: "dynamic" } }
};
var network = new vis.Network(container, data, options);

// ===== 摆好位置之后就让图彻底停下来 =====
// 物理引擎会一直算、一直微调，看上去就是"图在慢慢转"。
// 所以：等它自己稳定一下（1.2 秒），就把物理关掉，图彻底静止。
// 想重新排布就点「重置视图」（那时会重新打开物理算一次）。
var 物理开着 = true;
var 关物理的定时器 = null;
function 关物理() {
  if (关物理的定时器) { clearTimeout(关物理的定时器); 关物理的定时器 = null; }
  if (!物理开着) { return; }
  network.setOptions({ physics: false });
  物理开着 = false;
}
// 打开物理，并在指定毫秒之后自动关掉（不传毫秒 = 一直开着，由调用方自己负责关）。
// 自动关的意义：让它算一小会儿（小斥力让大家慢慢让开），然后停住，不会变成图一直转。
function 开物理(毫秒) {
  network.setOptions({ physics: true });
  物理开着 = true;
  if (关物理的定时器) { clearTimeout(关物理的定时器); 关物理的定时器 = null; }
  if (毫秒) { 关物理的定时器 = setTimeout(关物理, 毫秒); }
}
// 开场：让它自己稳定 1.2 秒，然后把物理关掉，图彻底静止
setTimeout(关物理, 1200);

var 选中 = null;
var 钉住的 = [];

// ===== 拖动：拖谁谁动，松手停在原地 =====
// 拖动期间物理【一直】开着（不能定时关！否则拖到一半就不动了）——
// 所以把一个人拖到别人旁边，全程都能看到他们互相让开。
// 松手后：钉住这个人（不回弹），再让物理跑 0.9 秒让大家归位，然后自动停下来。
network.on("dragStart", function (p) {
  if (p.nodes && p.nodes.length) {
    开物理();                                        // 不传毫秒 = 全程开着，直到松手
    // 解钉：不然已经被钉住的人就拖不动了
    nodes.update(p.nodes.map(function (id) { return { id: id, fixed: false }; }));
  }
});
network.on("dragEnd", function (p) {
  if (p.nodes && p.nodes.length) {
    var patch = [];
    p.nodes.forEach(function (id) {
      patch.push({ id: id, fixed: true });           // 钉住：松手停在原地，不回弹
      if (钉住的.indexOf(id) < 0) { 钉住的.push(id); }
    });
    nodes.update(patch);
    开物理(900);                                     // 松手后跑 0.9 秒物理：小斥力让大家慢慢归位
  }
});

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

// ===== 筛选：类别开关 + "只看选中的人"，两件事叠在一起算 =====
function applyFilter() {
  var on = {};
  document.querySelectorAll("#cats input").forEach(function (cb) {
    on[cb.dataset.cat] = cb.checked;
  });
  var 只看 = document.getElementById("onlySel").checked;
  // 勾了"只看选中的人"却还没选人时，自动挑关系最多的那个人，
  // 免得出现"勾了开关却什么都没变"的困惑
  if (只看 && !选中) {
    var 度数 = {};
    edgeList.forEach(function (e) {
      度数[e.from] = (度数[e.from] || 0) + 1;
      度数[e.to] = (度数[e.to] || 0) + 1;
    });
    var 最热门 = null, 最多 = -1;
    Object.keys(度数).forEach(function (k) {
      if (度数[k] > 最多) { 最多 = 度数[k]; 最热门 = k; }
    });
    if (最热门) {
      选中 = 最热门;
      network.selectNodes([选中]);
      network.focus(选中, { scale: 1.0, animation: { duration: 600 } });
      updateInfo(选中);
    }
  }
  var patch = [];
  var 可见 = 0;
  edgeList.forEach(function (e, i) {
    var ok = on[EDGES[i].cat];
    if (ok && 只看) ok = (e.from === 选中 || e.to === 选中);
    if (ok) 可见++;
    patch.push({ id: i, hidden: !ok });
  });
  edges.update(patch);
  var s = "显示 " + nodes.length + " 人 / " + 可见 + " 条关系";
  if (只看 && 选中) { s += "（只看「" + 选中 + "」的关系）"; }
  document.getElementById("stat").textContent = s;
}

// ===== 点节点：右边显示他的关系清单；"只看选中的人"打开时，只留他的线 =====
function updateInfo(me) {
  var box = document.getElementById("info");
  if (!me) { box.style.display = "none"; return; }
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
  选中 = target;
  network.selectNodes([target]);
  network.focus(target, { scale: 1.15, animation: { duration: 600 } });
  updateInfo(target);
  applyFilter();
  if (hit.length > 1) {
    document.getElementById("stat").textContent = "匹配 " + hit.length + " 人，已定位到「" + target + "」";
  }
}

document.getElementById("btnSearch").addEventListener("click", doSearch);
document.getElementById("search").addEventListener("keydown", function (ev) {
  if (ev.key === "Enter") doSearch();
});
document.getElementById("onlySel").addEventListener("change", applyFilter);

// ===== 重置视图：解钉、取消选中、重新排一次布局 =====
document.getElementById("btnReset").addEventListener("click", function () {
  if (钉住的.length) {
    nodes.update(钉住的.map(function (id) { return { id: id, fixed: false }; }));
    钉住的 = [];
  }
  选中 = null;
  network.unselectAll();
  updateInfo(null);
  applyFilter();
  // 重新打开物理引擎算一次，1.2 秒后再关掉（这样能重新排布，又不会一直转）
  开物理(1200);
  network.fit({ animation: { duration: 500 } });
});

// ===== 点节点 =====
network.on("click", function (params) {
  if (!params.nodes.length) {
    // "只看选中的人"开着的时候，点空白处不清空选中（否则筛选会突然全没了）
    if (document.getElementById("onlySel").checked && 选中) { return; }
    选中 = null;
    updateInfo(null);
    applyFilter();
    return;
  }
  选中 = params.nodes[0];
  updateInfo(选中);
  applyFilter();
});

// 初始化统计
applyFilter();
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
    实际输出 = OUT_HTML.replace(".html", OUT_TAG + ".html")
    with open(实际输出, "w", encoding="utf-8") as f:
        f.write(html)

    大小 = os.path.getsize(实际输出) / 1024 / 1024
    print("已生成 %s（%.2f MB）" % (实际输出, 大小))
    print("用浏览器双击打开即可：可拖动节点、滚轮缩放、悬停看详情、搜索人名、按类别开关")
    print("这个文件是自包含的，断网也能打开")


if __name__ == "__main__":
    main()
