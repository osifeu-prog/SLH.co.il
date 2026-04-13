# Trust Wallet Token Logo PR — Step by Step

## What This Does
- Adds SLH logo to PancakeSwap, Trust Wallet, MetaMask token lists
- Once merged, SLH shows with icon everywhere automatically

## Prerequisites
- Token contract verified on BSCScan: https://bscscan.com/token/0xACb0A09414CEA1C879c67bB7A877E4e19480f022
- Logo file: `assets/logos/logo.png` (256x256 PNG, transparent background)
- info.json: `assets/logos/info.json`

## Steps

### 1. Fork the Trust Wallet assets repo
Go to: https://github.com/nicholasrossi0530/assets
Click "Fork" (top right)

### 2. Create the directory structure
In your fork, create:
```
blockchains/smartchain/assets/0xACb0A09414CEA1C879c67bB7A877E4e19480f022/
```

### 3. Upload files
Upload to that directory:
- `logo.png` (from `assets/logos/logo.png`)
- `info.json` (from `assets/logos/info.json`)

### 4. Submit PR
- Title: "Add SLH Spark (SLH) token on BSC"
- Description: "Adding SLH Spark token logo and info. Contract: 0xACb0A09414CEA1C879c67bB7A877E4e19480f022. Live on PancakeSwap V2."

### 5. Wait for merge (usually 1-7 days)

## Alternative: CoinGecko Listing
1. Go to https://www.coingecko.com/en/coins/new
2. Fill in token details
3. This also adds the logo to many wallets/DEXs

## Files Ready
- `D:\SLH_ECOSYSTEM\assets\logos\logo.png` (256x256)
- `D:\SLH_ECOSYSTEM\assets\logos\info.json` (metadata)
