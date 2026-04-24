from fastapi import FastAPI
from app.api.v1.public import router as public_router

app = FastAPI(title='Airdrop Platform', version='stable')
app.include_router(public_router, prefix='/public', tags=['public'])

# ×›××Ÿ × ×•×›×œ ×œ×”×•×¡×™×£ ×‘×¢×ª×™×“ routers × ×•×¡×¤×™× ×œ-Airdrop, Users ×•×›×•'
