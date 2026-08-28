from supabase import create_client
from langchain_core.documents import Document
import time

from rag.embeddings import embeddings
from rag.reranker import rerank
from utils.supabase_client import supabase
from utils.anonymizer import anonymize_query

RERANK_THRESHOLD = 5.0

def hybrid_retrieve(question: str, request_id: str, candidate_k: int = 10, rerank_k: int = 3) -> tuple[list[Document], str]:
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

    safe_query = anonymize_query(question)

    with open("log/log_retrieval-docs.txt", "w", encoding="utf-8") as f:
        f.write(f"\n\n=== REQUEST {request_id} ===\nQUESTION: {safe_query}\n")

    for row in result.data or []:
        metadata = row.get("metadata") or {}
        metadata["retrieval_score"] = row["hybrid_score"]

        document = Document(page_content=row["content"], metadata=metadata)
        documents.append(document)

        with open("log/log_retrieval-docs.txt", "a", encoding="utf-8") as f:
            f.write(
                f"\n--- DOCUMENT ---\n"
                f"{document.page_content}\n\n"
                f"METADATA:\n"
                f"{document.metadata}\n"
            )

    rerank_start = time.perf_counter()
    documents = rerank(question, documents, top_k=rerank_k)
    rerank_time = time.perf_counter() - rerank_start

    with open("log/log_retrieval-docs.txt", "a", encoding="utf-8") as f:
        f.write("\n\n=== RERANK SCORES ===\n")
        for document in documents:
            f.write(
                f"score={document.metadata['rerank_score']:.4f} | "
                f"source={document.metadata.get('source')} | "
                f"page={document.metadata.get('page')}\n"
            )

    documents = [
        document
        for document in documents
        if document.metadata["rerank_score"] >= RERANK_THRESHOLD
    ]

    context = "\n\n".join(document.page_content for document in documents)

    total_time = time.perf_counter() - start

    log = (
        f"[{request_id}] question='{safe_query}'\n"
        f"[{request_id}] [RETRIEVAL] "
        f"embedding={embedding_time:.3f}s | "
        f"search={search_time:.3f}s | "
        f"rerank={rerank_time:.3f}s | "
        f"threshold={RERANK_THRESHOLD:.4f} | "
        f"relevant={len(documents)} | "
        f"total={total_time:.3f}s\n"
    )

    # print(log)
    with open("log/log_time.txt", "a", encoding="utf-8") as f:
        f.write(log)

    return documents, context