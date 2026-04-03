import os
from dotenv import load_dotenv
load_dotenv(".env", override=True)
print(f"DEBUG: Token from .env is: {os.getenv('BOT_TOKEN')}")
