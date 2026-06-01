# Web3 Integration + Marketplace - Implementation Plan

## Part 1: MetaMask / TrustWallet Connection

### What It Does
Users connect their crypto wallet (MetaMask, TrustWallet) to slh-nft.com.
The site reads real on-chain balances and displays them in the dashboard.

### Implementation Steps

#### A. Wallet Connection (wallet.html + shared.js)
```
1. Add "Connect Wallet" button to dashboard + wallet page
2. Use window.ethereum (injected by MetaMask/TrustWallet)
3. Request accounts: ethereum.request({ method: 'eth_requestAccounts' })
4. Store connected address in localStorage + send to API
5. Display shortened address (0x1234...5678) in nav bar
```

#### B. Read On-Chain Balances
```
1. BNB balance: eth_getBalance for native BNB
2. SLH token: call balanceOf() on 0xACb0A09414CEA1C879c67bB7A877E4e19480f022
3. Use ethers.js or web3.js (ethers recommended - lighter)
4. BSC RPC: https://bsc-dataseed.binance.org/
5. Cache balances client-side, refresh every 60s
```

#### C. API Integration
```
POST /api/wallet/connect
Body: {user_id, wallet_address, chain: "bsc"}
-> Stores wallet address in web_users table

GET /api/wallet/onchain/{user_id}
-> Returns cached on-chain balances (server fetches from RPC)
```

#### D. Token Management (max 2 tokens initially)
```
Dashboard > Portfolio section:
- Default: SLH + BNB
- User can add/remove tracked tokens (up to 2)
- Enter contract address -> auto-fetch name, symbol, decimals
- Display balance, price (from CoinGecko), % change
```

### Files to Modify
- `js/web3-wallet.js` - already exists (11.4KB), enhance with MetaMask
- `wallet.html` - add Connect Wallet UI
- `dashboard.html` - add wallet connection shortcut
- `js/shared.js` - add wallet state management
- API `main.py` - add wallet connect/onchain endpoints

---

## Part 2: Telegram Wallet Address Guide

### Implementation
Add a step-by-step visual guide to guides.html:

```
1. Open Telegram -> @wallet bot
2. Click "TON Wallet" or "Crypto"
3. Find your TON address (starts with UQ or EQ)
4. Copy the address
5. Paste in slh-nft.com/wallet.html -> "My TON Address" field
6. Your address is saved and linked to your account
```

Include screenshots/mockups for each step.
Accessible from: guides.html + registration panel + wallet.html

---

## Part 3: Ecommerce Marketplace

### Vision
Users publish products/services on community.html, like a mini Shopify.
Buyers browse by category, contact seller, pay in SLH/TON.

### Database Schema (new tables)
```sql
CREATE TABLE marketplace_listings (
    id SERIAL PRIMARY KEY,
    seller_id BIGINT REFERENCES web_users(telegram_id),
    title TEXT NOT NULL,
    description TEXT,
    price NUMERIC(12,4) NOT NULL,
    currency TEXT DEFAULT 'SLH',  -- SLH, TON, ILS
    category TEXT NOT NULL,       -- digital, physical, service, education
    images TEXT[],                 -- array of image URLs
    status TEXT DEFAULT 'active', -- active, sold, paused, removed
    created_at TIMESTAMP DEFAULT NOW(),
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0
);

CREATE TABLE marketplace_orders (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES marketplace_listings(id),
    buyer_id BIGINT,
    seller_id BIGINT,
    amount NUMERIC(12,4),
    currency TEXT,
    status TEXT DEFAULT 'pending', -- pending, paid, delivered, disputed
    created_at TIMESTAMP DEFAULT NOW()
);
```

### API Endpoints (planned)
```
GET  /api/marketplace/listings?category=&sort=&page=
POST /api/marketplace/listings (create listing, JWT required)
PUT  /api/marketplace/listings/{id} (edit, owner only)
DEL  /api/marketplace/listings/{id} (soft delete)
POST /api/marketplace/orders (create order)
GET  /api/marketplace/my-shop/{user_id} (seller dashboard)
```

### Frontend (community.html enhancement)
```
Community page gets new tabs:
- Posts (existing)
- Marketplace (new)
- Services (new)

Marketplace card layout:
+------------------+
| [Image]          |
| Title            |
| Price: 0.5 SLH   |
| Category: Digital |
| Seller: @username |
| [Contact] [Buy]  |
+------------------+
```

### Categories
- Digital Products (templates, guides, tools)
- Physical Products (merchandise, crafts)
- Services (consulting, development, design)
- Education (courses, tutoring, mentoring)
- NFT / Collectibles (digital art, tokens)

### Revenue Model
- Listing fee: Free for first 3, then 0.01 SLH per listing
- Transaction fee: 3% commission on sales (in SLH)
- Featured listing: 0.1 SLH for 7-day promotion
