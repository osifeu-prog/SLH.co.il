# -*- coding: utf-8 -*-
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get('/ping')
def ping():
    return {'pong': True}

@router.post('/airdrop')
def send_airdrop(user_id: str, amount: int):
    '''
    ׳₪׳•׳ ׳§׳¦׳™׳” ׳ ׳™׳¡׳™׳•׳ ׳™׳× ׳׳©׳׳™ן¿½-׳× ׳-׳™׳™׳¨׳“׳¨׳•׳₪
    - user_id: ׳׳–׳”׳” ׳”׳׳©׳×׳׳©
    - amount: ׳›׳׳•׳× tokens ׳׳©׳׳™ן¿½-׳”
    '''
    if amount <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')

    # ׳׳•׳’ ׳‘׳¡׳™׳¡׳™ ׳׳ ׳™׳¡׳•׳™׳™ ׳-׳™׳™׳¨׳“׳¨׳•׳₪
    print(f"[AIRDROP] Sending {amount} tokens to {user_id}")

    return {'user_id': user_id, 'amount': amount, 'status': 'success'}



