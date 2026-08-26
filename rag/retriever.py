from supabase import create_client
from langchain_core.documents import Document
import time

from config.settings import SUPABASE_URL, SUPABASE_KEY
from rag.embeddings import embeddings
from rag.reranker import rerank

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

RERANK_THRESHOLD = 5.0


def hybrid_retrieve(
    question: str,
    candidate_k: int = 10,
    rerank_k: int = 3
) -> tuple[list[Document], str]:

    start = time.perf_counter()

    # Embedding
    embedding_start = time.perf_counter()
    query_embedding = embeddings.embed_query(question)
    embedding_time = time.perf_counter() - embedding_start

    # Hybrid search
    search_start = time.perf_counter()

    result = supabase.rpc("hybrid_search", {
        "query_text": question,
        "query_embedding": query_embedding,
        "match_count": candidate_k,
        "rrf_k": 50,
    }).execute()

    search_time = time.perf_counter() - search_start

    # Convert search results to Documents
    documents = []

    with open("log/log_retrieval-docs.txt", "w", encoding="utf-8") as f:
        f.write(f"QUESTION: {question}\n")

    for row in result.data or []:
        metadata = row.get("metadata") or {}
        metadata["retrieval_score"] = row["hybrid_score"]

        document = Document(
            page_content=row["content"],
            metadata=metadata
        )

        documents.append(document)

        with open("log/log_retrieval-docs.txt", "a", encoding="utf-8") as f:
            f.write(
                f"\n--- DOCUMENT ---\n"
                f"{document.page_content}\n\n"
                f"METADATA:\n"
                f"{document.metadata}\n"
            )

    # Reranking
    rerank_start = time.perf_counter()

    documents = rerank(
        question,
        documents,
        top_k=rerank_k
    )

    rerank_time = time.perf_counter() - rerank_start

    # Log rerank scores
    with open("log/log_retrieval-docs.txt", "a", encoding="utf-8") as f:
        f.write("\n\n=== RERANK SCORES ===\n")

        for document in documents:
            f.write(
                f"score={document.metadata['rerank_score']:.4f} | "
                f"source={document.metadata.get('source')} | "
                f"page={document.metadata.get('page')}\n"
            )

    # Threshold filtering
    documents = [
        document
        for document in documents
        if document.metadata["rerank_score"] >= RERANK_THRESHOLD
    ]

    # Build context
    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    total_time = time.perf_counter() - start

    log = (
        f"question='{question}' "
        f"embedding={embedding_time:.3f}s | "
        f"search={search_time:.3f}s | "
        f"rerank={rerank_time:.3f}s | "
        f"threshold={RERANK_THRESHOLD:.4f} | "
        f"relevant={len(documents)} | "
        f"total={total_time:.3f}s\n"
    )

    print(f"[RETRIEVAL] {log}")

    with open("log/log_retrieval-time.txt", "a", encoding="utf-8") as f:
        f.write(log)

    return documents, context