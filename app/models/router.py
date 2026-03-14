# app/models/router.py

import os
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

MODEL_MANAGED = os.environ["OPENAI_MODEL_MANAGED"]


def call_managed_llm(prompt: str) -> tuple[str, dict]:

    response = client.chat.completions.create(
        model=MODEL_MANAGED,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    answer = response.choices[0].message.content

    meta = {
        "model": MODEL_MANAGED,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "total_tokens": response.usage.total_tokens,
    }

    return answer, meta