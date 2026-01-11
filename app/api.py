import os
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key="***REMOVED***",
)

completion = client.chat.completions.create(
    model="HuggingFaceH4/zephyr-7b-beta:featherless-ai",
    messages=[
        {
            "role": "user",
            "content": "What is the capital of France?"
        }
    ],
)

print(completion.choices[0].message)
