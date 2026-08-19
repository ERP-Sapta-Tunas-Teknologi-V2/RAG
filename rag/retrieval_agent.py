import json
from langchain_ollama import ChatOllama

from config.settings import OLLAMA_BASE_URL, LLM_MODEL
llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)

JUDGE_PROMPT = """
Anda adalah retrieval agent untuk chatbot dokumen perusahaan.

Tugas Anda menentukan apakah context yang tersedia sudah cukup untuk menjawab pertanyaan.

Perhatikan metadata:
- chunk_index menunjukkan urutan chunk dalam dokumen.
- section menunjukkan section dokumen.
- section_title menunjukkan judul section.

Jika sebuah chunk merupakan awal section dan pertanyaan meminta informasi yang kemungkinan berupa isi dari section tersebut, 
periksa apakah informasi mungkin berlanjut ke chunk berikutnya.

Jangan menjawab pertanyaan pengguna. Anda hanya menentukan tindakan retrieval.

Pilihan action:
1. "answer" jika context sudah cukup.
2. "next_chunks" jika perlu mengambil chunk setelah chunk tertentu.
3. "previous_chunks" jika perlu mengambil chunk sebelum chunk tertentu.

Jika memilih next_chunks atau previous_chunks, tentukan:
- anchor_chunk_index
- count

Output HANYA JSON valid dengan key: action, anchor_chunk_index, count, reason. Seperti ini:
{{
  "action": ,
  "anchor_chunk_index": ,
  "count": ,
  "reason": 
}}

Pertanyaan:
{question}

Context:
{context}

JSON:
"""

def judge_retrieval(question, documents):
    context = "\n\n".join(
        f"""[
            chunk_index={document.metadata.get('chunk_index')}, 
            section={document.metadata.get('section')}, 
            section_title={document.metadata.get('section_title')}
        ]\n{document.page_content}"""
        for document in documents
    )

    prompt = JUDGE_PROMPT.format(question=question, context=context)
    response = llm.invoke(prompt)

    text = response.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        print(json.loads(text))
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "action": "answer", 
            "anchor_chunk_index": None, 
            "count": 0, 
            "reason": "Invalid retrieval decision."
        }