from typing import Any

def kb_build(rows):
    return rows

def kb_main_menu():
    return kb_build([
        [{"text": "📊 סטטוס", "callback_data": "cmd_status"}, {"text": "💰 נקודות", "callback_data": "cmd_points"}],
        [{"text": "✅ צק-אין", "callback_data": "cmd_checkin"}, {"text": "📋 משימות", "callback_data": "cmd_daily"}],
        [{"text": "🏆 לוח מובילים", "callback_data": "cmd_leaderboard"}, {"text": "🔗 הפניה", "callback_data": "cmd_referral"}],
        [{"text": "💎 תמוך", "callback_data": "cmd_donate"}, {"text": "📖 עזרה", "callback_data": "cmd_help"}],
        [{"text": "🌐 לדף הקמפיין", "url": "https://slh-nft.com/campaign/"}],
    ])

def kb_after_checkin():
    return kb_build([
        [{"text": "📋 משימות", "callback_data": "cmd_daily"}, {"text": "🏆 לוח מובילים", "callback_data": "cmd_leaderboard"}],
        [{"text": "🔗 שתף", "callback_data": "cmd_referral"}],
    ])

def kb_after_points():
    return kb_build([
        [{"text": "✅ צק-אין", "callback_data": "cmd_checkin"}, {"text": "📋 משימות", "callback_data": "cmd_daily"}],
        [{"text": "🏆 לוח מובילים", "callback_data": "cmd_leaderboard"}],
    ])

def kb_donate():
    return kb_build([
        [{"text": "💎 תרום עכשיו", "url": "https://slh-nft.com/campaign/"}],
        [{"text": "📊 סטטוס", "callback_data": "cmd_status"}, {"text": "🗺 Roadmap", "callback_data": "cmd_roadmap"}],
    ])

def kb_status():
    return kb_build([
        [{"text": "💎 תמוך", "url": "https://slh-nft.com/campaign/"}, {"text": "🗺 Roadmap", "callback_data": "cmd_roadmap"}],
        [{"text": "📊 סטטיסטיקה", "callback_data": "cmd_stats"}],
    ])

def kb_leaderboard():
    return kb_build([
        [{"text": "✅ צק-אין", "callback_data": "cmd_checkin"}, {"text": "📋 משימות", "callback_data": "cmd_daily"}],
        [{"text": "🔗 הפנה חברים", "callback_data": "cmd_referral"}],
    ])

def kb_daily():
    return kb_build([
        [{"text": "✅ צק-אין", "callback_data": "cmd_checkin"}, {"text": "💰 נקודות", "callback_data": "cmd_points"}],
    ])

def kb_help():
    return kb_build([
        [{"text": "📊 סטטוס", "callback_data": "cmd_status"}, {"text": "✅ צק-אין", "callback_data": "cmd_checkin"}],
        [{"text": "🏆 לוח מובילים", "callback_data": "cmd_leaderboard"}, {"text": "💎 תמוך", "callback_data": "cmd_donate"}],
        [{"text": "💬 תמיכה", "url": "https://t.me/SLH_support"}],
    ])

def kb_referral():
    return kb_build([
        [{"text": "🏆 לוח מובילים", "callback_data": "cmd_leaderboard"}, {"text": "💰 נקודות", "callback_data": "cmd_points"}],
    ])

def kb_roadmap():
    return kb_build([
        [{"text": "📊 סטטוס", "callback_data": "cmd_status"}, {"text": "💎 תמוך", "callback_data": "cmd_donate"}],
        [{"text": "🌐 אתר SLH", "url": "https://slh-nft.com/campaign/"}],
    ])

def kb_back_to_menu():
    return kb_build([[{"text": "🏠 חזור לתפריט", "callback_data": "cmd_menu"}]])

def kb_admin_panel():
    return kb_build([
        [{"text": "📢 Broadcast", "callback_data": "admin_broadcast"}, {"text": "👥 משתמשים", "callback_data": "admin_users"}],
        [{"text": "📊 דוח בוקר", "callback_data": "admin_morning"}, {"text": "💾 גיבוי", "callback_data": "admin_backup"}],
    ])
