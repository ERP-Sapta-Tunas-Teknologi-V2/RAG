from supabase import create_client
from langchain_core.documents import Document

from config.settings import SUPABASE_URL, SUPABASE_KEY
from rag.embeddings import embeddings
from rag.reranker import rerank

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def hybrid_retrieve(question: str, candidate_k: int = 10, rerank_k: int = 3) -> list[Document]:
    query_embedding = embeddings.embed_query(question)

    result = supabase.rpc("hybrid_search", {
        "query_text": question,
        "query_embedding": query_embedding,
        "match_count": candidate_k,
        "rrf_k": 50,
    }).execute()

    documents = []

    for row in result.data or []:
        metadata = row.get("metadata") or {}
        metadata["retrieval_score"] = row["hybrid_score"]
        documents.append(Document(page_content=row["content"], metadata=metadata))

    return rerank(question, documents, top_k=rerank_k)