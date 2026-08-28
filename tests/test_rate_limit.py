import requests

url = "http://127.0.0.1:5000/api/rate-limit-test"

for i in range(12):
    r = requests.get(url)
    print(i + 1, r.status_code, r.text)