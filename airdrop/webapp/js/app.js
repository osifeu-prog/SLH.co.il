(function () {
  const API = location.origin; // backend serves webapp under same origin

  function getTelegramContext() {
    const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
    if (tg && tg.initData && tg.initDataUnsafe && tg.initDataUnsafe.user) {
      return { telegram_id: tg.initDataUnsafe.user.id, init_data: tg.initData };
    }
    // DEV fallback
    return { telegram_id: 111, init_data: "hash=dev" };
  }

  async function api(path, opts) {
    const res = await fetch(API + path, opts);
    const text = await res.text();
    let json = null;
    try { json = JSON.parse(text); } catch {}
    if (!res.ok) throw new Error(`${res.status} ${text}`);
    return json ?? text;
  }

  async function loadProfile() {
    const ctx = getTelegramContext();
    const data = await api(`/api/v1/user/info?telegram_id=${ctx.telegram_id}`);
    document.getElementById("profile").innerText = `User #${data.id} | telegram_id=${data.telegram_id} | role=${data.role}`;
  }

  async function loadBalance() {
    const ctx = getTelegramContext();
    const data = await api(`/api/v1/wallet/balance?telegram_id=${ctx.telegram_id}`);
    document.getElementById("balance").innerText = data.balance;
  }

  async function loadTokenConfig() {
    const data = await api(`/api/v1/token/price`);
    document.getElementById("tokenConfig").innerText = `price=${data.price} | max_airdrop_per_user=${data.max_airdrop_per_user}`;
  }

  async function requestAirdrop() {
    const ctx = getTelegramContext();
    const amount = document.getElementById("amount").value || "1";
    const data = await api(`/api/v1/airdrop/request?telegram_id=${ctx.telegram_id}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ amount })
    });
    document.getElementById("airdropResult").innerText = `Requested: id=${data.id} amount=${data.amount} status=${data.status}`;
    await loadBalance();
  }

  document.getElementById("refreshBalance").addEventListener("click", () => loadBalance().catch(alert));
  document.getElementById("requestAirdrop").addEventListener("click", () => requestAirdrop().catch(alert));

  Promise.all([loadProfile(), loadBalance(), loadTokenConfig()]).catch(err => alert(err.message));
})();
