# 第 1 回：人物与关系抽取（第一版，只跑一回，人工看结果）
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

# ---------- 1. 读入正文 ----------
text = open("data/clean/001.txt", encoding="utf-8").read()
print("第 1 回正文长度：", len(text), "字符")

# ---------- 2. 拼提示词 ----------
instruction = """请从下面这段《红楼梦》第一回的正文中，抽取人物和人物关系。

要求：
1. 只抽原文中明确写到的关系，不要推测、不要补全常识
2. 每条关系必须附上一句原文依据（从正文中原文摘抄）
3. 人名用原文中的写法，不要统一成学界叫法
4. 只输出 JSON，不要输出任何解释文字。格式如下：
{
  "人物": ["人名1", "人名2"],
  "关系": [
    {"甲": "", "乙": "", "关系类型": "", "原文依据": ""}
  ]
}

正文：
"""

user_prompt = instruction + text

# ---------- 3. 调用 ----------
response = client.chat.completions.create(
    model="deepseek-flash",
    messages=[
        {"role": "system", "content": "你是一个古典文学文本分析助手。你的任务是从《红楼梦》的章回正文中，抽取明确出现的人物和他们之间明确的关系。只依据原文，不做推测，不引入原文之外的知识。"},
        {"role": "user", "content": user_prompt},
    ],
)

answer = response.choices[0].message.content

# ---------- 4. 看结果 ----------
print("=== 模型输出（前 2000 字符）===")
print(answer[:2000])
print("...(后面还有，完整内容在文件里)")
print("")
print("=== token 用量 ===")
print(response.usage)

# ---------- 5. 存文件 ----------
os.makedirs("output", exist_ok=True)
with open("output/chapter_001_raw.json", "w", encoding="utf-8") as f:
    f.write(answer)
print("已保存到 output/chapter_001_raw.json")