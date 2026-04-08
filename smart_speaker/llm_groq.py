import os
from typing import List, Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # .env 읽기

_CLIENT: Optional[Groq] = None


def _get_client() -> Groq:
    global _CLIENT
    if _CLIENT is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY가 없습니다. .env에 키를 설정하세요.")
        _CLIENT = Groq(api_key=api_key)
    return _CLIENT


def generate_response(
    prompt: str,
    model: str = "llama-3.3-70b-versatile",
    history: Optional[List[dict]] = None,
    system_prompt: Optional[str] = None,
    temperature: float = 0.4,
    max_tokens: int = 512,
) -> str:
    client = _get_client()
    messages = []

    if history:
        for message in history:
            # LLM에 전달할 히스토리에는 'audio' 키를 제외합니다.
            if message["role"] in ["user", "assistant"]:
                messages.append({"role": message["role"], "content": message["content"]})

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return (chat_completion.choices[0].message.content or "").strip()


if __name__ == "__main__":
    reply = generate_response("안녕 좋은 아침이야")
    print(reply)
