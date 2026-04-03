import os


def load_admin_id() -> int:
    raw = os.getenv("ADMIN_USER_ID", "").strip()

    if not raw:
        raise RuntimeError("ADMIN_USER_ID missing in environment")

    if not raw.isdigit():
        raise RuntimeError(f"ADMIN_USER_ID invalid: {raw}")

    admin_id = int(raw)

    if admin_id <= 0:
        raise RuntimeError(f"ADMIN_USER_ID invalid numeric value: {admin_id}")

    return admin_id


ADMIN_USER_ID = load_admin_id()


def is_admin(user_id: int) -> bool:
    return int(user_id) == ADMIN_USER_ID