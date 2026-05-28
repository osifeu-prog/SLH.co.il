import logging

logger = logging.getLogger("slh_wallet.ton")


class TonService:
    def __init__(self) -> None:
        # בעתיד נ�-בר לכאן את TON API שלך (SLHMAINNET)
        pass

    async def get_slh_ton_balance(self, address: str) -> float:
        # כרגע ה�-זר לוגי בלבד – עד שנ�-בר API אמיתי
        if not address:
            return 0.0
        return 0.0


ton_service = TonService()

