#!/usr/bin/env bash
# Seed Academia UGC — run once after you have the admin key.
#
# Usage:
#   export ADMIN_KEY='your-rotated-or-railway-admin-key'
#   bash ops/SEED_ACADEMIA_RUN.sh
#
# What it does (idempotent — safe to re-run):
#   1. Approves Osif as instructor #1 (already registered)
#   2. Creates 3 draft courses (pending approval) — idempotent via slug
#   3. Approves all 3 courses (active=TRUE, visible in /academia.html)
#
# If you want to edit course content first, tweak the JSON payloads below.

set -e

: "${ADMIN_KEY:?ADMIN_KEY env var is required. Set it and re-run.}"
API="${SLH_API:-https://slh-api-production.up.railway.app}"

echo "→ 1/7 Approving instructor #1 (Osif)..."
curl -sS -X POST "$API/api/academia/instructor/approve" \
  -H "Content-Type: application/json" \
  -H "X-Admin-Key: $ADMIN_KEY" \
  -d '{"instructor_id":1,"approved":true}' | python -m json.tool
echo

echo "→ 2/7 Creating course: bot-bootcamp..."
C1=$(curl -sS -X POST "$API/api/academia/course/create" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @- <<'JSON'
{
  "instructor_user_id": 224223270,
  "slug": "telegram-bot-bootcamp-he",
  "title_he": "בוט טלגרם בעברית — bootcamp מ-0 ל-deploy",
  "description_he": "קורס מעשי בן 5 מודולים: aiogram 3.x · handlers · FSM · middleware · Railway deploy · webhook setup. כולל boilerplate מ-SLH Spark (ecosystem של 25 בוטים בייצור).",
  "price_ils": 99,
  "price_slh": 0,
  "language": "he",
  "materials_url": "https://slh-nft.com/academia.html#bot-bootcamp",
  "preview_url": ""
}
JSON
)
echo "$C1" | python -m json.tool
ID1=$(echo "$C1" | python -c "import sys,json; print(json.loads(sys.stdin.read()).get('id',''))")
echo

echo "→ 3/7 Creating course: slh-ecosystem-guide..."
C2=$(curl -sS -X POST "$API/api/academia/course/create" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @- <<'JSON'
{
  "instructor_user_id": 224223270,
  "slug": "slh-ecosystem-user-guide",
  "title_he": "מדריך SLH למשתמש — ecosystem end-to-end",
  "description_he": "המדריך הרשמי למשתמשי SLH Spark. מה זה SLH/ZVK/MNH/REP/ZUZ. איך עושים P2P. איך פותחים shop. referral. academy. experts. community.",
  "price_ils": 29,
  "price_slh": 0,
  "language": "he",
  "materials_url": "https://slh-nft.com/academia.html#slh-guide",
  "preview_url": ""
}
JSON
)
echo "$C2" | python -m json.tool
ID2=$(echo "$C2" | python -c "import sys,json; print(json.loads(sys.stdin.read()).get('id',''))")
echo

echo "→ 4/7 Creating course: crypto-wallet-israeli..."
C3=$(curl -sS -X POST "$API/api/academia/course/create" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary @- <<'JSON'
{
  "instructor_user_id": 224223270,
  "slug": "crypto-wallet-israeli",
  "title_he": "Crypto Wallet לישראלי — MetaMask + BSC",
  "description_he": "מ-0 ל-trading: MetaMask setup · BSC network · buy BNB · swap SLH ב-PancakeSwap · security · Israeli tax hints. לא ייעוץ השקעות/חשבונאי.",
  "price_ils": 149,
  "price_slh": 0,
  "language": "he",
  "materials_url": "https://slh-nft.com/academia.html#crypto-wallet",
  "preview_url": ""
}
JSON
)
echo "$C3" | python -m json.tool
ID3=$(echo "$C3" | python -c "import sys,json; print(json.loads(sys.stdin.read()).get('id',''))")
echo

for ID in "$ID1" "$ID2" "$ID3"; do
  if [ -n "$ID" ]; then
    echo "→ Approving course #$ID..."
    curl -sS -X POST "$API/api/academia/course/approve" \
      -H "Content-Type: application/json" \
      -H "X-Admin-Key: $ADMIN_KEY" \
      -d "{\"course_id\":$ID,\"approved\":true}" | python -m json.tool
    echo
  fi
done

echo "✅ Done. Verify: curl -s \"$API/api/academia/courses?approved=true&limit=10\" | python -m json.tool"
