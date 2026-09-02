import concurrent.futures
import requests

BASE_URL = "http://127.0.0.1:5000"
ENDPOINT = f"{BASE_URL}/api/chat"

USERS = 5
SESSIONS_PER_USER = 2
REQUESTS_PER_SESSION = 3
RATE_LIMIT_REQUESTS = 12

ALLOWED_ORIGIN = "https://saptatunas.com"
BLOCKED_ORIGIN = "http://evil.example.com"


def chat(user, session, i, origin=ALLOWED_ORIGIN):
    r = requests.post(
        ENDPOINT,
        json={
            "question": f"Test E2E user={user} session={session} request={i}",
            "session_id": session,
        },
        headers={"Origin": origin},
        timeout=120,
    )

    return {
        "user": user,
        "session": session,
        "status": r.status_code,
        "cors": r.headers.get("Access-Control-Allow-Origin"),
        "body": r.text[:200],
    }


def run_concurrent():
    jobs = [
        (u, f"user-{u}-session-{s}", i)
        for u in range(1, USERS + 1)
        for s in range(1, SESSIONS_PER_USER + 1)
        for i in range(1, REQUESTS_PER_SESSION + 1)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(lambda x: chat(*x), jobs))

    success = sum(r["status"] == 200 for r in results)
    errors = sum(r["status"] not in (200, 429) for r in results)

    print("\n=== MULTI-USER / MULTI-SESSION ===")
    print(f"Requests : {len(results)}")
    print(f"200      : {success}")
    print(f"Errors   : {errors}")

    for r in results:
        print(
            f"user={r['user']} "
            f"session={r['session']} "
            f"status={r['status']} "
            f"cors={r['cors']}"
        )

    return results


def test_rate_limit():
    print("\n=== RATE LIMIT ===")

    results = []

    for i in range(RATE_LIMIT_REQUESTS):
        r = chat("rate-limit-user", "rate-limit-session", i)
        results.append(r)

    status = [r["status"] for r in results]
    limited = status.count(429)

    print(f"Requests : {len(results)}")
    print(f"429      : {limited}")
    print(f"Status   : {status}")

    return limited > 0


def test_cors():
    print("\n=== CORS ===")

    allowed = chat(
        "cors-user",
        "cors-allowed",
        1,
        ALLOWED_ORIGIN,
    )

    blocked = chat(
        "cors-user",
        "cors-blocked",
        1,
        BLOCKED_ORIGIN,
    )

    allowed_ok = (
        allowed["cors"] == ALLOWED_ORIGIN
    )

    blocked_ok = (
        blocked["cors"] != BLOCKED_ORIGIN
    )

    print(
        f"Allowed origin : {allowed['cors']} "
        f"-> {'PASS' if allowed_ok else 'FAIL'}"
    )

    print(
        f"Blocked origin : {blocked['cors']} "
        f"-> {'PASS' if blocked_ok else 'FAIL'}"
    )

    return allowed_ok and blocked_ok


def main():
    print("=== E2E SECURITY / CONCURRENCY TEST ===")

    concurrent_results = run_concurrent()
    rate_limit_ok = test_rate_limit()
    cors_ok = test_cors()

    concurrent_ok = all(
        r["status"] in (200, 429)
        for r in concurrent_results
    )

    print("\n=== RESULT ===")
    print(
        f"Multi-user/session : "
        f"{'PASS' if concurrent_ok else 'FAIL'}"
    )
    print(
        f"Rate limit         : "
        f"{'PASS' if rate_limit_ok else 'FAIL'}"
    )
    print(
        f"CORS               : "
        f"{'PASS' if cors_ok else 'FAIL'}"
    )

    overall = concurrent_ok and rate_limit_ok and cors_ok

    print(
        f"\nOVERALL            : "
        f"{'PASS' if overall else 'FAIL'}"
    )

    raise SystemExit(0 if overall else 1)


if __name__ == "__main__":
    main()