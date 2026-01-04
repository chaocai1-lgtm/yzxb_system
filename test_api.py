"""
测试DeepSeek API调用
"""
import sys
sys.path.insert(0, '.')

from openai import OpenAI
from config.settings import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

print(f"DEEPSEEK_API_KEY: {DEEPSEEK_API_KEY[:15]}...")
print(f"DEEPSEEK_BASE_URL: {DEEPSEEK_BASE_URL}")

try:
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL
    )
    print("✅ OpenAI客户端创建成功")
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "你好，请简单回复"}],
        stream=False
    )
    print(f"✅ API调用成功: {response.choices[0].message.content}")
    
except Exception as e:
    import traceback
    print(f"❌ 错误: {str(e)}")
    print(f"完整堆栈:\n{traceback.format_exc()}")
