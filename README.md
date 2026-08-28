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

# API Contract

## POST /api/chat

Endpoint untuk mengirim pertanyaan pengguna dan mendapatkan jawaban RAG secara streaming.

### Request

```http
POST /api/chat
Content-Type: application/json
```

Body:

```json
{
  "question": "..."
}
```

### Request Parameters

| Parameter  | Type   | Required | Description         |
| ---------- | ------ | -------- | ------------------- |
| `question` | string | Yes      | Pertanyaan pengguna |

### Validation

| Condition                   | Response |
| --------------------------- | -------- |
| `question` tidak dikirim    | `400`    |
| `question` bukan string     | `400`    |
| `question` kosong           | `400`    |
| `question` > 1000 karakter  | `400`    |
| terdeteksi prompt injection | `400`    |

Contoh:

```json
{
  "error": "question is required"
}
```

## Response Type

Endpoint memiliki dua kemungkinan response:

1. **Relevant chunks ditemukan**
   - HTTP `200`
   - Content-Type: `text/event-stream`
   - Response berupa SSE

2. **Tidak ada relevant chunks**
   - HTTP `200`
   - Content-Type: `application/json`
   - Response berupa fallback JSON

## Response (SSE)

Endpoint menggunakan Server-Sent Events (SSE) untuk response normal.

Content-Type:

```text
text/event-stream
```

Response terdiri dari beberapa event.

### 1. Metadata Event

Dikirim sebelum token jawaban.

```text
data: {"type":"metadata","sources":[...],"fallback":false}
```

Format:

```json
{
  "type": "metadata",
  "sources": [
    {
      "source": "...",
      "section_title": "...",
      "uploaded_at": "..."
    }
  ],
  "fallback": false
}
```

### 2. Token Event

Berisi potongan jawaban dari LLM.

```text
data: {"type":"token","content":"..."}
data: {"type":"token","content":"..."}
data: {"type":"token","content":"..."}
```

Format:

```json
{
  "type": "token",
  "content": "..."
}
```

Frontend harus menggabungkan seluruh `content` dari event `token` untuk membentuk jawaban lengkap.

### 3. Done Event

Menandakan streaming telah selesai.

```text
data: {"type":"done"}
```

Format:

```json
{
  "type": "done"
}
```

## Successful Response Flow

```text
POST /api/chat
        ↓
metadata
        ↓
token
        ↓
token
        ↓
token
        ↓
...
        ↓
done
```

Contoh lengkap:

```text
data: {"type":"metadata","sources":[{"source":"...","section_title":"...","uploaded_at":"..."}],"fallback":false}

data: {"type":"token","content":"..."}

data: {"type":"token","content":"..."}

data: {"type":"token","content":"..."}

data: {"type":"done"}
```

## Fallback Response (JSON)

Jika tidak ada chunk yang memenuhi threshold retrieval, backend tidak melakukan proses generation LLM dan mengembalikan JSON biasa (bukan SSE).

Response:

```json
{
  "question": "...",
  "answer": "Informasi tidak ditemukan dalam knowledge base. Silakan hubungi kontak kami.",
  "sources": [],
  "fallback": true
}
```

`fallback: true` menunjukkan bahwa tidak ditemukan informasi yang relevan dalam knowledge base.

Untuk response normal (SSE), field `fallback` dikirim di dalam metadata event dengan nilai:

```text
fallback: false
```

## Sources

`metadata.sources` (pada SSE) berisi source dari chunk yang benar-benar digunakan untuk menghasilkan jawaban.

Contoh:

```json
{
  "sources": [
    {
      "source": "...",
      "section_title": "...",
      "uploaded_at": "..."
    }
  ]
}
```

Frontend dapat menggunakan `source` untuk menampilkan nama dokumen sumber.

Field internal berikut tidak perlu digunakan oleh frontend:

```text
retrieval_score
rerank_score
document_id
chunk_index
fingerprint
content
embedding
```

## Context

`context` tidak dikirim ke frontend.

Context merupakan data internal RAG yang digunakan oleh backend untuk memberikan informasi kepada LLM.

Frontend menerima:

- `question` pada fallback response
- `token.content` untuk membentuk answer (response normal/SSE)
- `sources` melalui metadata event (response normal/SSE) atau field `sources` (fallback)
- `fallback` untuk mengetahui apakah response merupakan fallback

## Error Response

### 400 Bad Request

Contoh:

```json
{
  "error": "question is required"
}
```

atau:

```json
{
  "error": "question must not exceed 1000 characters"
}
```

atau:

```json
{
  "error": "invalid question"
}
```

### 500 Internal Server Error

Jika terjadi error pada backend:

```json
{
  "error": "Internal server error"
}
```

## Frontend Integration

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

Response menggunakan SSE (normal) atau JSON (fallback):

```text
metadata
→ token
→ token
→ token
→ ...
→ done
```

FE tidak perlu mengetahui:

- Supabase
- pgvector
- embedding model
- Voyage AI
- hybrid search
- reranker
- RRF
- chunking
- fingerprint
- context

Dengan demikian implementasi RAG di backend dapat berubah tanpa mengubah kontrak API FE.

Frontend menggunakan `fetch()` karena request `/api/chat` menggunakan method `POST` dan response (normal) berupa streaming.

Contoh (dengan buffer, aman terhadap SSE event yang terpotong di tengah network chunk):

```js
const response = await fetch("/api/chat", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    question: userQuestion
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

let buffer = "";
let answer = "";

while (true) {
  const {value, done} = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, {stream: true});

  const events = buffer.split("\n\n");
  buffer = events.pop();

  for (const event of events) {
    if (!event.startsWith("data: ")) continue;

    const data = JSON.parse(event.slice(6));

    if (data.type === "metadata") {
      console.log("Sources:", data.sources);
    }

    if (data.type === "token") {
      answer += data.content;
      console.log(answer);
    }

    if (data.type === "done") {
      console.log("Streaming selesai");
    }
  }
}
```

## Backend Internal Flow

```text
User Question
     ↓
Query Validation
     ↓
Hybrid Search
     ↓
Candidate Documents
     ↓
Reranking
     ↓
Threshold Filtering
     ↓
No Relevant Chunk?
     ├── Yes → Fallback Response
     │
     └── No
          ↓
       Sources
          ↓
       Dola Seed
          ↓
       Streaming
          ↓
       SSE
          ↓
       FE Widget
```

## Retrieval Configuration

Parameter retrieval merupakan konfigurasi internal backend dan tidak perlu dikirim oleh frontend.

| Parameter           | Value |
| ------------------- | ----: |
| Candidate documents |    10 |
| Reranked documents  |     3 |
| RRF k               |    50 |
| Rerank threshold    |   5.0 |

## API Contract Summary

| Item                  | Value                |
| ---------------------- | -------------------- |
| Endpoint              | `/api/chat`          |
| Method                | `POST`               |
| Request               | JSON                 |
| Normal response       | SSE                  |
| Fallback response     | JSON                 |
| Normal Content-Type   | `text/event-stream`  |
| Fallback Content-Type | `application/json`   |
| Query field           | `question`           |
| Streaming event       | `token`              |
| Source event          | `metadata`           |
| Completion event      | `done`               |
| Fallback field        | `fallback`           |
| Max query length      | 1000 characters      |

## Performance Logging

Retrieval mencatat:

```text
embedding
search
rerank
threshold
relevant
total
```

Log waktu:

```text
log/log_retrieval-time.txt
```

Log dokumen dan rerank score:

```text
log/log_retrieval-docs.txt
```

Log ini digunakan untuk QA dan monitoring latency retrieval.

## QA Retrieval

Performance retrieval dapat dievaluasi menggunakan log:

```text
log/log_retrieval-time.txt
log/log_retrieval-docs.txt
```

Metric utama:

```text
Embedding latency
Semantic/hybrid search latency
Reranking latency
Total retrieval latency
```

Tujuannya untuk mengetahui tahap mana yang menjadi bottleneck sebelum API digunakan pada FE widget production.

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