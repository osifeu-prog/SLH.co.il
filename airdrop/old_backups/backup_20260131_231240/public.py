# -*- coding: utf-8 -*-
from fastapi import APIRouter

router = APIRouter()

@router.get("/ping")
def ping():
    return {"pong": True}


