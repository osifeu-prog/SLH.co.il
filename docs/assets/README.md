# docs/assets/ — תמונות וידאו ל-www.slh.co.il

הקבצים בתיקייה הזו מוגשים ב-`https://www.slh.co.il/assets/...`. דרוס את ה-placeholders ב-`guardian.html` על-ידי הוספת קבצים כאן:

## קבצים נדרשים ל-Guardian landing page

| קובץ | תיאור | מידות מומלצות | סטטוס |
|------|--------|----------------|--------|
| `guardian-1.jpg` | מכשיר מלא — חזית + מסך דולק | 800×600 | ⏳ חסר |
| `guardian-2.jpg` | תקריב על המסך עם לוגו SLH | 800×600 | ⏳ חסר |
| `guardian-3.jpg` | המכשיר בשימוש / בקונטקסט | 800×600 | ⏳ חסר |
| `guardian-demo.mp4` | וידאו קצר (15-30 שניות) של המכשיר פועל | 720p, < 5MB | ⏳ חסר |
| `guardian-og.png` | תמונת social sharing (WhatsApp/Facebook/Telegram preview) | **1200×630 בדיוק** | ⏳ חסר — כרגע ה-og:image מצביע לכאן ויחזיר 404 |

## איך לייצר `guardian-og.png`

התמונה הזו מופיעה בתצוגה מקדימה כשמישהו משתף את הלינק ב-WhatsApp / Telegram / Facebook. **חיוני שתהיה חדה ושהטקסט יהיה קריא בזעיר.**

הצעה למבנה:
- רקע כהה (#0f172a) כדי להתאים לעיצוב האתר
- תמונת המכשיר בצד אחד
- טקסט גדול בצד שני: "SLH Guardian" + "₪888 · 99 יחידות"
- לוגו SLH למטה

כלים שאפשר להשתמש:
- Canva — [חפש "Open Graph Image 1200x630"](https://www.canva.com/search/templates?q=og+image)
- Figma — יצירה + export PNG
- Photoshop — File → New → 1200×630px

אחרי הייצור, שמור כ-`guardian-og.png` בתיקייה הזו ו-push:
```
git add docs/assets/guardian-og.png
git commit -m "assets: guardian OG image"
git push
```

## סטטוס נוכחי
- תיקיית `assets/` הוקמה ב-commit A6 (SEO pass)
- אף אחד מהקבצים עדיין לא הועלה
- placeholders בדף מציגים טקסט "הוסף ב-assets/guardian-1.jpg" עד שקבצים אמיתיים יהיו
