import time
import voyageai
from transformers import AutoTokenizer
from supabase.client import create_client

from config.settings import SUPABASE_URL, SUPABASE_KEY, VOYAGE_EMB_MODEL
from rag.embeddings import embeddings

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

MAX_RPM = 3
MAX_TPM = 10_000
TARGET_BATCH_TOKENS = 9_000
MAX_RETRIES = 3

tokenizer = AutoTokenizer.from_pretrained(f"voyageai/{VOYAGE_EMB_MODEL}")

def _count_tokens(text):
    return len(tokenizer.encode(text, add_special_tokens=False))

def _create_batches(items):
    batches = []
    current_batch = []
    current_tokens = 0

    for item in items:
        text = item["chunk"].page_content
        tokens = _count_tokens(text)

        if tokens > TARGET_BATCH_TOKENS:
            print(f"Warning: chunk contains {tokens:,} tokens, which is larger than target batch size {TARGET_BATCH_TOKENS:,}.")

        if current_batch and current_tokens + tokens > TARGET_BATCH_TOKENS:
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0

        current_batch.append(item)
        current_tokens += tokens

    if current_batch:
        batches.append(current_batch)

    return batches

class VoyageRateLimiter:
    def __init__(self, max_rpm=MAX_RPM, max_tpm=MAX_TPM):
        self.max_rpm = max_rpm
        self.max_tpm = max_tpm
        self.history = []

    def _cleanup(self):
        now = time.time()
        self.history = [(timestamp, tokens) for timestamp, tokens in self.history if now - timestamp < 60]

    def wait(self, tokens):
        while True:
            self._cleanup()
            now = time.time()
            request_count = len(self.history)
            token_count = sum(tokens for _, tokens in self.history)
            rpm_exceeded = request_count >= self.max_rpm
            tpm_exceeded = token_count + tokens > self.max_tpm

            if not rpm_exceeded and not tpm_exceeded:
                return

            wait_time = 1

            if self.history:
                oldest_timestamp = self.history[0][0]
                wait_time = max(wait_time, 60 - (now - oldest_timestamp))

            reasons = []

            if rpm_exceeded:
                reasons.append(f"RPM {request_count}/{self.max_rpm}")
            if tpm_exceeded:
                reasons.append(f"TPM {token_count:,}+{tokens:,}/{self.max_tpm:,}")

            print(f"[RATE LIMIT] {', '.join(reasons)}. Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)

    def record(self, tokens):
        self.history.append((time.time(), tokens))

def _embed_batch(texts, batch_number, rate_limiter):
    token_count = sum(_count_tokens(text) for text in texts)
    print(f"Embedding batch {batch_number} | chunks={len(texts)} | tokens={token_count:,}")

    if token_count > MAX_TPM:
        raise ValueError(f"Batch {batch_number} contains {token_count:,} tokens, exceeding MAX_TPM={MAX_TPM:,}.")

    for attempt in range(MAX_RETRIES + 1):
        try:
            rate_limiter.wait(token_count)
            print(f"Sending batch {batch_number} to Voyage...")
            vectors = embeddings.embed_documents(texts)
            rate_limiter.record(token_count)
            print(f"Batch {batch_number} completed.")
            return vectors

        except voyageai.error.RateLimitError as e:
            if attempt == MAX_RETRIES:
                print(f"Rate limit: batch {batch_number} failed after {MAX_RETRIES + 1} attempts: {e}")
                return None
            wait_time = 60
            print(f"Rate limit on batch {batch_number}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

        except (TimeoutError, ConnectionError) as e:
            if attempt == MAX_RETRIES:
                print(f"Network error: batch {batch_number} failed after {MAX_RETRIES + 1} attempts: {e}")
                return None
            wait_time = 60
            print(f"Network error on batch {batch_number}: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

        except Exception as e:
            print(f"Permanent embedding error on batch {batch_number}: {type(e).__name__}: {e}")
            return None

    return None

def add_documents(chunks):
    inserted = 0
    skipped = 0
    failed = 0
    pending = []
    failed_chunks = []

    for chunk in chunks:
        metadata = chunk.metadata.copy()
        document_id = metadata.pop("document_id")
        fingerprint = metadata.pop("fingerprint")

        existing = (
            supabase_client
            .table("documents")
            .select("id")
            .eq("document_id", document_id)
            .eq("fingerprint", fingerprint)
            .limit(1)
            .execute()
        )

        if existing.data:
            skipped += 1
            continue

        pending.append({
            "chunk": chunk,
            "document_id": document_id,
            "fingerprint": fingerprint,
            "metadata": metadata
        })

    if not pending:
        print(f"New chunks: 0 | Skipped: {skipped}")
        return {"inserted": inserted, "skipped": skipped, "failed": failed, "failed_chunks": failed_chunks}

    batches = _create_batches(pending)
    print(f"New chunks: {len(pending)} | Batches: {len(batches)} | Target batch tokens: {TARGET_BATCH_TOKENS:,}")

    rate_limiter = VoyageRateLimiter(max_rpm=MAX_RPM, max_tpm=MAX_TPM)

    for batch_number, batch in enumerate(batches, start=1):
        texts = [item["chunk"].page_content for item in batch]
        vectors = _embed_batch(texts, batch_number, rate_limiter)

        if vectors is None:
            failed += len(batch)
            failed_chunks.extend(batch)
            print(f"Batch {batch_number} failed. Skipping {len(batch)} chunks.")
            continue

        rows = []

        for item, vector in zip(batch, vectors):
            rows.append({
                "content": item["chunk"].page_content,
                "metadata": item["metadata"],
                "document_id": item["document_id"],
                "fingerprint": item["fingerprint"],
                "embedding": vector
            })

        try:
            supabase_client.table("documents").insert(rows).execute()
            inserted += len(rows)
            print(f"Inserted batch {batch_number}: {len(rows)} chunks")

        except Exception as e:
            failed += len(batch)
            failed_chunks.extend(batch)
            print(f"Supabase insert failed for batch {batch_number}: {type(e).__name__}: {e}")

    print(f"Inserted: {inserted} | Skipped: {skipped} | Failed: {failed}")

    if failed_chunks:
        print("\nFailed chunks:")
        for item in failed_chunks:
            print(f"FAILED | document_id={item['document_id']} | fingerprint={item['fingerprint']}")

    return {"inserted": inserted, "skipped": skipped, "failed": failed, "failed_chunks": failed_chunks}