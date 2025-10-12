import os
from dotenv import load_dotenv

load_dotenv('.env.local')

# Ollama configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
LLAMA_MODEL = os.environ.get("LLAMA_MODEL", "llama3.1:8b")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
KNOWLEDGE_BASE_PATH = r"api/data_structure_q_&_a.txt"