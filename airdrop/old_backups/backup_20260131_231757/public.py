from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get('/ping')
def ping():
    return {'pong': True}

@router.post('/airdrop')
def send_airdrop(user_id: str, amount: int):
    '''
    פונקציה ניסיונית לשליחת איירדרופ
    - user_id: מזהה המשתמש
    - amount: כמות tokens לשליחה
    '''
    if amount <= 0:
        raise HTTPException(status_code=400, detail='Amount must be positive')

    # לוג בסיסי לניסויי איירדרופ
    print(f"[AIRDROP] Sending {amount} tokens to {user_id}")

    return {'user_id': user_id, 'amount': amount, 'status': 'success'}
