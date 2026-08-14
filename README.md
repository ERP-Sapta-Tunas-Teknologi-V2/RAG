# Stack

- Framework: Flask
- Database: Supabase
- pgvector
- LangChain
- Ollama

# Setup

## A. Buat database

1. Buka https://supabase.com/.

2. `Start your project`

3. `New project`

4. `Project name`: rag-chatbot

   `Database password`: rag-chatbot

   ☑ `Enable Data API`
   ☐ `Automatically expose new tables`
   ☑ `Enable automatic RLS`

5. `Create new project`

## B. Aktifkan `pgvector`

1. Klik `Database` di sidebar kiri (luar).

2. Klik `Extensions` di sidebar kiri (dalam).

3. Cari `vector` di kolom `NAME` (paling kiri).

4. Klik switch on di kolom `ENABLED`.

5. `Enable extension` (tidak ganti schema).

## C. Copy

1. Klik `Project Overview` di sidebar kiri (luar).

2. Di bawah `rag-chatbot`, klik `Copy`.

3. Klik `Project URL` dan `Publishable key`.

4. Paste di `.env`.

## D. Buat tabel

1. Klik `SQL Editor` di sidebar kiri (luar).

2. Masukkan SQL.

3. Klik `Save` atau tekan `CTRL + V`.

4. Klik `Run` atau tekan `CTRL + Enter`.

5. Di sidebar kiri (dalam), klik kanan pada query, klik `Rename query`.

6. Lihat tabel di `Database` di sidebar kiri (luar).

# Eksekusi

## Buat virtual environment

1. `python -m venv .venv`

2. `pip install -r requirements.txt`

## Tambahkan dokumen

1. Masukkan dokumen ke `RAG/documents`. Tipe file yang didukung saat ini adalah `.txt`, `.pdf`, dan `.docx`.

2. Masukkan path dokumen ke `ingest.py`.

3. Run command `python ingest.py`.

4. Run `select * from documents;` di SQL Supabase.

## Run

1. Pastikan Ollama berjalan di http://localhost:11434.

2. Run command `flask run --debug`.

## Postman

1. `POST` `http://127.0.0.1:5000/api/chat`

2. `Body` > `raw`

3. `{"question": "..."}`

4. `Send`