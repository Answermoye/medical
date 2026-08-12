from openai import OpenAI
client = OpenAI(api_key="0",base_url="https://afdd582ae4b14053bf887245cf39f59f--8000.ap-shanghai2.cloudstudio.club/v1")
messages = [{"role": "user", "content": "介绍一下你自己?"}]

completions = client.chat.completions.create(
    messages=messages,
    model="qwen",
    stream=True)

for chunk in completions:
    print(chunk.choices[0].delta.content, end="", sep="", flush=True)