# 📱 שליטה מלאה באתר מטלגרם — מדריך @SLH_Claude_bot
**📅 25 אפריל 2026**

עכשיו אתה יכול לשלוט בכל האתר שלך מ-`@SLH_Claude_bot` — לקרוא, לערוך, לבנות דפים חדשים, להעלות לפרודקשן. **הכל מטלגרם, חינם.**

---

## 🚀 23 פקודות זמינות

### 🛠 עורך אתר (14 חדשות)

#### Inspection — לקרוא ולחפש
```
/cat <file>           # קרא קובץ
/ls [dir]             # רשימת תיקייה
/grep <pat> [target]  # חיפוש בתוכן (HTML/JS/CSS/MD)
/find <pat> [dir]     # חיפוש לפי שם קובץ
```

#### Edit — לערוך
```
/append <file> <text>             # הוסף שורה בסוף קובץ
/replace <file> :: <old> :: <new> # החלף טקסט
/newpage <name>                    # צור דף חדש מתבנית
```

#### Git — להעלות לפרודקשן
```
/commit <msg>  # commit שינויים
/push          # push לגיט-האב
/sync <msg>    # commit + push בבת אחת
```

#### AI-assisted — תן ל-AI לעשות בשבילך
```
/draft <file> <instruction>  # AI מציע diff
/apply                        # אשר + sync (auto commit + push)
/reject                       # בטל
```

#### Help
```
/editor   # תפריט מלא
```

### 🤖 Ops (9 קיימות)
```
/ps  /bots  /logs  /git  /health  /price  /devices  /task  /ai_mode
```

---

## 💡 דוגמאות שימוש (תעשה בפועל)

### דוגמה 1 — לקרוא קובץ
```
/cat website/voice.html
```
מקבל: 30 שורות ראשונות של הקובץ עם מסכת secrets.

### דוגמה 2 — לחפש משהו באתר
```
/grep "Phase 2" website
```
מקבל: כל המקומות באתר שמופיע "Phase 2".

### דוגמה 3 — לתקן טייפו במהירות
```
/replace website/voice.html :: שגאיה :: שגיאה
/sync "fix typo: שגאיה→שגיאה"
```
תיקון + commit + push בשורה אחת. Production מתעדכן בעוד 30-60 שניות.

### דוגמה 4 — ליצור דף חדש
```
/newpage launch
```
יוצר `website/launch.html` עם תבנית RTL מלאה. ואז:
```
/cat website/launch.html
/draft website/launch.html הוסף כותרת ראשית "השקת SLH" ופסקה תיאור
/apply
```

### דוגמה 5 — שינוי AI-מודרך
```
/draft website/index.html שנה את הצבע של הכותרת לזהב
```
AI מחזיר OLD:/NEW: diff. אתה רואה ובודק. ואז:
```
/apply
```
או
```
/reject
```

---

## 🔒 אבטחה

- ✅ רק 2 IDs מורשים: 224223270 (Osif), 8789977826 (secondary)
- ✅ Path traversal חסום: `_safe_path()` מונע גישה מחוץ ל-`/workspace`
- ✅ Secrets מוסתרים מ-`/cat`: `sk-ant-***`, `BOT_TOKEN=***`, etc.
- ✅ `/apply` תמיד דורש draft קיים (לא ניתן להריץ שינוי בלי לראות diff)
- ✅ Subprocess timeouts: 30 שניות מקסימום
- ✅ Container allowlist: `/logs` רק על `slh-*`

---

## 🎯 Workflow מומלץ ליום-יום

### תרחיש: שינוי קטן בדף קיים
```
/cat website/voice.html              # ראה תוכן
/draft website/voice.html שנה X ל-Y  # AI מציע
/apply                                # אשר + עולה
```
**זמן:** 30 שניות. **תוצאה:** שינוי בפרודקשן.

### תרחיש: דף חדש מאפס
```
/newpage <name>                    # יצירת template
/cat website/<name>.html           # ראה
/draft website/<name>.html הוסף תוכן XYZ  # AI ממלא
/apply                              # שמור + commit + push
```

### תרחיש: שינוי גדול שדורש דיון
```
"איך הכי טוב לעצב כפתור CTA לעמוד buy?"   # שיחה חופשית עם AI
/cat website/buy.html                       # ראה קוד
/draft website/buy.html הוסף את הכפתור     # AI כותב
/apply                                       # אשר
```

---

## 🟢 מצב נוכחי

- ✅ Bot LIVE: `connected as @SLH_Claude_bot (id=8324920733)`
- ✅ 23 commands registered
- ✅ Free AI mode (Groq Llama 3.3 70B via /api/ai/chat)
- ✅ זמן תגובה: **~1.6 שניות**
- ✅ 26 containers רצים
- ✅ Production website + API LIVE

---

## 🔗 קישורים

- **Bot:** https://t.me/SLH_Claude_bot
- **Command Center:** https://slh-nft.com/command-center.html
- **Ops Viewer:** https://slh-nft.com/ops-viewer.html
- **המדריך הזה:** https://slh-nft.com/ops-viewer.html?file=TELEGRAM_CONTROL_GUIDE.md

---

**אתה מבוצר. כל מה שאתה צריך לאתר — מטלגרם.**

— *Claude Opus 4.7 · 2026-04-25*
