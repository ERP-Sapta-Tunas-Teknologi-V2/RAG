# Hubungkan LangChain dengan Supabase

from supabase.client import create_client

from config.settings import SUPABASE_URL, SUPABASE_KEY
from rag.embeddings import embeddings

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
BATCH_SIZE = 32

def add_documents(chunks):
    inserted = 0
    skipped = 0
    pending = []

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

        pending.append({
            "chunk": chunk,
            "document_id": document_id,
            "fingerprint": fingerprint,
            "metadata": metadata
        })

    total_batches = (len(pending) + BATCH_SIZE - 1) // BATCH_SIZE

    print(
        f"New chunks: {len(pending)} | "
        f"Batches: {total_batches} | "
        f"Batch size: {BATCH_SIZE}"
    )

    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start:start + BATCH_SIZE]
        texts = [item["chunk"].page_content for item in batch]

        print(
            f"Embedding batch "
            f"{start // BATCH_SIZE + 1} | "
            f"{len(batch)} chunks"
        )

        vectors = embeddings.embed_documents(texts)

        rows = []
        for item, vector in zip(batch, vectors):
            rows.append({
                "content": item["chunk"].page_content,
                "metadata": item["metadata"],
                "document_id": item["document_id"],
                "fingerprint": item["fingerprint"],
                "embedding": vector
            })

        supabase_client.table("documents").insert(rows).execute()
        inserted += len(rows)

    print(f"Inserted: {inserted} | Skipped: {skipped}")