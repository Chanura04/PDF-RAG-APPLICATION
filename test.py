from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# client = OpenAI(api_key="your_api_key")

# models = client.models.list()

# for m in models.data:
#     print(m.id)

from openai import OpenAI

client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = "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"
)

completion = client.chat.completions.create(
  model="openai/gpt-oss-20b",
  messages=[{"role":"user","content":"How are you?"}],
  temperature=1,
  top_p=1,
  max_tokens=4096,
  stream=True
)

for chunk in completion:
  if not getattr(chunk, "choices", None):
    continue
  reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
  if reasoning:
    print(reasoning, end="")
  if chunk.choices and chunk.choices[0].delta.content is not None:
    print(chunk.choices[0].delta.content, end="")

