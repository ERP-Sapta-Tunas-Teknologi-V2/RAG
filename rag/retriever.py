from supabase import create_client
from langchain_core.documents import Document

from config.settings import SUPABASE_URL, SUPABASE_KEY
from rag.embeddings import embeddings

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def hybrid_retrieve(question: str, k: int = 10) -> list[Document]:
    query_embedding = embeddings.embed_query(question)

    result = supabase.rpc("hybrid_search", {
        "query_text": question,
        "query_embedding": query_embedding,
        "match_count": k,
        "rrf_k": 50,
    }).execute()

    documents = []

    for row in result.data or []:
        metadata = row.get("metadata") or {}
        metadata["retrieval_score"] = row["hybrid_score"]

        document = Document(
            page_content=row["content"],
            metadata=metadata
        )

        documents.append(document)

    return documents