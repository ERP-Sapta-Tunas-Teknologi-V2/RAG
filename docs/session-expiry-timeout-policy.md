# Session Expiry / Timeout Policy

## Objective

Menentukan aturan masa aktif session chatbot agar conversation context tidak tersimpan atau digunakan tanpa batas waktu.

## Session Policy

| Parameter           | Policy                                       |
| ------------------- | -------------------------------------------- |
| Idle timeout        | 30 menit                                     |
| Absolute timeout    | 24 jam                                       |
| Session ID          | UUID v4                                      |
| Storage production  | Database / Redis                             |
| Storage development | In-memory diperbolehkan                      |
| Expired session     | Tidak dapat menggunakan conversation history |
| Cleanup             | Session expired dihapus secara berkala       |

## Idle Timeout

Session akan dianggap expired apabila tidak terdapat aktivitas selama **30 menit**.

Setiap request yang valid dari session aktif akan memperbarui waktu expiry.

Contoh:

```text
13:00  Session dibuat
       expires_at = 13:30

13:10  User mengirim follow-up
       expires_at = 13:40

13:35  User mengirim follow-up
       expires_at = 14:05

14:06  User mengirim request
       session expired
       → history lama tidak digunakan
       → session baru dibuat
```

## Absolute Timeout

Session memiliki batas maksimum **24 jam** sejak session dibuat.

Aktivitas user tidak boleh memperpanjang session melewati absolute timeout.

Contoh:

```text
08:00  Session dibuat
       absolute_expiry = 08:00 hari berikutnya

07:50  User masih aktif
       session tetap aktif

08:01  Session expired
       → session baru dibuat
```

## Session Data

Minimal setiap session menyimpan:

```text
session_id
created_at
last_activity_at
expires_at
```

Conversation history disimpan berdasarkan `session_id`.

Contoh struktur:

```text
sessions
├── id
├── created_at
├── last_activity_at
└── expires_at

conversation_messages
├── id
├── session_id
├── role
├── content
└── created_at
```

## Expired Session Behavior

Apabila request menggunakan session yang sudah expired:

1. Session dianggap tidak aktif.
2. Conversation history dari session tersebut tidak digunakan untuk RAG/LLM.
3. Session baru dibuat.
4. Request diproses menggunakan session baru.
5. Session lama menunggu proses cleanup sesuai retention policy.

## Cleanup

Expired session dan conversation history yang terkait harus dibersihkan secara berkala.

Cleanup dapat dilakukan menggunakan:

* scheduled job
* background worker
* database cleanup query
* Redis TTL apabila Redis digunakan

Cleanup tidak boleh menghapus session yang masih aktif.

## Security & Privacy

Conversation history hanya boleh digunakan selama session masih valid.

Session yang expired tidak boleh dikirim kembali sebagai context kepada LLM.

Retention period untuk data yang sudah expired harus mengikuti **Compliance Retention Policy** yang ditentukan oleh project.

Jika conversation history mengandung PII, penyimpanan dan retention harus mengikuti consent dan privacy requirements yang berlaku.