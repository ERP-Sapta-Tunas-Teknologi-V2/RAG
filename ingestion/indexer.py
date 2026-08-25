# Memasukkan dokumen ke Supabase
from pathlib import Path
from datetime import datetime

from ingestion.cleaner import preprocessing
from ingestion.loader import load_document
from ingestion.splitter import StructureAwareChunker
from rag.vectorstore import add_documents

chunker = StructureAwareChunker(max_tokens=1000)

def index_document(file_path: str):
    path = Path(file_path)

    source = path.name
    document_id = path.stem
    uploaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f'Cleaning document...')
    markdown = preprocessing(file_path)
    print("Cleaned.")

    print(f"Loading document...")
    documents = load_document(markdown)
    print("Loaded.")

    print("Creating chunks...")
    chunks = chunker.split_document(documents, source, document_id, uploaded_at)
    print(f"Created {len(chunks)} chunks.")

    print("Adding documents...")
    result = add_documents(chunks)
    if result["failed"]: 
        print("Some chunks failed to process.")
    else: 
        print("Documents successfully added.")