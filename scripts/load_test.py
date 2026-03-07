import requests
import threading

URL = "http://localhost:8000/agents/secure-action"

def send_request():
    payload = {"action": "test"}
    requests.post(URL, json=payload)

threads = []

for i in range(1000):
    t = threading.Thread(target=send_request)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
