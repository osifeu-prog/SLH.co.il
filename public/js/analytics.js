/* SLH Analytics Tracker — lightweight real-time analytics */
(function () {
  'use strict';
  const API = 'https://slh-api-production.up.railway.app/api/analytics';
  const HEARTBEAT_MS = 30000;
  const QUEUE_KEY = 'slh_analytics_queue';
  const STATS_KEY = 'slh_analytics_stats';
  const VID_KEY = 'slh_visitor_id';
  const SESSION_KEY = 'slh_session_start';

  /* ── Helpers ───────────────────────────────── */
  function uid() {
    return 'v_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
  }
  function getVisitorId() {
    let id = localStorage.getItem(VID_KEY);
    if (!id) { id = uid(); localStorage.setItem(VID_KEY, id); }
    return id;
  }
  function now() { return Date.now(); }
  function today() { return new Date().toISOString().slice(0, 10); }
  function readJSON(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) || fallback; } catch { return fallback; }
  }
  function writeJSON(key, val) { localStorage.setItem(key, JSON.stringify(val)); }

  /* ── State ─────────────────────────────────── */
  const visitorId = getVisitorId();
  const sessionStart = now();
  localStorage.setItem(SESSION_KEY, String(sessionStart));
  let maxScroll = 0;
  const scrollMarks = {};

  /* ── Stats Store ───────────────────────────── */
  function getStats() { return readJSON(STATS_KEY, { days: {}, pages: {}, referrers: {}, langs: {}, devices: {}, clicks: {}, visitors: {}, heartbeats: {} }); }
  function saveStats(s) { writeJSON(STATS_KEY, s); }

  function recordLocal(evt) {
    const s = getStats();
    const d = today();
    if (!s.days[d]) s.days[d] = { views: 0, visitors: [] };
    if (evt.type === 'pageview') {
      s.days[d].views++;
      if (!s.days[d].visitors.includes(evt.vid)) s.days[d].visitors.push(evt.vid);
      s.pages[evt.page] = s.pages[evt.page] || { views: 0, visitors: [], totalTime: 0 };
      s.pages[evt.page].views++;
      if (!s.pages[evt.page].visitors.includes(evt.vid)) s.pages[evt.page].visitors.push(evt.vid);
      const ref = evt.referrer ? (new URL(evt.referrer).hostname || 'direct') : 'direct';
      s.referrers[ref] = (s.referrers[ref] || 0) + 1;
      s.langs[evt.lang] = (s.langs[evt.lang] || 0) + 1;
      s.devices[evt.device] = (s.devices[evt.device] || 0) + 1;
    } else if (evt.type === 'click') {
      const label = evt.label || evt.page;
      s.clicks[label] = (s.clicks[label] || 0) + 1;
    } else if (evt.type === 'heartbeat') {
      s.heartbeats[evt.vid] = evt.ts;
    } else if (evt.type === 'session_end') {
      const pg = s.pages[evt.page];
      if (pg) pg.totalTime += evt.duration || 0;
    }
    saveStats(s);
  }

  /* ── Queue & Send ──────────────────────────── */
  function enqueue(evt) {
    const q = readJSON(QUEUE_KEY, []);
    q.push(evt);
    writeJSON(QUEUE_KEY, q);
  }
  function sendEvent(evt) {
    recordLocal(evt);
    const payload = JSON.stringify(evt);
    if (navigator.sendBeacon) {
      const ok = navigator.sendBeacon(API + '/event', new Blob([payload], { type: 'application/json' }));
      if (!ok) enqueue(evt);
    } else {
      fetch(API + '/event', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: payload, keepalive: true })
        .catch(function () { enqueue(evt); });
    }
  }
  function flushQueue() {
    const q = readJSON(QUEUE_KEY, []);
    if (!q.length) return;
    writeJSON(QUEUE_KEY, []);
    q.forEach(function (evt) {
      fetch(API + '/event', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(evt) })
        .catch(function () { enqueue(evt); });
    });
  }

  /* ── Collect device info ───────────────────── */
  function device() { return window.innerWidth < 768 ? 'mobile' : 'desktop'; }
  function baseMeta() {
    return { vid: visitorId, page: location.pathname, ts: now(), lang: (navigator.language || 'en').slice(0, 2), device: device(), screen: screen.width + 'x' + screen.height };
  }

  /* ── Pageview ──────────────────────────────── */
  function trackPageview() {
    sendEvent(Object.assign({ type: 'pageview', referrer: document.referrer || '' }, baseMeta()));
  }

  /* ── Heartbeat ─────────────────────────────── */
  function heartbeat() {
    sendEvent(Object.assign({ type: 'heartbeat' }, baseMeta()));
  }

  /* ── Scroll depth ──────────────────────────── */
  function onScroll() {
    var docH = document.documentElement.scrollHeight - window.innerHeight;
    if (docH <= 0) return;
    var pct = Math.round((window.scrollY / docH) * 100);
    if (pct > maxScroll) maxScroll = pct;
    [25, 50, 75, 100].forEach(function (mark) {
      if (maxScroll >= mark && !scrollMarks[mark]) {
        scrollMarks[mark] = true;
        sendEvent(Object.assign({ type: 'scroll', depth: mark }, baseMeta()));
      }
    });
  }

  /* ── Click tracking ────────────────────────── */
  function onClick(e) {
    var el = e.target.closest('[data-track]');
    if (!el) return;
    sendEvent(Object.assign({ type: 'click', label: el.getAttribute('data-track') }, baseMeta()));
  }

  /* ── Session end ───────────────────────────── */
  function onUnload() {
    var duration = Math.round((now() - sessionStart) / 1000);
    sendEvent(Object.assign({ type: 'session_end', duration: duration, maxScroll: maxScroll }, baseMeta()));
  }

  /* ── Public API ────────────────────────────── */
  function trackEvent(name, data) {
    sendEvent(Object.assign({ type: 'custom', name: name, data: data || {} }, baseMeta()));
  }

  /* ── Init ──────────────────────────────────── */
  trackPageview();
  setInterval(heartbeat, HEARTBEAT_MS);
  setInterval(flushQueue, 60000);
  window.addEventListener('scroll', onScroll, { passive: true });
  document.addEventListener('click', onClick);
  window.addEventListener('beforeunload', onUnload);

  window.SLH_Analytics = { trackEvent: trackEvent, getStats: getStats, visitorId: visitorId };
})();
