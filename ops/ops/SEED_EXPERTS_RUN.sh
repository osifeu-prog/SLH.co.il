#!/usr/bin/env bash
# Seed 2 Experts — fill in the fields below, then run with your admin key.
#
# Usage:
#   1. Edit the TZVIKA_* and ZOHAR_* vars below with real info
#   2. export ADMIN_KEY='your-admin-key'
#   3. bash ops/SEED_EXPERTS_RUN.sh
#
# At least ONE of linkedin_url / website_url / youtube_url / portfolio_url / credentials
# must be set per expert (legal proof-of-expertise requirement).

set -e

: "${ADMIN_KEY:?ADMIN_KEY env var is required.}"
API="${SLH_API:-https://slh-api-production.up.railway.app}"

# ═══════════════ Expert 1: Tzvika ═══════════════
TZVIKA_NAME="צביקה קאופמן"                # display name (Hebrew OK)
TZVIKA_TG="TzvikaLisha"                    # telegram username (no @)
TZVIKA_BIO="סוחר קריפטו, CEO SLH Spark, בעלים ExpertNet"
TZVIKA_DOMAINS='["crypto","finance"]'      # JSON array
TZVIKA_LANGS='["he","en"]'
TZVIKA_LINKEDIN=""                         # fill if you have
TZVIKA_WEBSITE=""                          # fill if you have
TZVIKA_YEARS=10
TZVIKA_CREDENTIALS="Co-founder SLH Spark; 10 שנות ניסיון במסחר קריפטו; מנהל PancakeSwap V2 pool 0xacea26b6e132cd45f2b8a4754170d4d0d3b8bbee"

# ═══════════════ Expert 2: Zohar Shefa Dror ═══════════════
ZOHAR_NAME="Zohar Shefa Dror"
ZOHAR_TG=""                                # fill if you have
ZOHAR_BIO="Active contributor + QA — SLH Spark community"
ZOHAR_DOMAINS='["tech","security"]'
ZOHAR_LANGS='["he","en"]'
ZOHAR_LINKEDIN=""
ZOHAR_WEBSITE=""
ZOHAR_YEARS=0
ZOHAR_CREDENTIALS="Active contributor + QA testing for SLH Spark platform (verified by Osif)"

# ═══════════════ Register ═══════════════
echo "→ Registering Tzvika..."
R1=$(python -c "
import json, os
print(json.dumps({
  'display_name': os.environ['TZVIKA_NAME'],
  'tg_username': os.environ['TZVIKA_TG'],
  'bio': os.environ['TZVIKA_BIO'],
  'domains': json.loads(os.environ['TZVIKA_DOMAINS']),
  'languages': json.loads(os.environ['TZVIKA_LANGS']),
  'linkedin_url': os.environ['TZVIKA_LINKEDIN'] or None,
  'website_url': os.environ['TZVIKA_WEBSITE'] or None,
  'years_experience': int(os.environ['TZVIKA_YEARS']),
  'credentials': os.environ['TZVIKA_CREDENTIALS'],
}, ensure_ascii=False))
")
export TZVIKA_NAME TZVIKA_TG TZVIKA_BIO TZVIKA_DOMAINS TZVIKA_LANGS TZVIKA_LINKEDIN TZVIKA_WEBSITE TZVIKA_YEARS TZVIKA_CREDENTIALS
RESULT1=$(curl -sS -X POST "$API/api/experts/register" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary "$R1")
echo "$RESULT1" | python -m json.tool
TZVIKA_ID=$(echo "$RESULT1" | python -c "import sys,json; print(json.loads(sys.stdin.read()).get('expert_id',''))")

echo "→ Registering Zohar..."
export ZOHAR_NAME ZOHAR_TG ZOHAR_BIO ZOHAR_DOMAINS ZOHAR_LANGS ZOHAR_LINKEDIN ZOHAR_WEBSITE ZOHAR_YEARS ZOHAR_CREDENTIALS
R2=$(python -c "
import json, os
print(json.dumps({
  'display_name': os.environ['ZOHAR_NAME'],
  'tg_username': os.environ['ZOHAR_TG'],
  'bio': os.environ['ZOHAR_BIO'],
  'domains': json.loads(os.environ['ZOHAR_DOMAINS']),
  'languages': json.loads(os.environ['ZOHAR_LANGS']),
  'linkedin_url': os.environ['ZOHAR_LINKEDIN'] or None,
  'website_url': os.environ['ZOHAR_WEBSITE'] or None,
  'years_experience': int(os.environ['ZOHAR_YEARS']),
  'credentials': os.environ['ZOHAR_CREDENTIALS'],
}, ensure_ascii=False))
")
RESULT2=$(curl -sS -X POST "$API/api/experts/register" \
  -H "Content-Type: application/json; charset=utf-8" \
  --data-binary "$R2")
echo "$RESULT2" | python -m json.tool
ZOHAR_ID=$(echo "$RESULT2" | python -c "import sys,json; print(json.loads(sys.stdin.read()).get('expert_id',''))")

# Approve both
for ID in "$TZVIKA_ID" "$ZOHAR_ID"; do
  if [ -n "$ID" ]; then
    echo "→ Approving expert #$ID..."
    curl -sS -X POST "$API/api/admin/experts/approve" \
      -H "Content-Type: application/json" \
      -H "X-Admin-Key: $ADMIN_KEY" \
      -d "{\"expert_id\":$ID,\"decision\":\"approved\",\"featured\":true,\"reviewed_by\":\"osif\"}" | python -m json.tool
    echo
  fi
done

echo "✅ Done. Verify: curl -s \"$API/api/experts/list\" | python -m json.tool"
