# SLH Flip — Integration Guide

Complete step-by-step guide to integrate SLH Flip into your website or application.

---

## Table of Contents

1. [For Website Pages](#for-website-pages)
2. [For Dynamic Content](#for-dynamic-content)
3. [Customization](#customization)
4. [Interactive Elements](#interactive-elements)
5. [Advanced Patterns](#advanced-patterns)
6. [Troubleshooting](#troubleshooting)

---

## For Website Pages

### Step 1: Add Version Meta Tag

Add this in the `<head>` section. This tells the upgrade tracker which primitive version you're using:

```html
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="slh-version" content="v1.0-flip">
    <!-- ... other meta tags ... -->
</head>
```

### Step 2: Add Script Tag

Add this before `</body>` or in `<head>` with `defer` attribute:

```html
<!-- Recommended: in <head> with defer -->
<script src="https://slh-nft.com/js/slh-flip.js" defer></script>

<!-- OR: before </body> without defer -->
<body>
    <!-- ... content ... -->
    <script src="https://slh-nft.com/js/slh-flip.js"></script>
</body>
```

**Best Practice:** Use `defer` in `<head>` for optimal performance.

### Step 3: Use Data Attributes

Add animations to your HTML elements:

```html
<!-- Flip on load -->
<h1 data-flip="Welcome to SLH">Welcome</h1>

<!-- Scramble on load -->
<p data-scramble="Building the Future">Building the Future</p>

<!-- Flip on hover -->
<button data-flip-on-hover="Click Here!">Click Here!</button>
```

### Step 4: Test

1. Open your page in a modern browser
2. Check browser console (F12 → Console tab)
3. Verify no JavaScript errors
4. Confirm animations play on page load
5. Test hover interactions if using `data-flip-on-hover`

### Minimal Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="slh-version" content="v1.0-flip">
    <title>SLH Flip Test</title>
    <script src="https://slh-nft.com/js/slh-flip.js" defer></script>
</head>
<body>
    <h1 data-flip="SLH SPARK">SLH SPARK</h1>
    <p data-scramble="Welcome">Welcome</p>
</body>
</html>
```

---

## For Dynamic Content

If you're loading content dynamically (AJAX, fetch, Fetch API, etc.), manually initialize animations:

### Pattern 1: After Fetch

```javascript
fetch('/api/content')
    .then(res => res.json())
    .then(data => {
        // Insert HTML
        document.getElementById('content').innerHTML = data.html;
        
        // Initialize animations
        SLHFlip.applyAll(document.getElementById('content'));
    });
```

### Pattern 2: After DOM Insertion

```javascript
// Create element
const container = document.createElement('div');
container.innerHTML = `
    <h2 data-flip="New Section">New Section</h2>
    <p data-scramble="Loading...">Loading...</p>
`;

// Insert into DOM
document.body.appendChild(container);

// Initialize animations
SLHFlip.applyAll(container);
```

### Pattern 3: Single Element Update

```javascript
// Update a single element
const element = document.querySelector('.status');
element.textContent = 'Processing...';

// Animate it
SLHFlip.scramble(element, 'Complete!', { duration: 800 });
```

---

## Customization

### Custom Flip Duration

Control how long the flip animation takes (in milliseconds):

```html
<!-- Fast flip (300ms) -->
<h1 data-flip="Quick" data-flip-duration="300">Quick</h1>

<!-- Slow flip (1500ms) -->
<h1 data-flip="Slow" data-flip-duration="1500">Slow</h1>

<!-- Default (600ms) -->
<h1 data-flip="Normal" data-flip-duration="600">Normal</h1>
```

### Custom Scramble Duration

Control scramble animation speed:

```html
<!-- Fast scramble (500ms) -->
<p data-scramble="Quick" data-scramble-duration="500">Quick</p>

<!-- Slow scramble (3000ms) -->
<p data-scramble="Slow" data-scramble-duration="3000">Slow</p>

<!-- Default (1500ms) -->
<p data-scramble="Normal" data-scramble-duration="1500">Normal</p>
```

### CSS Variables

Customize with CSS custom properties:

```css
:root {
    /* Flip duration */
    --slh-flip-duration: 1000ms;
    
    /* Scramble duration */
    --slh-scramble-duration: 2000ms;
    
    /* Animation color */
    --slh-flip-color: #00ffff;
    
    /* Text effects */
    --slh-text-shadow: 0 0 10px rgba(0, 255, 255, 0.5);
}

/* Apply to specific elements */
h1[data-flip] {
    color: var(--slh-flip-color);
    text-shadow: var(--slh-text-shadow);
}
```

### Custom Styling

Style animated elements directly:

```css
/* Style flip elements */
h1[data-flip] {
    font-size: 48px;
    color: #00ffff;
    text-shadow: 0 0 20px #00ffff;
    transform-origin: center;
}

/* Style on hover */
button[data-flip-on-hover]:hover {
    background-color: #00cccc;
    cursor: pointer;
}

/* Style scramble elements */
p[data-scramble] {
    font-family: 'Courier New', monospace;
    letter-spacing: 0.02em;
    color: #00ff00;
}
```

---

## Interactive Elements

### Buttons with Flip on Hover

Show action text on hover:

```html
<button data-flip-on-hover="START">START</button>

<style>
    button {
        padding: 10px 20px;
        background: #00ffff;
        color: #000;
        border: none;
        cursor: pointer;
        font-weight: bold;
    }
    
    button:hover {
        background: #00cccc;
    }
</style>
```

**Behavior:** Hover → flips to "START" → leave → flips back to original text

### Status Updates

Show loading/completion states with scramble:

```html
<div id="status">
    <p data-scramble="Initializing">Initializing</p>
</div>

<script>
    async function loadData() {
        // Show loading
        const status = document.querySelector('#status p');
        
        try {
            const res = await fetch('/api/data');
            const data = await res.json();
            
            // Success - update and animate
            SLHFlip.scramble(status, 'Ready!', { duration: 800 });
        } catch (error) {
            // Error - update with error state
            SLHFlip.scramble(status, 'Error loading', { duration: 600 });
        }
    }
    
    loadData();
</script>
```

### Menu Items

Reveal submenu text on hover:

```html
<nav>
    <a href="/home" data-flip-on-hover="Home">Home</a>
    <a href="/about" data-flip-on-hover="About">About</a>
    <a href="/contact" data-flip-on-hover="Contact">Contact</a>
</nav>

<style>
    a[data-flip-on-hover] {
        padding: 10px;
        display: inline-block;
        transition: background-color 0.2s;
    }
    
    a[data-flip-on-hover]:hover {
        background-color: rgba(0, 255, 255, 0.1);
    }
</style>
```

---

## Advanced Patterns

### Sequential Animations

Chain flip and scramble animations:

```javascript
const element = document.querySelector('h1');

// Step 1: Flip
SLHFlip.flip(element, 'Step 2', 600);

// Step 2: After flip, scramble
setTimeout(() => {
    SLHFlip.scramble(element, 'Complete!', { duration: 1000 });
}, 600); // Match flip duration
```

### Conditional Animations

Only animate under certain conditions:

```javascript
const element = document.querySelector('.hero h1');

// Only animate on desktop
if (window.innerWidth > 768) {
    SLHFlip.flip(element, 'Welcome', 800);
}

// Only animate if not reduced motion
const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!prefersReduced) {
    SLHFlip.flip(element, 'Welcome', 800);
}
```

### Responsive Text Updates

Show different text per breakpoint:

```html
<h1 data-flip="SLH Ecosystem" class="full">SLH Ecosystem</h1>
<h1 data-flip="SLH" class="short">SLH</h1>

<style>
    h1.full { display: block; }
    h1.short { display: none; }
    
    @media (max-width: 600px) {
        h1.full { display: none; }
        h1.short { display: block; }
    }
</style>
```

### Intersection Observer (Animate on Scroll)

Trigger animations when element enters viewport:

```javascript
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const el = entry.target;
            const text = el.dataset.flip;
            
            // Animate when visible
            SLHFlip.flip(el, text, 600);
            
            // Stop observing (animate only once)
            observer.unobserve(el);
        }
    });
});

// Observe all flip elements
document.querySelectorAll('[data-flip]').forEach(el => {
    observer.observe(el);
});
```

### Real-time Status Display

Update with live data:

```html
<p id="api-status" data-scramble="Connecting...">Connecting...</p>

<script>
    async function pollStatus() {
        try {
            const res = await fetch('/api/health');
            const status = res.ok ? 'Connected' : 'Error';
            
            const el = document.getElementById('api-status');
            SLHFlip.scramble(el, status, { duration: 400 });
        } catch {
            const el = document.getElementById('api-status');
            SLHFlip.scramble(el, 'Disconnected', { duration: 400 });
        }
    }
    
    // Poll every 5 seconds
    setInterval(pollStatus, 5000);
    pollStatus(); // First call immediately
</script>
```

---

## Troubleshooting

### Animation doesn't play

**Problem:** Added data-flip but text doesn't animate.

**Solution 1:** Check script loaded
```javascript
// In browser console:
console.log(window.SLHFlip);
// Should output: { flip: ƒ, scramble: ƒ, applyAll: ƒ, version: "v1.0-flip" }
```

**Solution 2:** Check data-attribute spelling
```html
<!-- Correct -->
<h1 data-flip="Text">Text</h1>

<!-- Wrong -->
<h1 data-flip"Text">Text</h1>  <!-- Missing = -->
<h1 data-flipp="Text">Text</h1>  <!-- Typo: flipp -->
<h1 flip="Text">Text</h1>  <!-- Missing data- -->
```

**Solution 3:** Check browser console for errors
```
Open DevTools → Console tab
Look for red error messages
```

**Solution 4:** Check `prefers-reduced-motion`
```javascript
// In console:
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
console.log('Reduced motion enabled:', reduced);
// If true, animations are disabled (OS-level accessibility setting)
```

### Animation is jerky

**Problem:** Animation stutters or drops frames.

**Solution 1:** Close other browser tabs and applications

**Solution 2:** Disable browser extensions (some interfere with animations)
- Open in Incognito mode to test

**Solution 3:** Check browser GPU acceleration
```javascript
// In console:
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
const gpu = !!ctx;
console.log('GPU support:', gpu);
```

**Solution 4:** Reduce animation duration
```html
<!-- From 1500ms to 800ms -->
<p data-scramble="Text" data-scramble-duration="800">Text</p>
```

### Mobile animation not working

**Problem:** Works on desktop but not on mobile.

**Solution 1:** Check iOS Safari version (needs 14+)
```javascript
// In console:
console.log(window.navigator.userAgent);
```

**Solution 2:** Check viewport meta tag
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

**Solution 3:** Test 3D transform support
```javascript
// In console:
const test = document.createElement('div');
const styles = test.style;
const support = !!(
    styles.transform !== undefined ||
    styles.webkitTransform !== undefined
);
console.log('3D Transform support:', support);
```

### Text shows both old and new briefly

**Problem:** See "Original" then "New Text" briefly.

**This is expected** when `data-flip` value differs from element content. The script:
1. Starts rotation animation
2. Swaps text at mid-flip (90°)
3. Completes rotation

The brief double-text is the transition.

### Performance issues with many animations

**Problem:** Page slows down with 20+ animated elements.

**Solution 1:** Reduce duration of animations
```html
<!-- From 1500ms to 800ms -->
<p data-scramble="Text" data-scramble-duration="800">Text</p>
```

**Solution 2:** Stagger animations with delay
```javascript
const elements = document.querySelectorAll('[data-flip]');
elements.forEach((el, index) => {
    setTimeout(() => {
        SLHFlip.flip(el, el.dataset.flip, 600);
    }, index * 100); // 100ms stagger between each
});
```

**Solution 3:** Only animate on desktop
```javascript
if (window.innerWidth > 768) {
    SLHFlip.applyAll();
}
```

### Script not loading from CDN

**Problem:** 404 error when loading from slh-nft.com

**Solution 1:** Check URL is correct
```html
<!-- Correct -->
<script src="https://slh-nft.com/js/slh-flip.js" defer></script>

<!-- Check domain is accessible -->
https://slh-nft.com
```

**Solution 2:** Use local copy
```html
<!-- Copy slh-flip.js to your project -->
<script src="./js/slh-flip.js" defer></script>
```

**Solution 3:** Check CORS if loading cross-origin
```
Server must set: Access-Control-Allow-Origin: *
```

---

## Best Practices

1. **Always use `defer` attribute** on script tags
2. **Test `prefers-reduced-motion`** during development
3. **Use semantic HTML** with role and aria attributes
4. **Provide fallback text** for accessibility
5. **Test on real devices** (not just desktop browser)
6. **Keep animations short** (< 1000ms for better UX)
7. **Document animated elements** with comments
8. **Monitor performance** with browser DevTools

---

## Support

For issues or questions:
- Check [README.md](./README.md) for detailed documentation
- See [CHANGELOG.md](./CHANGELOG.md) for version history
- Visit [github.com/osifeu-prog/slh-genesis](https://github.com/osifeu-prog/slh-genesis)
- Email support@slh-nft.com

Last Updated: 2026-04-18
