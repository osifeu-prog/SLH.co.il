import time
import requests

URL = "http://localhost:8000/health"

while True:
    try:
        r = requests.get(URL, timeout=5)
        print("HEALTH:", r.status_code)
    except Exception as e:
        print("CRASH DETECTED:", e)

    time.sleep(30)
