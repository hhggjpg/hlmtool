# 扫描 data/raw 里所有 txt，找出所有"私有区"怪字
import os

for name in sorted(os.listdir("data/raw")):     # 列出文件夹里所有东西，按名字排序，逐个处理
    if not name.endswith(".txt"):               # 只处理 .txt 结尾的
        continue                                # 其他的跳过，回到循环开头

    text = open("data/raw/" + name, encoding="utf-8").read()   # 读进整个文件
    count = 0

    for i, ch in enumerate(text):               # 一个一个字符走一遍，i 是位置，ch 是那个字符
        if ord(ch) >= 0xE000 and ord(ch) <= 0xF8FF:            # 落在私有区里？
            count = count + 1
            start = max(0, i - 8)               # 往左取 8 个字当上下文（防止开头越界）
            print(name, "位置", i, "码位", hex(ord(ch)), "| 上下文：", text[start:i+9])

    if count == 0:
        print(name, "：没有私有区字符")