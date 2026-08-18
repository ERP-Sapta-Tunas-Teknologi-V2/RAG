import os
os.environ["TORCHDYNAMO_DISABLE"] = "1"
os.environ["TORCH_COMPILE_DISABLE"] = "1"

from ingestion.indexer import index_document

if __name__ == "__main__":
    index_document("path/to/file.pdf")