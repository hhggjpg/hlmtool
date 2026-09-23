import os                                  # 引入 Python 自带的 os 工具箱，用来读取环境变量
from openai import OpenAI                  # 从 openai 工具箱里取出名为 OpenAI 的零件
from dotenv import load_dotenv             # 取出读取 .env 文件的零件

load_dotenv()                              # 执行：把 .env 里的内容加载进来

client = OpenAI(                           # 创建一个"客户端"，相当于办好手续的办事员
    api_key=os.getenv("DEEPSEEK_API_KEY"), # 从环境变量里取出密钥（不写在代码里）
    base_url="https://api.deepseek.com",   # 告诉它去哪个地址办事
)

response = client.chat.completions.create( # 发起一次对话请求，结果存进 response
    model="deepseek-flash",                # 用哪个模型
    messages=[                             # 对话内容：一个列表，每项有"角色"和"内容"
        {"role": "system", "content": "你是一个助手。"},   # 给模型的设定
        {"role": "user",   "content": "用一句话解释什么是API"},             # 你说的话
    ],
)

print("模型回复：", response.choices[0].message.content)   # 打印模型的回答
print("token 用量：", response.usage)                      # 打印这次消耗了多少 token
print("这条消息的角色是：", response.choices[0].message.role)
print("候选数量：", len(response.choices))
