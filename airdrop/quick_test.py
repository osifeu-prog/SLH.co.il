# -*- coding: utf-8 -*-
import requests
import sys

try:
    # ???? ????
    r = requests.get("http://localhost:8000/health", timeout=5)
    print(f"? Panel: {r.status_code} - {r.json()}")
    
    # ???? API ?????
    r = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"? API: {r.status_code}")
    
    print("?? System is responding!")
    sys.exit(0)
except Exception as e:
    print(f"? Error: {e}")
    sys.exit(1)



