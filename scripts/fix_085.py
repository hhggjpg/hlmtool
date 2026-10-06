# 专门修第 085 回：整回发过去会让模型"复读失控"（输出到 65536 上限被截断，返回空）
# 解法：把正文切成两半，分别抽取，再把结果合并成一个正常的 JSON
# 用法：python scripts/fix_085.py

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

SYSTEM = ("你是一个古典文学文本分析助手。你的任务是从《红楼梦》的章回正文中，"
          "抽取明确出现的人物和他们之间明确的关系。只依据原文，不做推测，"
          "不引入原文之外的知识。")

RULES = open("prompts/v2_生成现有数据.txt", encoding="utf-8").read()
CHAPTER = "085"
OUT_PATH = "output/chapter_" + CHAPTER + ".json"

text = open("data/clean/" + CHAPTER + ".txt", encoding="utf-8").read()
half = len(text) // 2
parts = [text[:half], text[half:]]
print("085 回共", len(text), "字符，切成 2 段：", len(parts[0]), "+", len(parts[1]))

people = []
relations = []
total_tokens = 0

for i, part in enumerate(parts, start=1):
    prompt = ("请从下面这段《红楼梦》的正文中，抽取人物和人物关系。\n\n"
              + RULES + "\n\n正文：\n" + part)
    print("正在抽取第", i, "段 ...")
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": prompt},
        ],
    )
    answer = response.choices[0].message.content or ""
    answer = answer.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(answer)
    except Exception as e:
        print("  第", i, "段解析失败：", e)
        continue

    people += data.get("人物", [])
    relations += data.get("关系", [])
    total_tokens += response.usage.total_tokens
    print("  第", i, "段完成：人物", len(data.get("人物", [])), "个，关系", len(data.get("关系", [])), "条")

# 人物去重（保持原顺序）
seen = set()
uniq_people = []
for p in people:
    if p not in seen:
        seen.add(p)
        uniq_people.append(p)

result = {"人物": uniq_people, "关系": relations}
with open(OUT_PATH, "w", encoding="utf-8") as fo:
    json.dump(result, fo, ensure_ascii=False, indent=2)

print("")
print("合并完成：人物", len(uniq_people), "个（去重前", len(people), "），关系", len(relations), "条")
print("token 合计:", total_tokens)
print("已写入", OUT_PATH, "，大小", os.path.getsize(OUT_PATH), "字节")

# 记一笔到运行日志
with open("output/run_log.txt", "a", encoding="utf-8") as log:
    log.write(CHAPTER + " 分段补抽完成 | 分2段 | 人物" + str(len(uniq_people))
              + " 关系" + str(len(relations)) + " | total=" + str(total_tokens) + "\n")
