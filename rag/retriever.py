from supabase import create_client
from langchain_core.documents import Document
import time

from config.settings import SUPABASE_URL, SUPABASE_KEY
from rag.embeddings import embeddings
from rag.reranker import rerank

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def hybrid_retrieve(question: str, candidate_k: int = 10, rerank_k: int = 3) -> list[Document]:
    start = time.perf_counter()

    embedding_start = time.perf_counter()
    query_embedding = embeddings.embed_query(question)
    embedding_time = time.perf_counter() - embedding_start

    search_start = time.perf_counter()
    result = supabase.rpc("hybrid_search", {
        "query_text": question,
        "query_embedding": query_embedding,
        "match_count": candidate_k,
        "rrf_k": 50,
    }).execute()
    search_time = time.perf_counter() - search_start

    documents = []

    for row in result.data or []:
        metadata = row.get("metadata") or {}
        metadata["retrieval_score"] = row["hybrid_score"]
        documents.append(Document(page_content=row["content"], metadata=metadata))

    rerank_start = time.perf_counter()
    documents = rerank(question, documents, top_k=rerank_k)
    rerank_time = time.perf_counter() - rerank_start

    total_time = time.perf_counter() - start

    log = f"question='{question}' embedding={embedding_time:.3f}s | search={search_time:.3f}s | rerank={rerank_time:.3f}s | total={total_time:.3f}s\n"
    print(f"[RETRIEVAL] {log}")
    with open("log/log_retrieval.txt", "a", encoding="utf-8") as f:
        f.write(log)

    return documents