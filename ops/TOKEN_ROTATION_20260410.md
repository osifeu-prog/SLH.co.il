# 🔐 SLH Token Rotation Worksheet
**Date:** 2026-04-10
**Status:** IN PROGRESS — all 25 tokens exposed in prior chats, rotating now.

---

## Rotation procedure (per bot)

For each bot below, in order:

1. Open [@BotFather](https://t.me/BotFather)
2. Type `/mybots`
3. Select the bot by the **Username** column below
4. Tap **API Token**
5. Tap **Revoke current token** → confirm
6. Copy the new token (format: `<id>:<hash>`)
7. Open `D:\SLH_ECOSYSTEM\.env` in your editor
8. Find the env var (left column) and paste the new value
9. Mark ✅ in the Done column
10. After all rotations, restart all bots:
    ```powershell
    cd D:\SLH_ECOSYSTEM
    docker compose up -d
    ```

---

## 📋 Rotation Checklist (25 tokens)

| # | Env Var | Bot Username | Bot ID | Current | Done |
|---|---------|--------------|--------|---------|------|
| 1 | `CORE_BOT_TOKEN` | @SLH_Academia_bot | 8351227223 | VALID | [ ] |
| 2 | `GUARDIAN_BOT_TOKEN` | @Grdian_bot | 8521882513 | VALID | [ ] |
| 3 | `BOTSHOP_BOT_TOKEN` | @Buy_My_Shop_bot | 8288632241 | VALID | [ ] |
| 4 | `WALLET_BOT_TOKEN` | @SLH_Wallet_bot | 8729004785 | VALID | [ ] |
| 5 | `FACTORY_BOT_TOKEN` | @Osifs_Factory_bot | 8216202784 | VALID | [ ] |
| 6 | `FUN_BOT_TOKEN` | @SLH_community_bot | 8554485332 | VALID | [ ] |
| 7 | `ADMIN_BOT_TOKEN` | @MY_SUPER_ADMIN_bot | 7644371589 | VALID | [ ] |
| 8 | `AIRDROP_BOT_TOKEN` | @SLH_AIR_bot | 8530795944 | VALID | [ ] |
| 9 | `CAMPAIGN_TOKEN` | @Campaign_SLH_bot | 8075933581 | VALID | [ ] |
| 10 | `GAME_BOT_TOKEN` | @G4meb0t_bot_bot | 8298897331 | VALID | [ ] |
| 11 | `TON_MNH_TOKEN` | @TON_MNH_bot | 8508943909 | VALID | [ ] |
| 12 | `SLH_TON_TOKEN` | @SLH_ton_bot | 8172123240 | VALID | [ ] |
| 13 | `SLH_LEDGER_TOKEN` | @SLH_Ledger_bot | 8494620699 | VALID | [ ] |
| 14 | `SLH_SELHA_TOKEN` | @Slh_selha_bot ⚡ ExpertNet | 8225059465 | VALID | [ ] |
| 15 | `NIFTI_PUBLISHER_TOKEN` | @NIFTI_Publisher_Bot | 8478252455 | VALID | [ ] |
| 16 | `OSIF_SHOP_TOKEN` | @OsifShop_bot | 8106987443 | VALID | [ ] |
| 17 | `CHANCE_PAIS_TOKEN` | @Chance_Pais_bot | 8415305046 | VALID | [ ] |
| 18 | `NFTY_MADNESS_TOKEN` | @NFTY_madness_bot | 7998856873 | VALID⚠️ | [ ] |
| 19 | `CRAZY_PANEL_TOKEN` | @My_crazy_panel_bot | 8238076648 | VALID | [ ] |
| 20 | `TS_SET_TOKEN` | @ts_set_bot | 8692123720 | VALID | [ ] |
| 21 | `MY_NFT_SHOP_TOKEN` | @MY_NFT_SHOP_bot | 8394483424 | VALID | [ ] |
| 22 | `BEYNONIBANK_TOKEN` | @beynonibank_bot | 8384883433 | VALID | [ ] |
| 23 | `TEST_BOT_TOKEN` | @TESTinbot_bot_bot | 8522542493 | VALID | [ ] |

### Known aliases (no action needed for these)

| # | Env Var | Points to | Note |
|---|---------|-----------|------|
| 24 | `EXPERTNET_BOT_TOKEN` | = `SLH_SELHA_TOKEN` (8225059465) | ✅ **Fixed 2026-04-10**: ExpertNet reassigned to @Slh_selha_bot (reused an empty bot). slh-selha container stopped, slh-expertnet runs as @Slh_selha_bot. When you rotate #14 SLH_SELHA_TOKEN, **also update #24 EXPERTNET_BOT_TOKEN with the same new value**. |
| 25 | `BOT_TOKEN` | = `${NFTY_MADNESS_TOKEN}` | Leave as-is — it references NFTY automatically via shell variable. |

### Note on #18 (NFTY_MADNESS_TOKEN)
⚠️ This token was exposed **twice** today (in different chats). Rotate it again — prefer rotating AFTER all other bots are confirmed working.

---

## ✅ ExpertNet already reassigned (2026-04-10)

Current state: `slh-expertnet` container is **running** as `@Slh_selha_bot`, and `slh-selha` container is **stopped** to avoid a 409 Conflict (Telegram allows only one polling instance per token).

Verification:
```powershell
docker logs slh-expertnet --tail 5
# Should show: "Run polling for bot @Slh_selha_bot id=8225059465"
```

**When you rotate #14 SLH_SELHA_TOKEN:**
1. Get new token from @BotFather for @Slh_selha_bot
2. Update BOTH values in `.env`:
   ```
   SLH_SELHA_TOKEN=<new_token>
   EXPERTNET_BOT_TOKEN=<same_new_token>
   ```
3. Restart: `docker compose restart expertnet-bot`
4. Verify: `docker logs slh-expertnet --tail 5`

**When you want the old Selha functionality back** (optional, not needed):
- You'd need a separate bot — create via `/newbot` in BotFather
- Put its token in `SLH_SELHA_TOKEN`, leave `EXPERTNET_BOT_TOKEN` pointing to the current value
- Then you can `docker compose start selha-bot`

---

## 🧪 Verification after rotation

After updating all tokens and restarting:

```powershell
cd D:\SLH_ECOSYSTEM
docker compose ps
# All 26+ containers should show "Up"

# Check each bot responds:
docker logs slh-core-bot --tail 5
docker logs slh-airdrop --tail 5
# ... etc

# Test /start in Telegram for each bot
```

---

## 🔐 Backup before rotation

**Current `.env` is backed up at:**
`D:\SLH_BACKUPS\FULL_20260410_125544\env.backup`

If rotation fails mid-way, restore with:
```powershell
Copy-Item D:\SLH_BACKUPS\FULL_20260410_125544\env.backup D:\SLH_ECOSYSTEM\.env
docker compose restart
```

---

## ⏰ Progress Tracker

- Started: ____________
- Bots rotated: 0 / 23
- Completed: ____________
