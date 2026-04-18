"""
ZVIKUSH ULTIMATE ARCADE - Interactive Game Module
Every game requires PLAYER INPUT - choose, aim, decide!

Telegram animated dice: send_dice with emoji returns animated result.
  🎲=dice(1-6) 🎯=darts(1-6,6=bull) 🏀=basket(1-5,4-5=score)
  🎳=bowling(1-6,6=strike) 🎰=slots(1-64,64=jackpot) ⚽=football(1-5,3-5=goal)
"""
import random
import asyncio
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB


# ═══════════════════════════════════
# Leaderboard & Stats
# ═══════════════════════════════════
leaderboard = {}  # uid -> {username, total_won, games_played, games_won}


def update_leaderboard(uid, username, u):
    leaderboard[uid] = {
        "username": username or "?",
        "total_won": u.get("total_won_zvk", 0),
        "games_played": u.get("games_played", 0),
        "games_won": u.get("games_won", 0),
    }


def get_leaderboard_text():
    if not leaderboard:
        return "\U0001f3c6 \u05dc\u05d5\u05d7 \u05de\u05d5\u05d1\u05d9\u05dc\u05d9\u05dd\n\n\u05e2\u05d3\u05d9\u05d9\u05df \u05d0\u05d9\u05df \u05e9\u05d7\u05e7\u05e0\u05d9\u05dd."
    sorted_lb = sorted(leaderboard.items(), key=lambda x: x[1]["total_won"], reverse=True)[:10]
    lines = ["\U0001f3c6 \u05dc\u05d5\u05d7 \u05de\u05d5\u05d1\u05d9\u05dc\u05d9\u05dd\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n"]
    medals = ["\U0001f947", "\U0001f948", "\U0001f949"]
    for i, (uid, data) in enumerate(sorted_lb):
        medal = medals[i] if i < 3 else f"{i+1}."
        wr = (data["games_won"] / max(1, data["games_played"])) * 100
        lines.append(f"{medal} @{data['username']} | {data['total_won']:.0f} ZVK | {wr:.0f}%")
    return "\n".join(lines)


# Easter eggs - unlocked by achievements
EASTER_EGGS = {
    "konami": {"text": "\U0001f3ae \u2b06\u2b06\u2b07\u2b07\u2b05\u27a1\u2b05\u27a1 BA START!\n\U0001f48e +30 ZVIKUSH!", "bonus": 30},
    "1337": {"text": "\U0001f4bb L33T MODE!\n\U0001f48e +13 ZVIKUSH!", "bonus": 13},
    "42": {"text": "\U0001f30c The Answer to Life, Universe & Everything\n\U0001f48e +42 ZVIKUSH!", "bonus": 42},
    "bitcoin": {"text": "\u20bf To the moon! \U0001f680\n\U0001f48e +21 ZVIKUSH!", "bonus": 21},
    "zvikush": {"text": "\U0001f451 ZVIKUSH FOREVER!\n\U0001f48e +50 ZVIKUSH!", "bonus": 50},
    "spark": {"text": "\u26a1 SPARK IND ACTIVATED!\n\U0001f48e +25 ZVIKUSH!", "bonus": 25},
}

# Free daily spins
DAILY_FREE_SPINS = 3


def get_daily_spins(u):
    today = datetime.now().strftime("%Y-%m-%d")
    if u.get("_free_spin_date") != today:
        u["_free_spin_date"] = today
        u["_free_spins"] = DAILY_FREE_SPINS
    return u.get("_free_spins", 0)


def use_free_spin(u):
    spins = get_daily_spins(u)
    if spins > 0:
        u["_free_spins"] = spins - 1
        return True
    return False


# ═══════════════════════════════════
# SLOTS - Player chooses bet amount
# ═══════════════════════════════════
async def play_slots(bot, chat_id, u):
    cost = 1
    free = use_free_spin(u)
    if not free and u["zvikush"] < cost:
        return False, "\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 ZVIKUSH!\n\u05e1\u05d9\u05d1\u05d5\u05d1\u05d9\u05dd \u05d7\u05d9\u05e0\u05dd: " + str(get_daily_spins(u))
    if not free:
        u["zvikush"] -= cost
    u["games_played"] += 1
    u["total_wagered"] += (0 if free else cost)

    prefix = "\U0001f3b0 \u05e1\u05dc\u05d5\u05d8\u05d9\u05dd" + (" (\u05d7\u05d9\u05e0\u05dd!)" if free else "") + "\n"
    result = await bot.send_dice(chat_id, emoji="\U0001f3b0")
    value = result.dice.value
    await asyncio.sleep(3)

    if value == 64:
        prize = 25
        text = prefix + "\U0001f525\U0001f525\U0001f525 7\ufe0f\u20e3 7\ufe0f\u20e3 7\ufe0f\u20e3 \u05d2'\u05e7\u05e4\u05d5\u05d8!!!\n+25 ZVIKUSH!"
    elif value in (1, 22, 43):
        prize = 10
        text = prefix + "\U0001f389 \u05d8\u05e8\u05d9\u05e4\u05dc! +10 ZVIKUSH!"
    elif value % 4 == 0:
        prize = 3
        text = prefix + "\u2705 \u05d6\u05d5\u05d2! +3 ZVIKUSH!"
    elif value > 50:
        prize = 2
        text = prefix + "\u2705 \u05db\u05de\u05e2\u05d8! +2 ZVIKUSH!"
    else:
        prize = 0
        text = prefix + "\u274c \u05dc\u05d0 \u05d4\u05e4\u05e2\u05dd. \u05e0\u05e1\u05d4 \u05e9\u05d5\u05d1!"

    if prize > 0:
        u["zvikush"] += prize
        u["games_won"] += 1
        u["total_won_zvk"] += prize

    spins_left = get_daily_spins(u)
    text += f"\n\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
    text += f"\n\U0001f3b0 \u05e1\u05d9\u05d1\u05d5\u05d1\u05d9\u05dd \u05d7\u05d9\u05e0\u05dd: {spins_left}"
    return True, text


# ═══════════════════════════════════
# DICE - Player guesses high/low BEFORE roll
# ═══════════════════════════════════
def dice_guess_keyboard():
    return IKM(inline_keyboard=[
        [IKB(text="\u2b06\ufe0f \u05d2\u05d1\u05d5\u05d4 (7+)", callback_data="dice_guess:high"),
         IKB(text="\u2b07\ufe0f \u05e0\u05de\u05d5\u05da (6-)", callback_data="dice_guess:low")],
        [IKB(text="\U0001f3af \u05d3\u05d0\u05d1\u05dc (x5!)", callback_data="dice_guess:double")],
    ])


async def play_dice_roll(bot, chat_id, u, guess):
    cost = 1
    free = use_free_spin(u)
    if not free and u["zvikush"] < cost:
        return "\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 ZVIKUSH!"
    if not free:
        u["zvikush"] -= cost
    u["games_played"] += 1
    u["total_wagered"] += (0 if free else cost)

    r1 = await bot.send_dice(chat_id, emoji="\U0001f3b2")
    await asyncio.sleep(0.5)
    r2 = await bot.send_dice(chat_id, emoji="\U0001f3b2")
    d1, d2 = r1.dice.value, r2.dice.value
    total = d1 + d2
    await asyncio.sleep(3)

    dice_faces = {1: "\u2680", 2: "\u2681", 3: "\u2682", 4: "\u2683", 5: "\u2684", 6: "\u2685"}
    guess_text = {
        "high": "\u05d2\u05d1\u05d5\u05d4 (7+)",
        "low": "\u05e0\u05de\u05d5\u05da (6-)",
        "double": "\u05d3\u05d0\u05d1\u05dc",
    }.get(guess, "?")

    won = False
    if guess == "high" and total >= 7:
        won = True
        prize = 2
    elif guess == "low" and total <= 6:
        won = True
        prize = 2
    elif guess == "double" and d1 == d2:
        won = True
        prize = 5
    else:
        prize = 0

    if d1 == d2 == 6:
        prize = 10
        won = True

    if won:
        u["zvikush"] += prize
        u["games_won"] += 1
        u["total_won_zvk"] += prize
        result = f"\U0001f389 \u05e6\u05d3\u05e7\u05ea! +{prize} ZVK"
    else:
        result = "\u274c \u05dc\u05d0 \u05e6\u05d3\u05e7\u05ea!"

    text = (
        f"\U0001f3b2 \u05e7\u05d5\u05d1\u05d9\u05d5\u05ea\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        f"  {dice_faces[d1]}  {dice_faces[d2]}  =  {total}\n\n"
        f"\u05d4\u05e0\u05d9\u05d7\u05d5\u05e9 \u05e9\u05dc\u05da: {guess_text}\n"
        f"{result}\n\n"
        f"\U0001f3ae ZVIKUSH: {u['zvikush']}"
    )
    return text


# ═══════════════════════════════════
# BASKETBALL - Player chooses power
# ═══════════════════════════════════
def basket_power_keyboard():
    return IKM(inline_keyboard=[
        [IKB(text="\U0001f4aa \u05e7\u05dc \u05e2\u05d3\u05d9\u05df", callback_data="bask_pow:soft"),
         IKB(text="\U0001f4aa\U0001f4aa \u05d1\u05d9\u05e0\u05d5\u05e0\u05d9", callback_data="bask_pow:medium"),
         IKB(text="\U0001f4aa\U0001f4aa\U0001f4aa \u05d7\u05d6\u05e7!", callback_data="bask_pow:hard")],
    ])


async def play_basket_shot(bot, chat_id, u, power):
    cost = 0.3
    free = use_free_spin(u)
    if not free and u["zvikush"] < cost:
        return "\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 ZVIKUSH!"
    if not free:
        u["zvikush"] -= cost
    u["games_played"] += 1

    # Power affects chance: soft=30%, medium=45%, hard=25%
    chances = {"soft": 0.30, "medium": 0.45, "hard": 0.25}
    # But hard gives x2 on hit
    multipliers = {"soft": 1, "medium": 1, "hard": 2}
    chance = chances.get(power, 0.35)
    multi = multipliers.get(power, 1)

    result = await bot.send_dice(chat_id, emoji="\U0001f3c0")
    val = result.dice.value
    await asyncio.sleep(3)

    # Combine telegram animation result with our power mechanic
    hit = val >= 4 or random.random() < chance
    power_text = {
        "soft": "\U0001f4aa \u05e7\u05dc \u05e2\u05d3\u05d9\u05df",
        "medium": "\U0001f4aa\U0001f4aa \u05d1\u05d9\u05e0\u05d5\u05e0\u05d9",
        "hard": "\U0001f4aa\U0001f4aa\U0001f4aa \u05d7\u05d6\u05e7!",
    }.get(power, "?")

    if hit:
        prize = 1 * multi
        u["zvikush"] += prize
        u["games_won"] += 1
        u["total_won_zvk"] += prize
        bonus = f" (x{multi}!)" if multi > 1 else ""
        text = f"\U0001f3c0 \u05db\u05d5\u05d7: {power_text}\n\n\U0001f945 \u05e7\u05dc\u05e2! +{prize} ZVK{bonus}"
    else:
        text = f"\U0001f3c0 \u05db\u05d5\u05d7: {power_text}\n\n\u274c \u05d4\u05d7\u05d8\u05d9\u05d0!"

    text += f"\n\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
    return text


# ═══════════════════════════════════
# DARTS - Player chooses aim zone
# ═══════════════════════════════════
def darts_aim_keyboard():
    return IKM(inline_keyboard=[
        [IKB(text="\U0001f3af \u05de\u05e8\u05db\u05d6 (x3)", callback_data="dart_aim:center"),
         IKB(text="\U0001f535 \u05d8\u05d1\u05e2\u05ea \u05e4\u05e0\u05d9\u05de\u05d9\u05ea (x1.5)", callback_data="dart_aim:inner")],
        [IKB(text="\u2b55 \u05d8\u05d1\u05e2\u05ea \u05d7\u05d9\u05e6\u05d5\u05e0\u05d9\u05ea (x1)", callback_data="dart_aim:outer")],
    ])


async def play_darts_throw(bot, chat_id, u, aim):
    cost = 0.5
    if u["zvikush"] < cost:
        return "\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 ZVIKUSH!"
    u["zvikush"] -= cost
    u["games_played"] += 1
    u["total_wagered"] += cost

    result = await bot.send_dice(chat_id, emoji="\U0001f3af")
    val = result.dice.value  # 6=bullseye
    await asyncio.sleep(3)

    # Aim affects scoring
    aim_text = {"center": "\U0001f3af \u05de\u05e8\u05db\u05d6", "inner": "\U0001f535 \u05e4\u05e0\u05d9\u05de\u05d9\u05ea", "outer": "\u2b55 \u05d7\u05d9\u05e6\u05d5\u05e0\u05d9\u05ea"}.get(aim, "?")
    if aim == "center":
        prize = 6 if val == 6 else 0  # Must hit bullseye
    elif aim == "inner":
        prize = 3 if val >= 4 else 0
    else:
        prize = 1 if val >= 2 else 0

    if prize > 0:
        u["zvikush"] += prize
        u["games_won"] += 1
        u["total_won_zvk"] += prize
        text = f"\U0001f3af \u05db\u05d9\u05d5\u05d5\u05df: {aim_text}\n\n\U0001f389 \u05e7\u05dc\u05e2! +{prize} ZVK"
    else:
        text = f"\U0001f3af \u05db\u05d9\u05d5\u05d5\u05df: {aim_text}\n\n\u274c \u05d4\u05d7\u05d8\u05d0\u05ea!"

    text += f"\n\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
    return text


# ═══════════════════════════════════
# BOWLING - Player chooses lane
# ═══════════════════════════════════
def bowling_lane_keyboard():
    return IKM(inline_keyboard=[
        [IKB(text="\u2b05\ufe0f \u05e9\u05de\u05d0\u05dc", callback_data="bowl_lane:left"),
         IKB(text="\u2b06\ufe0f \u05de\u05e8\u05db\u05d6", callback_data="bowl_lane:center"),
         IKB(text="\u27a1\ufe0f \u05d9\u05de\u05d9\u05df", callback_data="bowl_lane:right")],
    ])


async def play_bowling_roll(bot, chat_id, u, lane):
    cost = 0.5
    if u["zvikush"] < cost:
        return "\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 ZVIKUSH!"
    u["zvikush"] -= cost
    u["games_played"] += 1
    u["total_wagered"] += cost

    result = await bot.send_dice(chat_id, emoji="\U0001f3b3")
    val = result.dice.value
    await asyncio.sleep(3)

    # Lane choice: center is safest, left/right are riskier but higher reward
    lane_text = {
        "left": "\u2b05\ufe0f \u05e9\u05de\u05d0\u05dc",
        "center": "\u2b06\ufe0f \u05de\u05e8\u05db\u05d6",
        "right": "\u27a1\ufe0f \u05d9\u05de\u05d9\u05df",
    }.get(lane, "?")

    if lane == "center":
        prize = 5 if val == 6 else (2 if val >= 4 else 0)
    else:
        prize = 8 if val == 6 else (0)  # Side lanes: strike or nothing

    if prize > 0:
        u["zvikush"] += prize
        u["games_won"] += 1
        u["total_won_zvk"] += prize
        hit_text = "STRIKE!" if val == 6 else "\u05e7\u05dc\u05e2!"
        text = f"\U0001f3b3 \u05de\u05e1\u05dc\u05d5\u05dc: {lane_text}\n\n\U0001f389 {hit_text} +{prize} ZVK"
    else:
        pins = val
        text = f"\U0001f3b3 \u05de\u05e1\u05dc\u05d5\u05dc: {lane_text}\n\n\u274c {pins} \u05e4\u05d9\u05e0\u05d9\u05dd. \u05e0\u05e1\u05d4 \u05e9\u05d5\u05d1!"

    text += f"\n\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
    return text


# ═══════════════════════════════════
# FOOTBALL - Player chooses kick direction
# ═══════════════════════════════════
def football_kick_keyboard():
    return IKM(inline_keyboard=[
        [IKB(text="\u2b05\ufe0f \u05e9\u05de\u05d0\u05dc", callback_data="foot_dir:left"),
         IKB(text="\u2b06\ufe0f \u05de\u05e8\u05db\u05d6", callback_data="foot_dir:center"),
         IKB(text="\u27a1\ufe0f \u05d9\u05de\u05d9\u05df", callback_data="foot_dir:right")],
        [IKB(text="\u2197\ufe0f \u05e4\u05d9\u05e0\u05d4 \u05e2\u05dc\u05d9\u05d5\u05e0\u05d4", callback_data="foot_dir:top")],
    ])


async def play_football_kick(bot, chat_id, u, direction):
    cost = 0.5
    if u["zvikush"] < cost:
        return "\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 ZVIKUSH!"
    u["zvikush"] -= cost
    u["games_played"] += 1
    u["total_wagered"] += cost

    result = await bot.send_dice(chat_id, emoji="\u26bd")
    val = result.dice.value
    await asyncio.sleep(3)

    dir_text = {
        "left": "\u2b05\ufe0f \u05e9\u05de\u05d0\u05dc",
        "center": "\u2b06\ufe0f \u05de\u05e8\u05db\u05d6",
        "right": "\u27a1\ufe0f \u05d9\u05de\u05d9\u05df",
        "top": "\u2197\ufe0f \u05e4\u05d9\u05e0\u05d4 \u05e2\u05dc\u05d9\u05d5\u05e0\u05d4",
    }.get(direction, "?")

    # Direction affects outcome
    if direction == "top":
        prize = 5 if val >= 4 else 0  # Risky but high reward
    elif direction == "center":
        prize = 1 if val >= 3 else 0  # Safe
    else:
        prize = 3 if val >= 4 else 0  # Medium

    if prize > 0:
        u["zvikush"] += prize
        u["games_won"] += 1
        u["total_won_zvk"] += prize
        text = f"\u26bd \u05db\u05d9\u05d5\u05d5\u05df: {dir_text}\n\n\U0001f945 \u05d2\u05d5\u05dc! +{prize} ZVK"
    else:
        text = f"\u26bd \u05db\u05d9\u05d5\u05d5\u05df: {dir_text}\n\n\u274c \u05d4\u05e9\u05d5\u05e2\u05e8 \u05ea\u05e4\u05e1!"

    text += f"\n\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
    return text


# ═══════════════════════════════════
# BLACKJACK - Interactive Hit/Stand
# ═══════════════════════════════════
SUITS = ["\u2660\ufe0f", "\u2665\ufe0f", "\u2666\ufe0f", "\u2663\ufe0f"]
VALUES = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

# Store active blackjack games
bj_games = {}  # uid -> {player, dealer, deck, cost_paid}


def bj_hand_total(hand):
    t = sum(10 if c[0] in "JQK" else 11 if c[0] == "A" else int(c[0]) for c in hand)
    aces = sum(1 for c in hand if c[0] == "A")
    while t > 21 and aces:
        t -= 10
        aces -= 1
    return t


def bj_fmt(hand):
    return " ".join(f"{c[0]}{c[1]}" for c in hand)


def blackjack_action_keyboard():
    return IKM(inline_keyboard=[
        [IKB(text="\U0001f0cf \u05e7\u05dc\u05e3 \u05e0\u05d5\u05e1\u05e3 (Hit)", callback_data="bj:hit"),
         IKB(text="\u270b \u05e2\u05e6\u05d5\u05e8 (Stand)", callback_data="bj:stand")],
    ])


async def play_blackjack_start(bot, chat_id, u, uid):
    cost = 2
    if u["zvikush"] < cost:
        return False, "\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 ZVIKUSH!"
    u["zvikush"] -= cost
    u["games_played"] += 1
    u["total_wagered"] += cost

    deck = [(v, s) for v in VALUES for s in SUITS]
    random.shuffle(deck)
    player = [deck.pop(), deck.pop()]
    dealer = [deck.pop(), deck.pop()]

    bj_games[uid] = {"player": player, "dealer": dealer, "deck": deck, "cost_paid": True}

    pt = bj_hand_total(player)
    if pt == 21:
        # Instant blackjack!
        prize = 5
        u["zvikush"] += prize
        u["games_won"] += 1
        u["total_won_zvk"] += prize
        del bj_games[uid]
        text = (
            "\U0001f0cf \u05d1\u05dc\u05d0\u05e7 \u05d2'\u05e7!\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
            f"\U0001f464 \u05d0\u05ea\u05d4: {bj_fmt(player)} = {pt}\n\n"
            f"\U0001f451 \u05d1\u05dc\u05d0\u05e7 \u05d2'\u05e7! +5 ZVK!\n\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
        )
        return True, text

    text = (
        "\U0001f0cf \u05d1\u05dc\u05d0\u05e7 \u05d2'\u05e7\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        f"\U0001f464 \u05d0\u05ea\u05d4: {bj_fmt(player)} = *{pt}*\n"
        f"\U0001f916 \u05d3\u05d9\u05dc\u05e8: {player[0][0]}{player[0][1]} \U0001f0a0\n\n"
        "\u05de\u05d4 \u05ea\u05e2\u05e9\u05d4?"
    )
    return True, text


async def play_blackjack_action(bot, chat_id, u, uid, action):
    game = bj_games.get(uid)
    if not game:
        return "\u274c \u05d0\u05d9\u05df \u05de\u05e9\u05d7\u05e7 \u05e4\u05e2\u05d9\u05dc. \u05d4\u05ea\u05d7\u05dc \u05de\u05d4\u05d0\u05e8\u05e7\u05d9\u05d9\u05d3."

    player = game["player"]
    dealer = game["dealer"]
    deck = game["deck"]

    if action == "hit":
        player.append(deck.pop())
        pt = bj_hand_total(player)
        if pt > 21:
            del bj_games[uid]
            return (
                "\U0001f0cf \u05d1\u05dc\u05d0\u05e7 \u05d2'\u05e7\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
                f"\U0001f464 \u05d0\u05ea\u05d4: {bj_fmt(player)} = {pt}\n\n"
                f"\U0001f4a5 \u05e4\u05e8\u05e5! \u05e2\u05d1\u05e8\u05ea 21.\n\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
            )
        if pt == 21:
            action = "stand"  # Auto-stand on 21
        else:
            return (
                "\U0001f0cf \u05d1\u05dc\u05d0\u05e7 \u05d2'\u05e7\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
                f"\U0001f464 \u05d0\u05ea\u05d4: {bj_fmt(player)} = *{pt}*\n"
                f"\U0001f916 \u05d3\u05d9\u05dc\u05e8: {dealer[0][0]}{dealer[0][1]} \U0001f0a0\n\n"
                "\u05de\u05d4 \u05ea\u05e2\u05e9\u05d4?"
            )

    # Stand - dealer plays
    while bj_hand_total(dealer) < 17:
        dealer.append(deck.pop())

    pt = bj_hand_total(player)
    dt = bj_hand_total(dealer)
    del bj_games[uid]

    if dt > 21:
        prize = 4
        result = "\U0001f389 \u05d4\u05d3\u05d9\u05dc\u05e8 \u05e4\u05e8\u05e5! +4 ZVK"
    elif pt > dt:
        prize = 3
        result = "\u2705 \u05e0\u05d9\u05e6\u05d7\u05ea! +3 ZVK"
    elif pt == dt:
        prize = 2
        result = "\U0001f91d \u05ea\u05d9\u05e7\u05d5! +2 ZVK \u05d4\u05d7\u05d6\u05e8"
    else:
        prize = 0
        result = "\u274c \u05d4\u05d3\u05d9\u05dc\u05e8 \u05e0\u05d9\u05e6\u05d7!"

    if prize > 0:
        u["zvikush"] += prize
        u["games_won"] += 1
        u["total_won_zvk"] += prize

    return (
        "\U0001f0cf \u05ea\u05d5\u05e6\u05d0\u05d5\u05ea\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        f"\U0001f464 \u05d0\u05ea\u05d4: {bj_fmt(player)} = {pt}\n"
        f"\U0001f916 \u05d3\u05d9\u05dc\u05e8: {bj_fmt(dealer)} = {dt}\n\n"
        f"{result}\n\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
    )


# ═══════════════════════════════════
# MARIO - Player chooses action each step
# ═══════════════════════════════════
mario_games = {}  # uid -> {step, coins, alive, log}


def mario_action_keyboard(step):
    return IKM(inline_keyboard=[
        [IKB(text="\u2b06\ufe0f \u05e7\u05e4\u05d5\u05e5!", callback_data=f"mario_act:jump:{step}"),
         IKB(text="\u27a1\ufe0f \u05e8\u05d5\u05e5!", callback_data=f"mario_act:run:{step}"),
         IKB(text="\u2b07\ufe0f \u05d4\u05ea\u05db\u05d5\u05e4\u05e3!", callback_data=f"mario_act:duck:{step}")],
    ])


async def play_mario_start(bot, chat_id, u, uid):
    cost = 0.5
    if u["zvikush"] < cost:
        return False, "\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 ZVIKUSH!"
    u["zvikush"] -= cost
    u["games_played"] += 1
    u["total_wagered"] += cost

    mario_games[uid] = {"step": 0, "coins": 0, "alive": True, "log": []}

    text = (
        "\U0001f3c3 \u05e8\u05d9\u05e6\u05ea \u05de\u05e8\u05d9\u05d5 - \u05e9\u05dc\u05d1 1/6\n"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        "\U0001f3c3 \u05d0\u05ea\u05d4 \u05e8\u05d5\u05d0\u05d4 \u05de\u05db\u05e9\u05d5\u05dc \u05de\u05ea\u05e7\u05e8\u05d1!\n\n"
        "\u05de\u05d4 \u05ea\u05e2\u05e9\u05d4?"
    )
    return True, text


async def play_mario_action(bot, chat_id, u, uid, action, step):
    game = mario_games.get(uid)
    if not game or not game["alive"]:
        return None, "\u274c \u05d0\u05d9\u05df \u05de\u05e9\u05d7\u05e7 \u05e4\u05e2\u05d9\u05dc."

    if game["step"] != int(step):
        return None, "\u274c \u05e9\u05dc\u05d1 \u05d6\u05d4 \u05db\u05d1\u05e8 \u05e2\u05d1\u05e8."

    obstacles = [
        ("\U0001f4a3", "\u05e4\u05e6\u05e6\u05d4", "jump"),    # Must jump
        ("\U0001f422", "\u05e6\u05d1", "duck"),                 # Must duck
        ("\U0001f344", "\u05e4\u05d8\u05e8\u05d9\u05d4", "run"),# Just run
        ("\u2b50", "\u05db\u05d5\u05db\u05d1", "run"),          # Just run
        ("\U0001f48e", "\u05d9\u05d4\u05dc\u05d5\u05dd", "any"),# Any action works
    ]

    obs_emoji, obs_name, correct = random.choice(obstacles)
    game["step"] += 1
    current_step = game["step"]

    if correct == "any" or action == correct:
        coin_val = 3 if obs_emoji == "\U0001f48e" else (2 if obs_emoji == "\u2b50" else 1)
        game["coins"] += coin_val
        act_name = {
            "jump": "\u2b06\ufe0f \u05e7\u05e4\u05e5",
            "run": "\u27a1\ufe0f \u05e8\u05e5",
            "duck": "\u2b07\ufe0f \u05d4\u05ea\u05db\u05d5\u05e4\u05e3",
        }.get(action, "?")
        game["log"].append(f"{act_name} {obs_emoji} {obs_name} +{coin_val}\U0001f4b0")
    else:
        game["alive"] = False
        game["log"].append(f"\U0001f4a5 {obs_emoji} {obs_name} - \u05e0\u05e4\u05dc\u05ea!")
        del mario_games[uid]

        prize = game["coins"]
        if prize > 0:
            u["zvikush"] += prize
            u["total_won_zvk"] += prize

        progress = "\u2588" * current_step + "\U0001f4a5" + "\u2591" * (6 - current_step)
        text = (
            "\U0001f3c3 \u05e8\u05d9\u05e6\u05ea \u05de\u05e8\u05d9\u05d5\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
            + "\n".join(game["log"]) +
            f"\n\n[{progress}]\n\n\U0001f4a5 \u05e0\u05e4\u05dc\u05ea!\n\U0001f4b0 {prize} ZVK\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
        )
        return False, text

    # Still alive
    if current_step >= 6:
        # Completed!
        game["coins"] += 3  # Completion bonus
        prize = game["coins"]
        u["zvikush"] += prize
        u["games_won"] += 1
        u["total_won_zvk"] += prize
        del mario_games[uid]

        progress = "\u2588" * 6
        text = (
            "\U0001f3c3 \u05e1\u05d9\u05d5\u05dd!\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
            + "\n".join(game["log"]) +
            f"\n\n[{progress}] \U0001f3f0\n\n\U0001f3c6 +{prize} ZVK! (+3 \u05d1\u05d5\u05e0\u05d5\u05e1)\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
        )
        return False, text

    # Next step
    progress = "\u2588" * current_step + "\u2591" * (6 - current_step)
    text = (
        f"\U0001f3c3 \u05e9\u05dc\u05d1 {current_step + 1}/6\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        + "\n".join(game["log"]) +
        f"\n\n[{progress}]\n\U0001f4b0 {game['coins']}\n\n\u05de\u05db\u05e9\u05d5\u05dc \u05de\u05ea\u05e7\u05e8\u05d1! \u05de\u05d4 \u05ea\u05e2\u05e9\u05d4?"
    )
    return True, text


# ═══════════════════════════════════
# ALADDIN - Player chooses which cave
# ═══════════════════════════════════
aladdin_games = {}  # uid -> {caves, revealed, loot}


def aladdin_cave_keyboard(revealed):
    buttons = []
    row = []
    for i in range(8):
        if i in revealed:
            row.append(IKB(text=revealed[i], callback_data="noop"))
        else:
            row.append(IKB(text=f"\u2753 {i+1}", callback_data=f"cave:{i}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([IKB(text="\U0001f3c3 \u05d1\u05e8\u05d7 \u05e2\u05dd \u05d4\u05e9\u05dc\u05dc", callback_data="cave:escape")])
    return IKM(inline_keyboard=buttons)


async def play_aladdin_start(bot, chat_id, u, uid):
    cost = 1
    if u["zvikush"] < cost:
        return False, "\u274c \u05d0\u05d9\u05df \u05de\u05e1\u05e4\u05d9\u05e7 ZVIKUSH!"
    u["zvikush"] -= cost
    u["games_played"] += 1
    u["total_wagered"] += cost

    caves = ["\U0001f48e", "\U0001f40d", "\U0001f4b0", "\U0001f40d", "\U0001f48e", "\u2b50", "\U0001f40d", "\U0001f4b0"]
    random.shuffle(caves)
    aladdin_games[uid] = {"caves": caves, "revealed": {}, "loot": 0}

    text = (
        "\U0001f9de \u05de\u05d8\u05de\u05d5\u05df \u05d0\u05dc\u05d3\u05d9\u05df\n\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        "\U0001f3dc 8 \u05de\u05e2\u05e8\u05d5\u05ea \u05dc\u05e4\u05e0\u05d9\u05da.\n"
        "\U0001f48e = 3 ZVK | \u2b50 = 2 ZVK | \U0001f4b0 = 1 ZVK\n"
        "\U0001f40d = \u05e0\u05d7\u05e9! \u05d4\u05de\u05e2\u05e8\u05d4 \u05e0\u05e1\u05d2\u05e8\u05ea!\n\n"
        "\u05d1\u05d7\u05e8 \u05de\u05e2\u05e8\u05d4 \u05dc\u05e4\u05ea\u05d5\u05d7, \u05d0\u05d5 \u05d1\u05e8\u05d7 \u05e2\u05dd \u05de\u05d4 \u05e9\u05d9\u05e9 \u05dc\u05da!"
    )
    return True, text


async def play_aladdin_choose(bot, chat_id, u, uid, choice):
    game = aladdin_games.get(uid)
    if not game:
        return None, "\u274c \u05d0\u05d9\u05df \u05de\u05e9\u05d7\u05e7 \u05e4\u05e2\u05d9\u05dc."

    if choice == "escape":
        prize = game["loot"]
        if prize > 0:
            u["zvikush"] += prize
            u["games_won"] += 1
            u["total_won_zvk"] += prize
        del aladdin_games[uid]
        return None, (
            f"\U0001f3c3 \u05d1\u05e8\u05d7\u05ea \u05e2\u05dd {prize} ZVK!\n\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
        )

    idx = int(choice)
    cave_content = game["caves"][idx]
    game["revealed"][idx] = cave_content

    values = {"\U0001f48e": 3, "\u2b50": 2, "\U0001f4b0": 1, "\U0001f40d": 0}
    val = values.get(cave_content, 0)

    if val == 0:
        # Snake!
        prize = game["loot"]  # Keep what you found so far
        if prize > 0:
            u["zvikush"] += prize
            u["total_won_zvk"] += prize
        del aladdin_games[uid]
        return None, (
            f"\U0001f40d \u05e0\u05d7\u05e9!\n\n"
            f"\u05e9\u05dc\u05dc \u05e9\u05e0\u05e9\u05de\u05e8: {prize} ZVK\n\U0001f3ae ZVIKUSH: {u['zvikush']}"
        )
    else:
        game["loot"] += val
        return True, (
            f"\U0001f9de \u05de\u05e2\u05e8\u05d4 {idx+1}: {cave_content} +{val} ZVK!\n"
            f"\u05e1\u05d4\"\u05db \u05e9\u05dc\u05dc: {game['loot']}\n\n"
            "\u05dc\u05e4\u05ea\u05d5\u05d7 \u05e2\u05d5\u05d3 \u05de\u05e2\u05e8\u05d4 \u05d0\u05d5 \u05dc\u05d1\u05e8\u05d5\u05d7?"
        )
