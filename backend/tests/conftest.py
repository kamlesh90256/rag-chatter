import os

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./backend-test.db")
os.environ.setdefault("CHROMA_PERSIST_DIR", "./backend-test-chroma")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from backend.utils.settings import get_settings

get_settings.cache_clear()
