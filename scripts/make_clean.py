# 生成 data/clean/：因为原文不需要清洗，这里先"原样复制"一份，并逐字核对
import os
import sys

# Windows 中文终端默认是 GBK 编码，打不出下面用到的 ❌ 符号，会直接报错退出。
# 这一行让本脚本的输出统一走 UTF-8，什么符号都打得出来。
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

for f in sorted(os.listdir("data/raw")):
    if not f.endswith(".txt"):
        continue

    text = open("data/raw/" + f, encoding="utf-8").read()          # 读原文

    out = open("data/clean/" + f, "w", encoding="utf-8")           # "w" = 写入模式：新建或覆盖
    out.write(text)                                                # 把内容写进去
    out.close()                                                    # 关掉，确保真的落进硬盘

    back = open("data/clean/" + f, encoding="utf-8").read()         # 再读回来

    if back == text:                                               # "==" 是判断相等，不是赋值
        print(f, "已复制，核对一致，共", len(back), "个字符")
    else:
        print(f, "❌ 内容不一致，需要检查")
        