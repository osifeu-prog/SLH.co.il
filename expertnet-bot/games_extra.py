"""
ZVIKUSH ARCADE - Extra Games
Trivia (תשחצים), Minesweeper (שולה מוקשים), Sudoku hints
"""
import random
from aiogram.types import InlineKeyboardMarkup as IKM, InlineKeyboardButton as IKB

# ═══════════════════════════════════
# TRIVIA / תשחצים - Question Bank
# ═══════════════════════════════════

TRIVIA_TOPICS = {
    "crypto": {
        "name": "\U0001f4b0 \u05e7\u05e8\u05d9\u05e4\u05d8\u05d5",
        "questions": [
            {"q": "\u05de\u05d9 \u05d9\u05e6\u05e8 \u05d0\u05ea \u05d4\u05d1\u05d9\u05d8\u05e7\u05d5\u05d9\u05df?", "a": ["\u05e1\u05d0\u05d8\u05d5\u05e9\u05d9 \u05e0\u05e7\u05de\u05d5\u05d8\u05d5", "\u05d5\u05d9\u05d8\u05dc\u05d9\u05e7 \u05d1\u05d5\u05d8\u05e8\u05d9\u05df", "\u05d0\u05d9\u05dc\u05d5\u05df \u05de\u05d0\u05e1\u05e7"], "correct": 0, "level": 1},
            {"q": "\u05de\u05d4 \u05d4\u05e9\u05dd \u05e9\u05dc \u05d4\u05e8\u05e9\u05ea \u05e9\u05dc TON?", "a": ["The Open Network", "Token Online", "Telegram Onchain"], "correct": 0, "level": 1},
            {"q": "\u05de\u05d4 \u05d6\u05d4 NFT?", "a": ["\u05d0\u05e1\u05d9\u05de\u05d5\u05df \u05d3\u05d9\u05d2\u05d9\u05d8\u05dc\u05d9 \u05d9\u05d9\u05d7\u05d5\u05d3\u05d9", "\u05de\u05d8\u05d1\u05e2 \u05d5\u05d9\u05e8\u05d8\u05d5\u05d0\u05dc\u05d9", "\u05e1\u05d5\u05d2 \u05e9\u05dc \u05d0\u05e8\u05e0\u05e7"], "correct": 0, "level": 1},
            {"q": "\u05de\u05d4 \u05d6\u05d4 DeFi?", "a": ["\u05e4\u05d9\u05e0\u05e0\u05e1\u05d9\u05dd \u05de\u05d1\u05d5\u05d6\u05e8\u05d9\u05dd", "\u05d1\u05d5\u05e8\u05e1\u05d4 \u05d3\u05d9\u05d2\u05d9\u05d8\u05dc\u05d9\u05ea", "\u05de\u05d8\u05d1\u05e2 \u05e7\u05e8\u05d9\u05e4\u05d8\u05d5"], "correct": 0, "level": 2},
            {"q": "\u05de\u05d4 \u05d6\u05d4 staking?", "a": ["\u05e0\u05e2\u05d9\u05dc\u05ea \u05de\u05d8\u05d1\u05e2\u05d5\u05ea \u05dc\u05d4\u05e0\u05d1\u05ea \u05ea\u05e9\u05d5\u05d0\u05d4", "\u05de\u05e1\u05d7\u05e8 \u05d1\u05de\u05d8\u05d1\u05e2\u05d5\u05ea", "\u05d4\u05e2\u05d1\u05e8\u05ea \u05db\u05e1\u05e3"], "correct": 0, "level": 2},
            {"q": "\u05de\u05d4 APY?", "a": ["\u05ea\u05e9\u05d5\u05d0\u05d4 \u05e9\u05e0\u05ea\u05d9\u05ea \u05db\u05d5\u05dc\u05dc \u05e8\u05d9\u05d1\u05d9\u05ea \u05d3\u05e8\u05d9\u05d1\u05d9\u05ea", "\u05de\u05d7\u05d9\u05e8 \u05e9\u05e0\u05ea\u05d9", "\u05e2\u05de\u05dc\u05ea \u05d4\u05e2\u05d1\u05e8\u05d4"], "correct": 0, "level": 2},
        ]
    },
    "math": {
        "name": "\U0001f4d0 \u05de\u05ea\u05de\u05d8\u05d9\u05e7\u05d4",
        "questions": [
            {"q": "\u05db\u05de\u05d4 \u05d6\u05d4 15% \u05de-200?", "a": ["30", "25", "35"], "correct": 0, "level": 1},
            {"q": "\u05de\u05d4 \u05d4\u05e9\u05d5\u05e8\u05e9 \u05d4\u05e8\u05d9\u05d1\u05d5\u05e2\u05d9 \u05e9\u05dc 144?", "a": ["12", "14", "11"], "correct": 0, "level": 1},
            {"q": "\u05d0\u05dd \u05de\u05e9\u05e7\u05d9\u05e2\u05d9\u05dd 100\u20aa \u05d1-10% \u05e9\u05e0\u05ea\u05d9, \u05d0\u05d7\u05e8\u05d9 \u05e9\u05e0\u05ea\u05d9\u05d9\u05dd?", "a": ["121\u20aa", "120\u20aa", "110\u20aa"], "correct": 0, "level": 2},
            {"q": "50% \u05d4\u05e0\u05d7\u05d4 \u05d5\u05d0\u05d7\u05e8\u05d9\u05d4 50% \u05e2\u05dc\u05d9\u05d9\u05d4 = ?", "a": ["75% \u05de\u05d4\u05de\u05e7\u05d5\u05e8", "100% \u05de\u05d4\u05de\u05e7\u05d5\u05e8", "50% \u05de\u05d4\u05de\u05e7\u05d5\u05e8"], "correct": 0, "level": 3},
        ]
    },
    "general": {
        "name": "\U0001f30d \u05d9\u05d3\u05e2 \u05db\u05dc\u05dc\u05d9",
        "questions": [
            {"q": "\u05de\u05d4 \u05e2\u05d9\u05e8 \u05d4\u05d1\u05d9\u05e8\u05d4 \u05e9\u05dc \u05d9\u05e9\u05e8\u05d0\u05dc?", "a": ["\u05d9\u05e8\u05d5\u05e9\u05dc\u05d9\u05dd", "\u05ea\u05dc \u05d0\u05d1\u05d9\u05d1", "\u05d7\u05d9\u05e4\u05d4"], "correct": 0, "level": 1},
            {"q": "\u05db\u05de\u05d4 \u05e2\u05d5\u05d1\u05d3\u05d9\u05dd \u05d9\u05e9 \u05d1\u05de\u05e4\u05e2\u05dc \u05e9\u05dc \u05e6\u05d1\u05d9\u05e7\u05d4?", "a": ["600", "300", "1000"], "correct": 0, "level": 1},
            {"q": "\u05de\u05d4 \u05e1\u05d5\u05e6\u05d9\u05d5\u05e7\u05e8\u05d8\u05d9\u05d4?", "a": ["\u05e9\u05d9\u05d8\u05ea \u05de\u05de\u05e9\u05dc \u05de\u05d1\u05d5\u05e1\u05e1\u05ea \u05e9\u05d5\u05d5\u05d9\u05d5\u05df", "\u05de\u05e4\u05dc\u05d2\u05d4 \u05e4\u05d5\u05dc\u05d9\u05d8\u05d9\u05ea", "\u05e1\u05d5\u05d2 \u05e9\u05dc \u05db\u05dc\u05db\u05dc\u05d4"], "correct": 0, "level": 2},
        ]
    },
    "tech": {
        "name": "\U0001f4bb \u05d8\u05db\u05e0\u05d5\u05dc\u05d5\u05d2\u05d9\u05d4",
        "questions": [
            {"q": "\u05de\u05d4 \u05d6\u05d4 blockchain?", "a": ["\u05e9\u05e8\u05e9\u05e8\u05ea \u05d1\u05dc\u05d5\u05e7\u05d9\u05dd \u05de\u05d1\u05d5\u05d6\u05e8\u05ea", "\u05e1\u05d5\u05d2 \u05de\u05d7\u05e9\u05d1", "\u05e9\u05e4\u05ea \u05ea\u05db\u05e0\u05d5\u05ea"], "correct": 0, "level": 1},
            {"q": "\u05de\u05d4 \u05d6\u05d4 smart contract?", "a": ["\u05d7\u05d5\u05d6\u05d4 \u05d0\u05d5\u05d8\u05d5\u05de\u05d8\u05d9 \u05e2\u05dc \u05d4\u05d1\u05dc\u05d5\u05e7\u05e6'\u05d9\u05d9\u05df", "\u05d7\u05d5\u05d6\u05d4 \u05e2\u05dd \u05e2\u05d5\u05e8\u05da \u05d3\u05d9\u05df", "\u05d0\u05e4\u05dc\u05d9\u05e7\u05e6\u05d9\u05d4 \u05d7\u05db\u05de\u05d4"], "correct": 0, "level": 2},
            {"q": "\u05de\u05d4 \u05d6\u05d4 API?", "a": ["\u05de\u05de\u05e9\u05e7 \u05ea\u05db\u05e0\u05d5\u05ea \u05dc\u05ea\u05e7\u05e9\u05d5\u05e8\u05ea", "\u05e1\u05d5\u05d2 \u05de\u05e1\u05d3 \u05e0\u05ea\u05d5\u05e0\u05d9\u05dd", "\u05e9\u05e4\u05ea \u05ea\u05db\u05e0\u05d5\u05ea"], "correct": 0, "level": 2},
        ]
    },
}

trivia_games = {}  # uid -> {topic, qidx, score, total, level}


def trivia_topic_keyboard():
    buttons = []
    for key, topic in TRIVIA_TOPICS.items():
        buttons.append([IKB(text=topic["name"], callback_data=f"trv_topic:{key}")])
    return IKM(inline_keyboard=buttons)


def trivia_answer_keyboard(answers, q_idx):
    buttons = []
    for i, ans in enumerate(answers):
        buttons.append([IKB(text=ans, callback_data=f"trv_ans:{q_idx}:{i}")])
    return IKM(inline_keyboard=buttons)


def trivia_start(uid, topic_key, level=1):
    topic = TRIVIA_TOPICS.get(topic_key)
    if not topic:
        return None, "\u274c \u05e0\u05d5\u05e9\u05d0 \u05dc\u05d0 \u05e0\u05de\u05e6\u05d0"

    questions = [q for q in topic["questions"] if q["level"] <= level]
    if not questions:
        questions = topic["questions"]
    random.shuffle(questions)
    questions = questions[:5]  # 5 questions per round

    trivia_games[uid] = {
        "topic": topic_key,
        "topic_name": topic["name"],
        "questions": questions,
        "qidx": 0,
        "score": 0,
        "total": len(questions),
        "level": level,
    }

    return get_trivia_question(uid)


def get_trivia_question(uid):
    game = trivia_games.get(uid)
    if not game:
        return None, "\u274c \u05d0\u05d9\u05df \u05de\u05e9\u05d7\u05e7 \u05e4\u05e2\u05d9\u05dc", 0

    qidx = game["qidx"]
    if qidx >= len(game["questions"]):
        # Game over
        score = game["score"]
        total = game["total"]
        del trivia_games[uid]
        pct = int(score / max(1, total) * 100)
        stars = "\u2b50" * score + "\u2606" * (total - score)
        prize = score * 2  # 2 ZVK per correct answer
        text = (
            f"\U0001f3c6 \u05e1\u05d9\u05d5\u05dd {game['topic_name']}!\n"
            "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
            f"{stars}\n\n"
            f"\u05ea\u05e9\u05d5\u05d1\u05d5\u05ea \u05e0\u05db\u05d5\u05e0\u05d5\u05ea: {score}/{total} ({pct}%)\n"
            f"\u05e4\u05e8\u05e1: +{prize} ZVIKUSH"
        )
        return None, text, prize

    q = game["questions"][qidx]
    text = (
        f"\U0001f4dd {game['topic_name']} - \u05e9\u05d0\u05dc\u05d4 {qidx+1}/{game['total']}\n"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        f"\u2753 {q['q']}"
    )
    kb = trivia_answer_keyboard(q["a"], qidx)
    return kb, text, 0


def trivia_answer(uid, q_idx, ans_idx):
    game = trivia_games.get(uid)
    if not game or game["qidx"] != int(q_idx):
        return None, "\u274c \u05e9\u05d0\u05dc\u05d4 \u05db\u05d1\u05e8 \u05e2\u05d1\u05e8\u05d4", 0

    q = game["questions"][game["qidx"]]
    correct = q["correct"] == int(ans_idx)

    if correct:
        game["score"] += 1
        result = f"\u2705 \u05e0\u05db\u05d5\u05df! {q['a'][q['correct']]}"
    else:
        result = f"\u274c \u05dc\u05d0 \u05e0\u05db\u05d5\u05df. \u05d4\u05ea\u05e9\u05d5\u05d1\u05d4: {q['a'][q['correct']]}"

    game["qidx"] += 1

    # Get next question or game over
    next_kb, next_text, next_prize = get_trivia_question(uid)

    if next_kb is None:
        return None, f"{result}\n\n{next_text}", next_prize

    return next_kb, f"{result}\n\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n{next_text}", 0


# ═══════════════════════════════════
# MINESWEEPER / שולה מוקשים
# ═══════════════════════════════════

mine_games = {}  # uid -> {grid, revealed, flags, mines, size, game_over}

MINE_SIZES = {
    "easy": {"size": 4, "mines": 3, "cost": 0.5, "prize_per_safe": 0.5},
    "medium": {"size": 5, "mines": 6, "cost": 1, "prize_per_safe": 0.8},
    "hard": {"size": 6, "mines": 10, "cost": 2, "prize_per_safe": 1.5},
}


def mine_difficulty_keyboard():
    return IKM(inline_keyboard=[
        [IKB(text="\U0001f7e2 \u05e7\u05dc (4x4, 0.5 ZVK)", callback_data="mine_diff:easy")],
        [IKB(text="\U0001f7e1 \u05d1\u05d9\u05e0\u05d5\u05e0\u05d9 (5x5, 1 ZVK)", callback_data="mine_diff:medium")],
        [IKB(text="\U0001f534 \u05e7\u05e9\u05d4 (6x6, 2 ZVK)", callback_data="mine_diff:hard")],
    ])


def mine_start(uid, difficulty):
    config = MINE_SIZES.get(difficulty)
    if not config:
        return None, "\u274c"

    size = config["size"]
    num_mines = config["mines"]

    # Generate grid
    grid = [[0] * size for _ in range(size)]
    mines_placed = 0
    mine_positions = set()
    while mines_placed < num_mines:
        r, c = random.randint(0, size-1), random.randint(0, size-1)
        if (r, c) not in mine_positions:
            mine_positions.add((r, c))
            grid[r][c] = -1  # -1 = mine
            mines_placed += 1

    # Calculate numbers
    for r in range(size):
        for c in range(size):
            if grid[r][c] == -1:
                continue
            count = 0
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < size and 0 <= nc < size and grid[nr][nc] == -1:
                        count += 1
            grid[r][c] = count

    mine_games[uid] = {
        "grid": grid,
        "revealed": set(),
        "size": size,
        "mines": mine_positions,
        "difficulty": difficulty,
        "safe_revealed": 0,
        "total_safe": size * size - num_mines,
    }

    return mine_grid_keyboard(uid), (
        f"\U0001f4a3 \u05e9\u05d5\u05dc\u05d4 \u05de\u05d5\u05e7\u05e9\u05d9\u05dd ({difficulty})\n"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        f"\U0001f4a3 \u05de\u05d5\u05e7\u05e9\u05d9\u05dd: {num_mines}\n"
        f"\U0001f7e2 \u05de\u05e9\u05d1\u05e6\u05d5\u05ea \u05d1\u05d8\u05d5\u05d7\u05d5\u05ea: {size*size - num_mines}\n\n"
        "\u05dc\u05d7\u05e5 \u05e2\u05dc \u05de\u05e9\u05d1\u05e6\u05ea \u05dc\u05d7\u05e9\u05d5\u05e3. \u05d4\u05d9\u05de\u05e0\u05e2 \u05de\u05de\u05d5\u05e7\u05e9\u05d9\u05dd!"
    )


def mine_grid_keyboard(uid):
    game = mine_games.get(uid)
    if not game:
        return None
    size = game["size"]
    buttons = []
    num_emojis = ["\u2b1c", "1\ufe0f\u20e3", "2\ufe0f\u20e3", "3\ufe0f\u20e3", "4\ufe0f\u20e3", "5\ufe0f\u20e3"]
    for r in range(size):
        row = []
        for c in range(size):
            if (r, c) in game["revealed"]:
                val = game["grid"][r][c]
                if val == -1:
                    txt = "\U0001f4a5"
                elif val == 0:
                    txt = "\u2705"
                else:
                    txt = num_emojis[min(val, 5)]
                row.append(IKB(text=txt, callback_data="noop"))
            else:
                row.append(IKB(text="\u2b1b", callback_data=f"mine:{r}:{c}"))
        buttons.append(row)
    buttons.append([IKB(text="\U0001f3c3 \u05d1\u05e8\u05d7 \u05e2\u05dd \u05d4\u05e9\u05dc\u05dc", callback_data="mine:escape")])
    return IKM(inline_keyboard=buttons)


def mine_reveal(uid, row, col):
    game = mine_games.get(uid)
    if not game:
        return None, "\u274c \u05d0\u05d9\u05df \u05de\u05e9\u05d7\u05e7", 0

    r, c = int(row), int(col)
    if (r, c) in game["revealed"]:
        return mine_grid_keyboard(uid), "\u05db\u05d1\u05e8 \u05e0\u05d7\u05e9\u05e3!", 0

    game["revealed"].add((r, c))
    val = game["grid"][r][c]

    if val == -1:
        # BOOM!
        # Reveal all mines
        for mr, mc in game["mines"]:
            game["revealed"].add((mr, mc))
        prize = game["safe_revealed"]
        config = MINE_SIZES[game["difficulty"]]
        final_prize = int(prize * config["prize_per_safe"])
        del mine_games[uid]
        return mine_grid_keyboard_final(game), (
            f"\U0001f4a5 \u05d1\u05d5\u05dd! \u05e4\u05d2\u05e2\u05ea \u05d1\u05de\u05d5\u05e7\u05e9!\n\n"
            f"\u05de\u05e9\u05d1\u05e6\u05d5\u05ea \u05e9\u05e0\u05d7\u05e9\u05e4\u05d5: {prize}\n"
            f"\u05e4\u05e8\u05e1: +{final_prize} ZVK"
        ), final_prize

    # Safe!
    game["safe_revealed"] += 1

    # Auto-reveal zeros
    if val == 0:
        _flood_reveal(game, r, c)

    # Check win
    if game["safe_revealed"] >= game["total_safe"]:
        config = MINE_SIZES[game["difficulty"]]
        prize = int(game["total_safe"] * config["prize_per_safe"]) + 5  # +5 bonus for clearing
        del mine_games[uid]
        return None, (
            f"\U0001f3c6 \u05e0\u05d9\u05e6\u05d7\u05ea! \u05db\u05dc \u05d4\u05de\u05d5\u05e7\u05e9\u05d9\u05dd \u05e0\u05de\u05e6\u05d0\u05d5!\n\n"
            f"+{prize} ZVK! (+5 \u05d1\u05d5\u05e0\u05d5\u05e1 \u05e0\u05d9\u05e7\u05d5\u05d9)"
        ), prize

    return mine_grid_keyboard(uid), (
        f"\u2705 \u05d1\u05d8\u05d5\u05d7! ({game['safe_revealed']}/{game['total_safe']})"
    ), 0


def mine_escape(uid):
    game = mine_games.get(uid)
    if not game:
        return "\u274c \u05d0\u05d9\u05df \u05de\u05e9\u05d7\u05e7", 0
    config = MINE_SIZES[game["difficulty"]]
    prize = int(game["safe_revealed"] * config["prize_per_safe"])
    del mine_games[uid]
    return (
        f"\U0001f3c3 \u05d1\u05e8\u05d7\u05ea \u05e2\u05dd {prize} ZVK!\n"
        f"\u05de\u05e9\u05d1\u05e6\u05d5\u05ea \u05e9\u05e0\u05d7\u05e9\u05e4\u05d5: {game['safe_revealed']}"
    ), prize


def _flood_reveal(game, r, c):
    size = game["size"]
    stack = [(r, c)]
    while stack:
        cr, cc = stack.pop()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < size and 0 <= nc < size and (nr, nc) not in game["revealed"]:
                    game["revealed"].add((nr, nc))
                    game["safe_revealed"] += 1
                    if game["grid"][nr][nc] == 0:
                        stack.append((nr, nc))


def mine_grid_keyboard_final(game):
    """Show final grid with all mines revealed."""
    size = game["size"]
    num_emojis = ["\u2705", "1\ufe0f\u20e3", "2\ufe0f\u20e3", "3\ufe0f\u20e3", "4\ufe0f\u20e3", "5\ufe0f\u20e3"]
    buttons = []
    for r in range(size):
        row = []
        for c in range(size):
            val = game["grid"][r][c]
            if val == -1:
                txt = "\U0001f4a3"
            elif val == 0:
                txt = "\u2705"
            else:
                txt = num_emojis[min(val, 5)]
            row.append(IKB(text=txt, callback_data="noop"))
        buttons.append(row)
    return IKM(inline_keyboard=buttons)
