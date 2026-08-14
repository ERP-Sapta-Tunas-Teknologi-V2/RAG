# Memasukkan dokumen ke Supabase
from pathlib import Path

from ingestion.loader import load_document
from ingestion.splitter import split_documents
from rag.vectorstore import vectorstore

def index_document(file_path: str):
    print(f'Loading "{file_path}"...')
    documents = load_document(file_path)
    print(f"Loaded {len(documents)} document(s).")

    path = Path(file_path)
    source = path.name
    document_id = path.stem

    print("Creating chunks...")
    chunks = split_documents(documents, source=source, document_id=document_id)
    print(f"Created {len(chunks)} chunks.")

    print("Adding documents...")
    vectorstore.add_documents(chunks)
    print("Documents successfully indexed.")