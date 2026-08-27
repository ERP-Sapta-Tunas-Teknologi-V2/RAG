import re
import time
from flask import Blueprint, request, jsonify, Response, stream_with_context
import json
import uuid

from rag.retriever import hybrid_retrieve
from rag.chain import generate_answer
from utils.extensions import limiter

chat_bp = Blueprint("chat", __name__)

MAX_QUERY_LENGTH = 1000
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"abaikan\s+(semua\s+)?instruksi\s+sebelumnya",
    r"ignore\s+(all\s+)?prior\s+instructions",
    r"abaikan\s+(semua\s+)?instruksi\s+terdahulu",
    r"forget\s+(all\s+)?previous\s+instructions",
    r"lupakan\s+(semua\s+)?instruksi\s+sebelumnya",
    r"system\s+prompt",
    r"prompt\s+sistem",
    r"tampilkan\s+(instruksi|perintah)\s+(anda|kamu)",
    r"reveal\s+(your\s+)?instructions",
    r"ungkapkan\s+(instruksi|perintah)\s+(anda|kamu)",
    r"show\s+(me\s+)?(your\s+)?prompt",
    r"tunjukkan\s+(prompt|instruksi|perintah)\s+(anda|kamu)",
    r"act\s+as\s+",
    r"bertindaklah\s+sebagai\s+",
    r"berperanlah\s+sebagai\s+",
    r"you\s+are\s+now\s+",
    r"sekarang\s+anda\s+adalah\s+",
    r"mulai\s+sekarang\s+anda\s+adalah\s+",
]

def validate_query(question):
    if not isinstance(question, str):
        return "question must be a string"

    question = " ".join(question.split())

    if not question:
        return "question is required"

    if len(question) > MAX_QUERY_LENGTH:
        return f"question must not exceed {MAX_QUERY_LENGTH} characters"

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            return "invalid question"

    return None

@chat_bp.route("/chat", methods=["POST"])
@limiter.limit("10 per minute")
def chat():
    request_id = uuid.uuid4().hex[:8]
    request_start = time.perf_counter()

    data = request.get_json(silent=True) or {}
    question = data.get("question")

    error = validate_query(question)
    if error:
        return jsonify({"error": error}), 400

    question = " ".join(question.split())
    documents, context = hybrid_retrieve(question, request_id)

    if not documents:
        answer = "Informasi tidak ditemukan dalam knowledge base. Silakan hubungi kontak kami."

        return jsonify({
            "question": question,
            "answer": answer,
            "context": "",
            "sources": [],
            "fallback": True
        })

    sources = [document.metadata for document in documents]

# Non-Stream
#     answer = generate_answer(question, context)
#     return jsonify({
#         "question": question,
#         "answer": answer,
#         "context": context,
#         "sources": sources,
#         "fallback": False
#     })

    def generate():
        yield f"data: {json.dumps({'type': 'metadata', 'sources': sources, 'fallback': False}, ensure_ascii=False)}\n\n"

        llm_start = time.perf_counter()
        first_token_time = None
        full_answer = []

        stream = generate_answer(question, context)

        for chunk in stream:
            # Ollama
            # content = chunk.content

            # API
            if not chunk.choices:
                continue
            content = getattr(chunk.choices[0].delta, "content", None)

            if not content:
                continue

            if first_token_time is None:
                first_token_time = time.perf_counter() - llm_start

            full_answer.append(content)

            yield f"data: {json.dumps({'type': 'token', 'content': content}, ensure_ascii=False)}\n\n"

        llm_time = time.perf_counter() - llm_start
        total_time = time.perf_counter() - request_start

        answer = "".join(full_answer)

        log = (
            f"[{request_id}] [LLM] ttft={first_token_time:.3f}s | "
            f"total={llm_time:.3f}s\n"
            f"[{request_id}] [REQUEST] total={total_time:.3f}s\n"
        )

        with open("log/log_time.txt", "a", encoding="utf-8") as f:
            f.write(log)

        print("\n=== FULL ANSWER ===")
        print(answer)
        print("=====================\n")

        yield f"data: {json.dumps({'type': 'answer', 'content': answer}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@chat_bp.route("/rate-limit-test", methods=["GET"])
@limiter.limit("10 per minute")
def rate_limit_test():
    return jsonify({"message": "ok"})