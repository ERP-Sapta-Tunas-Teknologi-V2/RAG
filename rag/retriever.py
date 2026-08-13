from rag.vectorstore import vectorstore

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})