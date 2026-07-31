/**
 * SCM platform - Platform Governance & Analytics Script Engine
 * Location: static/js/analytics.js
 */

document.addEventListener("DOMContentLoaded", () => {
    console.log("SCM Analytics Script Engine Active.");

    // Highlight high-accuracy anomaly scores on load
    const confidenceMeters = document.querySelectorAll(".confidence-accuracy-meter");
    confidenceMeters.forEach(meter => {
        const value = parseFloat(meter.textContent.trim());
        if (value >= 85.0) {
            meter.classList.add("score-range-high");
        } else if (value >= 60.0) {
            meter.classList.add("score-range-alert");
        }
    });
});