
from openai import OpenAI

client = OpenAI(
  api_key="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"
)

completion = client.chat.completions.create(
  model="gpt-4o-mini",
  store=True,
  messages=[
    {"role": "user", "content": "write a haiku about ai"}
  ]
)

print(completion.choices[0].message)