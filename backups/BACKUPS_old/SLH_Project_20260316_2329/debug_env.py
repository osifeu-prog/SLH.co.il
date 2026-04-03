import os
from dotenv import load_dotenv

load_dotenv(".env", override=True)

print("BOT_TOKEN =", repr(os.getenv("BOT_TOKEN")))
print("SLH_BOT_TOKEN =", repr(os.getenv("SLH_BOT_TOKEN")))
