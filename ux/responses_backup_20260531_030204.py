# SLH Bot — responses.py
import re
from typing import Optional

def esc(text: Optional[str]) -> str:
    if text is None: return ""
    text = str(text)
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', text)

def tier_badge(tier: str = "free") -> str:
    badges = {"free":"⬜ Free","silver":"🥈 Silver","gold":"🥇 Gold","diamond":"💎 Diamond","admin":"👑 Admin"}
    return badges.get(tier.lower(), "⬜ Free")

def rank_medal(position: int) -> str:
    return {1:"🥇",2:"🥈",3:"🥉"}.get(position, f"{position}\\.")

def msg_welcome(username: str, tier: str = "free") -> str:
    name = esc(username)
    badge = esc(tier_badge(tier))
    return (
        "╔══════════════════════════════════╗\n"
        "║   ███████╗██╗     ██╗  ██╗      ║\n"
        "║   ██╔════╝██║     ██║  ██║      ║\n"
        "║   ███████╗██║     ███████║      ║\n"
        "║   ╚════██║██║     ██╔══██║      ║\n"
        "║   ███████║███████╗██║  ██║      ║\n"
        "║   ╚══════╝╚══════╝╚═╝  ╚═╝      ║\n"
        "║                                  ║\n"
        "║  AI PROJECT CREATION SYSTEM v2  ║\n"
        "║  ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆ ◆      ║\n"
        "╚══════════════════════════════════╝\n\n"
        f"👋 שלום, *{name}*!\n\n"
        "🤖 מה אני?\nSLH הוא מערכת AI ליצירה וניהול פרויקטים דיגיטליים\n"
        "מחנויות NFT ועד מסחר בטוקנים — הכל במקום אחד.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚡ יכולות המערכת\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "01 · AI Chat       Claude, Gemini, Groq\n"
        "02 · Marketplace   חנויות, מוצרים, NFT\n"
        "03 · Rewards       נקודות, הפניות, TON\n"
        "04 · Support       ניטור, כרטיסים, סשנים\n"
        "05 · CRM           משתמשים, tier, analytics\n"
        "06 · Quiz & XP     קריפטו, leaderboard\n"
        "07 · TON Wallet    תשלומים, תמלוגים\n"
        "08 · Infra         DB, Redis, FastAPI\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n🚀 התחל עכשיו\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "/register   → הצטרף למערכת\n/dashboard  → סטטיסטיקות\n/upgrade    → Premium plans\n"
        "/help       → כל הפקודות\n\nslh-nft.com · @SLH_Claude_bot"
    )

def msg_help() -> str:
    return ("📖 *רשימת הפקודות*\n━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👤 *משתמש*\n  /register — הרשמה\n  /donate — תרומה\n  /checkin — צ'ק אין יומי\n"
            "  /points — הנקודות שלי\n  /leaderboard — טופ 5\n  /daily — משימות יומיות\n"
            "  /referral — הפניה\n  /status — סטטוס קמפיין\n  /upgrade — מנויים\n\n"
            "👑 *אדמין*\n  /users — משתמשים\n  /broadcast — שליחה לכולם\n  /doctor — בדיקת מערכת\n\n"
            "🌐 [קמפיין SLH](https://slh-nft.com/campaign/)")

def msg_donate() -> str:
    return ("💎 *תמיכה ב‑SLH  תגמולים מידיים*\n\n"
            "🔹 *כל תורם מקבל:*\n• נקודות בונוס (1 = 10 נקודות)\n• תג מועדף: Supporter / Builder / Founder\n"
            "• גישה מוקדמת לחנויות NFT ולכלי AI\n• עדכונים שוטפים\n\n🔹 *איך תורמים?*\n"
            "שלחו TON לכתובת:\n`UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp`\n\n"
            "🔹 *לאחר התרומה:* /feedback עם txid\n\n🌐 [מפת הדרכים](https://slh-nft.com/campaign/)")

def msg_checkin_success(username: str, points_earned: int, total_points: int, streak: int = 1) -> str:
    name = esc(username)
    streak_text = f"🔥 *רצף:* {streak} ימים!" if streak > 1 else "🌱 יום ראשון — בהצלחה!"
    return f"✅ *צ'ק-אין הושלם!*\n\nכל הכבוד, *{name}* 🎉\n\n⚡ +{points_earned} נקודות\n💰 סה\"כ: {total_points}\n{streak_text}"

def msg_checkin_already() -> str:
    return "⏳ *כבר צ'קת אין היום!*\n\nחזור מחר."

def msg_points(username: str, points: int, tier: str, rank: int = None) -> str:
    name = esc(username)
    badge = esc(tier_badge(tier))
    rank_line = f"🏆 *דירוג:* #{rank}\n" if rank else ""
    return f"💰 *הנקודות שלך*\n\n👤 {name}\n🎖 Tier: {badge}\n{rank_line}\n⚡ נקודות: {points}"

def msg_leaderboard(entries: list) -> str:
    lines = ["🏆 *לוח המובילים — טופ 5*\n━━━━━━━━━━━━━━━━━━━━━\n"]
    for i, e in enumerate(entries[:5], 1):
        lines.append(f"{rank_medal(i)} *{esc(e.get('username','?'))}* — {e.get('points',0)} נקודות {esc(tier_badge(e.get('tier','free')))}")
    lines.append("\n━━━━━━━━━━━━━━━━━━━━━\n🔥 רוצה לעלות? עשה /checkin ו-/daily!")
    return "\n".join(lines)

def msg_status(raised: float, goal: float, backers: int, days_left: int) -> str:
    pct = min(int((raised/goal)*100),100)
    bar = "█" * (pct//5) + "░" * (20 - pct//5)
    return f"📊 *סטטוס קמפיין SLH*\n━━━━━━━━━━━━━━━━━━━━━\n\n💸 *גויס:* ${raised:,.0f} / ${goal:,.0f}\n📈 התקדמות: {pct}%\n{esc(bar)}\n\n👥 תומכים: {backers}\n⏳ ימים שנותרו: {days_left}\n\n🌐 [לדף הקמפיין](https://slh-nft.com/campaign/)"

def msg_daily(missions: list) -> str:
    lines = ["📋 *משימות יומיות*\n━━━━━━━━━━━━━━━━━━━━━\n"]
    total = sum(m["points"] for m in missions)
    earned = sum(m["points"] for m in missions if m.get("done"))
    for m in missions:
        lines.append(f"{'✅' if m.get('done') else '⬜'} {esc(m['title'])} — +{m['points']} נקודות")
    lines.append(f"\n━━━━━━━━━━━━━━━━━━━━━\n⚡ הרווחת: {earned}/{total} נקודות")
    return "\n".join(lines)

def msg_referral(username: str, link: str, count: int) -> str:
    return f"🔗 *לינק ההפניה שלך*\n\n{link}\n\n👥 הפניות: {count}\n💡 כל הפניה = +20 נקודות!"

def msg_register_success(username: str) -> str:
    return f"🎉 *ברוך הבא, {esc(username)}!*\n\n✅ נרשמת בהצלחה.\n⚡ +10 נקודות בונוס!\n👉 /checkin"

def msg_register_already() -> str:
    return "ℹ️ *כבר רשום!*"

def msg_feedback_success() -> str:
    return "📨 *תודה על המשוב!*\n\n+5 נקודות!"

def msg_roadmap() -> str:
    return ("🗺 *מפת הדרכים — SLH*\n\n✅ שלב 1  בוט Telegram + נקודות\n"
            "🔄 שלב 2  אינטגרציה AI + זהות דיגיטלית\n"
            "⏳ שלב 3  ממשק Web + NFT Access\n"
            "🔮 שלב 4  Sovereign Lab  קהילה אוטונומית\n\n🌐 https://slh-nft.com/campaign/")

def msg_error_generic() -> str:
    return "⚠️ *שגיאה זמנית*\n\nנסה שוב. אם הבעיה נמשכת  /support"

def msg_error_admin_only() -> str:
    return "🔒 *פקודה זו זמינה לאדמינים בלבד.*"

def msg_error_no_args(cmd: str) -> str:
    return f"❌ *שימוש שגוי!*\n\nדוגמה: /{cmd} <טקסט>"
