from fastapi import FastAPI
from pydantic import BaseModel
import random, time

app = FastAPI()

devices = {}
codes = {}

class RegisterRequest(BaseModel):
    serial: str
    phone: str

class VerifyRequest(BaseModel):
    serial: str
    code: str

@app.post("/register")
def register(req: RegisterRequest):
    code = str(random.randint(100000, 999999))
    codes[req.serial] = {
        "code": code,
        "expires": time.time() + 300
    }
    devices[req.serial] = {"phone": req.phone}

    print(f"[REGISTER] {req.serial} -> {code}")
    return {"status": "code_sent", "code": code}

@app.post("/verify")
def verify(req: VerifyRequest):
    entry = codes.get(req.serial)

    if not entry:
        return {"error": "no_code"}

    if time.time() > entry["expires"]:
        return {"error": "expired"}

    if req.code != entry["code"]:
        return {"error": "invalid"}

    token = f"TOKEN_{req.serial}_{int(time.time())}"
    devices[req.serial]["token"] = token

    return {"status": "verified", "token": token}
