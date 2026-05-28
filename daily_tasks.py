import json, os, datetime

DB_FILE = "daily_tasks.json"
CONTACTS_FILE = "contacts.json"

def load_db(file=DB_FILE):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_db(data, file=DB_FILE):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def checkin(user_id):
    db = load_db()
    today = datetime.date.today().isoformat()
    user = db.get(user_id, {"last_checkin": "", "streak": 0, "points": 0})
    if user["last_checkin"] == today:
        return {"status": "already_checked_in", "points": user["points"]}
    user["streak"] += 1
    user["last_checkin"] = today
    bonus = min(user["streak"], 7) * 5
    user["points"] += bonus
    db[user_id] = user
    save_db(db)
    return {"status": "ok", "points_added": bonus, "total_points": user["points"], "streak": user["streak"]}

def get_user(user_id):
    db = load_db()
    return db.get(user_id, {"points": 0, "streak": 0})

def leaderboard(limit=5):
    db = load_db()
    sorted_users = sorted(db.items(), key=lambda x: x[1]["points"], reverse=True)[:limit]
    return [{"user_id": uid, "points": data["points"], "streak": data["streak"]} for uid, data in sorted_users]

# ---- Contact List ----
def register_contact(user_id, username, full_name):
    contacts = load_db(CONTACTS_FILE)
    contacts[user_id] = {
        "username": username,
        "full_name": full_name,
        "joined": datetime.datetime.now().isoformat()
    }
    save_db(contacts, CONTACTS_FILE)

def get_contacts():
    return load_db(CONTACTS_FILE)


