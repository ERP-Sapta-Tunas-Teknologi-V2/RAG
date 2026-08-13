from pathlib import Path
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader

def load_document(file_path: str) -> list[Document]:
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".txt": loader = TextLoader(str(path), encoding="utf-8")
    elif extension == ".pdf": loader = PyPDFLoader(str(path))
    elif extension == ".docx": loader = Docx2txtLoader(str(path))
    else: raise ValueError(f"Unsupported file type: {extension}")

    documents = loader.load()
    return documents