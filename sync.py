import os
os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"

from pathlib import Path
from ingestion.indexer import index_document
from rag.vectorstore import get_document_ids, delete_document

SOURCE_DIR = Path("documents")
SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".docx"}

def sync_documents(category=None):
    source_files = {}

    for path in SOURCE_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS: 
            continue

        file_category = path.parent.name
        if category and file_category != category: 
            continue

        document_id = f"{file_category}:{path.stem}"
        source_files[document_id] = path

    source_ids = set(source_files)
    db_ids = get_document_ids()
    if category: 
        db_ids = {doc_id for doc_id in db_ids if doc_id.startswith(f"{category}:")}

    new_ids = source_ids - db_ids
    existing_ids = source_ids & db_ids
    deleted_ids = db_ids - source_ids

    print(f"[SYNC:{category or 'all'}] New: {len(new_ids)} | Existing: {len(existing_ids)} | Deleted: {len(deleted_ids)}")

    for document_id in new_ids | existing_ids:
        print(f"\n[SYNC] {source_files[document_id]}")
        index_document(str(source_files[document_id]))

    for document_id in deleted_ids:
        print(f"[SYNC] Removing: {document_id}")
        delete_document(document_id)

if __name__ == "__main__":
    sync_documents()