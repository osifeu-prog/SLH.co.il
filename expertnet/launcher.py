import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

def setup_diagnostics():
    print("--- ExpertNet System Health Check ---")
    base_path = Path(".")
    
    # בדיקת קבצים קריטיים
    critical_files = ["vault/.env", "abi/contract_abi.json", "scripts/blockchain_manager.py", "scripts/ui_manager.py", "telegram_bot.py"]
    
    all_ok = True
    for file_path in critical_files:
        if not (base_path / file_path).exists():
            print(f"[X] MISSING: {file_path}")
            all_ok = False
        else:
            print(f"[V] Verified: {file_path}")

    # גיבוי DB
    db_file = base_path / "vault/expertnet.db"
    if db_file.exists():
        backup_name = f"backups/expertnet_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy(db_file, backup_name)
        print(f"[V] Backup created: {backup_name}")
    
    return all_ok

if __name__ == "__main__":
    if setup_diagnostics():
        print("\n[!] Launching Bot...")
        subprocess.run(["python", "telegram_bot.py"])
    else:
        print("\n[!] Check failed. Fix missing files first.")