from fastapi import FastAPI
import os
import json

app = FastAPI(title="SLH Enterprise Gateway", version="v4")

BASE_DIR = os.path.dirname(__file__)
V4_DIR = os.path.join(BASE_DIR, "services", "slh-v4", "generated_v4")


def load_services():
    services = {}
    if not os.path.exists(V4_DIR):
        return services

    for service in os.listdir(V4_DIR):
        service_path = os.path.join(V4_DIR, service)
        app_file = os.path.join(service_path, "app.py")

        if os.path.exists(app_file):
            services[service] = app_file

    return services


SERVICES = load_services()


@app.get("/")
def root():
    return {
        "status": "SLH Gateway Running",
        "services_loaded": list(SERVICES.keys())
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/services")
def list_services():
    return SERVICES
