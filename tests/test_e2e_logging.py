import csv
import io

import routes.chat as chat
import routes.analytics as analytics
from app import app

class ImmediateThread:
    def __init__(self, target, args=(), daemon=False):
        self.target = target
        self.args = args

    def start(self):
        self.target(*self.args)

def create_client():
    app.config["TESTING"] = True
    return app.test_client()

def test_query_to_anonymized_export(monkeypatch):
    logged_rows = []

    def mock_log_query(query, anon_id):
        logged_rows.append({
            "id": len(logged_rows) + 1,
            "query": query,
            "timestamp": "2026-08-28T09:00:00+07:00",
            "anon_id": str(anon_id)
        })

    monkeypatch.setattr(chat, "Thread", ImmediateThread)
    monkeypatch.setattr(chat, "log_query", mock_log_query)
    monkeypatch.setattr(
        chat,
        "hybrid_retrieve",
        lambda question, request_id: ([], "")
    )

    def mock_export(*args, **kwargs):
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["id", "query", "timestamp"])

        for row in logged_rows:
            writer.writerow([
                row["id"],
                row["query"],
                row["timestamp"]
            ])

        return output.getvalue()

    monkeypatch.setattr(
        analytics,
        "export_query_logs",
        mock_export
    )

    client = create_client()

    question = (
        "Email saya test@example.com "
        "atau HP 081234567890"
    )

    response = client.post(
        "/api/chat",
        json={"question": question}
    )

    assert response.status_code == 200
    assert len(logged_rows) == 1
    assert logged_rows[0]["query"] == (
        "Email saya [EMAIL] atau HP [PHONE]"
    )

    export_response = client.get(
        "/api/logs/export",
        headers={"X-User-Role": "Marketing"}
    )

    assert export_response.status_code == 200
    assert export_response.content_type == "text/csv; charset=utf-8"

    csv_text = export_response.data.decode("utf-8")

    rows = list(
        csv.reader(
            io.StringIO(csv_text)
        )
    )

    assert rows[0] == ["id", "query", "timestamp"]
    assert len(rows) == 2

    assert rows[1][1] == (
        "Email saya [EMAIL] atau HP [PHONE]"
    )

    assert "test@example.com" not in csv_text
    assert "081234567890" not in csv_text

    assert "[EMAIL]" in csv_text
    assert "[PHONE]" in csv_text

def test_query_with_multiple_pii(monkeypatch):
    logged_rows = []

    def mock_log_query(query, anon_id):
        logged_rows.append(query)

    monkeypatch.setattr(chat, "Thread", ImmediateThread)
    monkeypatch.setattr(chat, "log_query", mock_log_query)

    monkeypatch.setattr(
        chat,
        "hybrid_retrieve",
        lambda question, request_id: ([], "")
    )

    client = create_client()

    question = (
        "Hubungi saya melalui "
        "john.doe@example.com atau 081234567890"
    )

    response = client.post(
        "/api/chat",
        json={"question": question}
    )

    assert response.status_code == 200
    assert len(logged_rows) == 1

    logged_query = logged_rows[0]

    assert logged_query == (
        "Hubungi saya melalui "
        "[EMAIL] atau [PHONE]"
    )

    assert "john.doe@example.com" not in logged_query
    assert "081234567890" not in logged_query

def test_export_requires_auth(monkeypatch):
    monkeypatch.setattr(
        analytics,
        "export_query_logs",
        lambda *args, **kwargs: "id,query,timestamp\n"
    )

    client = create_client()

    response = client.get("/api/logs/export")

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "authentication required"
    }

def test_export_marketing_after_query(monkeypatch):
    logged_rows = []

    def mock_log_query(query, anon_id):
        logged_rows.append(query)

    monkeypatch.setattr(chat, "Thread", ImmediateThread)
    monkeypatch.setattr(chat, "log_query", mock_log_query)
    monkeypatch.setattr(
        chat,
        "hybrid_retrieve",
        lambda question, request_id: ([], "")
    )

    def mock_export(*args, **kwargs):
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["id", "query", "timestamp"])

        for index, query in enumerate(logged_rows, start=1):
            writer.writerow([
                index,
                query,
                "2026-08-28T09:00:00+07:00"
            ])

        return output.getvalue()

    monkeypatch.setattr(
        analytics,
        "export_query_logs",
        mock_export
    )

    client = create_client()

    client.post(
        "/api/chat",
        json={
            "question": "Email test@example.com"
        }
    )

    response = client.get(
        "/api/logs/export",
        headers={"X-User-Role": "Marketing"}
    )

    assert response.status_code == 200

    csv_text = response.data.decode("utf-8")

    assert "[EMAIL]" in csv_text
    assert "test@example.com" not in csv_text

def test_export_product_after_query(monkeypatch):
    logged_rows = []

    def mock_log_query(query, anon_id):
        logged_rows.append(query)

    monkeypatch.setattr(chat, "Thread", ImmediateThread)
    monkeypatch.setattr(chat, "log_query", mock_log_query)
    monkeypatch.setattr(
        chat,
        "hybrid_retrieve",
        lambda question, request_id: ([], "")
    )
    monkeypatch.setattr(
        analytics,
        "export_query_logs",
        lambda *args, **kwargs: (
            "id,query,timestamp\n"
            f"1,{logged_rows[0]},2026-08-28T09:00:00+07:00\n"
        )
    )

    client = create_client()

    client.post(
        "/api/chat",
        json={
            "question": "Email test@example.com"
        }
    )

    response = client.get(
        "/api/logs/export",
        headers={"X-User-Role": "Product"}
    )

    assert response.status_code == 200

    csv_text = response.data.decode("utf-8")

    assert "[EMAIL]" in csv_text
    assert "test@example.com" not in csv_text