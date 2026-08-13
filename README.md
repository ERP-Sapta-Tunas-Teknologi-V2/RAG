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

6. Klik `Database` di sidebar kiri (luar).

7. Klik `Extensions` di sidebar kiri (dalam).

8. Cari `vector` di kolom `NAME` (paling kiri).

9. Klik switch on di kolom `ENABLED`.

10. `Enable extension` (tidak ganti schema).

## C. Copy

11. Klik `Project Overview` di sidebar kiri (luar).

12. Di bawah `rag-chatbot`, klik `Copy`.

13. Klik `Project URL` dan `Publishable key`.

14. Paste di `.env`.

## D. Buat tabel

15. Klik `SQL Editor` di sidebar kiri (luar).

16. Masukkan SQL.

17. Klik `Save` atau tekan `CTRL + V`.

18. Klik `Run` atau tekan `CTRL + Enter`.

19. Di sidebar kiri (dalam), klik kanan pada query, klik `Rename query`.

20. Lihat tabel di `Database` di sidebar kiri (luar).

# Eksekusi

## Tambahkan dokumen

1. Masukkan dokumen ke `RAG/documents`. Tipe file yang didukung saat ini adalah `.txt`, `.pdf`, dan `.docx`.

2. Masukkan path dokumen ke `ingest.py`.

3. Run command `python ingest.py`.

## Run

1. Pastikan Ollama berjalan di http://localhost:11434.

2. Run command `flask run --debug`.

## Postman

1. `POST` `http://127.0.0.1:5000/api/chat`

2. `Body` > `raw`

3. `{"question": "..."}`

4. `Send`
