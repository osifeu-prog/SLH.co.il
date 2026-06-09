/**
 * SLH Spark — Telegram Login Widget helper
 *
 * Usage (drop-in):
 *   <div id="tg-login"></div>
 *   <script src="/js/telegram-login.js"></script>
 *   <script>SLHTelegramLogin.mount('#tg-login', { bot: 'SLH_community_bot' });</script>
 *
 * Or with onAuth callback (no redirect):
 *   SLHTelegramLogin.mount('#tg-login', {
 *     bot: 'SLH_community_bot',
 *     onAuth: (user) => { console.log('Logged in', user); }
 *   });
 *
 * The widget calls window.onTelegramAuth(user) which we proxy to /api/auth/telegram
 * and, on success, stores the user in localStorage.slh_user and reloads the page.
 */

(function (global) {
  const API = 'https://slh-api-production.up.railway.app';
  const DEFAULT_BOT = 'SLH_community_bot';

  /**
   * Exchange Telegram widget payload for a verified session.
   * @param {object} user  { id, first_name, last_name, username, photo_url, auth_date, hash }
   * @returns {Promise<object>}  Full user profile returned by the API
   */
  async function verifyWithAPI(user) {
    const r = await fetch(API + '/api/auth/telegram', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user)
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || ('HTTP ' + r.status));
    }
    return r.json();
  }

  /**
   * Mount a Telegram Login Widget into `selector`.
   * @param {string} selector  CSS selector for the container (e.g. '#tg-login')
   * @param {object} opts
   * @param {string} opts.bot        Bot username WITHOUT @ (default: SLH_community_bot)
   * @param {string} opts.size       'large' | 'medium' | 'small' (default: 'large')
   * @param {boolean} opts.userpic   Show user photo (default: true)
   * @param {string} opts.radius     Border radius in px (default: '10')
   * @param {string} opts.lang       Language code (default: 'he')
   * @param {Function} opts.onAuth   Callback(userProfile). If not provided, redirect to /profile.html
   */
  function mount(selector, opts = {}) {
    const el = document.querySelector(selector);
    if (!el) {
      console.warn('[SLHTelegramLogin] Container not found:', selector);
      return;
    }
    const bot = opts.bot || DEFAULT_BOT;
    const size = opts.size || 'large';
    const userpic = opts.userpic !== false;
    const radius = opts.radius || '10';
    const lang = opts.lang || document.documentElement.lang || 'he';

    // Wire global callback BEFORE injecting the script (Telegram widget calls it by name)
    global.onTelegramAuth = async function (user) {
      try {
        const profile = await verifyWithAPI(user);
        try {
          localStorage.setItem('slh_user', JSON.stringify({
            id: user.id,
            username: user.username,
            first_name: user.first_name,
            photo_url: user.photo_url,
            authenticated_at: new Date().toISOString()
          }));
        } catch (_) { /* localStorage may be blocked */ }

        if (typeof opts.onAuth === 'function') {
          opts.onAuth(profile);
        } else {
          const next = new URLSearchParams(location.search).get('next') || '/profile.html';
          location.href = next;
        }
      } catch (e) {
        console.error('[SLHTelegramLogin] Auth failed:', e);
        alert('התחברות נכשלה: ' + e.message);
      }
    };

    // Clear previous widget (if re-mounting)
    el.innerHTML = '';

    const s = document.createElement('script');
    s.async = true;
    s.src = 'https://telegram.org/js/telegram-widget.js?22';
    s.setAttribute('data-telegram-login', bot);
    s.setAttribute('data-size', size);
    s.setAttribute('data-userpic', userpic ? 'true' : 'false');
    s.setAttribute('data-radius', radius);
    s.setAttribute('data-lang', lang);
    s.setAttribute('data-onauth', 'onTelegramAuth(user)');
    s.setAttribute('data-request-access', 'write');
    el.appendChild(s);
  }

  /** Quick check: is the current visitor logged in? */
  function currentUser() {
    try { return JSON.parse(localStorage.getItem('slh_user') || 'null'); }
    catch (_) { return null; }
  }

  function logout() {
    try { localStorage.removeItem('slh_user'); } catch (_) {}
    location.reload();
  }

  global.SLHTelegramLogin = { mount, currentUser, logout, verifyWithAPI };
})(window);
