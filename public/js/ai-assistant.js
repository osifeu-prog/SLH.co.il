/**
 * SLH Ecosystem — AI Chat Assistant Widget
 * Self-contained floating chat widget with dynamic CSS injection.
 * Usage: <script src="js/ai-assistant.js"></script>
 *
 * Calls POST /api/ai/chat on the SLH backend — NO API keys in frontend.
 */

(function () {
  'use strict';

  /* ===== CONFIG ===== */

  const AI_ENDPOINT = (typeof API_BASE !== 'undefined' ? API_BASE : 'https://slh-api-production.up.railway.app') + '/api/ai/chat';
  const STORAGE_KEY = 'slh_ai_chat_history';
  const MAX_HISTORY = 50;

  /* ===== i18n ===== */

  const AI_STRINGS = {
    he: {
      title: 'עוזר AI של SLH',
      placeholder: 'שאלו אותי כל דבר...',
      greeting: 'שלום! אני העוזר החכם של SLH Spark. איך אוכל לעזור?',
      send: 'שלח',
      thinking: 'חושב...',
      error: 'אירעה שגיאה, נסו שוב.',
      quick_market: 'מה המצב בשוק?',
      quick_coin: 'המלץ לי על מטבע',
      quick_explain: 'הסבר על SLH',
      powered: 'מופעל על ידי SLH AI',
      clear: 'נקה שיחה'
    },
    en: {
      title: 'SLH AI Assistant',
      placeholder: 'Ask me anything...',
      greeting: 'Hello! I\'m the SLH Spark AI assistant. How can I help you?',
      send: 'Send',
      thinking: 'Thinking...',
      error: 'An error occurred, please try again.',
      quick_market: 'Market status?',
      quick_coin: 'Recommend a coin',
      quick_explain: 'Explain SLH',
      powered: 'Powered by SLH AI',
      clear: 'Clear chat'
    },
    ru: {
      title: 'AI Помощник SLH',
      placeholder: 'Спросите что угодно...',
      greeting: 'Привет! Я AI ассистент SLH Spark. Чем могу помочь?',
      send: 'Отправить',
      thinking: 'Думаю...',
      error: 'Произошла ошибка, попробуйте снова.',
      quick_market: 'Ситуация на рынке?',
      quick_coin: 'Порекомендуй монету',
      quick_explain: 'Расскажи о SLH',
      powered: 'На базе SLH AI',
      clear: 'Очистить чат'
    },
    ar: {
      title: 'مساعد SLH الذكي',
      placeholder: 'اسألني أي شيء...',
      greeting: 'مرحبا! أنا مساعد SLH Spark الذكي. كيف يمكنني مساعدتك؟',
      send: 'إرسال',
      thinking: 'جاري التفكير...',
      error: 'حدث خطأ، حاول مرة أخرى.',
      quick_market: 'ما حالة السوق؟',
      quick_coin: 'أوصني بعملة',
      quick_explain: 'اشرح لي SLH',
      powered: 'مدعوم من SLH AI',
      clear: 'مسح المحادثة'
    },
    fr: {
      title: 'Assistant IA SLH',
      placeholder: 'Posez-moi une question...',
      greeting: 'Bonjour ! Je suis l\'assistant IA de SLH Spark. Comment puis-je vous aider ?',
      send: 'Envoyer',
      thinking: 'Réflexion...',
      error: 'Une erreur est survenue, veuillez réessayer.',
      quick_market: 'État du marché ?',
      quick_coin: 'Recommander une crypto',
      quick_explain: 'Expliquer SLH',
      powered: 'Propulsé par SLH AI',
      clear: 'Effacer le chat'
    }
  };

  function _lang() {
    if (typeof getLang === 'function') return getLang();
    return localStorage.getItem('slh_lang') || 'he';
  }

  function _isRTL() {
    const lang = _lang();
    return lang === 'he' || lang === 'ar';
  }

  /* ===== OFFLINE FALLBACK KB ===== */

  const FALLBACK_KB = {
    he: {
      market: 'שוק הקריפטו דינמי. מחיר SLH: ₪444 ($121.64). עקבו אחרי המחירים בזמן אמת בעמוד המסחר שלנו. ⚠️ אין זו המלצת השקעה.',
      coin: 'SLH Token הוא הטוקן המרכזי שלנו ברשת BSC. יש גם MNH — המטבע היציב שלנו הצמוד לשקל. בנוסף יש לנו 12 טוקנים נוספים באקוסיסטם. ⚠️ אין זו המלצת השקעה.',
      explain: 'SLH Spark הוא אקוסיסטם קריפטו ישראלי עם 20+ בוטים בטלגרם, אתר מסחר, סטייקינג עם תשואה דינמית מחלוקת הכנסות, מערכת הפניות, ארנק דיגיטלי ועוד. הצטרפו אלינו!',
      staking: 'אנחנו מציעים תוכניות סטייקינג ל-30/60/90/180 ימים עם תשואה דינמית מחלוקת הכנסות של האקוסיסטם. ככל שהתקופה ארוכה יותר, החלק שלכם גדול יותר.',
      wallet: 'הארנק שלנו תומך ב-BSC ו-TON. אפשר לשלוח, לקבל, להפקיד ולעשות סטייקינג ישירות מהאתר.',
      referral: 'מערכת ההפניות שלנו מאפשרת להרוויח עמלות על כל חבר שמצטרף דרככם. יש 5 רמות ובונוסים מיוחדים.',
      default: 'אני עוזר ה-AI של SLH Spark. כרגע אני עובד במצב לא מקוון — אבל אני יכול לעזור עם שאלות בסיסיות על האקוסיסטם, סטייקינג, ארנק והפניות. נסו לשאול!'
    },
    en: {
      market: 'The crypto market is dynamic. SLH price: ₪444 ($121.64). Track real-time prices on our Trade page. ⚠️ Not financial advice.',
      coin: 'SLH Token is our main token on BSC. We also have MNH — our stablecoin pegged to ILS. Plus 12 more tokens in the ecosystem. ⚠️ Not financial advice.',
      explain: 'SLH Spark is an Israeli crypto ecosystem with 20+ Telegram bots, a trading website, Dynamic Revenue-Share staking, a referral system, digital wallet and more. Join us!',
      staking: 'We offer staking plans for 30/60/90/180 days with Dynamic Revenue-Share yield — rewards scale with ecosystem revenue. Longer lock periods mean a larger share.',
      wallet: 'Our wallet supports BSC and TON networks. You can send, receive, deposit and stake directly from the website.',
      referral: 'Our referral system lets you earn commissions on every friend who joins through your link. 5 levels with special bonuses.',
      default: 'I\'m the SLH Spark AI assistant. Currently in offline mode — but I can help with basic questions about the ecosystem, staking, wallet and referrals. Try asking!'
    },
    ru: {
      market: 'Крипторынок динамичен. Цена SLH: ₪444 ($121.64). Следите за ценами в реальном времени на странице торговли. ⚠️ Не является финансовой рекомендацией.',
      coin: 'SLH Token — наш основной токен на BSC. Также есть MNH — стейблкоин, привязанный к шекелю. Плюс 12 токенов в экосистеме. ⚠️ Не является финансовой рекомендацией.',
      explain: 'SLH Spark — израильская крипто-экосистема: 20+ ботов в Telegram, торговый сайт, стейкинг с динамической доходностью от выручки, реферальная система, цифровой кошелёк.',
      staking: 'Планы стейкинга: 30/60/90/180 дней с динамической доходностью от выручки экосистемы. Чем дольше период — тем больше ваша доля.',
      wallet: 'Наш кошелёк поддерживает BSC и TON. Отправка, получение, депозит и стейкинг — прямо с сайта.',
      referral: 'Реферальная система позволяет зарабатывать комиссию за каждого приглашённого друга. 5 уровней с бонусами.',
      default: 'Я AI помощник SLH Spark. Сейчас работаю в офлайн-режиме, но могу ответить на базовые вопросы об экосистеме.'
    },
    ar: {
      market: 'سوق الكريبتو ديناميكي. سعر SLH: ₪444 ($121.64). تابعوا الأسعار في صفحة التداول. ⚠️ ليست نصيحة استثمارية.',
      coin: 'SLH Token هو الرمز الرئيسي على شبكة BSC. لدينا أيضاً MNH المستقر. بالإضافة إلى 12 رمزاً آخر. ⚠️ ليست نصيحة استثمارية.',
      explain: 'SLH Spark هو نظام كريبتو إسرائيلي يضم 20+ بوت تيليجرام، موقع تداول، ستيكينج بعائد ديناميكي من إيرادات النظام، نظام إحالة ومحفظة رقمية.',
      default: 'أنا مساعد SLH الذكي. أعمل حالياً بدون اتصال — لكن يمكنني المساعدة بأسئلة أساسية عن النظام.'
    },
    fr: {
      market: 'Le marché crypto est dynamique. Prix SLH : ₪444 ($121.64). Suivez les prix en temps réel sur notre page Trading. ⚠️ Pas un conseil financier.',
      coin: 'SLH Token est notre jeton principal sur BSC. Nous avons aussi MNH — notre stablecoin indexé au shekel. Plus 12 autres jetons. ⚠️ Pas un conseil financier.',
      explain: 'SLH Spark est un écosystème crypto israélien : 20+ bots Telegram, site de trading, staking à rendement dynamique partagé sur les revenus, système de parrainage et portefeuille numérique.',
      default: 'Je suis l\'assistant IA de SLH Spark. En mode hors ligne — mais je peux répondre aux questions de base sur l\'écosystème.'
    }
  };

  function _fallbackReply(text) {
    const lang = _lang();
    const kb = FALLBACK_KB[lang] || FALLBACK_KB.en;
    const lower = text.toLowerCase();

    if (/market|שוק|рынок|سوق|marché|price|מחיר|цена|سعر|prix/.test(lower)) return kb.market || kb.default;
    if (/coin|token|מטבע|טוקן|монет|токен|عملة|رمز|crypto|jeton/.test(lower)) return kb.coin || kb.default;
    if (/slh|spark|explain|הסבר|מה זה|что такое|اشرح|expliqu/.test(lower)) return kb.explain || kb.default;
    if (/stak|סטייק|стейк|ستيك|yield|תשואה|доход|عائد|rendement/.test(lower)) return kb.staking || kb.default;
    if (/wallet|ארנק|кошел|محفظ|portefeuille|send|שלח|отправ|ارسل|envoy/.test(lower)) return kb.wallet || kb.default;
    if (/refer|הפני|הזמנ|реферал|إحال|parrain|invite|friend|חבר|друг|صديق|ami/.test(lower)) return kb.referral || kb.default;

    return kb.default;
  }

  function _t(key) {
    const lang = _lang();
    return (AI_STRINGS[lang] && AI_STRINGS[lang][key]) || AI_STRINGS.en[key] || key;
  }

  function _userId() {
    if (typeof getCurrentUser === 'function') {
      const u = getCurrentUser();
      if (u && u.id) return String(u.id);
    }
    let anonId = sessionStorage.getItem('slh_ai_anon_id');
    if (!anonId) {
      anonId = 'anon_' + Math.random().toString(36).slice(2, 10);
      sessionStorage.setItem('slh_ai_anon_id', anonId);
    }
    return anonId;
  }

  /* ===== CSS INJECTION ===== */

  function injectStyles() {
    if (document.getElementById('slh-ai-styles')) return;
    const style = document.createElement('style');
    style.id = 'slh-ai-styles';
    style.textContent = `
/* ── AI Chat Widget ─────────────────────────────── */

.slh-ai-fab {
  position: fixed;
  z-index: 9999;
  bottom: 24px;
  width: 58px;
  height: 58px;
  border-radius: 50%;
  border: 2px solid var(--accent, #6c5ce7);
  background: linear-gradient(135deg, var(--accent, #6c5ce7), var(--accent2, #a29bfe));
  color: #fff;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 20px rgba(108, 92, 231, .45);
  transition: transform var(--transition, .25s), box-shadow var(--transition, .25s);
}
[dir="rtl"] .slh-ai-fab,
.slh-ai-fab.rtl { left: 24px; right: auto; }
[dir="ltr"] .slh-ai-fab,
.slh-ai-fab.ltr { right: 24px; left: auto; }
.slh-ai-fab:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 28px rgba(108, 92, 231, .6);
}
.slh-ai-fab.open {
  transform: rotate(45deg) scale(1);
}

/* Panel */
.slh-ai-panel {
  position: fixed;
  z-index: 9998;
  bottom: 94px;
  width: 380px;
  max-width: calc(100vw - 32px);
  height: 520px;
  max-height: calc(100vh - 130px);
  border-radius: var(--radius, 12px);
  background: var(--bg2, #0a0a1a);
  border: 1px solid var(--border, #1e1e3a);
  box-shadow: var(--shadow-lg, 0 8px 48px rgba(0,0,0,.6));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  opacity: 0;
  transform: translateY(20px) scale(.95);
  pointer-events: none;
  transition: opacity .3s ease, transform .3s ease;
}
[dir="rtl"] .slh-ai-panel,
.slh-ai-panel.rtl { left: 24px; right: auto; }
[dir="ltr"] .slh-ai-panel,
.slh-ai-panel.ltr { right: 24px; left: auto; }
.slh-ai-panel.visible {
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}

/* Header */
.slh-ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  background: var(--surface, #14142b);
  border-bottom: 1px solid var(--border, #1e1e3a);
  gap: 10px;
}
.slh-ai-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font, 'Inter', sans-serif);
  font-size: 15px;
  font-weight: 600;
  color: var(--text, #e8e8f0);
}
.slh-ai-header-title .slh-ai-icon {
  font-size: 18px;
  color: var(--accent2, #a29bfe);
}
.slh-ai-header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.slh-ai-header-btn {
  background: none;
  border: none;
  color: var(--text3, #6a6a88);
  font-size: 16px;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: var(--radius-xs, 4px);
  transition: color var(--transition, .25s), background var(--transition, .25s);
}
.slh-ai-header-btn:hover {
  color: var(--text, #e8e8f0);
  background: var(--surface2, #1a1a3e);
}

/* Messages Area */
.slh-ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  scrollbar-width: thin;
  scrollbar-color: var(--border2, #2a2a50) transparent;
}
.slh-ai-messages::-webkit-scrollbar { width: 5px; }
.slh-ai-messages::-webkit-scrollbar-track { background: transparent; }
.slh-ai-messages::-webkit-scrollbar-thumb { background: var(--border2, #2a2a50); border-radius: 3px; }

/* Message bubbles */
.slh-ai-msg {
  max-width: 85%;
  padding: 10px 14px;
  border-radius: var(--radius-sm, 8px);
  font-family: var(--font, 'Inter', sans-serif);
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--text, #e8e8f0);
  word-wrap: break-word;
  white-space: pre-wrap;
  animation: slhAiMsgIn .25s ease;
}
@keyframes slhAiMsgIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.slh-ai-msg.bot {
  align-self: flex-start;
  background: var(--surface, #14142b);
  border: 1px solid var(--border, #1e1e3a);
  border-start-start-radius: var(--radius-xs, 4px);
}
.slh-ai-msg.user {
  align-self: flex-end;
  background: linear-gradient(135deg, var(--accent, #6c5ce7), var(--accent2, #a29bfe));
  color: #fff;
  border-end-end-radius: var(--radius-xs, 4px);
}

/* Thinking indicator */
.slh-ai-thinking {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  align-self: flex-start;
  background: var(--surface, #14142b);
  border: 1px solid var(--border, #1e1e3a);
  border-radius: var(--radius-sm, 8px);
  border-start-start-radius: var(--radius-xs, 4px);
  font-family: var(--font, 'Inter', sans-serif);
  font-size: 13px;
  color: var(--text3, #6a6a88);
}
.slh-ai-thinking-dots {
  display: flex;
  gap: 4px;
}
.slh-ai-thinking-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent, #6c5ce7);
  animation: slhAiDot 1.4s infinite ease-in-out both;
}
.slh-ai-thinking-dots span:nth-child(2) { animation-delay: .2s; }
.slh-ai-thinking-dots span:nth-child(3) { animation-delay: .4s; }
@keyframes slhAiDot {
  0%, 80%, 100% { transform: scale(.4); opacity: .4; }
  40% { transform: scale(1); opacity: 1; }
}

/* Quick actions */
.slh-ai-quick-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 16px 10px;
}
.slh-ai-quick-btn {
  padding: 6px 12px;
  border-radius: 20px;
  border: 1px solid var(--border2, #2a2a50);
  background: var(--surface, #14142b);
  color: var(--accent2, #a29bfe);
  font-family: var(--font, 'Inter', sans-serif);
  font-size: 12px;
  cursor: pointer;
  transition: background var(--transition, .25s), border-color var(--transition, .25s), color var(--transition, .25s);
  white-space: nowrap;
}
.slh-ai-quick-btn:hover {
  background: var(--surface2, #1a1a3e);
  border-color: var(--accent, #6c5ce7);
  color: var(--text, #e8e8f0);
}

/* Input area */
.slh-ai-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-top: 1px solid var(--border, #1e1e3a);
  background: var(--surface, #14142b);
}
.slh-ai-input {
  flex: 1;
  background: var(--bg2, #0a0a1a);
  border: 1px solid var(--border, #1e1e3a);
  border-radius: var(--radius-sm, 8px);
  padding: 10px 14px;
  font-family: var(--font, 'Inter', sans-serif);
  font-size: 13.5px;
  color: var(--text, #e8e8f0);
  outline: none;
  transition: border-color var(--transition, .25s);
}
.slh-ai-input::placeholder { color: var(--text3, #6a6a88); }
.slh-ai-input:focus { border-color: var(--accent, #6c5ce7); }
.slh-ai-send-btn {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, var(--accent, #6c5ce7), var(--accent2, #a29bfe));
  color: #fff;
  font-size: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform var(--transition, .25s), opacity var(--transition, .25s);
  flex-shrink: 0;
}
.slh-ai-send-btn:hover { transform: scale(1.1); }
.slh-ai-send-btn:disabled { opacity: .4; cursor: default; transform: none; }

/* Footer powered-by */
.slh-ai-footer {
  text-align: center;
  padding: 6px 0;
  font-family: var(--font, 'Inter', sans-serif);
  font-size: 10px;
  color: var(--text3, #6a6a88);
  border-top: 1px solid var(--border, #1e1e3a);
  background: var(--surface, #14142b);
}

/* Pulse animation on FAB */
.slh-ai-fab::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  border: 2px solid var(--accent, #6c5ce7);
  opacity: 0;
  animation: slhAiPulse 2s infinite;
}
.slh-ai-fab.open::after { animation: none; opacity: 0; }
@keyframes slhAiPulse {
  0%   { opacity: .6; transform: scale(1); }
  100% { opacity: 0;  transform: scale(1.4); }
}

/* Mobile responsive */
@media (max-width: 480px) {
  .slh-ai-panel {
    width: calc(100vw - 16px);
    height: calc(100vh - 110px);
    bottom: 88px;
    left: 8px !important;
    right: 8px !important;
    border-radius: var(--radius-sm, 8px);
  }
  .slh-ai-fab {
    bottom: 18px;
    width: 52px;
    height: 52px;
    font-size: 22px;
  }
}
`;
    document.head.appendChild(style);
  }

  /* ===== DOM BUILDER ===== */

  let _panel, _messagesEl, _inputEl, _sendBtn, _quickWrap, _thinkingEl, _fab;
  let _isOpen = false;
  let _isSending = false;
  let _hasGreeted = false;

  function build() {
    injectStyles();
    const rtlClass = _isRTL() ? 'rtl' : 'ltr';

    // FAB button
    _fab = document.createElement('button');
    _fab.className = 'slh-ai-fab ' + rtlClass;
    _fab.setAttribute('aria-label', _t('title'));
    _fab.title = 'שיחה עם AI';
    _fab.innerHTML = '<i class="fas fa-brain"></i><span style="position:absolute;bottom:-18px;left:50%;transform:translateX(-50%);font-size:9px;white-space:nowrap;color:var(--accent,#6c5ce7);font-weight:700;text-shadow:0 1px 3px rgba(0,0,0,.8)">שיחה עם AI</span>';
    _fab.addEventListener('click', toggle);
    document.body.appendChild(_fab);

    // Panel
    _panel = document.createElement('div');
    _panel.className = 'slh-ai-panel ' + rtlClass;
    _panel.innerHTML = `
      <div class="slh-ai-header">
        <div class="slh-ai-header-title">
          <span class="slh-ai-icon"><i class="fas fa-robot"></i></span>
          <span>${_t('title')}</span>
        </div>
        <div class="slh-ai-header-actions">
          <button class="slh-ai-header-btn" title="${_t('clear')}" data-action="clear">
            <i class="fas fa-trash-alt"></i>
          </button>
          <button class="slh-ai-header-btn" title="Close" data-action="close">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      <div class="slh-ai-messages"></div>
      <div class="slh-ai-quick-wrap"></div>
      <div class="slh-ai-input-wrap">
        <input class="slh-ai-input" type="text" placeholder="${_t('placeholder')}" autocomplete="off" />
        <button class="slh-ai-send-btn" title="${_t('send')}">
          <i class="fas fa-paper-plane"></i>
        </button>
      </div>
      <div class="slh-ai-footer">${_t('powered')}</div>
    `;
    document.body.appendChild(_panel);

    // Cache elements
    _messagesEl = _panel.querySelector('.slh-ai-messages');
    _inputEl = _panel.querySelector('.slh-ai-input');
    _sendBtn = _panel.querySelector('.slh-ai-send-btn');
    _quickWrap = _panel.querySelector('.slh-ai-quick-wrap');

    // Events
    _panel.querySelector('[data-action="close"]').addEventListener('click', toggle);
    _panel.querySelector('[data-action="clear"]').addEventListener('click', clearChat);
    _sendBtn.addEventListener('click', sendMessage);
    _inputEl.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    renderQuickActions();
    restoreHistory();
  }

  /* ===== QUICK ACTIONS ===== */

  function renderQuickActions() {
    const actions = [
      { key: 'quick_market' },
      { key: 'quick_coin' },
      { key: 'quick_explain' },
      { key: 'quick_bug', label: '🐛 דווח באג', action: 'bug' },
      { key: 'quick_expert', label: '🎓 מצא מומחה', action: 'expert' }
    ];
    _quickWrap.innerHTML = actions.map(a => {
      const txt = a.label || _t(a.key);
      const dataAttr = a.action ? `data-action="${a.action}"` : `data-msg="${txt}"`;
      return `<button class="slh-ai-quick-btn" ${dataAttr}>${txt}</button>`;
    }).join('');
    _quickWrap.querySelectorAll('.slh-ai-quick-btn').forEach(btn => {
      btn.addEventListener('click', function () {
        const action = this.getAttribute('data-action');
        if (action === 'bug') {
          // Open bug-report.html with current page pre-filled
          const fromPage = encodeURIComponent(location.pathname);
          window.open('/bug-report.html?from=' + fromPage, '_blank');
          return;
        }
        if (action === 'expert') {
          window.open('/experts.html', '_blank');
          return;
        }
        const msg = this.getAttribute('data-msg');
        _inputEl.value = msg;
        sendMessage();
      });
    });
  }

  /* ===== TOGGLE ===== */

  function toggle() {
    _isOpen = !_isOpen;
    _panel.classList.toggle('visible', _isOpen);
    _fab.classList.toggle('open', _isOpen);
    _fab.innerHTML = _isOpen ? '<i class="fas fa-times"></i>' : '<i class="fas fa-brain"></i>';

    if (_isOpen) {
      _inputEl.focus();
      if (!_hasGreeted && getHistory().length === 0) {
        addBotMessage(_t('greeting'));
        _hasGreeted = true;
      }
    }
  }

  /* ===== MESSAGES ===== */

  function addMessage(text, role) {
    const div = document.createElement('div');
    div.className = 'slh-ai-msg ' + role;
    div.textContent = text;
    _messagesEl.appendChild(div);
    _messagesEl.scrollTop = _messagesEl.scrollHeight;
    saveToHistory(role, text);
  }

  function addBotMessage(text) {
    addMessage(text, 'bot');
  }

  function addUserMessage(text) {
    addMessage(text, 'user');
  }

  function showThinking() {
    _thinkingEl = document.createElement('div');
    _thinkingEl.className = 'slh-ai-thinking';
    _thinkingEl.innerHTML = `
      <div class="slh-ai-thinking-dots"><span></span><span></span><span></span></div>
      <span>${_t('thinking')}</span>
    `;
    _messagesEl.appendChild(_thinkingEl);
    _messagesEl.scrollTop = _messagesEl.scrollHeight;
  }

  function hideThinking() {
    if (_thinkingEl && _thinkingEl.parentNode) {
      _thinkingEl.remove();
      _thinkingEl = null;
    }
  }

  /* ===== SEND ===== */

  async function sendMessage() {
    const text = _inputEl.value.trim();
    if (!text || _isSending) return;

    addUserMessage(text);
    _inputEl.value = '';
    _isSending = true;
    _sendBtn.disabled = true;
    showThinking();

    try {
      const res = await fetch(AI_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          user_id: _userId(),
          lang: _lang()
        })
      });

      hideThinking();

      if (!res.ok) {
        addBotMessage(_fallbackReply(text));
        return;
      }

      const data = await res.json();
      const reply = data.reply || data.response || data.message || data.text || _t('error');
      addBotMessage(reply);
    } catch (err) {
      console.error('[SLH AI]', err);
      hideThinking();
      addBotMessage(_fallbackReply(text));
    } finally {
      _isSending = false;
      _sendBtn.disabled = false;
      _inputEl.focus();
    }
  }

  /* ===== SESSION STORAGE HISTORY ===== */

  function getHistory() {
    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]');
    } catch { return []; }
  }

  function saveToHistory(role, text) {
    const history = getHistory();
    history.push({ role, text, ts: Date.now() });
    if (history.length > MAX_HISTORY) history.splice(0, history.length - MAX_HISTORY);
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(history));
  }

  function restoreHistory() {
    const history = getHistory();
    if (!history.length) return;
    _hasGreeted = true; // skip greeting if we have history
    history.forEach(function (item) {
      const div = document.createElement('div');
      div.className = 'slh-ai-msg ' + item.role;
      div.textContent = item.text;
      _messagesEl.appendChild(div);
    });
    _messagesEl.scrollTop = _messagesEl.scrollHeight;
  }

  function clearChat() {
    sessionStorage.removeItem(STORAGE_KEY);
    _messagesEl.innerHTML = '';
    _hasGreeted = false;
    if (typeof showToast === 'function') showToast(_t('clear'));
  }

  /* ===== LANGUAGE REACTIVITY ===== */

  // Re-render text when language changes (observe html[lang] attribute)
  function watchLangChange() {
    const observer = new MutationObserver(function () {
      if (!_panel) return;
      const rtlClass = _isRTL() ? 'rtl' : 'ltr';

      // Update directional classes
      _fab.className = 'slh-ai-fab ' + rtlClass + (_isOpen ? ' open' : '');
      _panel.className = 'slh-ai-panel ' + rtlClass + (_isOpen ? ' visible' : '');

      // Update text content
      _panel.querySelector('.slh-ai-header-title span:last-child').textContent = _t('title');
      _inputEl.placeholder = _t('placeholder');
      _panel.querySelector('.slh-ai-footer').textContent = _t('powered');
      _panel.querySelector('[data-action="clear"]').title = _t('clear');
      _sendBtn.title = _t('send');
      renderQuickActions();
    });

    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['lang', 'dir'] });
  }

  /* ===== INIT ===== */

  function init() {
    // Wait for DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () { build(); watchLangChange(); });
    } else {
      build();
      watchLangChange();
    }
  }

  init();

})();
