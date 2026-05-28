import os, zipfile, datetime, shutil

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")

def create_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"backup_{timestamp}.zip"
    zip_path = os.path.join(BACKUP_DIR, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith(".py") or file.endswith(".json") or file.endswith(".html") or file.endswith(".env"):
                    full = os.path.join(root, file)
                    zf.write(full, os.path.relpath(full, "."))
    return zip_path

def restore_backup(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(".")
    return True
