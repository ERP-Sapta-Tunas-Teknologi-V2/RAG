# Memasukkan dokumen ke Supabase
from pathlib import Path

from ingestion.loader import load_document
from ingestion.splitter import DoclingHybridChunker
from rag.vectorstore import vectorstore

chunker = DoclingHybridChunker(max_tokens=1000)

def index_document(file_path: str):
    print(f'Loading "{file_path}"...')
    documents = load_document(file_path)
    print(f"Loaded document.")

    path = Path(file_path)
    source = path.name
    document_id = path.stem

    print("Creating chunks...")
    chunks = chunker.split_documents(documents, source=source, document_id=document_id)
    print(f"Created {len(chunks)} chunks.")

    print("Adding documents...")
    vectorstore.add_documents(chunks)
    print("Documents successfully indexed.")