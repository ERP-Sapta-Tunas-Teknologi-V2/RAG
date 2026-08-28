# RAG Chatbot API

API Retrieval-Augmented Generation (RAG) untuk melakukan pencarian dokumen dan menghasilkan jawaban berdasarkan konten yang telah di-index.

## Stack

- Framework: Flask
- Database: Supabase
- Vector database: pgvector
- RAG framework: LangChain
- LLM SDK: BytePlus Ark SDK
- LLM: Dola Seed
- Embedding: Voyage AI
- Document processing: Docling

# Setup

## A. Buat database

1. Buka [Supabase](https://supabase.com/).
2. Klik `Start your project`.
3. Klik `New project`.
4. Isi konfigurasi:
   - `Project name`: `rag-chatbot`
   - `Database password`: sesuai kebutuhan
   - `Enable Data API`: aktif
   - `Automatically expose new tables`: nonaktif
   - `Enable automatic RLS`: aktif
5. Klik `Create new project`.

## B. Aktifkan pgvector

1. Buka `Database` pada sidebar kiri.
2. Klik `Extensions`.
3. Cari `vector`.
4. Aktifkan extension `vector`.
5. Gunakan schema default dan jangan mengganti schema.

## C. Konfigurasi environment

1. Buka `Project Overview` di Supabase.
2. Salin:
   - `Project URL`
   - `Publishable key`
3. Masukkan ke file `.env`.

## D. Buat tabel dan function

1. Buka `SQL Editor` di Supabase.
2. Masukkan isi `supabase.sql`.
3. Klik `Run`.
4. Buka `Table Editor`
5. Pastikan tabel `documents` berhasil dibuat.

# Instalasi

Buat virtual environment

```bash
python -m venv .venv
```

Aktifkan virtual environment. Terminal:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

# Menambahkan Dokumen

Jalankan proses indexing sesuai kebutuhan:

```bash
python ingest.py
```

Untuk melakukan sinkronisasi seluruh dokumen:

```bash
python sync.py
```

## Sinkronisasi Dokumen

`sync.py` membandingkan source dokumen dengan data di vector database.

Status dokumen:

```text
New
Existing
Deleted
```

Contoh:

```text
New: 2 | Existing: 15 | Deleted: 1
```

Untuk dokumen baru atau existing:

```text
index_document()
```

dipanggil kembali.

Untuk dokumen yang sudah tidak ada di source:

```text
delete_document()
```

dipanggil untuk menghapus seluruh embedding berdasarkan `document_id`.

## Scheduler

Scheduler dapat menjalankan sinkronisasi berdasarkan kategori dokumen:

### Konten dinamis

Untuk konten dinamis seperti berita, jalankan sinkronisasi harian.

Contoh:

```text
Daily
01:00
→ sync berita
```

### Konten statis

Untuk konten statis seperti SOP, jalankan sinkronisasi mingguan.

Contoh:

```text
Weekly
Sunday 02:00
→ sync dokumen statis
```

# Menjalankan API

Pastikan environment variable telah dikonfigurasi pada `.env`.

Kemudian jalankan Flask:

```bash
flask run --debug
```

Default API:

```text
http://127.0.0.1:5000
```

Root endpoint:

```http
GET /
```

Response:

```json
{
  "message": "RAG Service is running"
}
```

## Postman

### Chat

1. Pilih method `POST`.
2. Masukkan URL:

```text
http://127.0.0.1:5000/api/chat
```

3. Pilih `Body`.
4. Pilih `raw`.
5. Pilih format `JSON`.
6. Masukkan:

```json
{
  "question": "..."
}
```

7. Klik `Send`.

### Export log

1. Pilih method `GET`.
2. Masukkan URL:

```text
http://127.0.0.1:5000/api/logs/export
```

3. Karena fitur export log hanya dibatasi untuk role Marketing dan Product, pilih `Headers` dan masukkan `"X-User-Role"` di `Key` dan `"Marketing"` atau `"Product"` di `Value`.

4. Klik `Send`.

Untuk mem-filter tanggal, masukkan parameter `start` dan/atau `end`.

Format:

```
http://127.0.0.1:5000/api/logs/export?start=YYYY-MM-DD&end=YYYY-MM-DD
```

## cURL

### Chat

```bash
curl -X POST "http://127.0.0.1:5000/api/chat" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"...\"}"
```

### Export log

```bash
curl -X GET "http://127.0.0.1:5000/api/logs/export" \
  -H "X-User-Role: Marketing" \
  -o query_logs.csv
```

# Test

Jalankan file test dalam folder `tests/` dengan command:

```
pytest tests/[nama file].py -v
```

# Database

Tabel utama:

```text
documents
```

Kolom:

| Column | Type | Description |
|---|---|---|
| `id` | bigint | Primary key |
| `content` | text | Isi chunk |
| `metadata` | jsonb | Metadata chunk |
| `document_id` | text | Identitas dokumen |
| `chunk_index` | int | Index chunk dalam dokumen |
| `fingerprint` | text | SHA-256 content |
| `embedding` | vector(1024) | Vector embedding |
| `fts` | tsvector | Full-text search index |

Function utama:

```text
match_documents()
hybrid_search()
```

# Project Flow

```text
Document
   ↓
Preprocessing
   ↓
Document Loader
   ↓
StructureAwareChunker
   ↓
Fingerprint
   ↓
Batch Embedding
   ↓
Supabase / pgvector
   ↓
Hybrid Search
   ↓
Reranker
   ↓
LLM
   ↓
/api/chat
   ↓
FE Widget
```