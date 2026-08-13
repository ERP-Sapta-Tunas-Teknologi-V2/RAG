from langchain_ollama import OllamaEmbeddings

from config.settings import OLLAMA_BASE_URL, EMBEDDING_MODEL
embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)