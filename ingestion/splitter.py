from langchain_core.documents import Document
from docling.chunking import HybridChunker
from transformers import AutoTokenizer

EMBEDDING_MODEL = "BAAI/bge-m3"

class DoclingHybridChunker:
    def __init__(self, max_tokens: int = 1000):
        self.tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL)
        self.chunker = HybridChunker(tokenizer=self.tokenizer, max_tokens=max_tokens, merge_peers=True,)

    def split_documents(self, docling_doc, source: str, document_id: str) -> list[Document]:
        chunks = list(self.chunker.chunk(dl_doc=docling_doc))
        documents = []

        for index, chunk in enumerate(chunks):
            # Tambahkan heading/context hierarchy
            contextualized_text = self.chunker.contextualize(chunk=chunk)

            pages = []
            if chunk.meta and chunk.meta.doc_items:
                for item in chunk.meta.doc_items:
                    if item.prov:
                        for prov in item.prov:
                            if prov.page_no not in pages:
                                pages.append(prov.page_no)

            metadata = {"source": source, "document_id": document_id, "chunk_index": index, "page": pages}
            documents.append(Document(page_content=contextualized_text, metadata=metadata))

        return documents