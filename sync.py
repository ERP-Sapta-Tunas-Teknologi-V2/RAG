import os
os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"

from pathlib import Path
from ingestion.indexer import index_document
from rag.vectorstore import get_document_ids, delete_document

SOURCE_DIR = Path("documents")
SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".docx"}

if __name__ == "__main__":
    source_files = {}

    for path in SOURCE_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        
        category = path.parent.name
        document_id = f"{category}:{path.stem}"
        source_files[document_id] = path

    source_ids = set(source_files)
    db_ids = get_document_ids()

    new_ids = source_ids - db_ids
    existing_ids = source_ids & db_ids
    deleted_ids = db_ids - source_ids

    print(f"New: {len(new_ids)} | Existing: {len(existing_ids)} | Deleted: {len(deleted_ids)}")

    for document_id in new_ids | existing_ids:
        print(f"[SYNC] {source_files[document_id]}")
        index_document(str(source_files[document_id]))

    for document_id in deleted_ids:
        print(f"[SYNC] Removing: {document_id}")
        delete_document(document_id)