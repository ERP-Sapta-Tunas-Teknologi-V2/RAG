# Memasukkan dokumen ke Supabase

from ingestion.loader import load_document
from ingestion.splitter import split_documents
from rag.vectorstore import vectorstore

def index_document(file_path: str):
    print(f'Loading "{file_path}"...')
    documents = load_document(file_path)
    print(f"Loaded {len(documents)} document(s)")

    print("Creating chunks...")
    chunks = split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    print("Adding documents...")
    vectorstore.add_documents(chunks)
    print("Documents successfully indexed.")