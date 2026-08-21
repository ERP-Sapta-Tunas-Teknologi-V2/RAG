from pathlib import Path
from docling.document_converter import DocumentConverter

def load_document(file_path: str):
    path = Path(file_path)

    if path.suffix.lower() not in {".pdf"}:
        raise ValueError(f"Unsupported file type: {path.suffix}")

    converter = DocumentConverter()
    result = converter.convert(str(path))

    return result.document