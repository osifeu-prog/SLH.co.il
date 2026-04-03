from cryptography.fernet import Fernet
import os

# הגדרת נתיב לשמירת המפתח
key_path = r"D:\ExpertNet_Core\vault\master.key"
os.makedirs(os.path.dirname(key_path), exist_ok=True)

# יצירת מפתח הצפנה (זה ה"מפתח לכספת")
secret_key = Fernet.generate_key()

with open(key_path, "wb") as key_file:
    key_file.write(secret_key)

print(f"--- SUCCESS ---")
print(f"Master Key Generated at: {key_path}")
print(f"KEEP THIS FILE SAFE! If you lose it, you lose access to your encrypted vault.")