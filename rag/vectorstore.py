# Hubungkan LangChain dengan Supabase

from supabase.client import create_client

from config.settings import SUPABASE_URL, SUPABASE_KEY
from rag.embeddings import embeddings

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

def add_documents(chunks):
    for chunk in chunks:
        document_id = chunk.metadata.pop("document_id")
        fingerprint = chunk.metadata.pop("fingerprint")

        embedding = embeddings.embed_query(chunk.page_content)
        
        supabase_client.table("documents").insert({
            "content": chunk.page_content,
            "metadata": chunk.metadata,
            "document_id": document_id,
            "fingerprint": fingerprint,
            "embedding": embedding
        }).execute()