/* SLH Mini App shared helpers.
 *
 * Every page boots with initMiniApp() which:
 *   1. Expands Telegram WebApp to full height
 *   2. Applies theme (Telegram already does — we just read values)
 *   3. Exposes window.SLH = { api, tg, user } for the page
 *
 * Every API call goes through SLH.api(path, opts). The helper sends the
 * Telegram initData as X-Telegram-Init-Data so api/telegram_gateway.py can
 * verify the signature and resolve the user server-side.
 */
(function () {
  "use strict";

  const API_BASE =
    (typeof window !== "undefined" && window.__SLH_API_BASE__) ||
    "https://slh-api-production.up.railway.app";

  const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;

  function isInTelegram() {
    return !!(tg && tg.initData && tg.initData.length > 0);
  }

  async function api(path, opts = {}) {
    const headers = new Headers(opts.headers || {});
    if (!headers.has("Accept")) headers.set("Accept", "application/json");
    if (isInTelegram()) {
      headers.set("X-Telegram-Init-Data", tg.initData);
    }
    if (opts.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const url = path.startsWith("http") ? path : API_BASE + path;
    const resp = await fetch(url, {
      method: opts.method || "GET",
      headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (!resp.ok) {
      let detail = resp.statusText;
      try {
        const j = await resp.json();
        detail = (j && (j.detail || j.message)) || detail;
      } catch (_) {}
      const err = new Error(detail);
      err.status = resp.status;
      throw err;
    }
    return resp.json();
  }

  function fmt(n, digits) {
    if (n === null || n === undefined || Number.isNaN(Number(n))) return "--";
    const num = Number(n);
    if (digits === undefined) digits = num < 1 ? 4 : 2;
    return num.toLocaleString("he-IL", {
      minimumFractionDigits: 0,
      maximumFractionDigits: digits,
    });
  }

  function renderErr(el, err) {
    if (!el) return;
    el.innerHTML =
      '<div class="err">שגיאה: ' + (err && err.message ? err.message : "לא ידוע") + "</div>";
  }

  function renderLoading(el, text) {
    if (!el) return;
    el.innerHTML = '<span class="spinner"></span> ' + (text || "טוען...");
  }

  function initMiniApp(opts) {
    opts = opts || {};
    if (tg) {
      tg.ready();
      tg.expand();
      if (opts.title) tg.setHeaderColor("secondary_bg_color");
    }
    const user = tg && tg.initDataUnsafe ? tg.initDataUnsafe.user : null;
    window.SLH = {
      api,
      tg,
      user,
      inTelegram: isInTelegram(),
      fmt,
      renderErr,
      renderLoading,
    };
    const greet = document.getElementById("user-greeting");
    if (greet) {
      greet.textContent = user
        ? "שלום " + (user.first_name || user.username || "משתמש")
        : "מצב מוטמע (ללא Telegram)";
    }
    return window.SLH;
  }

  window.SLH_init = initMiniApp;
})();
