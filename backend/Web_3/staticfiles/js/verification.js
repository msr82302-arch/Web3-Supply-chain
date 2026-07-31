/**
 * SCM platform - Client Geolocation Verification Connector
 * Location: static/js/verification.js
 */

document.addEventListener("DOMContentLoaded", () => {
    console.log("SCM Client Geolocation Connector Engine Active.");

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                // Dynamically append coordinates to the URL if not already present
                const urlParams = new URLSearchParams(window.location.search);
                if (!urlParams.has("lat") && !urlParams.has("lng")) {
                    urlParams.set("lat", lat.toFixed(7));
                    urlParams.set("lng", lng.toFixed(7));
                    window.location.search = urlParams.toString();
                }
            },
            (error) => {
                console.log("Consumer denied geolocation access or hardware timeout occurred.");
            },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    }
});