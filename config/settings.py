import os
from dotenv import load_dotenv

load_dotenv(override=True)

def get_env(key, default=None):
    val = os.getenv(key)
    if val is None:
        for k, v in os.environ.items():
            if k.strip() == key:
                val = v
                break
    if isinstance(val, str):
        return val.strip()
    return default

SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_KEY = get_env("SUPABASE_KEY")
SUPABASE_SECRET_KEY = get_env("SUPABASE_SECRET_KEY")

OLLAMA_BASE_URL = get_env("OLLAMA_BASE_URL")
OLLAMA_LLM = get_env("OLLAMA_LLM")
LOCAL_EMB_MODEL = get_env("LOCAL_EMB_MODEL")

RERANKER_MODEL = get_env("RERANKER_MODEL")

VOYAGE_KEY = get_env("VOYAGE_KEY")
VOYAGE_EMB_MODEL = get_env("VOYAGE_EMB_MODEL")

ARK_API_KEY = get_env("ARK_API_KEY")
ARK_BASE_URL = get_env("ARK_BASE_URL")
ARK_LLM = get_env("ARK_LLM")

SYNTHORAI_API_KEY = get_env("SYNTHORAI_API_KEY")