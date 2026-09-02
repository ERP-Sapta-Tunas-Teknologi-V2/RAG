import requests
from concurrent.futures import ThreadPoolExecutor

url = "http://127.0.0.1:5000/api/rate-limit-test"

def send_request(i):
    r = requests.get(url)
    return (
        i + 1,
        r.status_code,
        r.headers.get("X-RateLimit-Limit"),
        r.headers.get("X-RateLimit-Remaining"),
        r.headers.get("Retry-After"),
        r.text,
    )

with ThreadPoolExecutor(max_workers=12) as executor:
    results = list(executor.map(send_request, range(12)))

for result in sorted(results):
    i, status, limit, remaining, retry_after, text = result
    print(
        f"i: {i} | "
        f"Status code: {status} | "
        f"Rate limit: {limit} | "
        f"Remaining: {remaining} | "
        f"Retry after: {retry_after}\n"
        f"{text}\n"
    )

success = sum(r[1] == 200 for r in results)
limited = sum(r[1] == 429 for r in results)

print(f"200 responses: {success}")
print(f"429 responses: {limited}")

assert success == 10
assert limited == 2