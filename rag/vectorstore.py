# Hubungkan LangChain dengan Supabase

from supabase.client import create_client

from config.settings import SUPABASE_URL, SUPABASE_KEY
from rag.embeddings import embeddings

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_documents(chunks):
    inserted = 0
    skipped = 0

    for chunk in chunks:
        metadata = chunk.metadata.copy()

        document_id = metadata.pop("document_id")
        fingerprint = metadata.pop("fingerprint")

        existing = (
            supabase_client
            .table("documents")
            .select("id")
            .eq("document_id", document_id)
            .eq("fingerprint", fingerprint)
            .limit(1)
            .execute()
        )

        if existing.data:
            skipped += 1
            continue

        embedding = embeddings.embed_query(chunk.page_content)

        supabase_client.table("documents").insert({
            "content": chunk.page_content,
            "metadata": metadata,
            "document_id": document_id,
            "fingerprint": fingerprint,
            "embedding": embedding
        }).execute()

        inserted += 1

    print(f"Inserted: {inserted} | Skipped: {skipped}")