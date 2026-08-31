# Rate Limit Policy

## Objective

Membatasi jumlah request chatbot dari setiap IP untuk mencegah abuse, burst traffic, dan penggunaan resource secara berlebihan.

## Rate Limit

| Parameter                      | Policy                                                                   |
| ------------------------------ | ------------------------------------------------------------------------ |
| Endpoint                       | `POST /api/chat`                                                         |
| Limit                          | 10 request per menit                                                     |
| Scope                          | Per IP address                                                           |
| Response ketika limit tercapai | HTTP 429                                                                 |
| Response format                | JSON                                                                     |
| Rate limit headers             | Enabled                                                                  |
| Retry                          | Client menunggu hingga rate-limit window memungkinkan request berikutnya |

## Threshold

Setiap IP diperbolehkan melakukan maksimal:

```text
10 request / 1 menit
```

Request ke-11 dan request berikutnya dalam rate-limit window akan ditolak.

Contoh:

```text
Request 1  → 200
Request 2  → 200
Request 3  → 200
...
Request 10 → 200
Request 11 → 429
Request 12 → 429
```

## Response

Ketika rate limit tercapai, API mengembalikan:

```json
{
  "error": "rate limit exceeded",
  "message": "Terlalu banyak request. Silakan coba lagi nanti."
}
```

HTTP status:

```text
429 Too Many Requests
```

## Scope

Rate limit dihitung berdasarkan IP address menggunakan Flask-Limiter dan `get_remote_address`.

Contoh:

```text
IP A
├── Request 1
├── ...
└── Request 10 → allowed

IP B
├── Request 1
├── ...
└── Request 10 → allowed
```

Limit IP A tidak memengaruhi limit IP B.

## Client Behavior

Client yang menerima HTTP 429 tidak boleh melakukan retry secara agresif.

Client harus menunggu hingga rate-limit window memungkinkan request berikutnya.

## Security

Rate limiting dilakukan sebelum proses chatbot yang mahal seperti:

```text
Contextualizer
→ Embedding
→ Retrieval
→ Reranking
→ LLM
```

Request yang ditolak tidak boleh menjalankan proses tersebut.

## Testing

Test dilakukan dengan mengirimkan lebih dari 10 request dalam satu menit dari IP yang sama.

Expected:

```text
Request 1–10  → HTTP 200
Request 11+   → HTTP 429
```

## Production Consideration

Jika aplikasi dijalankan di belakang reverse proxy atau load balancer, konfigurasi trusted proxy harus diperhatikan agar IP client yang digunakan untuk rate limiting dapat diidentifikasi dengan benar.