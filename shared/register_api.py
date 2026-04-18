import requests

REGISTRY_URL = "http://slh-device-registry:8090"

def register_device(serial, phone):
    return requests.post(f"{REGISTRY_URL}/register", json={
        "serial": serial,
        "phone": phone
    }).json()

def verify_device(serial, code):
    return requests.post(f"{REGISTRY_URL}/verify", json={
        "serial": serial,
        "code": code
    }).json()
