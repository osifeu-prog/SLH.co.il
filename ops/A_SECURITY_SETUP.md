# A — SECURITY SETUP
**SLH Ecosystem · שלב 0 אבטחה**
**הרץ לפני כל דבר אחר. לא לדלג.**

---

## 🔴 0.1 Railway — Env Vars חסרים (P0)

פתח את Railway dashboard → project `SLH.co.il` → **Variables** → הוסף את כולם:

```powershell
# הרץ ב-PowerShell המקומי כדי לייצר ערכים:
# JWT_SECRET
[System.Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Max 256) }))

# ENCRYPTION_KEY (אותו דבר)
[System.Convert]::ToBase64String((1..32 | ForEach-Object { [byte](Get-Random -Max 256) }))

# ADMIN_API_KEYS — בחר 2-3 מחרוזות חזקות, מופרדות בפסיק:
# לדוגמה: slh_admin_$(Get-Random),slh_ops_$(Get-Random)
```

**ערכים להגדיר ב-Railway:**
```
JWT_SECRET=<תוצאת הפקודה הראשונה>
ENCRYPTION_KEY=<תוצאת הפקודה השנייה>
ADMIN_API_KEYS=<key1>,<key2>
ADMIN_BROADCAST_KEY=<מחרוזת חזקה>
INITIAL_ADMIN_PASSWORD=<סיסמה חזקה לOsif>
INITIAL_TZVIKA_PASSWORD=<סיסמה חזקה לTzvika>
ADMIN_USER_ID=224223270
BOT_SYNC_SECRET=<מחרוזת חזקה>
```

**וודא שקיים (כבר אמור להיות):**
```
DATABASE_URL=<Railway provides>
REDIS_URL=<Railway provides>
OPENAI_API_KEY=<שלך>
```

---

## 🔴 0.2 Binance Keys — להחליף מיד

1. כנס ל-[binance.com/en/my/settings/api-management](https://binance.com/en/my/settings/api-management)
2. מחק את ה-API key הקיים
3. צור key חדש עם **IP whitelist** (הכנס את ה-IP של Railway)
4. עדכן ב-.env המקומי + ב-Railway:
```
EXCHANGE_API_KEY=<חדש>
EXCHANGE_SECRET=<חדש>
```

---

## 🔴 0.3 Bot Token Rotation — 30 בוטים

**הרץ פעם אחת ב-@BotFather עבור כל בוט:**
```
/mybots → בחר בוט → API Token → Revoke current token
```

**רשימת כל הטוקנים להחליף ב-.env:**
```env
# קיים (נעשה ב-2026-04-17):
GAME_BOT_TOKEN=✅ done

# נדרש עדיין — 30 בוטים:
CORE_BOT_TOKEN=          # @SLH_Academia_bot
GUARDIAN_BOT_TOKEN=      # Guardian
BOTSHOP_BOT_TOKEN=       # BotShop
WALLET_BOT_TOKEN=        # Wallet
FACTORY_BOT_TOKEN=       # Factory/Investment
FUN_BOT_TOKEN=           # Fun/Promo
ADMIN_BOT_TOKEN=         # @MY_SUPER_ADMIN_bot
AIRDROP_BOT_TOKEN=       # @AIRDROP_bot
CAMPAIGN_TOKEN=          # Campaign
TON_MNH_TOKEN=           # TON/MNH marketplace
SLH_TON_TOKEN=           # SLH TON
SLH_LEDGER_TOKEN=        # Ledger
OSIF_SHOP_TOKEN=         # Osif shop
NIFTI_PUBLISHER_TOKEN=   # NIFTI Publisher
CHANCE_PAIS_TOKEN=       # Chance Pais
NFTY_MADNESS_TOKEN=      # NFTY Madness
TS_SET_TOKEN=            # TS Set
CRAZY_PANEL_TOKEN=       # Crazy Panel
MY_NFT_SHOP_TOKEN=       # My NFT Shop
BEYNONIBANK_TOKEN=       # Beynoni Bank
TEST_BOT_TOKEN=          # Test bot
WEWORK_TEAMVIWER_TOKEN=  # WeWork TeamViewer
EXPERTNET_BOT_TOKEN=     # ExpertNet
MATCH_BOT_TOKEN=         # Match
SCHOOL_BOT_TOKEN=        # School
WELLNESS_BOT_TOKEN=      # Wellness
USERINFO_BOT_TOKEN=      # UserInfo
NFTY_BOT_TOKEN=          # NFTY shop
SLH_CLAUDE_BOT_TOKEN=    # Claude bot
```

**אחרי כל rotation:**
```powershell
# עדכן .env המקומי, ואז restart docker:
docker-compose restart <bot_service_name>

# לדוגמה:
docker-compose restart slh-core-bot
```

---

## 🟠 0.4 הסרת קבצי .bak (102 קבצים)

```powershell
# בדוק מה יימחק קודם (dry run):
Get-ChildItem -Path "D:\SLH_ECOSYSTEM" -Recurse -Filter "*.bak*" | Select-Object FullName

# יצור archive:
$archivePath = "D:\SLH_ECOSYSTEM\archive\bak_files"
New-Item -ItemType Directory -Force -Path $archivePath

# העבר את כולם:
Get-ChildItem -Path "D:\SLH_ECOSYSTEM" -Recurse -Filter "*.bak*" |
    Where-Object { $_.FullName -notlike "*\archive\*" } |
    ForEach-Object {
        $dest = Join-Path $archivePath $_.Name
        Move-Item $_.FullName $dest -Force
        Write-Host "Moved: $($_.FullName)"
    }

Write-Host "Done. Files in archive: $(Get-ChildItem $archivePath | Measure-Object).Count"
```

**קבצים מיוחדים למחיקה ידנית (גיבויים ישנים):**
```powershell
# airdrop/old_backups/ — גיבויים מינואר 2026:
Remove-Item -Recurse "D:\SLH_ECOSYSTEM\airdrop\old_backups"

# tonmnh-bot .bak files (26+ גרסאות של TelegramBot_Core.py):
Get-ChildItem "D:\SLH_ECOSYSTEM\tonmnh-bot\src" -Filter "*.bak*" | Remove-Item

# airdrop/bot/ versions (clean_bot, production_bot, professional_bot, updated_bot*):
# שמור רק: bot/main_bot.py
# Remove:
@("clean_bot.py","production_bot.py","professional_bot.py","updated_bot.py","updated_bot_v2.py","ton_bot.py") |
    ForEach-Object { Remove-Item "D:\SLH_ECOSYSTEM\airdrop\bot\$_" -ErrorAction SilentlyContinue }
```

---

## 🟠 0.5 Archive ops/ folder

```powershell
# 305 קבצי ops → ZIP ארכיון + 5 מסמכים חדשים:
$opsPath = "D:\SLH_ECOSYSTEM\ops"
$archiveDest = "D:\SLH_ECOSYSTEM\archive\ops_snapshots"
New-Item -ItemType Directory -Force -Path $archiveDest

# צור ZIP עם timestamp:
$zipName = "ops_archive_$(Get-Date -Format 'yyyyMMdd').zip"
Compress-Archive -Path "$opsPath\*" -DestinationPath "$archiveDest\$zipName"
Write-Host "Archived to: $archiveDest\$zipName"

# לאחר מכן ניתן לרוקן את ops/ ולהשאיר רק את 5 הקבצים החדשים
```

---

## 🟢 0.6 בדיקת אבטחה — Checklist

לאחר כל השלבים, הרץ:

```powershell
# בדוק שאין סודות exposed ב-git:
git log --all --full-history -- "*.env" --name-only | head -20

# בדוק .gitignore מכסה הכל:
Get-Content "D:\SLH_ECOSYSTEM\.gitignore" | Select-String "\.env|secret|token|key"

# בדוק Railway health:
curl https://slh-fastapi-production.up.railway.app/api/health

# בדוק שJWT_SECRET לא ריק:
# (ב-Railway logs תראה [Startup][WARN] JWT_SECRET empty אם חסר)
```

**Expected health response לאחר תיקון:**
```json
{
  "status": "ok",
  "db": "connected",
  "version": "1.1.0",
  "jwt": "configured",
  "env": "production"
}
```

---

## ⚡ סדר עדיפויות ביצוע

```
[ ] 1. Railway env vars (JWT_SECRET, ADMIN_API_KEYS) — 10 דקות
[ ] 2. Binance keys rotation — 5 דקות
[ ] 3. .bak files → archive — PowerShell, 2 דקות
[ ] 4. Bot tokens (30) — @BotFather, ~1 שעה
[ ] 5. ops/ ZIP archive — 1 דקה
[ ] 6. Health check — curl + בדיקה ב-Railway logs
```
