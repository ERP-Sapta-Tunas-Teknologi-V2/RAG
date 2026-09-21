# import os
# os.environ["TORCHDYNAMO_DISABLE"] = "1"
# os.environ["TORCH_COMPILE_DISABLE"] = "1"

# from ingestion.indexer import index_document

# if __name__ == "__main__":
#     file_path = "path/to/file"
#     print(f'Indexing "{file_path}"...')
#     index_document(file_path)

import os
os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"

from pathlib import Path
from ingestion.indexer import index_document

if __name__ == "__main__":
    data_dir = Path("path/to/file")  # folder tempat dokumen kamu
    for file_path in data_dir.iterdir():
        if file_path.is_file():
            print(f'Indexing "{file_path}"...')
            index_document(str(file_path))