/**
 * SCM platform - Client-Side Validation, Security & Clipboard Copy Engine
 * Location: static/js/account.js
 */

document.addEventListener("DOMContentLoaded", () => {
    console.log("SCM Accounts & Companies Management Script Engine Active.");

    // --- Part 1: Anti-Double Submission & Form Validation ---
    const criticalForms = document.querySelectorAll("form");
    
    criticalForms.forEach(form => {
        const passwordInput = form.querySelector("input[type='password']");
        const emailInput = form.querySelector("input[type='email']");

        form.addEventListener("submit", (event) => {
            let isValid = true;

            // Client-side Email Format Validation
            if (emailInput) {
                const emailVal = emailInput.value.trim();
                const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
                if (!emailPattern.test(emailVal)) {
                    isValid = false;
                    alert("Please enter a valid corporate email format.");
                    event.preventDefault();
                    return;
                }
            }

            // Client-side Password Length Check
            if (passwordInput) {
                const passwordVal = passwordInput.value;
                if (passwordVal.length < 8) {
                    isValid = false;
                    alert("Your security passphrase must contain at least 8 characters.");
                    event.preventDefault();
                    return;
                }
            }

            // Double-Submission Protection Guard (Fires only if form passes validation)
            if (isValid) {
                const submitBtn = form.querySelector("button[type='submit']");
                if (submitBtn) {
                    const originalHTML = submitBtn.innerHTML;
                    submitBtn.disabled = true;
                    submitBtn.style.opacity = "0.75";
                    submitBtn.style.cursor = "not-allowed";
                    
                    submitBtn.innerHTML = `
                        <svg class="animate-spin h-5 w-5 text-white inline-block mr-2" fill="none" viewBox="0 0 24 24" style="animation: spin 1s linear infinite; width: 1.25rem; height: 1.25rem; display: inline-block; vertical-align: middle;">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" style="opacity: 0.25;"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" style="opacity: 0.75;"></circle>
                        </svg> Validating Node Identity...`;
                    
                    // Fallback reset
                    setTimeout(() => {
                        if (submitBtn.disabled) {
                            submitBtn.disabled = false;
                            submitBtn.style.opacity = "1";
                            submitBtn.style.cursor = "pointer";
                            submitBtn.innerHTML = originalHTML;
                        }
                    }, 10000);
                }
            }
        });
    });

    // --- Part 2: Cryptographic UUID Hash Truncator & Copy Engine ---
    const cryptoHashes = document.querySelectorAll('[data-crypto-truncate="true"]');
    cryptoHashes.forEach(element => {
        const cleanHash = element.textContent.trim();
        if (cleanHash.length > 12) {
            // Truncate the key visually (e.g., "0ea5e9...f1a2")
            element.textContent = `${cleanHash.substring(0, 6)}...${cleanHash.substring(cleanHash.length - 4)}`;
            element.title = "Click to clone raw key value to clipboard";
            element.classList.add('cursor-pointer', 'hover:text-sky-400', 'transition-colors');
            
            element.addEventListener('click', (e) => {
                e.preventDefault();
                navigator.clipboard.writeText(cleanHash).then(() => {
                    const originalText = element.textContent;
                    element.textContent = "Copied Key!";
                    element.style.color = "#34d399"; // Change color to emerald green temporarily
                    
                    setTimeout(() => {
                        element.textContent = originalText;
                        element.style.color = "";
                    }, 1000);
                }).catch(err => {
                    console.error('Failed to copy text: ', err);
                });
            });
        }
    });

    // Add inline keyframe spin styles dynamically if missing
    if (!document.getElementById("accounts-animation-keyframes")) {
        const styleSheet = document.createElement("style");
        styleSheet.id = "accounts-animation-keyframes";
        styleSheet.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(styleSheet);
    }
});