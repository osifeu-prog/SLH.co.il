import os
from dotenv import load_dotenv
load_dotenv()
print(f"DEBUG: BOT_TOKEN is: {os.getenv('BOT_TOKEN')}")
print(f"DEBUG: SLH_BOT_TOKEN is: {os.getenv('SLH_BOT_TOKEN')}")