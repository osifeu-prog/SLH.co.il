/**
 * SLH Flip Demo — Interactive Examples
 *
 * This script powers the interactive examples in demo.html
 * Shows how to use SLHFlip.flip(), SLHFlip.scramble(), and SLHFlip.applyAll()
 */

// Wait for DOM and SLHFlip to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('✨ SLH Flip Demo Started');
    console.log('Version:', window.SLHFlip.version);
    console.log('API:', Object.keys(window.SLHFlip));

    // Initialize all data-flip and data-scramble attributes
    // (This is already done by slh-flip.js on DOMContentLoaded,
    //  but we call it again for any dynamically added elements)
    window.SLHFlip.applyAll();

    console.log('✅ All animations initialized');
});

/**
 * Example: Manual flip animation
 * Triggered by button click
 */
function flipManually() {
    const element = document.getElementById('manual-flip');
    if (!element) return;

    // Flip to new text with 800ms duration
    window.SLHFlip.flip(element, 'Flipped!', 800);

    console.log('Flipped element:', element.textContent);
}

/**
 * Example: Manual scramble animation
 * Triggered by button click
 */
function scrambleManually() {
    const element = document.getElementById('manual-scramble');
    if (!element) return;

    // Scramble to new text with custom duration
    window.SLHFlip.scramble(element, 'Scrambled!', {
        duration: 1200
    });

    console.log('Scrambled element:', element.textContent);
}

/**
 * Example: Show version information
 * Triggered by button click
 */
function showVersion() {
    const version = window.SLHFlip.version;
    const display = document.getElementById('version-display');

    if (display) {
        display.textContent = 'Version: ' + version;
    }

    console.log('SLH Flip version:', version);
    alert('SLH Flip ' + version + ' is loaded and working!');
}

/**
 * Example: Load and animate dynamic content
 * Triggered by button click
 */
function loadDynamicContent() {
    const container = document.getElementById('dynamic-content');
    if (!container) return;

    // Clear existing content
    container.innerHTML = '';

    // Create new HTML with data-flip attribute
    const html = `
        <div style="text-align: center; padding: 20px; background: rgba(255, 0, 255, 0.1); border-radius: 6px;">
            <h2 data-flip="✨ Dynamically Loaded!">Loading...</h2>
            <p style="color: #888; font-size: 12px;">This content was added after page load and animated</p>
        </div>
    `;

    container.innerHTML = html;

    // Initialize animations on the new content
    window.SLHFlip.applyAll(container);

    console.log('✅ Dynamic content loaded and animated');
}

/**
 * Example: Update status with animation
 * Triggered by button click
 */
function updateStatus() {
    const statuses = ['Ready', 'Processing', 'Complete', 'Ready'];
    const display = document.getElementById('status-display');

    if (!display) return;

    // Get current state
    let currentIndex = statuses.indexOf(display.textContent);
    if (currentIndex === -1) currentIndex = 0;

    // Move to next status
    const nextIndex = (currentIndex + 1) % statuses.length;
    const nextStatus = statuses[nextIndex];

    // Animate to new status
    window.SLHFlip.scramble(display, nextStatus, {
        duration: 600
    });

    console.log('Status updated to:', nextStatus);
}

// Attach status button listener
document.addEventListener('DOMContentLoaded', function() {
    const statusButton = document.getElementById('status-button');
    if (statusButton) {
        statusButton.addEventListener('click', updateStatus);
    }
});

/**
 * Console logging helper
 * Call this in browser console to see all SLHFlip API methods
 */
window.showSLHFlipAPI = function() {
    console.log('=== SLH Flip API ===');
    console.log('Version:', window.SLHFlip.version);
    console.log('');
    console.log('Methods:');
    console.log('1. SLHFlip.flip(element, text, durationMs)');
    console.log('   Example: SLHFlip.flip(document.querySelector("h1"), "New Text", 800)');
    console.log('');
    console.log('2. SLHFlip.scramble(element, text, options)');
    console.log('   Example: SLHFlip.scramble(el, "Final", { duration: 1500 })');
    console.log('');
    console.log('3. SLHFlip.applyAll(root)');
    console.log('   Example: SLHFlip.applyAll(document.body)');
    console.log('');
    console.log('Data Attributes:');
    console.log('- data-flip="text"             → Flip on load');
    console.log('- data-flip-on-hover="text"    → Flip on hover');
    console.log('- data-scramble="text"         → Scramble on load');
    console.log('- data-flip-duration="600"     → Custom duration (ms)');
    console.log('- data-scramble-duration="1500" → Custom duration (ms)');
};

/**
 * Performance monitoring
 * Shows animation performance metrics in console
 */
window.monitorSLHFlipPerformance = function() {
    console.log('=== SLH Flip Performance Monitoring ===');

    // Check for prefers-reduced-motion
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    console.log('Prefers reduced motion:', prefersReduced);

    // Check for 3D transform support
    const test = document.createElement('div');
    const styles = test.style;
    const has3D = !!(
        styles.transform !== undefined ||
        styles.webkitTransform !== undefined
    );
    console.log('3D Transform support:', has3D);

    // List all animated elements
    const flips = document.querySelectorAll('[data-flip]').length;
    const hovers = document.querySelectorAll('[data-flip-on-hover]').length;
    const scrambles = document.querySelectorAll('[data-scramble]').length;

    console.log('Animated elements:');
    console.log('- [data-flip]:', flips);
    console.log('- [data-flip-on-hover]:', hovers);
    console.log('- [data-scramble]:', scrambles);
    console.log('- Total:', flips + hovers + scrambles);

    // Check viewport size
    console.log('Viewport:', window.innerWidth + 'x' + window.innerHeight);

    // Measure time to initialize
    const start = performance.now();
    window.SLHFlip.applyAll();
    const duration = performance.now() - start;
    console.log('Initialize time:', duration.toFixed(2) + 'ms');
};

/**
 * Auto-log helpful info on page load
 */
console.log('===========================================');
console.log('🎬 SLH Flip Demo Interactive Examples');
console.log('===========================================');
console.log('');
console.log('Try these in the browser console:');
console.log('');
console.log('• showSLHFlipAPI()');
console.log('  → Display all SLH Flip methods and data attributes');
console.log('');
console.log('• monitorSLHFlipPerformance()');
console.log('  → Show performance metrics and animation stats');
console.log('');
console.log('• flipManually()');
console.log('  → Manually trigger a flip animation');
console.log('');
console.log('• scrambleManually()');
console.log('  → Manually trigger a scramble animation');
console.log('');
console.log('• loadDynamicContent()');
console.log('  → Load and animate HTML dynamically');
console.log('');
console.log('===========================================');
