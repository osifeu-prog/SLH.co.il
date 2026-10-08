/**
 * SLH OS — canonical public truth beacon
 * Read-only UI layer for the public website.
 */
(function () {
  'use strict';

  const STATUS_URL = 'https://slh-cloud-bot-production.up.railway.app/api/public/site-status';

  function esc(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[ch]));
  }

  function statusLabel(value, fallback) {
    return value === 'OPEN' ? 'פתוח' : value === 'CLOSED' ? 'סגור' : fallback;
  }

  function tone(value, openTone) {
    return value === 'OPEN' ? openTone : 'closed';
  }

  function render(data) {
    if (!data || data.ok !== true) return;
    if (document.getElementById('slh-truth-bar')) return;

    const exchangeOpen = data.exchange?.gate === 'OPEN' && data.exchange?.verdict === 'OPEN';
    const tonOpen = data.settlement?.ton?.gate === 'OPEN';
    const bnbOpen = data.settlement?.bnb?.gate === 'OPEN';
    const participationActive = data.participation?.active === true;

    const bar = document.createElement('div');
    bar.id = 'slh-truth-bar';
    bar.innerHTML = `
      <style>
        #slh-truth-bar{
          position:relative;z-index:9997;width:100%;
          background:#07101b;border-bottom:1px solid rgba(94,214,255,.18);
          color:#eaf7ff;font:600 12px/1.4 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
        }
        #slh-truth-bar .inner{
          max-width:1280px;margin:0 auto;padding:7px 14px;
          display:flex;align-items:center;justify-content:center;gap:8px 14px;flex-wrap:wrap;
        }
        #slh-truth-bar .label{color:#9fb3c8}
        #slh-truth-bar .pill{
          display:inline-flex;align-items:center;gap:5px;
          padding:3px 8px;border-radius:999px;border:1px solid rgba(255,255,255,.12)
        }
        #slh-truth-bar .pill.open{color:#00e887;border-color:rgba(0,232,135,.25);background:rgba(0,232,135,.06)}
        #slh-truth-bar .pill.closed{color:#ffd166;border-color:rgba(255,209,102,.22);background:rgba(255,209,102,.05)}
        #slh-truth-bar .pill.design{color:#c6a7ff;border-color:rgba(198,167,255,.22);background:rgba(198,167,255,.05)}
        #slh-truth-bar a{color:#5ed6ff;text-decoration:underline}
        @media(max-width:700px){#slh-truth-bar .inner{justify-content:flex-start}}
      </style>
      <div class="inner">
        <span class="label">SLH OS · מקור אמת חי</span>
        <span class="pill ${exchangeOpen ? 'open' : 'closed'}">מסחר פנימי: ${exchangeOpen ? 'פתוח' : 'סגור'}</span>
        <span class="pill ${tone(data.settlement?.ton?.gate)}">TON: ${statusLabel(data.settlement?.ton?.gate, 'לא זמין')}</span>
        <span class="pill ${tone(data.settlement?.bnb?.gate)}">BNB: ${statusLabel(data.settlement?.bnb?.gate, 'לא זמין')}</span>
        <span class="pill ${participationActive ? 'open' : 'design'}">Participation: ${participationActive ? 'פעיל' : 'תכנון בלבד'}</span>
        <span class="label">ממשק ראשי: Telegram Mini App</span>
        <a href="/status.html">פרטי סטטוס ↗</a>
      </div>`;
    document.body.insertBefore(bar, document.body.firstChild);
  }

  async function init() {
    try {
      const response = await fetch(STATUS_URL, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        cache: 'no-store'
      });
      if (!response.ok) return;
      render(await response.json());
    } catch (_) {
      // Public truth is additive; never block the site if the beacon is unavailable.
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
