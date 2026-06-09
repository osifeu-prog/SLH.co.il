/**
 * SLH Ecosystem — Web3 Wallet Module
 * MetaMask/Trust Wallet (BSC) + TonConnect (TON)
 */

/* ===== CONSTANTS ===== */
const SLH_BSC_CHAIN = {
  chainId: '0x38',
  chainName: 'BNB Smart Chain',
  nativeCurrency: { name: 'BNB', symbol: 'BNB', decimals: 18 },
  rpcUrls: ['https://bsc-dataseed.binance.org/'],
  blockExplorerUrls: ['https://bscscan.com/']
};

const SLH_ADMIN_BSC = '0xD0617B54FB4b6b66307846f217b4D685800E3dA4';
const SLH_ADMIN_TON = 'UQCr743gEr_nqV_0SBkSp3CtYS_15R3LDLBvLmKeEv7XdGvp';
const SLH_TOKEN_CONTRACT = '0xACb0A09414CEA1C879c67bB7A877E4e19480f022';

/* ===== STATE ===== */
let _tonConnectUI = null;
let _bscConnected = false;
let _tonConnected = false;

/* ===== USER WALLET PERSISTENCE ===== */

function getUserWallets() {
  try {
    const raw = localStorage.getItem('slh_user');
    const user = raw ? JSON.parse(raw) : null;
    return user?.wallets || { bsc: null, ton: null };
  } catch { return { bsc: null, ton: null }; }
}

function saveUserWallet(chain, address) {
  try {
    let raw = localStorage.getItem('slh_user');
    let user = raw ? JSON.parse(raw) : {};
    if (!user.wallets) user.wallets = { bsc: null, ton: null };
    user.wallets[chain] = address;
    localStorage.setItem('slh_user', JSON.stringify(user));

    // Sync to backend
    if (user.id) {
      apiPost('/api/user/' + user.id + '/wallets', {
        chain, address, user_id: user.id
      }).catch(() => {});
    }

    // Dispatch event for UI updates
    window.dispatchEvent(new CustomEvent('wallet-changed', { detail: { chain, address } }));
  } catch (e) { console.error('[Wallet] save error:', e); }
}

function disconnectWallet(chain) {
  saveUserWallet(chain, null);
  if (chain === 'bsc') _bscConnected = false;
  if (chain === 'ton') {
    _tonConnected = false;
    if (_tonConnectUI) _tonConnectUI.disconnect().catch(() => {});
  }
  window.dispatchEvent(new CustomEvent('wallet-changed', { detail: { chain, address: null } }));
}

/* ===== BSC: MetaMask / Trust Wallet ===== */

function isBSCAvailable() {
  return typeof window.ethereum !== 'undefined';
}

async function connectBSC() {
  if (!window.ethereum) {
    // Show install prompt
    const isMobile = /Android|iPhone|iPad/i.test(navigator.userAgent);
    if (isMobile) {
      // Deep link to Trust Wallet
      window.open('https://link.trustwallet.com/open_url?coin_id=20000714&url=' + encodeURIComponent(window.location.href), '_blank');
    } else {
      window.open('https://metamask.io/download/', '_blank');
    }
    showToast('Please install MetaMask or Trust Wallet', true);
    return null;
  }

  try {
    // Request accounts
    const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
    if (!accounts || accounts.length === 0) {
      showToast('No account selected', true);
      return null;
    }

    // Switch to BSC
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: SLH_BSC_CHAIN.chainId }]
      });
    } catch (switchError) {
      // Chain not added, add it
      if (switchError.code === 4902) {
        await window.ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [SLH_BSC_CHAIN]
        });
      } else {
        throw switchError;
      }
    }

    const address = accounts[0];
    _bscConnected = true;
    saveUserWallet('bsc', address);
    showToast('BSC Wallet Connected');
    return address;

  } catch (err) {
    console.error('[BSC] connect error:', err);
    if (err.code === 4001) {
      showToast('Connection rejected by user', true);
    } else {
      showToast('BSC connection failed', true);
    }
    return null;
  }
}

async function getBSCBalance(address) {
  if (!window.ethereum) return null;
  try {
    const balance = await window.ethereum.request({
      method: 'eth_getBalance',
      params: [address, 'latest']
    });
    return parseInt(balance, 16) / 1e18;
  } catch { return null; }
}

async function getSLHTokenBalance(address) {
  if (!window.ethereum) return null;
  try {
    // ERC-20 balanceOf(address)
    const data = '0x70a08231' + address.slice(2).padStart(64, '0');
    const result = await window.ethereum.request({
      method: 'eth_call',
      params: [{ to: SLH_TOKEN_CONTRACT, data }, 'latest']
    });
    return parseInt(result, 16) / 1e15; // SLH has 15 decimals
  } catch { return null; }
}

async function sendBSCTransaction(toAddress, amountBNB) {
  if (!window.ethereum) return null;
  try {
    const accounts = await window.ethereum.request({ method: 'eth_accounts' });
    if (!accounts.length) return null;

    const amountWei = '0x' + Math.floor(amountBNB * 1e18).toString(16);
    const txHash = await window.ethereum.request({
      method: 'eth_sendTransaction',
      params: [{
        from: accounts[0],
        to: toAddress,
        value: amountWei,
        chainId: SLH_BSC_CHAIN.chainId
      }]
    });
    return txHash;
  } catch (err) {
    console.error('[BSC] tx error:', err);
    return null;
  }
}

// Listen for account/chain changes
if (typeof window.ethereum !== 'undefined') {
  window.ethereum.on('accountsChanged', (accounts) => {
    if (accounts.length > 0) {
      saveUserWallet('bsc', accounts[0]);
    } else {
      disconnectWallet('bsc');
    }
  });
  window.ethereum.on('chainChanged', () => window.location.reload());
}


/* ===== TON: TonConnect ===== */

async function initTonConnect() {
  if (_tonConnectUI) return _tonConnectUI;

  // Wait for TonConnect SDK to load
  if (typeof TonConnectUI === 'undefined' && typeof TON_CONNECT_UI !== 'undefined') {
    // Already loaded via global
  }

  try {
    const TC = window.TON_CONNECT_UI?.TonConnectUI || window.TonConnectUI;
    if (!TC) {
      console.warn('[TON] TonConnect SDK not loaded');
      return null;
    }

    _tonConnectUI = new TC({
      manifestUrl: 'https://slh-nft.com/tonconnect-manifest.json',
      buttonRootId: null // We manage UI ourselves
    });

    // Listen for status changes
    _tonConnectUI.onStatusChange((wallet) => {
      if (wallet) {
        const addr = wallet.account?.address || '';
        // Convert raw address to user-friendly format
        const friendlyAddr = addr;
        _tonConnected = true;
        saveUserWallet('ton', friendlyAddr);
      } else {
        _tonConnected = false;
        saveUserWallet('ton', null);
      }
    });

    // Check if already connected
    if (_tonConnectUI.connected) {
      const wallet = _tonConnectUI.wallet;
      if (wallet?.account?.address) {
        _tonConnected = true;
        saveUserWallet('ton', wallet.account.address);
      }
    }

    return _tonConnectUI;
  } catch (err) {
    console.error('[TON] init error:', err);
    return null;
  }
}

async function connectTON() {
  try {
    const tc = await initTonConnect();
    if (!tc) {
      // Fallback: manual address entry
      const addr = prompt('Enter your TON wallet address:');
      if (addr && addr.startsWith('UQ') || addr?.startsWith('EQ')) {
        saveUserWallet('ton', addr);
        showToast('TON Wallet linked');
        return addr;
      }
      showToast('TonConnect unavailable. Install Tonkeeper.', true);
      return null;
    }

    if (tc.connected) {
      return tc.wallet?.account?.address;
    }

    await tc.openModal();
    // The onStatusChange callback will handle the rest
    return 'pending';
  } catch (err) {
    console.error('[TON] connect error:', err);
    showToast('TON connection failed', true);
    return null;
  }
}


/* ===== WALLET CONNECTION UI COMPONENT ===== */

function shortAddress(addr) {
  if (!addr) return '';
  return addr.slice(0, 6) + '...' + addr.slice(-4);
}

function renderWalletConnectButtons(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const wallets = getUserWallets();
  const lang = getLang ? getLang() : 'en';
  const isHe = lang === 'he' || lang === 'ar';

  container.innerHTML = `
    <div class="wallet-connect-grid">
      <!-- BSC Wallet -->
      <div class="wallet-connect-card ${wallets.bsc ? 'connected' : ''}">
        <div class="wc-chain-icon">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none"><path d="M14 2L7 6v4l7-4 7 4V6L14 2zm0 8L7 14v4l7-4 7 4v-4l-7-4zm-7 8l7 4 7-4v-4l-7 4-7-4v4z" fill="#F0B90B"/></svg>
        </div>
        <div class="wc-chain-name">BNB Smart Chain</div>
        ${wallets.bsc
          ? `<div class="wc-address" title="${wallets.bsc}">${shortAddress(wallets.bsc)}</div>
             <div class="wc-actions">
               <button class="wc-btn wc-btn-copy" onclick="copyToClipboard('${wallets.bsc}')"><i class="fas fa-copy"></i></button>
               <a href="https://bscscan.com/address/${wallets.bsc}" target="_blank" class="wc-btn wc-btn-scan"><i class="fas fa-external-link-alt"></i></a>
               <button class="wc-btn wc-btn-disconnect" onclick="disconnectWallet('bsc')"><i class="fas fa-unlink"></i></button>
             </div>`
          : `<button class="wc-connect-btn wc-bsc" onclick="connectBSC().then(()=>renderWalletConnectButtons('${containerId}'))">
               <i class="fas fa-wallet"></i> ${isHe ? 'חבר ארנק BSC' : 'Connect BSC Wallet'}
             </button>
             <div class="wc-hint">${isHe ? 'MetaMask / Trust Wallet' : 'MetaMask / Trust Wallet'}</div>`
        }
      </div>

      <!-- TON Wallet -->
      <div class="wallet-connect-card ${wallets.ton ? 'connected' : ''}">
        <div class="wc-chain-icon">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none"><path d="M14 2L3 8v12l11 6 11-6V8L14 2z" fill="#0088CC"/><path d="M14 6L7 10v8l7 4 7-4v-8l-7-4z" fill="#fff" opacity=".3"/></svg>
        </div>
        <div class="wc-chain-name">TON Network</div>
        ${wallets.ton
          ? `<div class="wc-address" title="${wallets.ton}">${shortAddress(wallets.ton)}</div>
             <div class="wc-actions">
               <button class="wc-btn wc-btn-copy" onclick="copyToClipboard('${wallets.ton}')"><i class="fas fa-copy"></i></button>
               <a href="https://tonscan.org/address/${wallets.ton}" target="_blank" class="wc-btn wc-btn-scan"><i class="fas fa-external-link-alt"></i></a>
               <button class="wc-btn wc-btn-disconnect" onclick="disconnectWallet('ton')"><i class="fas fa-unlink"></i></button>
             </div>`
          : `<button class="wc-connect-btn wc-ton" onclick="connectTON().then(()=>setTimeout(()=>renderWalletConnectButtons('${containerId}'),1000))">
               <i class="fas fa-gem"></i> ${isHe ? 'חבר ארנק TON' : 'Connect TON Wallet'}
             </button>
             <div class="wc-hint">${isHe ? 'Tonkeeper / MyTonWallet' : 'Tonkeeper / MyTonWallet'}</div>`
        }
      </div>
    </div>`;
}


/* ===== NAVBAR WALLET BADGE ===== */

function getWalletBadgeHTML() {
  const wallets = getUserWallets();
  if (!wallets.bsc && !wallets.ton) return '';

  let badges = '';
  if (wallets.bsc) {
    badges += `<span class="nav-wallet-badge bsc" title="BSC: ${wallets.bsc}">
      <span class="chain-dot bsc-dot"></span>${shortAddress(wallets.bsc)}
    </span>`;
  }
  if (wallets.ton) {
    badges += `<span class="nav-wallet-badge ton" title="TON: ${wallets.ton}">
      <span class="chain-dot ton-dot"></span>${shortAddress(wallets.ton)}
    </span>`;
  }
  return `<div class="nav-wallets">${badges}</div>`;
}
