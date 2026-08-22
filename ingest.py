import os
os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"

from ingestion.indexer import index_document
from config.settings import FILE_TO_INGEST

if __name__ == "__main__":
    file_path = FILE_TO_INGEST
    print(f'Indexing "{file_path}"...')
    index_document(file_path)