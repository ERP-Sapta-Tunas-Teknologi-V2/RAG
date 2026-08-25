from pathlib import Path
import docx2md
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from config.settings import OLLAMA_BASE_URL, LLM_MODEL
llm = ChatOllama(model=LLM_MODEL, base_url=OLLAMA_BASE_URL, temperature=0)

header_prompt = ChatPromptTemplate.from_template("""
Anda adalah AI yang bertugas menentukan bagian teks yang seharusnya menjadi header. 
Tugas: Tentukan teks mana yang berfungsi sebagai header.

Teks:
"{markdown}"

Anda adalah AI yang bertugas menentukan bagian teks yang seharusnya menjadi header. 
Tugas: Tentukan teks mana yang berfungsi sebagai header.

Headers:
""")

rewrite_prompt = ChatPromptTemplate.from_template("""
Anda adalah AI yang bertugas menulis ulang teks berdasarkan hasil identifikasi header.

Tugas:
Tulis ulang isi teks dengan menambahkan `## ` di awal setiap teks yang telah didefinisikan sebagai header.

Aturan:
1. Jangan mengubah isi teks.
2. Jangan menghapus atau menambahkan informasi.
3. Pertahankan urutan dan struktur teks asli.
4. Hanya teks yang telah ditentukan sebagai header yang diberi prefix `## `.
5. Jangan memberikan `## ` pada teks yang bukan header.
6. Jika respons sebelumnya adalah `NONE`, jangan tambahkan header.
7. Kembalikan hanya teks yang telah ditulis ulang tanpa penjelasan tambahan.

Header:
{headers}

Teks:
{markdown}

Anda adalah AI yang bertugas menulis ulang teks berdasarkan hasil identifikasi header.

Tugas:
Tulis ulang isi teks dengan menambahkan `## ` di awal setiap teks yang telah didefinisikan sebagai header.

Aturan:
1. Jangan mengubah isi teks.
2. Jangan menghapus atau menambahkan informasi.
3. Pertahankan urutan dan struktur teks asli.
4. Hanya teks yang telah ditentukan sebagai header yang diberi prefix `## `.
5. Jangan memberikan `## ` pada teks yang bukan header.
6. Jika respons sebelumnya adalah `NONE`, jangan tambahkan header.
7. Kembalikan hanya teks yang telah ditulis ulang tanpa penjelasan tambahan.

Teks dengan header:
""")

def docx_to_md(path):
    markdown = docx2md.do_convert(path, use_md_table=True)
    return markdown

def has_headings(markdown):
    return bool(re.search(r"^#{1,6}\s+.+$", markdown, re.MULTILINE))

def h1_to_h2(markdown):
    markdown = re.sub(r"^# (?!#)", "## ", markdown, flags=re.MULTILINE)
    return markdown

def determine_headers(markdown):
    print("Determining headers...")
    messages = header_prompt.format_messages(markdown=markdown)
    response = llm.invoke(messages)
    headers = response.content
    return headers

def rewrite_with_headers(headers, markdown):
    print("Rewriting markdown...")
    messages = rewrite_prompt.format_messages(headers=headers, markdown=markdown)
    response = llm.invoke(messages)
    new_markdown = response.content
    return new_markdown

def preprocessing(file_path):
    path = Path(file_path)
    if path.suffix.lower() != ".docx": 
        raise ValueError(f"Unsupported file type: {path.suffix}")

    markdown = docx_to_md(path)

    if has_headings(markdown):
        new_markdown = h1_to_h2(markdown)
    else:
        headers = determine_headers(markdown)
        new_markdown = rewrite_with_headers(headers, markdown)

    return new_markdown