# -*- coding: utf-8 -*-
"""
One-off: send 6 personalized DMs to SLH community members (night 21.4).
Uses POST /api/broadcast/send with target=custom per recipient.
After run: safe to delete. Contains the broadcast key (default),
so NOT checked into git long-term.
"""
import json
import sys
import urllib.request
import urllib.error

API = "https://slh-api-production.up.railway.app/api/broadcast/send"
KEY = "slh-broadcast-2026-change-me"

MSG_ZVIKA = (
    "היי צביקה 👋\n"
    "\n"
    "מכינים לך ב-SLH Spark משהו אישי — סוכן שיעזור לשפר לך את מה שלא עובד.\n"
    "\n"
    "מבקש ממך דבר אחד בלבד:\n"
    "✍️ כתוב על דף רשימה של כל מה שהיום לא עובד (בעבודה, במערכות שאתה משתמש בהן, בשגרה).\n"
    "📝 העתק את הרשימה לצ'אט כאן בטלגרם\n"
    "📸 גם צלם את הדף ושלח תמונה\n"
    "\n"
    "נקרא, נזהה, ונתאים את המערכת לצעדים שלך.\n"
    "בעתיד זיהוי אוטומטי מתמונה — בינתיים נקרא ביד.\n"
    "\n"
    "— Osif + הסוכן של SLH"
)

MSG_ELIEZER = (
    "היי אליעזר 👋\n"
    "\n"
    "מכינים לך ב-SLH Spark משהו אישי — סוכן שיעזור לשפר לך את מה שלא עובד.\n"
    "\n"
    "מבקש ממך דבר אחד בלבד:\n"
    "✍️ כתוב על דף רשימה של כל מה שהיום לא עובד (בעבודה, במערכות שאתה משתמש בהן, בשגרה).\n"
    "📝 העתק את הרשימה לצ'אט כאן בטלגרם\n"
    "📸 גם צלם את הדף ושלח תמונה\n"
    "\n"
    "נקרא, נזהה, ונתאים את המערכת לצעדים שלך.\n"
    "בעתיד זיהוי אוטומטי מתמונה — בינתיים נקרא ביד.\n"
    "\n"
    "— Osif + הסוכן של SLH"
)

MSG_ZOHAR = (
    "היי זוהר 👋\n"
    "\n"
    "יש לך קהילה גדולה, ואני רוצה להציע לך להיות מהראשונים לפיילוט חדש של SLH Spark — מערכת ניהול קהילה בשפה שלך.\n"
    "\n"
    "הרעיון: במקום \"דולר\"/\"שקל\", כל חבר בקהילה שלך ייתן שמות משלו לנקודות:\n"
    "• דולר = \"חיבוקים\" 🤗\n"
    "• יורו = \"מטבעות\" 🪙\n"
    "• שקל = \"אהבה\" ❤️\n"
    "(או כל שם שהקהילה תבחר)\n"
    "\n"
    "זה מרגיש יותר חם, יותר שלנו, ופחות מאיים.\n"
    "בעתיד נוסיף שכבת פרטיות נוספת לארנקים.\n"
    "\n"
    "📋 תרצה להיות חלק מהפיילוט הראשון?\n"
    "כתוב לי מה חסר לך עכשיו בניהול הקהילה — וננסה להתאים.\n"
    "\n"
    "— Osif"
)

MSG_YAHAV = (
    "היי יהב 👋\n"
    "\n"
    "יש לך קהילה גדולה ואני רוצה לצרף אותך לפיילוט של מערכת ניהול קהילה ב-SLH Spark.\n"
    "\n"
    "הרעיון הייחודי: כל קהילה בוחרת שם משלה לנקודות — דולר יכול להיות \"חיבוקים\", שקל \"אהבה\", יורו \"מטבעות\". שפה רכה ונעימה, לא כספית-מאיימת.\n"
    "זה מנגנון של ביטחון פסיכולוגי לחברים + פחות חסמים כניסה.\n"
    "\n"
    "תכתוב לי:\n"
    "📋 איך אתה מנהל היום את הקהילה?\n"
    "📋 מה שיפור אחד היה משנה לך את השבוע?\n"
    "\n"
    "בונה לך את הכלי.\n"
    "\n"
    "— Osif"
)

MSG_YAARA = (
    "היי יערה 👋\n"
    "\n"
    "ראינו את הקורס החדש שלך ואנחנו רוצים להציע לך חבילת פעילות מלאה ב-SLH Spark:\n"
    "\n"
    "📚 העלאת הקורס לחנות הקהילה + פיד + כל המיקומים הציבוריים\n"
    "📸 קטלוג עם תמונות + מחירים\n"
    "🤖 בוט טלגרם אישי למכירות\n"
    "💰 ארנק + מנגנון מבצעים מובנה\n"
    "📢 הפצה אוטומטית ל-Facebook + Instagram\n"
    "👤 סוכן אישי שיעלה, יפרסם, וילווה אותך לאורך כל הדרך\n"
    "\n"
    "💵 מחיר חד-פעמי: ₪22,221\n"
    "תשלום: Bit / PayBox / אשראי / PayPal / העברה בנקאית / TON / BNB\n"
    "\n"
    "אם זה נשמע מעניין — כתבי חזרה ונעבור לפרטים.\n"
    "\n"
    "— Osif"
)

MSG_RAMI = (
    "היי 👋\n"
    "\n"
    "אני Osif מ-SLH Spark — ראיתי שנרשמת למערכת ורציתי להכיר אותך טוב יותר לפני שאני מציע משהו.\n"
    "\n"
    "3 שאלות קצרות:\n"
    "• מה הביא אותך אלינו?\n"
    "• במה אתה מתעסק ביומיום?\n"
    "• איפה חסר לך כלי/תמיכה/מערכת שהיית רוצה?\n"
    "\n"
    "אחרי התשובה — אתאים לך סוכן אישי. לא אעביר לך מכירה לפני שאני יודע איך המערכת יכולה לתרום לך.\n"
    "\n"
    "— Osif"
)

TARGETS = [
    (1185887485, "Zvika",    MSG_ZVIKA),
    (8088324234, "Eliezer",  MSG_ELIEZER),
    (480100522,  "Zohar",    MSG_ZOHAR),
    (7940057720, "Yahav",    MSG_YAHAV),
    (590733872,  "Yaara",    MSG_YAARA),
    (920721513,  "Rami",     MSG_RAMI),
]


def send_one(tg_id: int, name: str, message: str) -> dict:
    payload = json.dumps({
        "target": "custom",
        "custom_ids": [tg_id],
        "message": message,
        "admin_key": KEY,
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        API,
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return {"ok": True, "http": resp.status, "body": body}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return {"ok": False, "http": e.code, "body": body}
    except Exception as e:
        return {"ok": False, "http": 0, "body": str(e)}


def main() -> int:
    print(f"[INFO] Sending to {len(TARGETS)} recipients via {API}\n")
    summary = []
    for tg_id, name, msg in TARGETS:
        r = send_one(tg_id, name, msg)
        status = "OK " if r["ok"] else "ERR"
        body_preview = r["body"][:300].replace("\n", " ")
        print(f"[{status}] {name:<10s} tg={tg_id}  http={r['http']}")
        print(f"         {body_preview}")
        summary.append((name, tg_id, r["ok"], r["http"]))
        print()

    print("\n=== SUMMARY ===")
    for name, tid, ok, code in summary:
        mark = "✅" if ok else "❌"
        print(f"  {mark}  {name:<10s} tg={tid}  http={code}")

    fails = sum(1 for _, _, ok, _ in summary if not ok)
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
