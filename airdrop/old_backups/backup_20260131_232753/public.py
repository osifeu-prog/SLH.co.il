from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging, os

# Logging מתקדם
log_folder = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_folder, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_folder, 'airdrop.log'),
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

class AirdropRequest(BaseModel):
    user_id: str
    amount: int

router = APIRouter()

@router.get('/ping')
def ping():
    return {'pong': True}

@router.post('/airdrop')
def send_airdrop(request: AirdropRequest):
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')

    message = f"[AIRDROP] Sending {request.amount} tokens to {request.user_id}"
    print(message)
    logging.info(message)

    return {
        'user_id': request.user_id,
        'amount': request.amount,
        'status': 'success',
        'note': 'mock send - ניסוי'
    }
