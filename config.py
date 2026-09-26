import os

from dotenv import load_dotenv

load_dotenv()

GROQ_MODEL = "openai/gpt-oss-120b"
GROQ_TEMPERATURE = 0
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
