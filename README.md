# RAG Chatbot API

API Retrieval-Augmented Generation (RAG) untuk melakukan pencarian dokumen dan menghasilkan jawaban berdasarkan konten yang telah di-index.

## Stack

- Framework: Flask
- Database: Supabase
- Vector database: pgvector
- RAG framework: LangChain
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

## Chunking

Dokumen dipecah menggunakan `StructureAwareChunker`.

Default maximum chunk:

```text
1000 tokens
```

Setiap chunk menyimpan metadata:

```text
source
document_id
chunk_index
section_title
uploaded_at
fingerprint
```

`fingerprint` menggunakan SHA-256 dari isi chunk dan digunakan untuk mendeteksi perubahan isi.

## Deduplication

Setiap chunk memiliki:

```text
document_id
chunk_index
fingerprint
```

Database memiliki unique constraint:

```text
document_id + chunk_index
```

Jika dokumen di-index kembali:

- Chunk dengan fingerprint yang sama → `Skipped`
- Chunk baru → `Inserted`
- Chunk dengan fingerprint berbeda → `Updated`
- Chunk yang sudah tidak ada pada source → `Deleted`

Contoh output:

```text
Inserted: 5 | Updated: 2 | Skipped: 43 | Failed: 0 | Deleted: 1
```

## Embedding

Embedding dilakukan secara batch.

Konfigurasi Voyage AI:

```text
MAX_RPM = 3
MAX_TPM = 10,000
TARGET_BATCH_TOKENS = 9,000
MAX_RETRIES = 3
```

Batch dibuat berdasarkan jumlah token agar tidak melebihi batas token yang ditentukan.

Jika terjadi:

- rate limit
- timeout
- connection error

batch akan dicoba kembali sampai batas `MAX_RETRIES`.

Chunk yang tetap gagal tidak dimasukkan ke database dan dilaporkan pada akhir proses.

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

### Scheduler

Scheduler dapat menjalankan sinkronisasi berdasarkan kategori dokumen:

#### Konten dinamis

Untuk konten dinamis seperti berita, jalankan sinkronisasi harian.

Contoh:

```text
Daily
01:00
→ sync berita
```

#### Konten statis

Untuk konten statis seperti SOP, jalankan sinkronisasi mingguan.

Contoh:

```text
Weekly
Sunday 02:00
→ sync dokumen statis
```

# Menjalankan API

Pastikan Ollama berjalan pada:

```text
http://localhost:11434
```

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

## API Retrieval

### POST /api/chat

Endpoint untuk mengirim pertanyaan pengguna dan mendapatkan jawaban berdasarkan dokumen yang tersedia.

### Request

URL:

```text
http://127.0.0.1:5000/api/chat
```

Method:

```text
POST
```

Header:

```text
Content-Type: application/json
```

Body:

```json
{
  "question": "..."
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `question` | string | Yes | Pertanyaan pengguna |

### Retrieval Pipeline

Request diproses melalui:

```text
Question
   ↓
Query Embedding
   ↓
Supabase Hybrid Search
   ├── Full-text search
   └── Semantic/vector search
   ↓
RRF
   ↓
Candidate Documents
   ↓
Reranking
   ↓
LLM
   ↓
Answer + Sources
```

Konfigurasi retrieval:

| Parameter | Value |
|---|---:|
| Candidate documents | 10 |
| Reranked documents | 3 |
| RRF k | 50 |

Parameter tersebut merupakan konfigurasi internal backend dan tidak perlu dikirim oleh FE.

### Response

Response API:

```json
{
  "question": "...",
  "answer": "...",
  "sources": [
    {
      "source": "...",
      "section_title": "...",
      "uploaded_at": "..."
    }
  ]
}
```

### Response Parameters

| Field | Type | Description |
|---|---|---|
| `question` | string | Pertanyaan yang dikirim |
| `answer` | string | Jawaban yang dihasilkan LLM |
| `sources` | array | Dokumen yang digunakan sebagai sumber |
| `sources[].source` | string | Nama file sumber |
| `sources[].section_title` | string/null | Judul section |
| `sources[].uploaded_at` | string | Waktu dokumen di-index |

`context` dan `retrieval_score` merupakan data internal backend dan tidak perlu digunakan oleh FE.

## Error Response

### 400 Bad Request

Jika `question` tidak dikirim atau kosong:

```json
{
  "error": "question is required"
}
```

### 500 Internal Server Error

Jika terjadi error pada proses retrieval atau answer generation:

```json
{
  "error": "Internal server error"
}
```

## Postman

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

7. Pilih `Send`.

## cURL

```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"...\"}"
```

# Frontend Integration

FE widget hanya perlu berkomunikasi dengan satu endpoint:

```text
POST /api/chat
```

Request:

```json
{
  "question": "..."
}
```

Response utama:

```json
{
  "question": "...",
  "answer": "...",
  "sources": []
}
```

FE tidak perlu mengetahui:

- Supabase
- pgvector
- embedding model
- Voyage AI
- Ollama
- hybrid search
- reranker
- RRF
- chunking
- fingerprint

Dengan demikian implementasi RAG di backend dapat berubah tanpa mengubah kontrak API FE.

## Performance Logging

Retrieval mencatat waktu:

```text
embedding
search
rerank
total
```

Log disimpan di:

```text
log/log_retrieval.txt
```

Format:

```text
embedding = waktu query embedding
search    = waktu Supabase hybrid search
rerank    = waktu reranking
total     = total waktu retrieval
```

Log ini digunakan untuk QA dan monitoring latency retrieval.

## QA Retrieval

Performance retrieval dapat dievaluasi menggunakan log:

```text
log/log_retrieval.txt
```

Metric utama:

```text
Embedding latency
Semantic/hybrid search latency
Reranking latency
Total retrieval latency
```

Tujuannya untuk mengetahui tahap mana yang menjadi bottleneck sebelum API digunakan pada FE widget production.

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