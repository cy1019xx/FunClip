import os
from openai import OpenAI

# 固定参数
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("DASHSCOPE_API_KEY")

API_KEY = os.getenv("DASHSCOPE_API_KEY")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-vl-plus"

# 封装的函数
def call_qwen_vl(messages):
    # 检查messages格式
    if not isinstance(messages, list) or not messages:
        print("错误: messages必须是一个非空的列表。")
        return None

    for message in messages:
        if not isinstance(message, dict):
            print("错误: 每条消息必须是一个字典。")
            return None
        if 'role' not in message or 'content' not in message:
            print("错误: 每条消息必须包含'role'和'content'。")
            return None
        if not message['content']:
            print("错误: 'content'不能为空。")
            return None
        
    try:
        client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
        )
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        
        # 提取content字段
        content = completion.choices[0].message.content
        return content
        
    except Exception as e:
        print(f"调用API过程中出现错误: {e}")
        return None  # 返回None或者其他适当的值，表示调用失败

# 示例调用
if __name__ == "__main__":
    
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": "这是什么"},
            {"type": "image_url", "image_url": {"url": "https://dashscope.oss-cn-beijing.aliyuncs.com/images/dog_and_girl.jpeg"}}
        ]
    }]
    response = call_qwen_vl(messages)
    
    if response is not None:
        print(response)
    else:
        print("未能获取有效的响应。")
