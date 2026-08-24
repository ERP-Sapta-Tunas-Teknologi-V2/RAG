from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config.settings import OLLAMA_BASE_URL, LLM_MODEL
llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)

prompt = ChatPromptTemplate.from_template("""
Anda adalah chatbot perusahaan.

Jawablah pertanyaan berdasarkan context yang diberikan.
Jika informasi tidak terdapat dalam context, jawab: 
"Informasi tidak ditemukan dalam knowledge base. Silakan hubungi kontak kami."
Jangan membuat informasi yang tidak terdapat dalam context.
Jangan sebut "context".

Context:
{context}

Pertanyaan:
{question}

Jawaban:
""")

def generate_answer(question: str, documents):
    context = "\n\n".join(
        document.page_content
        for document in documents
    )
    messages = prompt.format_messages(context=context, question=question)
    response = llm.invoke(messages)
    return response.content, context