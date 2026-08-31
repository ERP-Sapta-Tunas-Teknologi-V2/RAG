import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from datetime import datetime

URL = "http://127.0.0.1:5000/api/chat"

QUESTIONS = [
    "apa spesialisasi dari Sapta Tunas Teknologi?",
    "jelaskan tentang AI Avatar",
    "kapan Sapta Tunas Teknologi didirikan?",
    "Apa solusi infrastruktur IT yang ditawarkan untuk industri Financial Services?",
    "Bagaimana perusahaan telekomunikasi dapat melindungi jaringan 4G dan 5G?",
]

def send_request(question):
    start = time.perf_counter()

    try:
        response = requests.post(
            URL,
            json={"question": question},
            stream=True,
            timeout=120
        )

        for _ in response.iter_lines():
            pass

        return response.status_code, time.perf_counter() - start

    except Exception:
        return "ERROR", time.perf_counter() - start

def run_load_test(concurrency):
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(send_request, QUESTIONS[i % len(QUESTIONS)])
            for i in range(concurrency)
        ]

        results = [future.result() for future in as_completed(futures)]

    elapsed = time.perf_counter() - start
    latencies = [latency for _, latency in results]

    success = sum(status == 200 for status, _ in results)
    rate_limited = sum(status == 429 for status, _ in results)
    errors = sum(status == "ERROR" for status, _ in results)

    latencies.sort()
    p50 = latencies[len(latencies) // 2]
    p95 = latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))]

    print(f"\nTime: {datetime.now()}")
    print(f"Concurrency: {concurrency}")
    print(f"Requests: {len(results)}")
    print(f"Success: {success}")
    print(f"Rate limited: {rate_limited}")
    print(f"Errors: {errors}")
    print(f"Avg latency: {sum(latencies) / len(latencies):.2f}s")
    print(f"P50 latency: {p50:.2f}s")
    print(f"P95 latency: {p95:.2f}s")
    print(f"Min latency: {min(latencies):.2f}s")
    print(f"Max latency: {max(latencies):.2f}s")
    print(f"RPS: {len(results) / elapsed:.2f}")

if __name__ == "__main__":
    for concurrency in [1, 5, 10, 20]:
        run_load_test(concurrency)