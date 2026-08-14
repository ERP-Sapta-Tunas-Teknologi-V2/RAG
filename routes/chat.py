from flask import Blueprint, request, jsonify

from rag.retriever import retrieve_with_neighbors
from rag.chain import generate_answer

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    question = data.get("question")

    if not question: 
        return jsonify({"error": "question is required"}), 400

    documents = retrieve_with_neighbors(question, neighbor_count=1)
    answer, context = generate_answer(question, documents)

    sources = []
    for document in documents: 
        sources.append(document.metadata)

    return jsonify({
        "question": question, 
        "answer": answer, 
        "context": "\n\n".join(
            document.page_content
            for document in documents
        ),
        "sources": sources
    })