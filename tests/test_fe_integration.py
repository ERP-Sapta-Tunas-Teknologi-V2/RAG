import os
import uuid
import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")
ENDPOINT = f"{BASE_URL}/api/chat"

ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "https://saptatunas.com")
LIMIT = 10


def chat(question, session_id, origin=ALLOWED_ORIGIN):
    return requests.post(
        ENDPOINT,
        json={"question": question, "session_id": session_id},
        headers={
            "Content-Type": "application/json",
            "Origin": origin,
        },
        timeout=120,
    )


def test_session():
    print("\n=== SESSION TEST ===")

    session_id = f"fe-{uuid.uuid4()}"

    r1 = chat("Apa itu cuti?", session_id)
    print("request 1:", r1.status_code)

    r2 = chat("Berapa lama pengajuannya?", session_id)
    print("request 2:", r2.status_code)

    assert r1.status_code in (200, 429)
    assert r2.status_code in (200, 429)

    print("session_id:", session_id)
    print("PASS: FE dapat menggunakan session_id yang sama")


def test_multiple_sessions():
    print("\n=== MULTI SESSION TEST ===")

    session_a = f"fe-a-{uuid.uuid4()}"
    session_b = f"fe-b-{uuid.uuid4()}"

    r1 = chat("Apa itu cuti?", session_a)
    r2 = chat("Apa itu cuti?", session_b)

    print("session A:", r1.status_code)
    print("session B:", r2.status_code)

    assert r1.status_code in (200, 429)
    assert r2.status_code in (200, 429)

    print("PASS: session berbeda tidak saling break")


def test_rate_limit():
    print("\n=== RATE LIMIT TEST ===")

    session_id = f"rate-{uuid.uuid4()}"
    statuses = []

    for i in range(LIMIT + 3):
        r = chat(f"rate-limit-test-{i}", session_id)
        statuses.append(r.status_code)
        print(f"request {i + 1}: {r.status_code}")

    assert 429 in statuses, "Expected rate limit 429"

    print("PASS: rate limit aktif")


def test_cors():
    print("\n=== CORS TEST ===")

    session_id = f"cors-{uuid.uuid4()}"

    r = chat("hello", session_id)

    cors = r.headers.get("Access-Control-Allow-Origin")

    print("status:", r.status_code)
    print("CORS:", cors)

    assert cors == ALLOWED_ORIGIN

    print("PASS: FE origin diizinkan")


def main():
    print(f"BASE_URL: {BASE_URL}")
    print(f"ENDPOINT: {ENDPOINT}")

    test_session()
    test_multiple_sessions()
    test_rate_limit()
    test_cors()

    print("\n=== ALL INTEGRATION TESTS PASSED ===")


if __name__ == "__main__":
    main()