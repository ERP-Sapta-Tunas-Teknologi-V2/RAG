# Memasukkan dokumen ke Supabase
from pathlib import Path

from ingestion.cleaner import preprocessing
from ingestion.loader import load_markdown, load_document
from ingestion.splitter import StructureAwareChunker
from rag.vectorstore import vectorstore

chunker = StructureAwareChunker(max_tokens=1000)

def index_document(file_path: str):
    if "documents/sop" in file_path:
        print(f'Cleaning document...')
        markdown = preprocessing(file_path)
        print("Cleaned.")

        print(f"Loading document...")
        documents = load_markdown(markdown)

    elif "documents/datasheet" in file_path:
        print(f"Loading document...")
        documents = load_document(file_path)

    print("Loaded.")

    path = Path(file_path)
    source = path.name
    document_id = path.stem

    print("Creating chunks...")
    chunks = chunker.split_documents(documents, source=source, document_id=document_id)
    print(f"Created {len(chunks)} chunks.")

    print("Adding documents...")
    vectorstore.add_documents(chunks)
    print("Documents successfully added.")