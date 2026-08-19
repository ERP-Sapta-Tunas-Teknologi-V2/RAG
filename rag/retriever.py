from supabase import create_client
from langchain_core.documents import Document

from config.settings import SUPABASE_URL, SUPABASE_KEY
from rag.embeddings import embeddings
from rag.reranker import rerank
from rag.retrieval_agent import judge_retrieval

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def hybrid_search(question: str, candidate_k: int = 20) -> list[Document]:
    query_embedding = embeddings.embed_query(question)

    result = supabase.rpc("hybrid_search", {
        "query_text": question, 
        "query_embedding": query_embedding, 
        "match_count": candidate_k, 
        "rrf_k": 50
    }).execute()

    documents = []

    for row in result.data or []:
        metadata = row.get("metadata") or {}
        metadata["retrieval_score"] = row["hybrid_score"]
        documents.append(Document(page_content=row["content"], metadata=metadata))

    return documents

def get_next_chunks(document_id: str, chunk_index: int, count: int = 3) -> list[Document]:
    result = (supabase
        .table("documents")
        .select("content, metadata")
        .eq("metadata->>document_id", document_id)
        .gt("metadata->>chunk_index", str(chunk_index))
        .order("metadata->>chunk_index")
        .limit(count)
        .execute()
    )

    documents = []

    for row in result.data or []:
        metadata = row.get("metadata") or {}
        documents.append(Document(page_content=row["content"], metadata=metadata))

    return documents

def get_previous_chunks(document_id: str, chunk_index: int, count: int = 3) -> list[Document]:
    result = (supabase
        .table("documents")
        .select("content, metadata")
        .eq("metadata->>document_id", document_id)
        .lt("metadata->>chunk_index", str(chunk_index))
        .order("metadata->>chunk_index", desc=True)
        .limit(count)
        .execute()
    )

    documents = []

    for row in reversed(result.data or []):
        metadata = row.get("metadata") or {}
        documents.append(Document(page_content=row["content"], metadata=metadata))

    return documents

def hybrid_retrieve(question: str, candidate_k: int = 20, rerank_k: int = 10, max_iterations: int = 3) -> list[Document]:
    documents = hybrid_search(question, candidate_k)
    documents = rerank(question, documents, top_k=rerank_k)
    selected = {document.metadata.get("chunk_index"): document for document in documents}

    for _ in range(max_iterations):
        decision = judge_retrieval(question, documents)
        action = decision.get("action")
        if action == "answer": break

        anchor = decision.get("anchor_chunk_index")
        count = min(int(decision.get("count", 3)), 5)

        anchor_document = next(
            (document for document in documents if document.metadata.get("chunk_index") == anchor),
            None
        )
        if not anchor_document: break

        document_id = anchor_document.metadata.get("document_id")

        if action == "next_chunks":
            new_documents = get_next_chunks(document_id, anchor, count)
        elif action == "previous_chunks":
            new_documents = get_previous_chunks(document_id, anchor, count)
        else:
            break

        for document in new_documents:
            chunk_index = document.metadata.get("chunk_index")

            if chunk_index not in selected:
                selected[chunk_index] = document

        documents = rerank(question, list(selected.values()), top_k=rerank_k)

    return documents