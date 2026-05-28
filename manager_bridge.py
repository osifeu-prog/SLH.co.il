import requests
MANAGER_URL = "http://localhost:9000"

def send_to_manager(endpoint, params=None):
    try:
        url = f"{MANAGER_URL}/{endpoint}"
        if params:
            url += "?" + "&".join(f"{k}={v}" for k,v in params.items())
        r = requests.get(url, timeout=10)
        return r.json() if r.ok else {"error": r.status_code}
    except Exception as e:
        return {"error": str(e)}
