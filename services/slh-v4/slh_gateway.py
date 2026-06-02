from fastapi import FastAPI, Request
import json

app = FastAPI(title="SLH Enterprise Gateway", version="v4")


# =========================
# LOAD MAP
# =========================
def load_map():
    with open("enterprise_map/full_map.json", "r", encoding="utf-8") as f:
        return json.load(f)


SYSTEM_MAP = load_map()


# =========================
# SIMPLE ROUTER CORE
# =========================
def resolve_endpoint(path: str):
    return SYSTEM_MAP.get(path, None)


# =========================
# GATEWAY ENTRYPOINT
# =========================
@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    path = request.url.path

    route_info = SYSTEM_MAP.get("endpoints", {}).get(path)

    if route_info:
        request.state.slh_route = route_info

    response = await call_next(request)
    return response


# =========================
# GENERIC HANDLER (catch-all)
# =========================
@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(full_path: str, request: Request):
    full_path = "/" + full_path

    endpoint_data = SYSTEM_MAP.get("endpoints", {}).get(full_path)

    if not endpoint_data:
        return {
            "status": "error",
            "message": "endpoint not mapped in SLH Enterprise Layer",
            "path": full_path
        }

    return {
        "status": "ok",
        "gateway": "slh-v4",
        "route": endpoint_data
    }
