# SLH Bot â€” responses.py
# All bot messages with rich Markdown formatting (MarkdownV2 safe)
import re

def esc(text: str) -> str:
    """Escape special chars for MarkdownV2."""
    return re.sub(r'([_*\[\]()~>#+\-=|{}.!])', r'\\\\\1', str(text))

def tier_badge(tier: str) -> str:
    badges = {"free":"â¬œ Free","silver":"ðŸ¥ˆ Silver","gold":"ðŸ¥‡ Gold","diamond":"ðŸ’Ž Diamond","admin":"ðŸ‘‘ Admin"}
    return badges.get(tier.lower(), "â¬œ Free")

def rank_medal(position: int) -> str:
    return {1:"ðŸ¥‡",2:"ðŸ¥ˆ",3:"ðŸ¥‰"}.get(position, f"{position}\\.")

def msg_welcome(username: str, tier: str = "free") -> str:
    badge = esc(tier_badge(tier))
    name  = esc(username)
    return f"âœ¦ *SLH â€” Sovereign Lab Hub* âœ¦\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\n×©×œ×•×, *{name}*\\! ðŸ‘‹\n\n×× ×™ ×”×‘×•×˜ ×”××•×˜×•× ×•×ž×™ ×©×œ SLH\\.\n×× ×™ ×¢×•×–×¨ ×œ×š ×œ×¢×§×•×‘ ××—×¨×™ ×”×§×ž×¤×™×™×Ÿ, ×œ×¦×‘×•×¨ × ×§×•×“×•×ª, ×•×œ×”×™×©××¨ ×ž×—×•×‘×¨\\.\n\nðŸŽ– *Tier ×©×œ×š:* {badge}\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ‘‡ *×‘×—×¨ ×ž×” ×ª×¨×¦×” ×œ×¢×©×•×ª:*"

def msg_help() -> str:
    return ("ðŸ“– *×¨×©×™×ž×ª ×”×¤×§×•×“×•×ª*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\n"
            "ðŸ‘¤ *×ž×©×ª×ž×©*\n"
            "  /register â€” ×”×¦×˜×¨×¤×•×ª ×œ×¢×“×›×•× ×™×\n"
            "  /donate â€” ×ª×ž×™×›×” ×‘×¤×¨×•×™×§×˜\n"
            "  /status â€” ×¡×˜×˜×•×¡ ×”×§×ž×¤×™×™×Ÿ\n"
            "  /checkin â€” ×¦×§\\-××™×Ÿ ×™×•×ž×™ \\(\\+5 × ×§×•×“×•×ª\\)\n"
            "  /points â€” ×”× ×§×•×“×•×ª ×©×œ×™\n"
            "  /leaderboard â€” ×˜×•×¤ 5\n"
            "  /daily â€” ×ž×©×™×ž×•×ª ×™×•×ž×™×•×ª\n"
            "  /referral â€” ×œ×™× ×§ ×”×¤× ×™×” ××™×©×™\n"
            "  /stats â€” ×¡×˜×˜×™×¡×˜×™×§×ª ×§×ž×¤×™×™×Ÿ\n"
            "  /roadmap â€” ×ž×¤×ª ×”×“×¨×›×™×\n"
            "  /feedback â€” ×©×œ×— ×ž×©×•×‘\n"
            "  /tasks â€” ×ž×©×™×ž×•×ª ×¡×•×£ ×©×‘×•×¢\n"
            "  /myid â€” Telegram ID ×©×œ×™\n"
            "  /support â€” ×§×”×™×œ×ª ×”×ª×ž×™×›×”\n"
            "  /backup â€” ×’×™×‘×•×™\n\n"
            "ðŸ‘‘ *Admin ×‘×œ×‘×“*\n"
            "  /broadcast â€” ×©×œ×— ×œ×›×•×œ×\n"
            "  /users â€” ×ž×©×ª×ž×©×™× ×¨×©×•×ž×™×\n"
            "  /morning â€” ×“×•×— ×‘×•×§×¨\n\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "ðŸŒ [×§×ž×¤×™×™×Ÿ SLH](https://slh\\-nft\\.com/campaign/)")

def msg_checkin_success(username: str, points_earned: int, total_points: int, streak: int = 1) -> str:
    name = esc(username)
    streak_text = f"ðŸ”¥ *×¨×¦×£:* {esc(streak)} ×™×ž×™×\\!" if streak > 1 else "ðŸ“… ×™×•× ×¨××©×•×Ÿ â€” ×‘×”×¦×œ×—×”\\!"
    return f"âœ… *×¦×§\\-××™×Ÿ ×”×•×©×œ×\\!*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\n×›×œ ×”×›×‘×•×“, *{name}*\\! ðŸŽ‰\n\nâš¡ *× ×§×•×“×•×ª ×©×”×¨×•×•×—×ª:* \\+{esc(points_earned)}\nðŸ’° *×¡×”×› × ×§×•×“×•×ª:* {esc(total_points)}\n{streak_text}\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ“Œ ×—×–×•×¨ ×ž×—×¨ ×œ×¦×§\\-××™×Ÿ × ×•×¡×£\\!"

def msg_checkin_already() -> str:
    return "â³ *×›×‘×¨ ×¦×§×ª ××™×Ÿ ×”×™×•×\\!*\n\n×—×–×•×¨ ×ž×—×¨ ×œ×¦×‘×•×¨ × ×§×•×“×•×ª × ×•×¡×¤×•×ª\\.\nðŸ”” ×ª×§×‘×œ ×ª×–×›×•×¨×ª ×‘\\-08:00\\."

def msg_points(username: str, points: int, tier: str, rank: int = None) -> str:
    name  = esc(username)
    badge = esc(tier_badge(tier))
    rank_line = f"ðŸ† *×“×™×¨×•×’ ×©×œ×š:* \\#{esc(rank)}\n" if rank else ""
    return f"ðŸ’° *×”× ×§×•×“×•×ª ×©×œ×š*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\nðŸ‘¤ *{name}*\nðŸŽ– *Tier:* {badge}\n{rank_line}\nâš¡ *× ×§×•×“×•×ª:* {esc(points)}\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ“ˆ ×”×ž×©×š ×œ×¦×‘×•×¨ â€” ×¢×©×” /checkin ×•\\-/daily\\!"

def msg_leaderboard(entries: list) -> str:
    lines = ["ðŸ† *×œ×•×— ×”×ž×•×‘×™×œ×™× â€” ×˜×•×¤ 5*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"]
    for i, entry in enumerate(entries[:5], 1):
        medal = rank_medal(i)
        name  = esc(entry.get("username","?"))
        pts   = esc(entry.get("points",0))
        badge = esc(tier_badge(entry.get("tier","free")))
        lines.append(f"{medal} *{name}* â€” {pts} × ×§×•×“×•×ª {badge}")
    lines.append("\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”")
    lines.append("ðŸ”¥ ×¨×•×¦×” ×œ×¢×œ×•×ª? ×¢×©×” /checkin ×•\\-/daily\\!")
    return "\n".join(lines)

def msg_status(raised: float, goal: float, backers: int, days_left: int) -> str:
    pct = min(int((raised / goal) * 100), 100)
    bar = "â–ˆ" * (pct // 5) + "â–‘" * (20 - pct // 5)
    return f"ðŸ“Š *×¡×˜×˜×•×¡ ×§×ž×¤×™×™×Ÿ SLH*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\nðŸ’¸ *×’×•×™×¡:*  / \nðŸ“ˆ *×”×ª×§×“×ž×•×ª:* {esc(pct)}%\n{esc(bar)}\n\nðŸ‘¥ *×ª×•×ž×›×™×:* {esc(backers)}\nâ³ *×™×ž×™× ×©× ×•×ª×¨×•:* {esc(days_left)}\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸŒ [×œ×“×£ ×”×§×ž×¤×™×™×Ÿ](https://slh\\-nft\\.com/campaign/)"

def msg_daily(missions: list) -> str:
    lines = ["ðŸ“‹ *×ž×©×™×ž×•×ª ×™×•×ž×™×•×ª*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"]
    total = sum(m["points"] for m in missions)
    earned = sum(m["points"] for m in missions if m.get("done"))
    for m in missions:
        icon = "âœ…" if m.get("done") else "â¬œ"
        lines.append(f"{icon} {esc(m['title'])} â€” \\+{esc(m['points'])} × ×§×•×“×•×ª")
    lines.append(f"\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”")
    lines.append(f"âš¡ *×”×¨×•×•×—×ª:* {esc(earned)} / {esc(total)} × ×§×•×“×•×ª")
    return "\n".join(lines)

def msg_referral(username: str, referral_link: str, referral_count: int) -> str:
    return f"ðŸ”— *×œ×™× ×§ ×”×”×¤× ×™×” ×©×œ×š*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\nðŸ‘¤ *{esc(username)}*\nðŸ‘¥ *×”×¤× ×™×•×ª:* {esc(referral_count)}\n\nðŸ“Ž *×”×œ×™× ×§ ×©×œ×š:*\n{esc(referral_link)}\n\nðŸ’¡ *×›×œ ×”×¤× ×™×” ×ž×•×¦×œ×—×ª = \\+20 × ×§×•×“×•×ª\\!*\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n×©×ª×£ ×¢× ×—×‘×¨×™× ×•×¢×œ×” ×‘×œ×•×—\\!"

def msg_donate() -> str:
    return ("ðŸ’Ž *×ª×ž×•×š ×‘×¤×¨×•×™×§×˜ SLH*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\n"
            "×›×œ ×ª×¨×•×ž×” ×ž×§×¨×‘×ª ××•×ª× ×• ×œ×ž×˜×¨×”\\!\n\n"
            "ðŸŽ *×ª×’×ž×•×œ×™× ×œ×ª×•×¨×ž×™×:*\n"
            "  ðŸ’° \\\\+ â†’ Tier Silver \\+ 50 × ×§×•×“×•×ª\n"
            "  ðŸ¥‡ \\\\+ â†’ Tier Gold \\+ 300 × ×§×•×“×•×ª\n"
            "  ðŸ’Ž \\\\+ â†’ Tier Diamond \\+ ×’×™×©×” ×ž×•×§×“×ž×ª\n\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n"
            "ðŸŒ [×œ×“×£ ×”×ª×¨×•×ž×”](https://slh\\-nft\\.com/campaign/)")

def msg_register_success(username: str) -> str:
    return f"ðŸŽ‰ *×‘×¨×•×š ×”×‘×, {esc(username)}\\!*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\nâœ… × ×¨×©×ž×ª ×‘×”×¦×œ×—×” ×œ×ž×¢×¨×›×ª SLH\\.\n\nâš¡ *×§×™×‘×œ×ª \\+10 × ×§×•×“×•×ª ×‘×•× ×•×¡\\!*\n\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸ“Œ ×”×¦×¢×“ ×”×‘×: /checkin ×œ×¦×§\\-××™×Ÿ ×™×•×ž×™"

def msg_register_already() -> str:
    return "â„¹ï¸ *×›×‘×¨ ×¨×©×•×\\!*\n\n××ª×” ×›×‘×¨ ×—×œ×§ ×ž×”×ž×¢×¨×›×ª\\.\n×‘×“×•×§ ××ª /points ×œ×¨××•×ª ××ª ×”× ×§×•×“×•×ª ×©×œ×š\\."

def msg_feedback_success() -> str:
    return "ðŸ“¨ *×ª×•×“×” ×¢×œ ×”×ž×©×•×‘\\!*\n\n×§×™×‘×œ× ×• ××ª ×”×¤×™×“×‘×§ ×©×œ×š ×•× ×ª×—×©×‘ ×‘×•\\. ðŸ™\nâš¡ \\+5 × ×§×•×“×•×ª ×¢×œ ×©×™×ª×•×£ ×”×¤×¢×•×œ×”\\!"

def msg_roadmap() -> str:
    return ("ðŸ—º *×ž×¤×ª ×”×“×¨×›×™× â€” SLH*\nâ”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\n"
            "âœ… *×©×œ×‘ 1 â€” ×”×•×©×œ×*\n  ×‘×•×˜ Telegram \\+ ×ž×¢×¨×›×ª × ×§×•×“×•×ª\n\n"
            "ðŸ”„ *×©×œ×‘ 2 â€” ×‘×ª×”×œ×™×š*\n  ××™× ×˜×’×¨×¦×™×” AI \\+ ×–×”×•×ª ×“×™×’×™×˜×œ×™×ª\n\n"
            "â³ *×©×œ×‘ 3 â€” ×ž×ª×•×›× ×Ÿ*\n  ×ž×ž×©×§ Web \\+ NFT Access Tokens\n\n"
            "ðŸ”® *×©×œ×‘ 4 â€” ×¢×ª×™×“*\n  Sovereign Lab â€” ×§×”×™×œ×” ××•×˜×•× ×•×ž×™×ª\n\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\nðŸŒ [××ª×¨ SLH](https://slh\\-nft\\.com/campaign/)")

def msg_error_generic() -> str:
    return "âš ï¸ *×©×’×™××” ×–×ž× ×™×ª*\n\n×ž×©×”×• ×”×©×ª×‘×©\\. × ×¡×” ×©×•×‘ ×‘×¢×•×“ ×›×ž×” ×©× ×™×•×ª\\.\n×× ×”×‘×¢×™×” × ×ž×©×›×ª â€” ×›×ª×‘ ×‘\\-/support"

def msg_error_admin_only() -> str:
    return "ðŸ”’ *×¤×§×•×“×” ×–×• ×–×ž×™× ×” ×œ××“×ž×™× ×™× ×‘×œ×‘×“\\.*"

def msg_error_no_args(command: str) -> str:
    return f"âŒ *×©×™×ž×•×© ×©×’×•×™\\!*\n\n×“×•×’×ž×”: /{esc(command)} <×”×˜×§×¡×˜ ×©×œ×š>"
