/**
 * Hospital Pharmacy Management System (HPMS)
 * Vanilla JavaScript Application Logic (static/js/app.js)
 * VIT Chennai DBMS PAT 4 Project
 */

document.addEventListener("DOMContentLoaded", function () {
  initBillingScreen();
  initPrescriptionScreen();
  initCustomerTypeToggle();
});

/**
 * Billing Point of Sale (POS) Dynamic Behavior
 */
function initBillingScreen() {
  const itemsContainer = document.getElementById("billing-items-container");
  const addRowBtn = document.getElementById("add-billing-row-btn");
  if (!itemsContainer || !addRowBtn) return;

  const discountInput = document.getElementById("discount_pct");
  const taxInput = document.getElementById("tax_pct");

  addRowBtn.addEventListener("click", function () {
    addBillingRow();
  });

  if (discountInput) discountInput.addEventListener("input", recalculateTotals);
  if (taxInput) taxInput.addEventListener("input", recalculateTotals);

  // Initialize with at least one row if empty
  if (itemsContainer.children.length === 0) {
    addBillingRow();
  } else {
    // Attach listeners to initial rows
    attachRowListeners(itemsContainer.firstElementChild);
    recalculateTotals();
  }
}

function addBillingRow() {
  const itemsContainer = document.getElementById("billing-items-container");
  const template = document.getElementById("billing-row-template");
  if (!itemsContainer || !template) return;

  const clone = template.content.cloneNode(true);
  const rowElement = clone.querySelector(".billing-item-row");

  itemsContainer.appendChild(clone);
  attachRowListeners(rowElement);
  recalculateTotals();
}

function attachRowListeners(row) {
  if (!row) return;

  const select = row.querySelector(".medicine-select");
  const qtyInput = row.querySelector(".qty-input");
  const priceDisplay = row.querySelector(".price-display");
  const lineTotalDisplay = row.querySelector(".line-total-display");
  const stockInfo = row.querySelector(".stock-info");
  const removeBtn = row.querySelector(".remove-row-btn");

  if (select) {
    select.addEventListener("change", function () {
      const medId = this.value;
      if (!medId) {
        priceDisplay.textContent = "₹ 0.00";
        lineTotalDisplay.textContent = "₹ 0.00";
        stockInfo.textContent = "";
        row.dataset.unitPrice = "0";
        row.dataset.maxStock = "0";
        recalculateTotals();
        return;
      }

      // Fetch live medicine details from Oracle backend API
      fetch(`/billing/api/medicine/${medId}`)
        .then((response) => {
          if (!response.ok) throw new Error("Medicine details unavailable");
          return response.json();
        })
        .then((data) => {
          row.dataset.unitPrice = data.unit_price;
          row.dataset.maxStock = data.quantity;

          priceDisplay.textContent = `₹ ${data.unit_price.toFixed(2)}`;
          stockInfo.innerHTML = `Avail: <strong>${data.quantity}</strong> | Batch: ${data.batch_number}`;

          qtyInput.max = data.quantity;
          if (parseInt(qtyInput.value) > data.quantity) {
            qtyInput.value = data.quantity;
          }

          updateLineTotal(row);
          recalculateTotals();
        })
        .catch((err) => {
          console.error(err);
          stockInfo.textContent = "Error fetching drug info";
        });
    });
  }

  if (qtyInput) {
    qtyInput.addEventListener("input", function () {
      const maxStock = parseInt(row.dataset.maxStock || "0");
      let val = parseInt(this.value || "1");

      if (val < 1) {
        this.value = 1;
        val = 1;
      }
      if (maxStock > 0 && val > maxStock) {
        alert(`Maximum available stock is ${maxStock} units.`);
        this.value = maxStock;
      }

      updateLineTotal(row);
      recalculateTotals();
    });
  }

  if (removeBtn) {
    removeBtn.addEventListener("click", function () {
      const container = document.getElementById("billing-items-container");
      if (container.querySelectorAll(".billing-item-row").length > 1) {
        row.remove();
        recalculateTotals();
      } else {
        alert("At least one medicine item is required.");
      }
    });
  }
}

function updateLineTotal(row) {
  const unitPrice = parseFloat(row.dataset.unitPrice || "0");
  const qtyInput = row.querySelector(".qty-input");
  const qty = parseInt(qtyInput ? qtyInput.value : "1") || 0;
  const lineTotalDisplay = row.querySelector(".line-total-display");

  const lineTotal = unitPrice * qty;
  row.dataset.lineTotal = lineTotal;
  if (lineTotalDisplay) {
    lineTotalDisplay.textContent = `₹ ${lineTotal.toFixed(2)}`;
  }
}

function recalculateTotals() {
  const container = document.getElementById("billing-items-container");
  if (!container) return;

  const rows = container.querySelectorAll(".billing-item-row");
  let subtotal = 0;

  rows.forEach((r) => {
    const lineVal = parseFloat(r.dataset.lineTotal || "0");
    subtotal += lineVal;
  });

  const discountInput = document.getElementById("discount_pct");
  const taxInput = document.getElementById("tax_pct");

  const discPct = parseFloat(discountInput ? discountInput.value : "0") || 0;
  const taxPct = parseFloat(taxInput ? taxInput.value : "0") || 0;

  const discountAmount = subtotal * (discPct / 100);
  const taxableBase = Math.max(0, subtotal - discountAmount);
  const taxAmount = taxableBase * (taxPct / 100);
  const grandTotal = taxableBase + taxAmount;

  const subtotalElem = document.getElementById("summary-subtotal");
  const discElem = document.getElementById("summary-discount");
  const taxElem = document.getElementById("summary-tax");
  const grandTotalElem = document.getElementById("summary-grand-total");

  if (subtotalElem) subtotalElem.textContent = `₹ ${subtotal.toFixed(2)}`;
  if (discElem) discElem.textContent = `- ₹ ${discountAmount.toFixed(2)} (${discPct}%)`;
  if (taxElem) taxElem.textContent = `+ ₹ ${taxAmount.toFixed(2)} (${taxPct}%)`;
  if (grandTotalElem) grandTotalElem.textContent = `₹ ${grandTotal.toFixed(2)}`;
}

/**
 * Customer Type Toggle (Registered Patient vs Walk-in Counter)
 */
function initCustomerTypeToggle() {
  const patientRadio = document.getElementById("cust_type_patient");
  const walkinRadio = document.getElementById("cust_type_walkin");
  const patientGroup = document.getElementById("patient_select_group");
  const walkinGroup = document.getElementById("walkin_name_group");

  if (!patientRadio || !walkinRadio || !patientGroup || !walkinGroup) return;

  function updateVisibility() {
    if (patientRadio.checked) {
      patientGroup.style.display = "block";
      walkinGroup.style.display = "none";
    } else {
      patientGroup.style.display = "none";
      walkinGroup.style.display = "block";
    }
  }

  patientRadio.addEventListener("change", updateVisibility);
  walkinRadio.addEventListener("change", updateVisibility);
  updateVisibility();
}

/**
 * Dynamic Prescription Lines
 */
function initPrescriptionScreen() {
  const container = document.getElementById("prescription-items-container");
  const addBtn = document.getElementById("add-pres-row-btn");
  if (!container || !addBtn) return;

  addBtn.addEventListener("click", function () {
    const template = document.getElementById("prescription-row-template");
    if (!template) return;
    const clone = template.content.cloneNode(true);
    const row = clone.querySelector(".pres-item-row");
    container.appendChild(clone);
    attachPrescriptionRowListeners(row);
  });

  // Attach to existing
  container.querySelectorAll(".pres-item-row").forEach(attachPrescriptionRowListeners);
}

function attachPrescriptionRowListeners(row) {
  if (!row) return;
  const removeBtn = row.querySelector(".remove-pres-row-btn");
  if (removeBtn) {
    removeBtn.addEventListener("click", function () {
      const container = document.getElementById("prescription-items-container");
      if (container.querySelectorAll(".pres-item-row").length > 1) {
        row.remove();
      } else {
        alert("A prescription requires at least one medication.");
      }
    });
  }
}

/**
 * Global Safe Delete Confirmation
 */
function confirmDelete(entityName) {
  return confirm(
    `Are you sure you want to delete this ${entityName}? This action will verify referential integrity constraints in Oracle Database.`
  );
}
