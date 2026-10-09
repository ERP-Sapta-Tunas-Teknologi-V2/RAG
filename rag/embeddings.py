from langchain_ollama import OllamaEmbeddings
from transformers import AutoTokenizer
from config.settings import OLLAMA_BASE_URL, LOCAL_EMB_MODEL

embeddings = OllamaEmbeddings(model=LOCAL_EMB_MODEL, base_url=OLLAMA_BASE_URL)
hf_model_name = LOCAL_EMB_MODEL.split(":")[0] if LOCAL_EMB_MODEL else "bge-m3"
hf_repo = f"BAAI/{hf_model_name}" if "/" not in hf_model_name else hf_model_name
tokenizer = AutoTokenizer.from_pretrained(hf_repo)
def count_embedding_tokens(text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=True))