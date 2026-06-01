# 🚨 SECURITY — Bot Token Rotation Required

> Created: 2026-04-09
> Priority: **CRITICAL**
> Owner: Osif

## Situation

During the last testing session, all 20+ Telegram bot tokens were pasted in the
Claude chat (from BotFather `/token` responses). Any token that has been shared
outside a secure vault MUST be considered **compromised** and rotated
immediately — even if the chat log itself is private.

## Why this matters

A leaked bot token allows an attacker to:
1. Read every private message sent to your bot
2. Reply as you, on your behalf
3. Broadcast to every user that ever talked to the bot
4. Exfiltrate user database (via bot API)
5. Run arbitrary bot commands (ban/unban, payment flows, admin functions)

There is no way to "unsend" a token — once it's out of the vault, rotate.

## Rotation procedure (per bot)

For EACH of the ~23 bots listed in `docker-compose.yml`:

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. `/mybots` → select the bot
3. `API Token` → `Revoke current token`
4. Copy the new token
5. Update `.env` on the host:
   - Edit `D:\SLH_ECOSYSTEM\.env` (or the specific bot's `.env`)
   - Replace the `XXX_BOT_TOKEN=...` line with the new value
6. Restart the container:
   ```powershell
   cd D:\SLH_ECOSYSTEM
   docker compose restart <bot-service-name>
   ```
7. Verify with `/start` in Telegram that the bot still responds
8. Mark the bot as rotated in the table below

## Rotation checklist

| # | Bot | Service | Rotated? | New token stored in |
|---|-----|---------|----------|---------------------|
| 1  | @SLH_AIR_bot             | slh-air             | [ ] | .env |
| 2  | @SLH_Wallet_bot          | slh-wallet          | [ ] | .env |
| 3  | @SLH_Ledger_bot          | slh-ledger          | [ ] | .env |
| 4  | @SLH_ton_bot             | slh-ton-mnh         | [ ] | .env |
| 5  | @SLH_Academia_bot        | slh-academia        | [ ] | .env |
| 6  | @SLH_community_bot       | slh-community       | [ ] | .env |
| 7  | @OsifShop_bot            | osif-shop           | [ ] | .env |
| 8  | @MY_NFT_SHOP_bot         | nft-shop            | [ ] | .env |
| 9  | @Buy_My_Shop_bot         | buy-my-shop         | [ ] | .env |
| 10 | @NFTY_madness_bot        | slh-nfty            | [ ] | .env |
| 11 | @NIFTI_Publisher_Bot     | slh-wellness        | [ ] | .env |
| 12 | @TON_MNH_bot             | slh-ton-mnh-main    | [ ] | .env |
| 13 | @MY_SUPER_ADMIN_bot      | slh-admin           | [ ] | .env |
| 14 | @My_crazy_panel_bot      | slh-crazy-panel     | [ ] | .env |
| 15 | @Chance_Pais_bot         | slh-chance          | [ ] | .env |
| 16 | @G4meb0t_bot_bot         | slh-matchmaking     | [ ] | .env |
| 17 | @Campaign_SLH_bot        | slh-campaign        | [ ] | .env |
| 18 | @Osifs_Factory_bot       | slh-factory         | [ ] | .env |
| 19 | @Grdian_bot              | slh-guardian        | [ ] | .env |
| 20 | @Slh_selha_bot           | slh-selha           | [ ] | .env |

## Prevention — never again

**Rule:** Tokens live ONLY in:
- `D:\SLH_ECOSYSTEM\.env` (file, file, file — never chat)
- GitHub Actions secrets (for CI)
- Railway environment variables

**Do not:**
- Paste tokens in chat (Telegram, Claude, Slack, WhatsApp)
- Commit them to git
- Print them in logs
- Include them in screenshots
- Send them in email

**Do use:**
- `.env` files that are in `.gitignore`
- `docker compose --env-file` to inject at runtime
- Environment variable substitution: `${SLH_AIR_BOT_TOKEN}` in compose yaml
- A password manager (1Password, Bitwarden) for the master copy

## Quick rotation script

After updating `.env`, restart everything:
```powershell
cd D:\SLH_ECOSYSTEM
docker compose down
docker compose up -d
docker compose ps
```

Then smoke-test each bot with `/start` in Telegram.

## Verification that rotation worked

Old tokens will return `401 Unauthorized` from the Telegram Bot API.
You can verify a token is dead with:
```powershell
curl.exe "https://api.telegram.org/bot<OLD_TOKEN>/getMe"
# Should return: {"ok":false,"error_code":401,"description":"Unauthorized"}
```

And confirm new tokens work:
```powershell
curl.exe "https://api.telegram.org/bot<NEW_TOKEN>/getMe"
# Should return: {"ok":true,"result":{"id":..., "username":"...", ...}}
```

## Sign-off

- [ ] All 20+ bots rotated
- [ ] All containers restarted
- [ ] All bots responding to `/start`
- [ ] Old tokens verified dead
- [ ] New tokens stored only in `.env`
- [ ] `.env` still in `.gitignore`
- [ ] Nothing pasted in any chat this session

Date completed: __________
