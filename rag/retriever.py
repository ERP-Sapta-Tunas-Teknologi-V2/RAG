from supabase import create_client
from langchain_core.documents import Document

from rag.vectorstore import vectorstore
from config.settings import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

def retrieve_with_neighbors(question: str, neighbor_count: int = 1):
    # 1. Vector search
    relevant_documents = retriever.invoke(question)

    results = []

    # 2. Expand setiap hasil
    for document in relevant_documents:
        metadata = document.metadata

        document_id = metadata.get("document_id")
        chunk_index = metadata.get("chunk_index")

        if document_id is None:
            results.append(document)
            continue
        if chunk_index is None:
            results.append(document)
            continue

        start_index = max(0, chunk_index - neighbor_count)
        end_index = chunk_index + neighbor_count

        response = supabase.rpc("get_neighbor_chunks", {
            "p_document_id": document_id,
            "p_start_index": start_index,
            "p_end_index": end_index,
        }).execute()

        for row in response.data:
            results.append(
                Document(
                    page_content=row["content"],
                    metadata=row["metadata"],
                )
            )

    # 3. Remove duplicate chunks
    unique = {}

    for document in results:
        metadata = document.metadata
        key = (metadata.get("document_id"), metadata.get("chunk_index"))
        unique[key] = document

    results = list(unique.values())

    # 4. Sort berdasarkan posisi dokumen
    results.sort(
        key=lambda document: (
            document.metadata.get("document_id", ""),
            document.metadata.get("chunk_index", 0),
        )
    )

    return results