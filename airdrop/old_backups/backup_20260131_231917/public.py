from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import os

# ----------------------------
# Logging ×ž×ª×§×“×
# ----------------------------
log_folder = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_folder, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_folder, 'airdrop.log'),
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# ----------------------------
# ×ž×•×“×œ Pydantic ×œ-POST JSON
# ----------------------------
class AirdropRequest(BaseModel):
    user_id: str
    amount: int

router = APIRouter()

@router.get('/ping')
def ping():
    return {'pong': True}

@router.post('/airdrop')
def send_airdrop(request: AirdropRequest):
    '''
    ×¤×•× ×§×¦×™×” × ×™×¡×™×•× ×™×ª ×œ×©×œ×™×—×ª ××™×™×¨×“×¨×•×¤
    - request.user_id: ×ž×–×”×” ×”×ž×©×ª×ž×©
    - request.amount: ×›×ž×•×ª tokens ×œ×©×œ×™×—×”
    '''
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')

    # ×œ×•×’ ×œ×ž×¡×•×£ ×•×§×•×‘×¥
    message = f"[AIRDROP] Sending {request.amount} tokens to {request.user_id}"
    print(message)
    logging.info(message)

    # ×›××Ÿ × ×™×ª×Ÿ ×œ×”×•×¡×™×£ ×©×œ×™×—×” ××ž×™×ª×™×ª ×‘×¢×ª×™×“ (DB / Blockchain / Telegram)
    return {
        'user_id': request.user_id,
        'amount': request.amount,
        'status': 'success',
        'note': 'mock send - × ×™×¡×•×™'
    }
