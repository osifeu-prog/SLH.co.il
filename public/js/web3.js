// SLH Web3 Integration — MetaMask / Trust Wallet / WalletConnect
// Requires ethers.js v6 loaded BEFORE this script
// CDN: https://cdnjs.cloudflare.com/ajax/libs/ethers/6.13.2/ethers.umd.min.js

(function () {
  'use strict';

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

  function log(...args) {
    if (typeof console !== 'undefined') console.log('[SLH Web3]', ...args);
  }

  function hasEthers() {
    return typeof ethers !== 'undefined';
  }

  // ---- Helper: get logged-in user from either global currentUser or shared.js ----
  function _getUser() {
    try {
      if (typeof currentUser !== 'undefined' && currentUser && currentUser.id) return currentUser;
    } catch (_) { /* currentUser not declared on this page */ }
    if (typeof getCurrentUser === 'function') {
      try { return getCurrentUser(); } catch (_) { return null; }
    }
    return null;
  }

  // ---- No-wallet helper modal ----
  function _showNoWalletModal() {
    // Remove previous modal if exists
    var prev = document.getElementById('slh-nowallet-overlay');
    if (prev) prev.remove();

    var pageUrl = location.href;
    var isMobile = /Mobi|Android|iPhone/i.test(navigator.userAgent);

    var overlay = document.createElement('div');
    overlay.id = 'slh-nowallet-overlay';
    overlay.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,.75);display:flex;align-items:center;justify-content:center;padding:16px;direction:rtl;font-family:var(--font,Inter,sans-serif)';

    var box = document.createElement('div');
    box.style.cssText = 'background:var(--surface,#14142b);border:1px solid var(--border,#1e1e3a);border-radius:var(--radius,12px);max-width:440px;width:100%;padding:28px 24px;position:relative;color:var(--text,#e0e0e0);box-shadow:0 8px 40px rgba(0,0,0,.5)';

    // Close button
    var closeBtn = document.createElement('button');
    closeBtn.textContent = '\u2715';
    closeBtn.style.cssText = 'position:absolute;top:12px;left:12px;background:none;border:none;color:var(--text2,#888);font-size:20px;cursor:pointer;padding:4px 8px;line-height:1';
    closeBtn.onclick = function () { overlay.remove(); };

    // Title
    var title = document.createElement('h3');
    title.style.cssText = 'margin:0 0 18px;font-size:18px;font-weight:700;color:var(--accent,#6c5ce7)';
    title.textContent = '\u05DC\u05D0 \u05D6\u05D5\u05D4\u05D4 \u05D0\u05E8\u05E0\u05E7 Web3?';

    // --- Option 1: Mobile ---
    var opt1 = document.createElement('div');
    opt1.style.cssText = 'background:var(--bg3,#111127);border:1px solid var(--border,#1e1e3a);border-radius:8px;padding:14px 16px;margin-bottom:12px';
    var opt1Title = document.createElement('div');
    opt1Title.style.cssText = 'font-weight:700;font-size:14px;margin-bottom:6px;color:var(--accent2,#a29bfe)';
    opt1Title.innerHTML = '\uD83D\uDCF1 \u05DE\u05D4\u05D8\u05DC\u05E4\u05D5\u05DF?';
    var opt1Desc = document.createElement('div');
    opt1Desc.style.cssText = 'font-size:13px;line-height:1.5;color:var(--text2,#888);margin-bottom:10px';
    opt1Desc.textContent = '\u05E4\u05EA\u05D7 \u05D0\u05EA \u05D4\u05DC\u05D9\u05E0\u05E7 \u05D4\u05D6\u05D4 \u05DE\u05EA\u05D5\u05DA \u05D0\u05E4\u05DC\u05D9\u05E7\u05E6\u05D9\u05D9\u05EA MetaMask \u05D0\u05D5 Trust Wallet (\u05DC\u05D0 \u05DE\u05DB\u05E8\u05D5\u05DD \u05E8\u05D2\u05D9\u05DC)';
    var copyRow = document.createElement('div');
    copyRow.style.cssText = 'display:flex;gap:8px;align-items:center';
    var urlBox = document.createElement('input');
    urlBox.type = 'text';
    urlBox.readOnly = true;
    urlBox.value = pageUrl;
    urlBox.style.cssText = 'flex:1;background:var(--bg,#050510);border:1px solid var(--border2,#2a2a50);border-radius:6px;padding:8px 10px;font-size:12px;color:var(--text,#e0e0e0);direction:ltr;text-align:left;outline:none';
    var copyBtn = document.createElement('button');
    copyBtn.innerHTML = '\uD83D\uDCCB \u05D4\u05E2\u05EA\u05E7';
    copyBtn.style.cssText = 'background:var(--accent,#6c5ce7);color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap';
    copyBtn.onclick = function () {
      navigator.clipboard.writeText(pageUrl).then(function () {
        copyBtn.innerHTML = '\u2713 \u05D4\u05D5\u05E2\u05EA\u05E7!';
        setTimeout(function () { copyBtn.innerHTML = '\uD83D\uDCCB \u05D4\u05E2\u05EA\u05E7'; }, 2000);
      }).catch(function () {
        urlBox.select();
        document.execCommand('copy');
        copyBtn.innerHTML = '\u2713 \u05D4\u05D5\u05E2\u05EA\u05E7!';
        setTimeout(function () { copyBtn.innerHTML = '\uD83D\uDCCB \u05D4\u05E2\u05EA\u05E7'; }, 2000);
      });
    };
    copyRow.appendChild(urlBox);
    copyRow.appendChild(copyBtn);
    opt1.appendChild(opt1Title);
    opt1.appendChild(opt1Desc);
    opt1.appendChild(copyRow);

    // --- Option 2: Desktop ---
    var opt2 = document.createElement('div');
    opt2.style.cssText = 'background:var(--bg3,#111127);border:1px solid var(--border,#1e1e3a);border-radius:8px;padding:14px 16px;margin-bottom:12px';
    var opt2Title = document.createElement('div');
    opt2Title.style.cssText = 'font-weight:700;font-size:14px;margin-bottom:6px;color:var(--accent2,#a29bfe)';
    opt2Title.innerHTML = '\uD83D\uDDA5\uFE0F \u05DE\u05D4\u05DE\u05D7\u05E9\u05D1?';
    var opt2Desc = document.createElement('div');
    opt2Desc.style.cssText = 'font-size:13px;line-height:1.5;color:var(--text2,#888);margin-bottom:10px';
    opt2Desc.textContent = '\u05D4\u05EA\u05E7\u05DF \u05D0\u05EA \u05EA\u05D5\u05E1\u05E3 MetaMask \u05DC\u05D3\u05E4\u05D3\u05E4\u05DF \u05D5\u05EA\u05E8\u05E2\u05E0\u05DF \u05D0\u05EA \u05D4\u05E2\u05DE\u05D5\u05D3';
    var installLink = document.createElement('a');
    installLink.href = 'https://metamask.io/download/';
    installLink.target = '_blank';
    installLink.rel = 'noopener';
    installLink.style.cssText = 'display:inline-flex;align-items:center;gap:6px;background:rgba(246,133,27,.15);border:1px solid rgba(246,133,27,.35);border-radius:6px;padding:8px 14px;font-size:13px;font-weight:600;color:#f6851b;text-decoration:none';
    installLink.innerHTML = '\uD83E\uDD8A \u05D4\u05EA\u05E7\u05DF MetaMask';
    opt2.appendChild(opt2Title);
    opt2.appendChild(opt2Desc);
    opt2.appendChild(installLink);

    // --- Option 3: No wallet ---
    var opt3 = document.createElement('div');
    opt3.style.cssText = 'background:var(--bg3,#111127);border:1px solid var(--border,#1e1e3a);border-radius:8px;padding:14px 16px';
    var opt3Title = document.createElement('div');
    opt3Title.style.cssText = 'font-weight:700;font-size:14px;margin-bottom:6px;color:var(--accent2,#a29bfe)';
    opt3Title.innerHTML = '\u274C \u05DC\u05D0 \u05E8\u05D5\u05E6\u05D4 \u05D0\u05E8\u05E0\u05E7?';
    var opt3Desc = document.createElement('div');
    opt3Desc.style.cssText = 'font-size:13px;line-height:1.5;color:var(--text2,#888);margin-bottom:10px';
    opt3Desc.textContent = '\u05D0\u05E4\u05E9\u05E8 \u05DC\u05D4\u05EA\u05D7\u05D1\u05E8 \u05D2\u05DD \u05E2\u05DD Telegram ID \u05D1\u05DC\u05D1\u05D3';
    var dashLink = document.createElement('a');
    dashLink.href = '/dashboard.html';
    dashLink.style.cssText = 'display:inline-flex;align-items:center;gap:6px;background:rgba(0,229,255,.12);border:1px solid rgba(0,229,255,.3);border-radius:6px;padding:8px 14px;font-size:13px;font-weight:600;color:var(--cyan,#00e5ff);text-decoration:none';
    dashLink.innerHTML = '\uD83D\uDC49 \u05DC\u05D3\u05E9\u05D1\u05D5\u05E8\u05D3 \u05E2\u05DD Telegram';
    opt3.appendChild(opt3Title);
    opt3.appendChild(opt3Desc);
    opt3.appendChild(dashLink);

    box.appendChild(closeBtn);
    box.appendChild(title);
    box.appendChild(opt1);
    box.appendChild(opt2);
    box.appendChild(opt3);
    overlay.appendChild(box);

    // Close on overlay background click
    overlay.addEventListener('click', function (e) { if (e.target === overlay) overlay.remove(); });
    // Close on Escape
    var escHandler = function (e) { if (e.key === 'Escape') { overlay.remove(); document.removeEventListener('keydown', escHandler); } };
    document.addEventListener('keydown', escHandler);

    document.body.appendChild(overlay);
  }

  // ---- Connect / disconnect ----
  async function connectWallet() {
    if (!window.ethereum) {
      _showNoWalletModal();
      return null;
    }
    if (!hasEthers()) {
      log('ethers.js not loaded — add <script src="https://cdnjs.cloudflare.com/ajax/libs/ethers/6.13.2/ethers.umd.min.js"></script>');
      if (typeof showToast === 'function') showToast('Web3 library not loaded, please refresh', true);
      return null;
    }
    try {
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      web3Address = accounts[0];
      web3Provider = new ethers.BrowserProvider(window.ethereum);
      web3Signer = await web3Provider.getSigner();
      localStorage.setItem('slh_web3_addr', web3Address);
      // Persist on server (requires user to be logged in)
      const u = _getUser();
      if (typeof apiPost === 'function' && u && u.id) {
        apiPost('/api/user/link-wallet', { user_id: u.id, address: web3Address })
          .then((r) => { if (r && r.ok) log('linked on server', r); })
          .catch(() => {});
      }
      if (typeof showToast === 'function') {
        const short = web3Address.slice(0, 6) + '...' + web3Address.slice(-4);
        showToast('✓ ' + short + ' connected');
      }
      log('connected', web3Address);
      return web3Address;
    } catch (err) {
      log('connect failed', err);
      if (typeof showToast === 'function') showToast('Failed to connect wallet', true);
      return null;
    }
  }

  async function disconnectWallet() {
    const prev = web3Address;
    web3Address = null;
    web3Provider = null;
    web3Signer = null;
    localStorage.removeItem('slh_web3_addr');
    // Best-effort server unlink
    const u = _getUser();
    if (typeof apiPost === 'function' && u && u.id) {
      try { await apiPost('/api/user/unlink-wallet', { user_id: u.id, address: prev || '' }); } catch (_) {}
    }
    log('disconnected');
  }

  // ---- Read balances ----
  async function getBSCBalance(address, contractAddress) {
    if (!hasEthers()) return 0;
    try {
      const rpc = new ethers.JsonRpcProvider(BSC_RPC);
      const contract = new ethers.Contract(contractAddress, ERC20_ABI, rpc);
      const [bal, dec] = await Promise.all([
        contract.balanceOf(address),
        contract.decimals()
      ]);
      return parseFloat(ethers.formatUnits(bal, dec));
    } catch (e) { log('getBSCBalance', e); return 0; }
  }

  async function getBSCNativeBalance(address) {
    if (!hasEthers()) return 0;
    try {
      const rpc = new ethers.JsonRpcProvider(BSC_RPC);
      const bal = await rpc.getBalance(address);
      return parseFloat(ethers.formatEther(bal));
    } catch (e) { log('getBSCNativeBalance', e); return 0; }
  }

  async function getETHBalance(address) {
    if (!hasEthers()) return 0;
    try {
      const rpc = new ethers.JsonRpcProvider(ETH_RPC);
      const bal = await rpc.getBalance(address);
      return parseFloat(ethers.formatEther(bal));
    } catch (e) { log('getETHBalance', e); return 0; }
  }

  async function getTONBalance(tonAddress) {
    if (!tonAddress) return 0;
    try {
      const res = await fetch(`${TON_API}/getAddressBalance?address=${tonAddress}`);
      const data = await res.json();
      if (data && data.ok) return parseFloat(data.result) / 1e9;
    } catch (e) { log('getTONBalance', e); }
    return 0;
  }

  // ---- Render balances into the UI ----
  // Writes to two possible places:
  //   1. Dedicated Web3 panel: #w3-slh / #w3-bnb / #w3-eth / #w3-usdt
  //   2. Main wallet.html balance cards: #bal-bnb / #bal-usdt / etc.
  //      (so the user sees on-chain values even in the "big" cards)
  async function renderWeb3Balances(address) {
    if (!address) return;
    const setIf = (id, val, decimals) => {
      const el = document.getElementById(id);
      if (!el) return;
      const d = decimals !== undefined ? decimals : 4;
      el.textContent = (val || 0).toFixed(d);
      // if this is a main balance card, also update the fiat label
      const fiatEl = document.getElementById(id + '-fiat');
      if (fiatEl && val > 0) {
        fiatEl.textContent = '🔗 on-chain';
        fiatEl.style.color = '#22c55e';
      }
    };
    try {
      const [slh, bnb, eth, usdt] = await Promise.all([
        getBSCBalance(address, SLH_CONTRACT_BSC),
        getBSCNativeBalance(address),
        getETHBalance(address),
        getBSCBalance(address, USDT_CONTRACT_BSC)
      ]);
      // Web3 panel (dashboard + wallet pages)
      setIf('w3-slh', slh);
      setIf('w3-bnb', bnb);
      setIf('w3-eth', eth);
      setIf('w3-usdt', usdt);

      // Main balance cards (wallet.html) - overwrite internal 0 with on-chain
      // Only overwrite if on-chain value > 0, otherwise keep internal display
      if (bnb > 0) setIf('bal-bnb', bnb);
      // Don't overwrite bal-slh - that's internal ledger (199,788)
      // Add a new card for on-chain USDT BSC if the ID exists
      if (usdt > 0) setIf('bal-usdt-bsc', usdt);
      if (eth > 0)  setIf('bal-eth', eth);

      // Save last-known values for TON fetching by address
      if (typeof window !== 'undefined') {
        window.__slh_web3_last = { slh, bnb, eth, usdt, address, at: Date.now() };
      }
    } catch (e) { log('renderWeb3Balances', e); }
  }

  // ---- Sign a human-readable message (for P2P listings, auth proofs) ----
  async function signMessage(msg) {
    if (!web3Signer) throw new Error('Not connected');
    return await web3Signer.signMessage(msg);
  }

  // ---- Wire up the Connect / Disconnect UI ----
  function initWeb3UI() {
    const btnConnect = document.getElementById('btn-connect-wallet');
    const btnDisconnect = document.getElementById('btn-disconnect-wallet');
    const statusEl = document.getElementById('web3-status');
    const balancesEl = document.getElementById('web3-balances');
    const addrEl = document.getElementById('web3-addr-short');

    if (!btnConnect) return; // page has no Web3 panel

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

    btnConnect.addEventListener('click', async () => {
      const addr = await connectWallet();
      if (addr) showConnected(addr);
    });
    if (btnDisconnect) {
      btnDisconnect.addEventListener('click', () => {
        disconnectWallet();
        showDisconnected();
      });
    }

    // Auto-reconnect if previously authorized — fully re-initialize provider
    const saved = localStorage.getItem('slh_web3_addr');
    if (saved && window.ethereum && hasEthers()) {
      try {
        web3Provider = new ethers.BrowserProvider(window.ethereum);
        web3Address = saved;
        showConnected(saved);
        // Silently try to get signer (won't prompt if already authorized)
        web3Provider.getSigner().then(s => { web3Signer = s; }).catch(() => {});
        log('auto-reconnected', saved);
      } catch(e) {
        log('auto-reconnect failed', e);
        web3Address = saved;
        showConnected(saved);
      }
    }

    // Listen for account switch
    if (window.ethereum && window.ethereum.on) {
      window.ethereum.on('accountsChanged', (accs) => {
        if (!accs || accs.length === 0) {
          disconnectWallet();
          showDisconnected();
        } else {
          web3Address = accs[0];
          localStorage.setItem('slh_web3_addr', accs[0]);
          showConnected(accs[0]);
        }
      });
      window.ethereum.on('chainChanged', () => {
        if (web3Address) renderWeb3Balances(web3Address);
      });
    }
  }

  // ---- Mobile banner (injected once per page) ----
  function _showMobileBanner() {
    if (!(/Mobi|Android|iPhone/i.test(navigator.userAgent))) return;
    if (window.ethereum) return; // already inside a dapp browser, no need
    if (document.getElementById('slh-mobile-wallet-banner')) return;

    var banner = document.createElement('div');
    banner.id = 'slh-mobile-wallet-banner';
    banner.style.cssText = 'position:fixed;bottom:70px;left:12px;right:12px;z-index:9990;background:linear-gradient(135deg,var(--surface,#14142b),var(--bg3,#111127));border:1px solid var(--accent,#6c5ce7);border-radius:var(--radius,12px);padding:14px 16px;direction:rtl;font-family:var(--font,Inter,sans-serif);box-shadow:0 4px 24px rgba(0,0,0,.5);display:flex;align-items:center;gap:12px';

    var text = document.createElement('div');
    text.style.cssText = 'flex:1;font-size:13px;line-height:1.5;color:var(--text,#e0e0e0)';
    text.innerHTML = '\uD83D\uDCF1 <strong>\u05DE\u05D4\u05D8\u05DC\u05E4\u05D5\u05DF?</strong> \u05E4\u05EA\u05D7 \u05D0\u05EA \u05D4\u05DC\u05D9\u05E0\u05E7 \u05D4\u05D6\u05D4 \u05DE\u05EA\u05D5\u05DA Trust Wallet \u05D0\u05D5 MetaMask';

    var closeBtn = document.createElement('button');
    closeBtn.textContent = '\u2715';
    closeBtn.style.cssText = 'background:none;border:none;color:var(--text2,#888);font-size:18px;cursor:pointer;padding:2px 6px;flex-shrink:0';
    closeBtn.onclick = function () { banner.remove(); sessionStorage.setItem('slh_mobile_banner_closed', '1'); };

    if (sessionStorage.getItem('slh_mobile_banner_closed') === '1') return;

    banner.appendChild(text);
    banner.appendChild(closeBtn);
    document.body.appendChild(banner);
  }

  // ---- Expose globals ----
  window.SLHWeb3 = {
    connect: connectWallet,
    disconnect: disconnectWallet,
    sign: signMessage,
    getAddress: () => web3Address,
    getBalances: renderWeb3Balances,
    getBSCBalance: getBSCBalance,
    getBSCNative: getBSCNativeBalance,
    getETH: getETHBalance,
    getTON: getTONBalance,
    init: initWeb3UI,
    showNoWalletHelp: _showNoWalletModal,
    showMobileBanner: _showMobileBanner,
    SLH_CONTRACT_BSC,
    USDT_CONTRACT_BSC
  };

  // Auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { initWeb3UI(); _showMobileBanner(); });
  } else {
    initWeb3UI();
    _showMobileBanner();
  }
})();
