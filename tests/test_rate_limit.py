import requests

url = "http://127.0.0.1:5000/api/rate-limit-test"

for i in range(12):
    r = requests.get(url)

    print(
        f'i: {i + 1} | '
        f'Status code: {r.status_code} | '
        f'Rate limit: {r.headers.get("X-RateLimit-Limit")} | '
        f'Remaining: {r.headers.get("X-RateLimit-Remaining")} | '
        f'Retry after: {r.headers.get("Retry-After")}\n'
        f'{r.text}'
    )