# from langchain_ollama import OllamaEmbeddings
# from config.settings import OLLAMA_BASE_URL, LOCAL_EMB_MODEL
# embeddings = OllamaEmbeddings(model=LOCAL_EMB_MODEL, base_url=OLLAMA_BASE_URL)
# from transformers import AutoTokenizer
# tokenizer = AutoTokenizer.from_pretrained(f"BAAI/{LOCAL_EMB_MODEL}")
# def count_embedding_tokens(text: str) -> int:
#     return len(tokenizer.encode(text, add_special_tokens=True))

# from langchain_voyageai import VoyageAIEmbeddings
# from config.settings import VOYAGE_KEY, VOYAGE_EMB_MODEL
# embeddings = VoyageAIEmbeddings(voyage_api_key=VOYAGE_KEY, model=VOYAGE_EMB_MODEL, output_dimension=1024, truncation=False)

import voyageai
from config.settings import VOYAGE_KEY, VOYAGE_EMB_MODEL
client = voyageai.Client(api_key=VOYAGE_KEY)
last_usage = {"total_tokens": 0}
def embed_query_with_usage(text: str):
    result = client.embed(
        [text],
        model=VOYAGE_EMB_MODEL,
        input_type="query",
        output_dimension=1024,
    )
    last_usage["total_tokens"] = result.total_tokens
    return result.embeddings[0]
def get_embedding_tokens():
    return last_usage["total_tokens"]