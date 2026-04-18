/**
 * SLH Flip + Scramble v1.0
 * Two text animation primitives — declarative via data-attributes.
 *
 * Usage:
 *   <h1 data-flip="SLH Spark">SLH Spark</h1>
 *   <span data-scramble="ברוך הבא"></span>
 *   <button data-flip-on-hover="קנה עכשיו">קנה עכשיו</button>
 *
 * Respects prefers-reduced-motion — all animations become instant text swaps.
 * Zero dependencies, < 2kb gzipped, vanilla JS.
 *
 * Upgrade marker — pages using either effect must include:
 *   <meta name="slh-version" content="v1.0-flip">
 * so the upgrade-tracker can detect them.
 */
(function (w) {
  const REDUCED = w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const SCRAMBLE_CHARS = '!<>-_\\/[]{}—=+*^?#אבגדהוזחטיכלמנסעפצקרשת0123456789';

  // ----------- FLIP -----------
  function flipOnce(el, nextText, durationMs = 600) {
    if (!el) return;
    if (REDUCED) { el.textContent = nextText; return; }
    el.style.display = 'inline-block';
    el.style.transition = `transform ${durationMs}ms cubic-bezier(.4,0,.2,1)`;
    el.style.transformStyle = 'preserve-3d';
    el.style.transform = 'rotateY(90deg)';
    setTimeout(() => {
      el.textContent = nextText;
      el.style.transform = 'rotateY(0deg)';
    }, durationMs / 2);
  }

  function initFlipOnLoad(root) {
    const nodes = (root || document).querySelectorAll('[data-flip]:not([data-flip-applied])');
    nodes.forEach(el => {
      el.setAttribute('data-flip-applied', 'true');
      const target = el.dataset.flip;
      if (!target) return;
      const original = el.textContent.trim();
      if (original !== target) {
        // If attribute differs from content, animate to the attribute value
        flipOnce(el, target);
      } else {
        // Self-identical — flip once as a visual "loaded" cue
        el.style.display = 'inline-block';
        el.style.animation = 'slh-flip-in 0.8s ease';
      }
    });
  }

  function initFlipOnHover(root) {
    const nodes = (root || document).querySelectorAll('[data-flip-on-hover]:not([data-flip-hover-applied])');
    nodes.forEach(el => {
      el.setAttribute('data-flip-hover-applied', 'true');
      const original = el.textContent;
      const alt = el.dataset.flipOnHover;
      el.addEventListener('mouseenter', () => flipOnce(el, alt, 400));
      el.addEventListener('mouseleave', () => flipOnce(el, original, 400));
    });
  }

  // ----------- SCRAMBLE -----------
  function scrambleTo(el, finalText, opts = {}) {
    if (!el) return;
    if (REDUCED) { el.textContent = finalText; return; }
    const duration = opts.duration || 1500;
    const fps = 30;
    const totalFrames = Math.floor(duration / (1000 / fps));
    const len = finalText.length;
    let frame = 0;

    const queue = [];
    for (let i = 0; i < len; i++) {
      queue.push({
        from: SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)],
        to: finalText[i],
        startFrame: Math.floor((i / len) * totalFrames * 0.7),
        endFrame: Math.floor((i / len) * totalFrames * 0.7) + Math.floor(totalFrames * 0.3),
      });
    }

    function step() {
      let output = '';
      let complete = 0;
      for (let i = 0; i < queue.length; i++) {
        const q = queue[i];
        if (frame >= q.endFrame) { output += q.to; complete++; }
        else if (frame >= q.startFrame) {
          output += SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
        } else { output += q.from; }
      }
      el.textContent = output;
      if (complete === queue.length) return;
      frame++;
      setTimeout(step, 1000 / fps);
    }
    step();
  }

  function initScrambleOnLoad(root) {
    const nodes = (root || document).querySelectorAll('[data-scramble]:not([data-scramble-applied])');
    nodes.forEach(el => {
      el.setAttribute('data-scramble-applied', 'true');
      const target = el.dataset.scramble || el.textContent.trim();
      if (target) scrambleTo(el, target);
    });
  }

  // ----------- INJECT CSS -----------
  function injectStyles() {
    if (document.getElementById('slh-flip-styles')) return;
    const css = `
      @keyframes slh-flip-in {
        0% { transform: rotateY(90deg); opacity: 0; }
        50% { transform: rotateY(0deg); opacity: 1; }
        100% { transform: rotateY(0deg); opacity: 1; }
      }
      [data-flip], [data-flip-on-hover] {
        display: inline-block;
        transform-origin: center;
        perspective: 1000px;
      }
      [data-scramble] {
        font-variant-numeric: tabular-nums;
        letter-spacing: 0.02em;
      }
      @media (prefers-reduced-motion: reduce) {
        [data-flip], [data-flip-on-hover] { animation: none !important; transition: none !important; }
      }
    `;
    const style = document.createElement('style');
    style.id = 'slh-flip-styles';
    style.textContent = css;
    document.head.appendChild(style);
  }

  // ----------- PUBLIC API -----------
  w.SLHFlip = {
    flip: flipOnce,
    scramble: scrambleTo,
    applyAll: (root) => { initFlipOnLoad(root); initFlipOnHover(root); initScrambleOnLoad(root); },
    version: 'v1.0-flip',
  };

  // ----------- AUTO-INIT -----------
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { injectStyles(); w.SLHFlip.applyAll(); });
  } else {
    injectStyles();
    w.SLHFlip.applyAll();
  }
})(window);
