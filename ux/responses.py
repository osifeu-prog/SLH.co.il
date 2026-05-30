# SLH Bot — responses.py
# All bot messages with rich Markdown formatting (MarkdownV2 safe)
import re

def esc(text: str) -> str:
    """Escape special chars for MarkdownV2."""
    return re.sub(r'([_*\[\]()~>#+\-=|{}.!])', r'\\\\\1', str(text))

def tier_badge(tier: str) -> str:
    badges = {"free":"⬜ Free","silver":"🥈 Silver","gold":"🥇 Gold","diamond":"💎 Diamond","admin":"👑 Admin"}
    return badges.get(tier.lower(), "⬜ Free")

def rank_medal(position: int) -> str:
    return {1:"🥇",2:"🥈",3:"🥉"}.get(position, f"{position}\\.")

def msg_welcome(username: str, tier: str = "free") -> str:
    badge = esc(tier_badge(tier))
    name  = esc(username)
    return f"✦ *SLH — Sovereign Lab Hub* ✦\n━━━━━━━━━━━━━━━━━━━━━\n\nשלום, *{name}*\\! 👋\n\nאני הבוט האוטונומי של SLH\\.\nאני עוזר לך לעקוב אחרי הקמפיין, לצבור נקודות, ולהישאר מחובר\\.\n\n🎖 *Tier שלך:* {badge}\n\n━━━━━━━━━━━━━━━━━━━━━\n👇 *בחר מה תרצה לעשות:*"

def msg_help() -> str:
    return ("📖 *רשימת הפקודות*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👤 *משתמש*\n"
            "  /register — הצטרפות לעדכונים\n"
            "  /donate — תמיכה בפרויקט\n"
            "  /status — סטטוס הקמפיין\n"
            "  /checkin — צק\\-אין יומי \\(\\+5 נקודות\\)\n"
            "  /points — הנקודות שלי\n"
            "  /leaderboard — טופ 5\n"
            "  /daily — משימות יומיות\n"
            "  /referral — לינק הפניה אישי\n"
            "  /stats — סטטיסטיקת קמפיין\n"
            "  /roadmap — מפת הדרכים\n"
            "  /feedback — שלח משוב\n"
            "  /tasks — משימות סוף שבוע\n"
            "  /myid — Telegram ID שלי\n"
            "  /support — קהילת התמיכה\n"
            "  /backup — גיבוי\n\n"
            "👑 *Admin בלבד*\n"
            "  /broadcast — שלח לכולם\n"
            "  /users — משתמשים רשומים\n"
            "  /morning — דוח בוקר\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🌐 [קמפיין SLH](https://slh\\-nft\\.com/campaign/)")

def msg_checkin_success(username: str, points_earned: int, total_points: int, streak: int = 1) -> str:
    name = esc(username)
    streak_text = f"🔥 *רצף:* {esc(streak)} ימים\\!" if streak > 1 else "📅 יום ראשון — בהצלחה\\!"
    return f"✅ *צק\\-אין הושלם\\!*\n━━━━━━━━━━━━━━━━━━━━━\n\nכל הכבוד, *{name}*\\! 🎉\n\n⚡ *נקודות שהרווחת:* \\+{esc(points_earned)}\n💰 *סהכ נקודות:* {esc(total_points)}\n{streak_text}\n\n━━━━━━━━━━━━━━━━━━━━━\n📌 חזור מחר לצק\\-אין נוסף\\!"

def msg_checkin_already() -> str:
    return "⏳ *כבר צקת אין היום\\!*\n\nחזור מחר לצבור נקודות נוספות\\.\n🔔 תקבל תזכורת ב\\-08:00\\."

def msg_points(username: str, points: int, tier: str, rank: int = None) -> str:
    name  = esc(username)
    badge = esc(tier_badge(tier))
    rank_line = f"🏆 *דירוג שלך:* \\#{esc(rank)}\n" if rank else ""
    return f"💰 *הנקודות שלך*\n━━━━━━━━━━━━━━━━━━━━━\n\n👤 *{name}*\n🎖 *Tier:* {badge}\n{rank_line}\n⚡ *נקודות:* {esc(points)}\n\n━━━━━━━━━━━━━━━━━━━━━\n📈 המשך לצבור — עשה /checkin ו\\-/daily\\!"

def msg_leaderboard(entries: list) -> str:
    lines = ["🏆 *לוח המובילים — טופ 5*\n━━━━━━━━━━━━━━━━━━━━━\n"]
    for i, entry in enumerate(entries[:5], 1):
        medal = rank_medal(i)
        name  = esc(entry.get("username","?"))
        pts   = esc(entry.get("points",0))
        badge = esc(tier_badge(entry.get("tier","free")))
        lines.append(f"{medal} *{name}* — {pts} נקודות {badge}")
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━")
    lines.append("🔥 רוצה לעלות? עשה /checkin ו\\-/daily\\!")
    return "\n".join(lines)

def msg_status(raised: float, goal: float, backers: int, days_left: int) -> str:
    pct = min(int((raised / goal) * 100), 100)
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    return f"📊 *סטטוס קמפיין SLH*\n━━━━━━━━━━━━━━━━━━━━━\n\n💸 *גויס:*  / \n📈 *התקדמות:* {esc(pct)}%\n{esc(bar)}\n\n👥 *תומכים:* {esc(backers)}\n⏳ *ימים שנותרו:* {esc(days_left)}\n\n━━━━━━━━━━━━━━━━━━━━━\n🌐 [לדף הקמפיין](https://slh\\-nft\\.com/campaign/)"

def msg_daily(missions: list) -> str:
    lines = ["📋 *משימות יומיות*\n━━━━━━━━━━━━━━━━━━━━━\n"]
    total = sum(m["points"] for m in missions)
    earned = sum(m["points"] for m in missions if m.get("done"))
    for m in missions:
        icon = "✅" if m.get("done") else "⬜"
        lines.append(f"{icon} {esc(m['title'])} — \\+{esc(m['points'])} נקודות")
    lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━")
    lines.append(f"⚡ *הרווחת:* {esc(earned)} / {esc(total)} נקודות")
    return "\n".join(lines)

def msg_referral(username: str, referral_link: str, referral_count: int) -> str:
    return f"🔗 *לינק ההפניה שלך*\n━━━━━━━━━━━━━━━━━━━━━\n\n👤 *{esc(username)}*\n👥 *הפניות:* {esc(referral_count)}\n\n📎 *הלינק שלך:*\n{esc(referral_link)}\n\n💡 *כל הפניה מוצלחת = \\+20 נקודות\\!*\n\n━━━━━━━━━━━━━━━━━━━━━\nשתף עם חברים ועלה בלוח\\!"

def msg_donate() -> str:
    return ("💎 *תמוך בפרויקט SLH*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            "כל תרומה מקרבת אותנו למטרה\\!\n\n"
            "🎁 *תגמולים לתורמים:*\n"
            "  💰 \\\\+ → Tier Silver \\+ 50 נקודות\n"
            "  🥇 \\\\+ → Tier Gold \\+ 300 נקודות\n"
            "  💎 \\\\+ → Tier Diamond \\+ גישה מוקדמת\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🌐 [לדף התרומה](https://slh\\-nft\\.com/campaign/)")

def msg_register_success(username: str) -> str:
    return f"🎉 *ברוך הבא, {esc(username)}\\!*\n━━━━━━━━━━━━━━━━━━━━━\n\n✅ נרשמת בהצלחה למערכת SLH\\.\n\n⚡ *קיבלת \\+10 נקודות בונוס\\!*\n\n━━━━━━━━━━━━━━━━━━━━━\n📌 הצעד הבא: /checkin לצק\\-אין יומי"

def msg_register_already() -> str:
    return "ℹ️ *כבר רשום\\!*\n\nאתה כבר חלק מהמערכת\\.\nבדוק את /points לראות את הנקודות שלך\\."

def msg_feedback_success() -> str:
    return "📨 *תודה על המשוב\\!*\n\nקיבלנו את הפידבק שלך ונתחשב בו\\. 🙏\n⚡ \\+5 נקודות על שיתוף הפעולה\\!"

def msg_roadmap() -> str:
    return ("🗺 *מפת הדרכים — SLH*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            "✅ *שלב 1 — הושלם*\n  בוט Telegram \\+ מערכת נקודות\n\n"
            "🔄 *שלב 2 — בתהליך*\n  אינטגרציה AI \\+ זהות דיגיטלית\n\n"
            "⏳ *שלב 3 — מתוכנן*\n  ממשק Web \\+ NFT Access Tokens\n\n"
            "🔮 *שלב 4 — עתיד*\n  Sovereign Lab — קהילה אוטונומית\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n🌐 [אתר SLH](https://slh\\-nft\\.com/campaign/)")

def msg_error_generic() -> str:
    return "⚠️ *שגיאה זמנית*\n\nמשהו השתבש\\. נסה שוב בעוד כמה שניות\\.\nאם הבעיה נמשכת — כתב ב\\-/support"

def msg_error_admin_only() -> str:
    return "🔒 *פקודה זו זמינה לאדמינים בלבד\\.*"

def msg_error_no_args(command: str) -> str:
    return f"❌ *שימוש שגוי\\!*\n\nדוגמה: /{esc(command)} <הטקסט שלך>"
