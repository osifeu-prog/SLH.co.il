# -*- coding: utf-8 -*-
import requests

try:
    # ???? ?? ???? ??
    url = "https://api.telegram.org/bot8530795944:AAFXDx-vWZPpiXTlfsv5izUayJ4OpLLq3Ls/getMe"
    response = requests.get(url)
    
    if response.status_code == 200:
        bot_info = response.json()
        print(f"? ???? ??: {bot_info['result']['username']}")
        print(f"?? ??: {bot_info['result']['first_name']}")
    else:
        print(f"? ?????: {response.status_code}")
        
except Exception as e:
    print(f"? ?????: {e}")



