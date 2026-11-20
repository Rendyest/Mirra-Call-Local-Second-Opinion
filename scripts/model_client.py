import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-vl:2b")
client = OpenAI(
    api_key=os.getenv("MODEL_API_KEY") or "ollama",
    base_url=os.getenv("MODEL_API_BASE_URL", "http://127.0.0.1:11434/v1"),
)


def response_text(response):
    content = response.choices[0].message.content
    if not isinstance(content, str):
        raise ValueError("Model returned no text")
    content = re.sub(r"<think>[\s\S]*?</think>", "", content).strip()
    return re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE)