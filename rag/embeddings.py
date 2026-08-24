# from langchain_ollama import OllamaEmbeddings
# from config.settings import OLLAMA_BASE_URL, EMBEDDING_MODEL
# embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL, base_url=OLLAMA_BASE_URL)

from langchain_voyageai import VoyageAIEmbeddings
from config.settings import VOYAGE_KEY, VOYAGE_EMB_MODEL
embeddings = VoyageAIEmbeddings(voyage_api_key=VOYAGE_KEY, model=VOYAGE_EMB_MODEL, output_dimension=1024, truncation=False)