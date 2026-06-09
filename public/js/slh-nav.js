/**
 * SLH Unified Navigation v1.0
 * Injects a consistent navbar into any SLH page.
 * Depends on: slh-design-system.css + Font Awesome 6.
 */
(function () {
  let currentUser = {
    isLoggedIn: false,
    role: 'guest',
    name: 'Guest',
    avatarInitials: 'G',
    email: ''
  };

  if (window.SLH_USER) currentUser = { ...currentUser, ...window.SLH_USER };
  const stored = localStorage.getItem('slh_user');
  if (stored) { try { currentUser = { ...currentUser, ...JSON.parse(stored) }; } catch (e) {} }

  const navLinks = {
    guest: [
      { label: { en: 'Home', he: 'בית' }, href: '/' },
      { label: { en: 'About', he: 'אודות' }, href: '/about.html' },
      { label: { en: 'Tour', he: 'סיור' }, href: '/tour.html' },
      { label: { en: 'Blog', he: 'בלוג' }, href: '/blog.html' },
      { label: { en: 'Login', he: 'התחברות' }, href: '/login.html' }
    ],
    user: [
      { label: { en: 'Dashboard', he: 'לוח בקרה' }, href: '/' },
      { label: { en: 'Community', he: 'קהילה' }, href: '/community.html' },
      { label: { en: 'Learning', he: 'למידה' }, href: '/learning-path.html' },
      { label: { en: 'Experts', he: 'מומחים' }, href: '/experts.html' },
      { label: { en: 'Settings', he: 'הגדרות' }, href: '/settings.html' }
    ],
    admin: [
      { label: { en: 'Dashboard', he: 'לוח בקרה' }, href: '/' },
      { label: { en: 'Mission Control', he: 'Mission Control' }, href: '/mission-control.html' },
      { label: { en: 'Tokens', he: 'טוקנים' }, href: '/admin-tokens.html' },
      { label: { en: 'Agents', he: 'סוכנים' }, href: '/agent-tracker.html' },
      { label: { en: 'Admin', he: 'ניהול' }, href: '/admin.html' }
    ]
  };

  const themes = ['dark', 'light', 'zen', 'sunset', 'ocean'];
  let currentTheme = localStorage.getItem('slh_theme') || 'dark';
  let currentLang = localStorage.getItem('slh_lang') || (document.documentElement.lang || 'he');

  const t = (en, he) => (currentLang === 'he' ? he : en);

  function setTheme(name) {
    themes.forEach(x => document.body.classList.remove(`theme-${x}`));
    document.body.classList.add(`theme-${name}`);
    localStorage.setItem('slh_theme', name);
    currentTheme = name;
  }

  function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('slh_lang', lang);
    document.documentElement.setAttribute('dir', lang === 'he' ? 'rtl' : 'ltr');
    document.documentElement.setAttribute('lang', lang);
    renderNav();
  }

  function logout() {
    localStorage.removeItem('slh_user');
    currentUser = { isLoggedIn: false, role: 'guest', name: 'Guest', avatarInitials: 'G', email: '' };
    window.location.href = '/';
  }

  function renderNav() {
    const existing = document.getElementById('slh-nav');
    if (existing) existing.remove();
    const links = navLinks[currentUser.role] || navLinks.guest;
    const nav = document.createElement('nav');
    nav.id = 'slh-nav';
    nav.className = 'slh-nav';
    nav.setAttribute('aria-label', t('Main navigation', 'ניווט ראשי'));
    nav.innerHTML = `
      <div class="nav-container">
        <a href="/" class="brand-link"><span class="brand-icon">✨</span><span class="brand-name">SLH Spark</span></a>
        <button class="nav-hamburger" id="navHamburger" aria-label="${t('Menu','תפריט')}" aria-expanded="false"><i class="fas fa-bars"></i></button>
        <div class="nav-menu" id="navMenu">
          <ul class="nav-links">${links.map(l => `<li><a href="${l.href}" class="nav-link">${t(l.label.en, l.label.he)}</a></li>`).join('')}</ul>
          <div class="nav-actions">
            <div class="nav-dropdown">
              <button class="nav-icon-btn" id="themeBtn" aria-label="${t('Theme','ערכת נושא')}"><i class="fas fa-palette"></i></button>
              <div class="dropdown-menu" id="themeMenu">
                ${themes.map(x => `<button class="dropdown-item" data-theme="${x}"><i class="fas fa-circle"></i> ${x}</button>`).join('')}
              </div>
            </div>
            <div class="nav-dropdown">
              <button class="nav-icon-btn" id="langBtn" aria-label="${t('Language','שפה')}"><i class="fas fa-globe"></i> ${currentLang === 'he' ? 'עב' : 'EN'}</button>
              <div class="dropdown-menu" id="langMenu">
                <button class="dropdown-item" data-lang="he">🇮🇱 עברית</button>
                <button class="dropdown-item" data-lang="en">🇬🇧 English</button>
              </div>
            </div>
            <div class="nav-dropdown">
              <button class="avatar-btn" id="userBtn" aria-label="${t('User','משתמש')}"><div class="avatar">${currentUser.avatarInitials}</div></button>
              <div class="dropdown-menu" id="userMenu">
                ${currentUser.isLoggedIn ? `
                  <div class="dropdown-header">${currentUser.name}</div>
                  <a href="/settings.html" class="dropdown-item"><i class="fas fa-cog"></i> ${t('Settings','הגדרות')}</a>
                  <button id="logoutBtn" class="dropdown-item"><i class="fas fa-sign-out-alt"></i> ${t('Logout','התנתקות')}</button>
                ` : `
                  <a href="/login.html" class="dropdown-item"><i class="fas fa-sign-in-alt"></i> ${t('Login','התחברות')}</a>
                  <a href="/register.html" class="dropdown-item"><i class="fas fa-user-plus"></i> ${t('Register','הרשמה')}</a>
                `}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
    document.body.insertAdjacentElement('afterbegin', nav);
    document.body.style.paddingTop = '70px';
    attach();
  }

  function attach() {
    const ham = document.getElementById('navHamburger');
    const menu = document.getElementById('navMenu');
    ham?.addEventListener('click', () => {
      const exp = ham.getAttribute('aria-expanded') === 'true';
      ham.setAttribute('aria-expanded', !exp);
      menu?.classList.toggle('nav-menu-open');
    });

    const bind = (btnId, menuId, handler) => {
      const btn = document.getElementById(btnId);
      const m = document.getElementById(menuId);
      btn?.addEventListener('click', e => { e.stopPropagation(); m?.classList.toggle('show'); });
      m?.querySelectorAll('.dropdown-item').forEach(item => item.addEventListener('click', () => { handler(item); m.classList.remove('show'); }));
    };
    bind('themeBtn', 'themeMenu', item => item.dataset.theme && setTheme(item.dataset.theme));
    bind('langBtn', 'langMenu', item => item.dataset.lang && setLanguage(item.dataset.lang));
    bind('userBtn', 'userMenu', () => {});
    document.getElementById('logoutBtn')?.addEventListener('click', logout);

    document.addEventListener('click', e => {
      if (!e.target.closest('.nav-dropdown')) {
        document.querySelectorAll('.dropdown-menu.show').forEach(x => x.classList.remove('show'));
      }
    });
  }

  function init() { setTheme(currentTheme); setLanguage(currentLang); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
