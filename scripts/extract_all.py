# 批量抽取：读 data/clean/*.txt → 调 API 抽取人物与关系 → 存 output/chapter_XXX.json
# 提示词从 prompts/ 里的文件读取（见下方 PROMPT_FILE）

import os
import time
import datetime
from openai import OpenAI
from dotenv import load_dotenv

# ==================== 配置区（要改只改这里） ====================
PROMPT_FILE  = "prompts/v2_生成现有数据.txt"   # 用哪版提示词（改成你实际的文件名）
ONLY_CHAPTER = ""            # 只跑某一回，例如 "003"；留空 = 全部跑
OUT_SUFFIX   = ""            # 输出文件名后缀，例如 "_v3test"；留空 = 不加
# ==============================================================

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

SYSTEM = ("你是一个古典文学文本分析助手。你的任务是从《红楼梦》的章回正文中，"
          "抽取明确出现的人物和他们之间明确的关系。只依据原文，不做推测，"
          "不引入原文之外的知识。")

# ---------- 读提示词（循环外读一次就够，不用每回都读） ----------
RULES = open(PROMPT_FILE, encoding="utf-8").read()
print("提示词文件：", PROMPT_FILE)
print("提示词长度：", len(RULES), "字符")

os.makedirs("output", exist_ok=True)

# 日志改成追加模式（"a"），不会把上次的记录冲掉
log = open("output/run_log.txt", "a", encoding="utf-8")
log.write("\n===== 运行开始 " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          + " | 提示词=" + PROMPT_FILE + " =====\n")
log.flush()

for f in sorted(os.listdir("data/clean")):
    if not f.endswith(".txt"):
        continue

    chapter = f[0:3]                                 # "001"

    if ONLY_CHAPTER and chapter != ONLY_CHAPTER:     # 配了"只跑某一回"就跳过别的
        continue

    out_path = "output/chapter_" + chapter + OUT_SUFFIX + ".json"

    if os.path.exists(out_path):                     # 已跑过就跳过：省钱，也防止覆盖
        print(chapter, "已存在，跳过 →", out_path)
        continue

    text = open("data/clean/" + f, encoding="utf-8").read()

    prompt = ("请从下面这段《红楼梦》的正文中，抽取人物和人物关系。\n\n"
              + RULES
              + "\n\n正文：\n"
              + text)

    print("正在处理第", chapter, "回 ...")
    try:
        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user",   "content": prompt},
            ],
        )
        answer = response.choices[0].message.content
        answer = answer.replace("```json", "").replace("```", "").strip()

        with open(out_path, "w", encoding="utf-8") as fo:
            fo.write(answer)

        u = response.usage
        line = (chapter + OUT_SUFFIX
                + " 完成 | prompt=" + str(u.prompt_tokens)
                + " completion=" + str(u.completion_tokens)
                + " total=" + str(u.total_tokens))
        log.write(line + "\n")
        log.flush()
        print("  →", line)

    except Exception as e:                           # 出错不中断，继续跑下一回
        log.write(chapter + " 失败 | " + str(e) + "\n")
        log.flush()
        print("  → 失败：", e)

    time.sleep(1)

log.close()
print("全部结束。日志：output/run_log.txt")