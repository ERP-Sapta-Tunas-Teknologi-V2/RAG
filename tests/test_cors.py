import requests

base_url = "http://127.0.0.1:5000"
allowed = "https://saptatunas.com"
blocked = "https://evil.com"

# Allowed origin
r = requests.get(f"{base_url}/api/rate-limit-test", headers={"Origin": allowed})
assert r.headers.get("Access-Control-Allow-Origin") == allowed

# Blocked origin
r = requests.get(f"{base_url}/api/rate-limit-test", headers={"Origin": blocked})
assert r.headers.get("Access-Control-Allow-Origin") is None

# Preflight
r = requests.options(
    f"{base_url}/api/chat",
    headers={
        "Origin": allowed,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
)
assert r.headers.get("Access-Control-Allow-Origin") == allowed

print("CORS tests passed")