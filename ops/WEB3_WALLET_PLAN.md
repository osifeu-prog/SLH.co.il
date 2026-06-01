# 🔗 Web3 Wallet Integration Plan

> Created: 2026-04-09
> Priority: 🟠 P1 — Users need to see REAL balances to trust the system
> Est: 1.5–2 hours

## Goal

Let users connect MetaMask or Trust Wallet (mobile) to the dashboard and see
their **real on-chain balances** side-by-side with the internal SLH ledger:

| Token | Chain    | Source                                       |
|-------|----------|----------------------------------------------|
| SLH   | BSC      | ERC-20 `balanceOf` on `0xACb0A09414CEA1C879c67bB7A877E4e19480f022` |
| BNB   | BSC      | native `eth_getBalance`                      |
| ETH   | Ethereum | native `eth_getBalance`                      |
| TON   | TON      | TON HTTP API `getAddressBalance`             |
| USDT  | BSC      | ERC-20 `balanceOf` on `0x55d398326f99059fF775485246999027B3197955` |

## User flow

```
1. Dashboard → nav shows "Connect Wallet" button (when not connected)
2. User clicks → browser asks for MetaMask/Trust Wallet permission
3. Accept → we receive eth address (0x...)
4. Store in currentUser.wallet_address + localStorage
5. Dashboard widget shows live balances from chain
6. User can sign a message to prove ownership (for P2P features)
7. "Disconnect" button to clear
```

## Implementation

### 1. HTML (dashboard.html + wallet.html)

Add ethers.js UMD + a connect button near the balance cards:

```html
<!-- In <head> -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/6.13.2/ethers.umd.min.js"></script>

<!-- In the wallet panel -->
<div class="web3-panel">
  <div id="web3-status">
    <button id="btn-connect-wallet" class="btn btn-primary">
      <i class="fas fa-wallet"></i> Connect Wallet
    </button>
  </div>
  <div id="web3-balances" style="display:none">
    <div class="web3-addr"><span id="web3-addr-short"></span></div>
    <div class="web3-balance-grid">
      <div class="web3-card" data-token="SLH">
        <span class="label">SLH on-chain</span>
        <span class="amount" id="w3-slh">—</span>
      </div>
      <div class="web3-card" data-token="BNB">
        <span class="label">BNB</span>
        <span class="amount" id="w3-bnb">—</span>
      </div>
      <div class="web3-card" data-token="ETH">
        <span class="label">ETH</span>
        <span class="amount" id="w3-eth">—</span>
      </div>
      <div class="web3-card" data-token="TON">
        <span class="label">TON</span>
        <span class="amount" id="w3-ton">—</span>
      </div>
    </div>
    <button id="btn-disconnect-wallet" class="btn btn-outline btn-sm">Disconnect</button>
  </div>
</div>
```

### 2. JavaScript module (js/web3.js)

Create a new file so it's importable from any page:

```javascript
// SLH Web3 Integration
// Requires ethers.js already loaded

const BSC_RPC = 'https://bsc-dataseed.binance.org/';
const ETH_RPC = 'https://eth.llamarpc.com';
const TON_API = 'https://toncenter.com/api/v2';
const SLH_CONTRACT_BSC = '0xACb0A09414CEA1C879c67bB7A877E4e19480f022';
const USDT_CONTRACT_BSC = '0x55d398326f99059fF775485246999027B3197955';

const ERC20_ABI = [
  'function balanceOf(address) view returns (uint256)',
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)'
];

let web3Provider = null;
let web3Signer = null;
let web3Address = null;

// Connect to MetaMask / Trust Wallet
async function connectWallet() {
  if (!window.ethereum) {
    alert('No Web3 wallet detected. Install MetaMask (desktop) or open this page in Trust Wallet browser (mobile).');
    window.open('https://metamask.io/download/', '_blank');
    return null;
  }
  try {
    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
    web3Address = accounts[0];
    web3Provider = new ethers.BrowserProvider(window.ethereum);
    web3Signer = await web3Provider.getSigner();
    localStorage.setItem('slh_web3_addr', web3Address);
    // Save on server for cross-device persistence
    if (typeof apiPost === 'function' && typeof currentUser !== 'undefined' && currentUser?.id) {
      apiPost('/api/user/link-wallet', { user_id: currentUser.id, address: web3Address });
    }
    return web3Address;
  } catch (err) {
    console.error('[Web3] connect failed', err);
    return null;
  }
}

function disconnectWallet() {
  web3Address = null;
  web3Provider = null;
  web3Signer = null;
  localStorage.removeItem('slh_web3_addr');
}

// Read balance from BSC (read-only, no wallet needed)
async function getBSCBalance(address, contractAddress) {
  const rpc = new ethers.JsonRpcProvider(BSC_RPC);
  const contract = new ethers.Contract(contractAddress, ERC20_ABI, rpc);
  const [bal, dec] = await Promise.all([
    contract.balanceOf(address),
    contract.decimals()
  ]);
  return parseFloat(ethers.formatUnits(bal, dec));
}

async function getBSCNativeBalance(address) {
  const rpc = new ethers.JsonRpcProvider(BSC_RPC);
  const bal = await rpc.getBalance(address);
  return parseFloat(ethers.formatEther(bal));
}

async function getETHBalance(address) {
  const rpc = new ethers.JsonRpcProvider(ETH_RPC);
  const bal = await rpc.getBalance(address);
  return parseFloat(ethers.formatEther(bal));
}

async function getTONBalance(tonAddress) {
  // User must provide their TON address separately (different format)
  try {
    const res = await fetch(`${TON_API}/getAddressBalance?address=${tonAddress}`);
    const data = await res.json();
    if (data.ok) return parseFloat(data.result) / 1e9;
  } catch (e) {
    console.error('[Web3] TON balance', e);
  }
  return 0;
}

// Render all balances in the dashboard
async function renderWeb3Balances(address) {
  try {
    const [slh, bnb, eth] = await Promise.all([
      getBSCBalance(address, SLH_CONTRACT_BSC).catch(() => 0),
      getBSCNativeBalance(address).catch(() => 0),
      getETHBalance(address).catch(() => 0)
    ]);
    const setIf = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val.toFixed(4); };
    setIf('w3-slh', slh);
    setIf('w3-bnb', bnb);
    setIf('w3-eth', eth);
    // TON requires a separate address field — skip for now
    setIf('w3-ton', 0);
  } catch (err) {
    console.error('[Web3] render balances', err);
  }
}

// Sign a message to prove wallet ownership (for P2P listings)
async function signMessage(msg) {
  if (!web3Signer) throw new Error('Not connected');
  return await web3Signer.signMessage(msg);
}

// Auto-reconnect on page load
function initWeb3UI() {
  const btnConnect = document.getElementById('btn-connect-wallet');
  const btnDisconnect = document.getElementById('btn-disconnect-wallet');
  const statusEl = document.getElementById('web3-status');
  const balancesEl = document.getElementById('web3-balances');
  const addrEl = document.getElementById('web3-addr-short');

  const showConnected = (addr) => {
    if (statusEl) statusEl.style.display = 'none';
    if (balancesEl) balancesEl.style.display = 'block';
    if (addrEl) addrEl.textContent = addr.slice(0, 6) + '...' + addr.slice(-4);
    renderWeb3Balances(addr);
  };
  const showDisconnected = () => {
    if (statusEl) statusEl.style.display = 'block';
    if (balancesEl) balancesEl.style.display = 'none';
  };

  btnConnect?.addEventListener('click', async () => {
    const addr = await connectWallet();
    if (addr) showConnected(addr);
  });
  btnDisconnect?.addEventListener('click', () => {
    disconnectWallet();
    showDisconnected();
  });

  // Auto-reconnect if previously connected
  const saved = localStorage.getItem('slh_web3_addr');
  if (saved && window.ethereum) {
    web3Address = saved;
    showConnected(saved);
  }

  // React to account switch
  if (window.ethereum) {
    window.ethereum.on('accountsChanged', (accs) => {
      if (accs.length === 0) {
        disconnectWallet();
        showDisconnected();
      } else {
        web3Address = accs[0];
        localStorage.setItem('slh_web3_addr', accs[0]);
        showConnected(accs[0]);
      }
    });
  }
}

// Auto-init on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initWeb3UI);
} else {
  initWeb3UI();
}
```

### 3. API endpoint (api/main.py)

```python
@app.post("/api/user/link-wallet")
async def link_wallet(req: Request):
    body = await req.json()
    user_id = int(body.get("user_id", 0))
    address = (body.get("address") or "").lower()
    if not user_id or not address.startswith("0x") or len(address) != 42:
        raise HTTPException(400, "Invalid request")
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE web_users SET eth_wallet = $1, eth_wallet_linked_at = NOW() WHERE telegram_id = $2",
            address, user_id
        )
    return {"ok": True}
```

### 4. DB migration

```sql
ALTER TABLE web_users ADD COLUMN IF NOT EXISTS eth_wallet VARCHAR(42);
ALTER TABLE web_users ADD COLUMN IF NOT EXISTS eth_wallet_linked_at TIMESTAMP;
CREATE INDEX IF NOT EXISTS idx_web_users_eth_wallet ON web_users(eth_wallet);
```

## Security notes

- **Never** ask user for their seed phrase or private key
- Only request `eth_requestAccounts` — read-only by default
- For signatures, use `personal_sign` with a human-readable message that
  includes a nonce (prevents replay)
- Store addresses as lowercase to avoid case mismatch
- Validate address format on both client and server
- The SLH contract is already deployed and immutable — we only READ from it

## Testing

1. Open dashboard in Chrome + MetaMask
2. Click Connect → MetaMask popup → accept
3. Verify address shown, balances loaded
4. Switch account in MetaMask → verify dashboard updates
5. Disconnect → verify balances hidden
6. Refresh page → verify auto-reconnect

Mobile testing:
1. Open Trust Wallet app → Browser tab → navigate to slh-nft.com/dashboard.html
2. Click Connect → Trust Wallet should pop native wallet selector
3. Verify balances

## Rollout

- Phase 1: Read-only balances (this plan)
- Phase 2: Sign messages for P2P listings
- Phase 3: Actual transactions (deposits, withdrawals)
- Phase 4: TON wallet integration (separate UX due to different address format)

## Related files

- `D:\SLH_ECOSYSTEM\website\js\web3.js` (new)
- `D:\SLH_ECOSYSTEM\website\dashboard.html` (add panel)
- `D:\SLH_ECOSYSTEM\website\wallet.html` (add panel)
- `D:\SLH_ECOSYSTEM\api\main.py` (add /api/user/link-wallet)
