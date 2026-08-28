import requests
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
    try:
        response = requests.post(
            URL,
            json={"question": question},
            stream=True,
            timeout=120
        )

        for _ in response.iter_lines():
            pass

        return response.status_code

    except Exception:
        return "ERROR"

def test_concurrent_requests():
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(send_request, question)
            for question in QUESTIONS
        ]

        results = [
            future.result()
            for future in as_completed(futures)
        ]

    success = sum(status == 200 for status in results)
    rate_limited = sum(status == 429 for status in results)
    errors = sum(status == "ERROR" for status in results)

    assert success == len(QUESTIONS)
    assert rate_limited == 0
    assert errors == 0