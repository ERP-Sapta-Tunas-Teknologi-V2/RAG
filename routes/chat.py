import re
from flask import Blueprint, request, jsonify

from rag.retriever import hybrid_retrieve
from rag.chain import generate_answer

chat_bp = Blueprint("chat", __name__)

MAX_QUERY_LENGTH = 1000
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions", r"abaikan\s+(semua\s+)?instruksi\s+sebelumnya",
    r"ignore\s+(all\s+)?prior\s+instructions", r"abaikan\s+(semua\s+)?instruksi\s+terdahulu",
    r"forget\s+(all\s+)?previous\s+instructions", r"lupakan\s+(semua\s+)?instruksi\s+sebelumnya",
    r"system\s+prompt", r"prompt\s+sistem", r"tampilkan\s+(instruksi|perintah)\s+(anda|kamu)",
    r"reveal\s+(your\s+)?instructions", r"ungkapkan\s+(instruksi|perintah)\s+(anda|kamu)",
    r"show\s+(me\s+)?(your\s+)?prompt", r"tunjukkan\s+(prompt|instruksi|perintah)\s+(anda|kamu)",
    r"act\s+as\s+", r"bertindaklah\s+sebagai\s+", r"berperanlah\s+sebagai\s+",
    r"you\s+are\s+now\s+", r"sekarang\s+anda\s+adalah\s+", r"mulai\s+sekarang\s+anda\s+adalah\s+",
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
def chat():
    data = request.get_json(silent=True) or {}
    question = data.get("question")

    error = validate_query(question)

    if error:
        return jsonify({"error": error}), 400

    question = " ".join(question.split())

    documents, context = hybrid_retrieve(question)
    answer = generate_answer(question, context)

    sources = [document.metadata for document in documents]

    return jsonify({
        "question": question,
        "answer": answer,
        "context": context,
        "sources": sources
    })