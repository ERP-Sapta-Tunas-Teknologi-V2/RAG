import re
import time
from flask import Blueprint, request, jsonify, Response, stream_with_context
import json
import uuid
from threading import Thread

from rag.retriever import hybrid_retrieve
from rag.chain import generate_answer
from utils.extensions import limiter
from utils.anonymizer import anonymize_query
from utils.query_logger import log_query
from session.manager import SessionManager

session_manager = SessionManager()

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

def log_query_background(query, anon_id):
    try:
        log_time = log_query(query, anon_id)
        return log_time
    except Exception as e:
        print(f"[LOGGING] failed: {e}")

@chat_bp.route("/chat", methods=["POST"])
@limiter.limit("10 per minute")
def chat():
    request_id = uuid.uuid4().hex[:8]
    request_start = time.perf_counter()

    data = request.get_json(silent=True) or {}
    question = data.get("question")
    session_id = data.get("session_id")

    error = validate_query(question)
    if error:
        return jsonify({"error": error}), 400

    question = " ".join(question.split())

    session, is_new = session_manager.get_or_create(session_id)
    session_id = session["session_id"]
    history = session_manager.get_history(session_id, limit=10)
    session_manager.add_message(session_id, "user", question)

    print(f"[SESSION] id={session_id} new={is_new}")
    print(f"[SESSION] history={history}")

    safe_query = anonymize_query(question)
    anon_id = uuid.uuid4()

    log_start = time.perf_counter()
    Thread(target=log_query_background, args=(safe_query, anon_id), daemon=True).start()
    log_time = time.perf_counter() - log_start
    with open("log/log_time.txt", "a", encoding="utf-8") as f:
        f.write(f"[{request_id}] [LOGGING] total={log_time:.3f}s\n")

    documents, context = hybrid_retrieve(question, request_id)

    if not documents:
        answer = "Informasi tidak ditemukan dalam knowledge base. Silakan hubungi kontak kami."

        session_manager.add_message(session_id, "assistant", answer)

        return jsonify({
            "session_id": session_id,
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
        yield f"data: {json.dumps({
            'type': 'metadata',
            'session_id': session_id,
            'sources': sources,
            'fallback': False
        }, ensure_ascii=False)}\n\n"

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

        session_manager.add_message(session_id, "assistant", answer)

        log = (
            f"[{request_id}] [LLM] ttft={first_token_time:.3f}s | "
            f"total={llm_time:.3f}s\n"
            f"[{request_id}] [REQUEST] total={total_time:.3f}s\n\n"
        )

        with open("log/log_time.txt", "a", encoding="utf-8") as f:
            f.write(log)

        # print("\n=== FULL ANSWER ===")
        # print(answer)
        # print("=====================\n")

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