import os, psycopg2

# âš ï¸ ×”×—×œ×£ ××ª ×”×›×ª×•×‘×ª ×œ×ž×˜×” ×‘×›×ª×•×‘×ª ×”×¦×™×‘×•×¨×™×ª (Public URL) ×©×”×¢×ª×§×ª!
DB_URL = "postgresql://..." # <-- ×¢×“×›×Ÿ ×¤×”

# ×¨×©×™×ž×ª ×”×¢×ž×•×“×•×ª ×©×¦×¨×™×š ×œ×”×•×¡×™×£
columns = {
    "points": "INTEGER DEFAULT 0",
    "streak": "INTEGER DEFAULT 0",
    "last_checkin": "DATE",
    "balance": "REAL DEFAULT 0",
    "tier": "TEXT DEFAULT 'free'",
    "energy": "INTEGER DEFAULT 100",
    "last_energy_update": "TIMESTAMP DEFAULT NOW()"
}

try:
    print("Connecting to Railway DB via public URL...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    print("Connected successfully.")

    for col_name, col_type in columns.items():
        try:
            cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
            print(f"âœ… Column '{col_name}' added or already exists.")
        except Exception as e:
            print(f"âš ï¸ Could not add column '{col_name}': {e}")

    conn.commit()
    cur.close()
    conn.close()
    print("âœ… DB schema fix completed successfully!")

except Exception as e:
    print(f"âŒ An error occurred: {e}")

