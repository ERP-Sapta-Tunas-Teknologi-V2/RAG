from pathlib import Path
import docx2md
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from transformers import AutoTokenizer

from config.settings import OLLAMA_BASE_URL, OLLAMA_LLM
llm = ChatOllama(model=OLLAMA_LLM, base_url=OLLAMA_BASE_URL, temperature=0)

TOKENIZER_MODEL = "BAAI/bge-m3"
MAX_BATCH_TOKENS = 1000

tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_MODEL)

header_prompt = ChatPromptTemplate.from_template("""
Anda adalah AI yang bertugas menentukan bagian teks yang seharusnya menjadi header.

Tugas:
Tentukan teks mana yang berfungsi sebagai header.

Aturan:
1. Hanya satu jenis header yang digunakan.
2. Kembalikan teks header persis seperti aslinya.
3. Jangan mengubah teks.
4. Jangan mengembalikan paragraf, tabel, atau isi biasa.
5. Jika tidak ada header, jawab `NONE`.
6. Kembalikan satu header per baris.
7. Jangan berikan penjelasan.

Teks:
{markdown}

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
    return docx2md.do_convert(path, use_md_table=True)

def has_headings(markdown):
    return bool(re.search(r"^#{1,6}\s+.+$", markdown, re.MULTILINE))

def h1_to_h2(markdown):
    return re.sub(r"^# (?!#)", "## ", markdown, flags=re.MULTILINE)

def count_tokens(text):
    return len(tokenizer.encode(text, add_special_tokens=False))

def is_table_row(line):
    stripped = line.strip()
    return (stripped.startswith("|") and stripped.endswith("|"))

def parse_atomic_blocks(markdown):
    lines = markdown.splitlines()

    blocks = []
    current = []
    in_table = False

    def flush():
        nonlocal current
        if current:
            text = "\n".join(current).strip()
            if text:
                blocks.append(text)
            current = []

    for line in lines:
        stripped = line.strip()

        if is_table_row(line):
            if not in_table:
                flush()
                in_table = True
            current.append(line)
            continue

        if in_table:
            flush()
            in_table = False

        if not stripped:
            flush()
            continue

        current.append(line)

    flush()
    return blocks

def split_large_table(table, max_tokens):
    lines = table.splitlines()

    if len(lines) <= 2:
        return [table]

    header = lines[:2]
    rows = lines[2:]

    parts = []
    current = header.copy()

    for row in rows:
        candidate = "\n".join(current + [row])
        if (len(current) > 2 and count_tokens(candidate) > max_tokens):
            parts.append("\n".join(current))
            current = header.copy()
        current.append(row)

    if len(current) > 2:
        parts.append("\n".join(current))

    return parts

def split_batches(markdown, max_tokens=MAX_BATCH_TOKENS):
    blocks = parse_atomic_blocks(markdown)

    batches = []

    current_batch = []
    current_tokens = 0

    for block in blocks:
        tokens = count_tokens(block)

        if (is_table_row(block.splitlines()[0]) and tokens > max_tokens):
            if current_batch:
                batches.append("\n\n".join(current_batch))
                current_batch = []
                current_tokens = 0

            table_parts = split_large_table(block, max_tokens)
            batches.extend(table_parts)
            continue

        if (tokens > max_tokens and not is_table_row(block.splitlines()[0])):
            if current_batch:
                batches.append("\n\n".join(current_batch))
                current_batch = []
                current_tokens = 0

            batches.append(block)
            continue

        if (current_batch and current_tokens + tokens > max_tokens):
            batches.append("\n\n".join(current_batch))
            current_batch = []
            current_tokens = 0

        current_batch.append(block)
        current_tokens += tokens

    if current_batch:
        batches.append("\n\n".join(current_batch))

    return batches

def compact_for_header_detection(markdown):
    blocks = parse_atomic_blocks(markdown)
    result = []

    for block in blocks:
        lines = block.splitlines()
        if lines and is_table_row(lines[0]):
            continue
        result.append(block)

    return "\n\n".join(result)

def determine_headers(markdown):
    print("Determining headers...")
    markdown = compact_for_header_detection(markdown)
    messages = header_prompt.format_messages(markdown=markdown)
    response = llm.invoke(messages)
    headers = response.content.strip()
    return headers

def add_headers(markdown, headers):
    if not headers or headers.strip().upper() == "NONE":
        return markdown

    header_set = {
        line.strip()
        for line in headers.splitlines()
        if line.strip()
    }

    lines = markdown.splitlines()
    result = []

    for line in lines:
        stripped = line.strip()

        if stripped in header_set:
            result.append(f"## {line}")
        else:
            result.append(line)

    return "\n".join(result)

def rewrite_with_headers(headers, markdown):
    print("Rewriting markdown...")
    messages = rewrite_prompt.format_messages(headers=headers, markdown=markdown)
    response = llm.invoke(messages)
    new_markdown = response.content.strip()
    return new_markdown

def preprocessing(file_path):
    path = Path(file_path)
    if path.suffix.lower() != ".docx":
        raise ValueError(f"Unsupported file type: {path.suffix}")

    markdown = docx_to_md(path)

    if has_headings(markdown):
        return h1_to_h2(markdown)

    batches = split_batches(markdown)
    results = []
    for i, batch in enumerate(batches, 1):
        print(f"[PREPROCESS] Batch {i}/{len(batches)} | tokens={count_tokens(batch)}")
        headers = determine_headers(batch)
        print(f"[HEADER] Batch {i}: {headers}")
        results.append(add_headers(batch, headers))

    return "\n\n".join(results)