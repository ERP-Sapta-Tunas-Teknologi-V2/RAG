# Query Log Retention Policy

## 1. Objective

Kebijakan ini mengatur penyimpanan dan penghapusan data query user yang digunakan untuk kebutuhan analytics, monitoring, dan peningkatan kualitas chatbot.

## 2. Stored Data

System menyimpan data berikut pada tabel `public.query_logs`:

- `id` — unique identifier log.
- `query` — query user yang telah melalui proses anonymization.
- `timestamp` — waktu query diterima, disimpan menggunakan `timestamptz` dan direpresentasikan dalam UTC.
- `anon_id` — anonymous identifier untuk kebutuhan analisis session.

Data pribadi seperti nama, email, dan nomor telepon tidak boleh disimpan dalam query log.

## 3. Retention Period

Query log disimpan selama maksimal **30 hari** sejak nilai `timestamp`.

Setelah melewati periode 30 hari, data akan dihapus secara otomatis dari storage analytics.

Contoh:

```text
Query timestamp : 1 August 2026 10:00 UTC
Retention       : 30 days
Eligible delete : 31 August 2026 10:00 UTC
````

## 4. Automatic Deletion

System menyediakan scheduled job yang secara berkala menghapus query log yang telah melewati retention period.

Kriteria penghapusan:

```sql
timestamp < now() - interval '30 days'
```

Penghapusan hanya dilakukan terhadap data pada tabel `query_logs` yang telah melewati retention period.

## 5. Purpose Limitation

Query log hanya digunakan untuk:

* Analytics penggunaan chatbot.
* Identifikasi top FAQ.
* Identifikasi potential content gaps.
* Monitoring dan peningkatan kualitas chatbot.
* Reporting yang berkaitan dengan penggunaan chatbot.

Query log tidak digunakan untuk tujuan di luar kebutuhan tersebut tanpa persetujuan dan review yang sesuai.

## 6. Privacy

Sebelum disimpan, query user diproses melalui mekanisme anonymization untuk mengurangi kemungkinan penyimpanan Personally Identifiable Information (PII).

Data raw query tidak disimpan pada `query_logs`.

PII yang terdeteksi oleh mekanisme anonymization, seperti email dan nomor telepon, harus di-anonymize sebelum proses penyimpanan.

Mekanisme anonymization dan pengujian PII harus di-review secara berkala untuk memastikan query log tidak menyimpan data pribadi.

## 7. Access Control

Akses terhadap query log dan fitur export dibatasi kepada role yang memiliki kebutuhan bisnis yang sah, khususnya:

* Marketing
* Product

Akses database secara langsung harus mengikuti permission dan security policy yang telah ditentukan.

## 8. Export

Query log dapat diekspor untuk kebutuhan analytics atau reporting yang sah.

Export harus tetap mengikuti retention, privacy, dan access-control policy yang berlaku.

File hasil export yang mengandung query log harus diperlakukan sebagai data terbatas dan tidak boleh disimpan lebih lama dari kebutuhan yang ditentukan.

## 9. Audit & Compliance

Implementasi retention harus dapat diverifikasi melalui:

* Konfigurasi scheduled deletion job.
* Database query untuk memeriksa data berdasarkan `timestamp`.
* Test bahwa data lebih dari 30 hari terhapus.
* Review access control terhadap query log.
* Review anonymization sebelum data disimpan.

## 10. Policy Review

Retention policy ini harus di-review apabila terdapat perubahan pada:

* PRD atau business requirement.
* Kebutuhan analytics.
* Privacy atau compliance requirement.
* Struktur data query log.
* Mekanisme storage atau export.

**Retention period saat ini: 30 hari.**