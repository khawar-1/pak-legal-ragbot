import os
from dotenv import load_dotenv

# Use absolute path so it's found regardless of working directory
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.local')
load_dotenv(_env_path)

# Groq configuration (free LLM for answer generation)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# HuggingFace configuration (free embeddings - no daily quota)
HUGGINGFACE_API_TOKEN = os.environ.get("HUGGINGFACE_API_TOKEN", "")

# Keep Gemini key for any legacy references
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ocr_training_dataset.json")
