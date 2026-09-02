from routes.analytics import analytics_bp
import routes.analytics as analytics

class MockApp:
    testing = True

def create_client():
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.config["TESTING"] = True

    return app.test_client()

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


def test_export_marketing_allowed(monkeypatch):
    monkeypatch.setattr(
        analytics,
        "export_query_logs",
        lambda *args, **kwargs: "id,query,timestamp\n"
    )

    client = create_client()

    response = client.get(
        "/api/logs/export",
        headers={"X-User-Role": "Marketing"}
    )

    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"


def test_export_product_allowed(monkeypatch):
    monkeypatch.setattr(
        analytics,
        "export_query_logs",
        lambda *args, **kwargs: "id,query,timestamp\n"
    )

    client = create_client()

    response = client.get(
        "/api/logs/export",
        headers={"X-User-Role": "Product"}
    )

    assert response.status_code == 200
    assert response.content_type == "text/csv; charset=utf-8"


def test_export_other_role_forbidden(monkeypatch):
    monkeypatch.setattr(
        analytics,
        "export_query_logs",
        lambda *args, **kwargs: "id,query,timestamp\n"
    )

    client = create_client()

    response = client.get(
        "/api/logs/export",
        headers={"X-User-Role": "Engineering"}
    )

    assert response.status_code == 403
    assert response.get_json() == {
        "error": "forbidden"
    }


def test_export_invalid_role_forbidden(monkeypatch):
    monkeypatch.setattr(
        analytics,
        "export_query_logs",
        lambda *args, **kwargs: "id,query,timestamp\n"
    )

    client = create_client()

    response = client.get(
        "/api/logs/export",
        headers={"X-User-Role": "marketing"}
    )

    assert response.status_code == 403
    assert response.get_json() == {
        "error": "forbidden"
    }