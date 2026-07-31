/**
 * SCM platform - Interactive Orders Dynamic Calculator & Line Builder
 * Location: static/js/orders.js
 */

document.addEventListener("DOMContentLoaded", () => {
    console.log("SCM Procurement Ledger Script Engine Active.");

    const itemContainer = document.getElementById("order-items-container");
    const addItemBtn = document.getElementById("add-line-item-btn");
    const grandTotalDisplay = document.getElementById("grand-total-display");

    if (addItemBtn && itemContainer) {
        addItemBtn.addEventListener("click", () => {
            const rowIndex = itemContainer.children.length;
            const newRow = document.createElement("div");
            newRow.className = "grid grid-cols-1 sm:grid-cols-4 gap-4 items-end p-4 bg-slate-950 border border-slate-900 rounded-xl animate-pulse";
            newRow.style.animationDuration = "0.5s";
            
            newRow.innerHTML = `
                <div class="sm:col-span-2">
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Select Product</label>
                    <select name="items[${rowIndex}][product]" required class="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white text-sm focus:outline-none product-select-field">
                        <option value="" disabled selected>-- Select Product --</option>
                        ${window.productOptionsHTML || ''}
                    </select>
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Quantity</label>
                    <input type="number" name="items[${rowIndex}][quantity]" min="1" required class="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white text-sm font-mono focus:outline-none qty-field" placeholder="1">
                </div>
                <div>
                    <label class="block text-xs font-bold text-slate-500 uppercase mb-1">Unit Price ($)</label>
                    <input type="number" step="0.01" name="items[${rowIndex}][unit_price]" min="0" required class="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-2 text-white text-sm font-mono focus:outline-none price-field" placeholder="0.00">
                </div>
            `;
            
            itemContainer.appendChild(newRow);
            bindCalculationListeners(newRow);
            setTimeout(() => newRow.classList.remove("animate-pulse"), 500);
        });

        // Initialize calculation listeners on any existing pre-rendered rows
        Array.from(itemContainer.children).forEach(row => bindCalculationListeners(row));
    }

    function bindCalculationListeners(row) {
        const qtyInput = row.querySelector(".qty-field");
        const priceInput = row.querySelector(".price-field");

        if (qtyInput && priceInput) {
            qtyInput.addEventListener("input", recalculateGrandTotal);
            priceInput.addEventListener("input", recalculateGrandTotal);
        }
    }

    function recalculateGrandTotal() {
        let runningTotal = 0;
        const rows = itemContainer.querySelectorAll(".grid");

        rows.forEach(row => {
            const qty = parseFloat(row.querySelector(".qty-field")?.value) || 0;
            const price = parseFloat(row.querySelector(".price-field")?.value) || 0;
            runningTotal += qty * price;
        });

        if (grandTotalDisplay) {
            grandTotalDisplay.textContent = `$${runningTotal.toFixed(2)}`;
        }
    }
});