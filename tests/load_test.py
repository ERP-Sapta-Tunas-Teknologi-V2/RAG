import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "http://127.0.0.1:5000/api/chat"
QUESTIONS = [
    "apa spesialisasi dari Sapta Tunas Teknologi?",
    "jelaskan tentang AI Avatar",
    "kapan Sapta Tunas Teknologi didirikan?",
    "siapa manager Sapta Tunas Teknologi?",
    "Sapta Tunas Teknologi punya berapa karyawan?",
] * 2

def send_request(question):
    start = time.perf_counter()

    try:
        response = requests.post(
            URL,
            json={"question": question},
            stream=True,
            timeout=120
        )

        for line in response.iter_lines():
            if line:
                print(line.decode())

        return {
            "status": response.status_code,
            "time": time.perf_counter() - start
        }

    except Exception as e:
        elapsed = time.perf_counter() - start
        return {
            "status": "ERROR",
            "time": elapsed,
            "error": str(e)
        }

start = time.perf_counter()

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(send_request, question)
        for question in QUESTIONS
    ]

    results = [future.result() for future in as_completed(futures)]

total = time.perf_counter() - start

success = sum(r["status"] == 200 for r in results)
rate_limited = sum(r["status"] == 429 for r in results)
errors = sum(r["status"] == "ERROR" for r in results)

print(f"Total request : {len(results)}")
print(f"Success       : {success}")
print(f"Rate limited  : {rate_limited}")
print(f"Errors        : {errors}")
print(f"Total time    : {total:.3f}s")

for i, result in enumerate(results, 1):
    print(f"{i:02} | status={result['status']} | time={result['time']:.3f}s | {result.get('error', '')}")