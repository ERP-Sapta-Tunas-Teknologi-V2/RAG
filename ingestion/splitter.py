from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(documents, source: str, document_id: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = splitter.split_documents(documents)

    for index, chunk in enumerate(chunks):
        chunk.metadata["source"] = source
        chunk.metadata["document_id"] = document_id
        chunk.metadata["chunk_index"] = index

    return chunks