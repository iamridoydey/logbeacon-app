from groq import Groq
from app.config import Config

client = Groq(api_key=Config.GROQ_API_KEY)

SYSTEM_PROMPT = (
    "You are a DevOps assistant. The user will paste an error log or "
    "stack trace. Explain, in plain English, what caused it and give a "
    "concrete fix. Be concise and practical — no filler."
)


def ask_groq(error_log):
    response = client.chat.completions.create(
        model=Config.GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": error_log},
        ],
    )

    return {
        "log_solution": response.choices[0].message.content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
    }