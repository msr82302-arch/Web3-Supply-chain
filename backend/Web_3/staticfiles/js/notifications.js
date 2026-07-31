/**
 * SCM platform - Asynchronous Notifications Interactivity Engine
 * Location: static/js/notifications.js
 */

document.addEventListener("DOMContentLoaded", () => {
    console.log("SCM Notifications Interactivity Engine Active.");

    const markAllBtn = document.getElementById("mark-all-read-btn");
    if (markAllBtn) {
        markAllBtn.addEventListener("click", async (e) => {
            e.preventDefault();
            const verifyUrl = markAllBtn.getAttribute("data-url");
            const csrfToken = markAllBtn.getAttribute("data-csrf");

            try {
                const response = await fetch(verifyUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    }
                });
                const data = await response.json();
                if (data.success) {
                    // Instantly update UI indicators
                    const unreadBadges = document.querySelectorAll(".border-l-4");
                    unreadBadges.forEach(badge => {
                        badge.classList.remove("border-l-4", "border-l-sky-500", "bg-sky-50/10", "dark:bg-sky-950/5");
                    });
                    const counter = document.getElementById("unread-counter-badge");
                    if (counter) counter.remove();
                    alert(data.message);
                }
            } catch (err) {
                console.error("Failed to mark all alerts as read asynchronously: ", err);
            }
        });
    }
});