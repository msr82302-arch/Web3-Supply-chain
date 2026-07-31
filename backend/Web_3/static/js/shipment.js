/**
 * SCM platform - Logistics Telemetry & GPS Bounds Validation Engine
 * Location: static/js/shipments.js
 */

document.addEventListener("DOMContentLoaded", () => {
    console.log("SCM Logistics Telemetry Script Engine Active.");

    const telemetryForm = document.querySelector("form[action*='update']");
    
    if (telemetryForm) {
        const latitudeInput = telemetryForm.querySelector("#latitude");
        const longitudeInput = telemetryForm.querySelector("#longitude");

        telemetryForm.addEventListener("submit", (event) => {
            let isValid = true;

            // 1. Validate Latitude (Must be between -90 and 90 degrees)
            if (latitudeInput && latitudeInput.value !== "") {
                const latVal = parseFloat(latitudeInput.value);
                if (isNaN(latVal) || latVal < -90.0 || latVal > 90.0) {
                    isValid = false;
                    alert("Validation Mismatch: Latitude must be a valid decimal between -90.0000000 and 90.0000000 degrees.");
                    event.preventDefault();
                    return;
                }
            }

            // 2. Validate Longitude (Must be between -180 and 180 degrees)
            if (longitudeInput && longitudeInput.value !== "") {
                const lngVal = parseFloat(longitudeInput.value);
                if (isNaN(lngVal) || lngVal < -180.0 || lngVal > 180.0) {
                    isValid = false;
                    alert("Validation Mismatch: Longitude must be a valid decimal between -180.0000000 and 180.0000000 degrees.");
                    event.preventDefault();
                    return;
                }
            }
        });
    }

    // Interactive copy-to-clipboard handler for tracking numbers on Detail View
    const trackingCode = document.getElementById("tracking-number-badge");
    if (trackingCode) {
        trackingCode.addEventListener("click", () => {
            const rawCode = trackingCode.textContent.trim();
            navigator.clipboard.writeText(rawCode).then(() => {
                const originalText = trackingCode.textContent;
                trackingCode.textContent = "Copied Tracking Code!";
                trackingCode.style.color = "#34d399"; // Success green

                setTimeout(() => {
                    trackingCode.textContent = originalText;
                    trackingCode.style.color = "";
                }, 1000);
            });
        });
    }
});