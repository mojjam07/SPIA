import { StorageManager } from "./storage.js";
import { ReportManager } from "./reports.js";

const storage = new StorageManager();
const reports = new ReportManager();

// Chart configurations
const chartConfigs = {
  topProducts: {
    type: "bar",
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: true,
          text: "Top Selling Products",
        },
      },
    },
  },
  salesTrend: {
    type: "line",
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: true,
          text: "Sales Trends",
        },
      },
    },
  },
  inventory: {
    type: "pie",
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: true,
          text: "Inventory Levels",
        },
      },
    },
  },
  revenue: {
    type: "doughnut",
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "top",
        },
        title: {
          display: true,
          text: "Revenue Breakdown",
        },
      },
    },
  },
};

// Variables to store Chart instances
let topProductsChartInstance = null;
let salesTrendChartInstance = null;
let inventoryChartInstance = null;
let revenueChartInstance = null;

// Initialize the application
document.addEventListener("DOMContentLoaded", () => {
  refreshInventoryTable();
  refreshSaleItems();
  setupEventListeners();
  reports.updateCharts();

  const printButton = document.getElementById("printReceiptButton");
  if (printButton) {
    printButton.addEventListener("click", () => {
      window.printReceipt();
    });
  }
});

function setupEventListeners() {
  const addItemForm = document.getElementById("add-item-form");
  if (addItemForm) {
    addItemForm.addEventListener("submit", handleAddItem);
  }
  const saleForm = document.getElementById("sale-form");
  if (saleForm) {
    saleForm.addEventListener("submit", handleAddToCart);
  }
  const completeSaleBtn = document.getElementById("complete-sale-btn");
  if (completeSaleBtn) {
    completeSaleBtn.addEventListener("click", () => {
      window.completeSale();
    });
  }
}

async function handleAddItem(e) {
  e.preventDefault();
  try {
    const nameInput = document.getElementById("item-name");
    const priceInput = document.getElementById("item-price");
    const quantityInput = document.getElementById("item-quantity");
    const sizeInput = document.getElementById("item-size");
    const imageInput = document.getElementById("item-image");

    if (
      !nameInput ||
      !priceInput ||
      !quantityInput ||
      !sizeInput ||
      !imageInput
    ) {
      throw new Error("Inventory form elements not found on this page.");
    }

    const name = nameInput.value.trim();
    const price = parseFloat(priceInput.value);
    const quantity = parseInt(quantityInput.value);
    const size = sizeInput.value.trim();

    validateItemInput(name, price, quantity, size);

    let image = "";
    if (imageInput.files && imageInput.files[0]) {
      image = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (event) => resolve(event.target.result);
        reader.onerror = (error) => reject(error);
        reader.readAsDataURL(imageInput.files[0]);
      });
    }

    storage.addItem({ name, price, quantity, size, image });
    refreshInventoryTable();
    refreshSaleItems();
    e.target.reset();
  } catch (error) {
    alert(error.message);
  }
}

function validateItemInput(name, price, quantity, size) {
  if (!name || typeof name !== "string" || name === "") {
    throw new Error("Item name is required and must be a valid string.");
  }
  if (isNaN(price) || price <= 0) {
    throw new Error("Price must be a positive number.");
  }
  if (isNaN(quantity) || quantity <= 0 || !Number.isInteger(quantity)) {
    throw new Error("Quantity must be a positive integer.");
  }
  if (!size || typeof size !== "string" || size === "") {
    throw new Error("Size is required and must be a valid string.");
  }
}

function validateSaleInput(itemName, quantity, availableQuantity) {
  if (!itemName) {
    throw new Error("Please select an item.");
  }
  if (isNaN(quantity) || quantity <= 0 || !Number.isInteger(quantity)) {
    throw new Error("Quantity must be a positive integer.");
  }
  if (quantity > availableQuantity) {
    throw new Error("Insufficient stock for the selected item.");
  }
}

function refreshInventoryTable() {
  const items = storage.getItems();
  const container = document.getElementById("inventory-cards");
  container.innerHTML = "";

  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "card inventory-card m-2 p-3";

    card.innerHTML = `
      <div class="inventory-card">
        <img
          src="${item.image || ''}"
          alt="${item.name}"
          style="max-height: 150px; object-fit: contain; width: 100%; margin-bottom: 1rem; border-radius: 8px;"
        />
        <h5><strong>${item.name}</strong></h5>
        <p><strong>Size:</strong> ${item.size || "N/A"}</p>
        <p><strong>Price:</strong> ₦${item.price.toFixed(2)}</p>
        <p><strong>Quantity:</strong> ${item.quantity}</p>
        <div style="margin-top: 1rem; display: flex; flex-direction: row; justify-content: space-between; align-items: center;">
          <button
            class="btn-primary"
            style="margin-right: 0.5rem; padding: 0.5rem 1rem;"
            onclick="openUpdateModal('${item.name}', '${item.size}', ${item.quantity}, ${item.price})"
          >
            <i class="fas fa-edit"></i> Edit
          </button>
          <button
            class="btn btn-danger"
            style="padding: 0.5rem 1rem; background: #e53e3e; border: none; border-radius: 8px; color: white;"
            onclick="deleteItem('${item.name}', '${item.size}')"
          >
            <i class="fas fa-trash"></i> Delete
          </button>
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

window.openUpdateModal = function (name, size, quantity, price) {
  const updateModal = new bootstrap.Modal(
    document.getElementById("updateItemModal")
  );
  document.getElementById("update-item-name").value = name;
  document.getElementById("update-item-size").value = size;
  document.getElementById("update-item-quantity").value = quantity;
  document.getElementById("update-item-price").value = price.toFixed(2);
  updateModal.show();
};

document
  .getElementById("update-item-form")
  .addEventListener("submit", function (e) {
    e.preventDefault();
    const name = document.getElementById("update-item-name").value;
    const size = document.getElementById("update-item-size").value;
    const quantity = parseInt(
      document.getElementById("update-item-quantity").value
    );
    const price = parseFloat(
      document.getElementById("update-item-price").value
    );

    if (isNaN(quantity) || quantity < 0) {
      alert("Quantity must be a non-negative integer.");
      return;
    }
    if (isNaN(price) || price < 0) {
      alert("Price must be a non-negative number.");
      return;
    }

    const items = storage.getItems();
    const item = items.find((i) => i.name === name && i.size === size);
    if (item) {
      item.quantity = quantity;
      item.price = price;
      localStorage.setItem("inventory", JSON.stringify(items));
      refreshInventoryTable();
      refreshSaleItems();
      const updateModal = bootstrap.Modal.getInstance(
        document.getElementById("updateItemModal")
      );
      updateModal.hide();
    } else {
      alert("Item not found.");
    }
  });

function refreshSaleItems() {
  const select = document.getElementById("sale-item");
  const items = storage.getItems();
  select.innerHTML = '<option value="">Select an item...</option>';

  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.name + "|" + item.size; // include size in value for uniqueness
    option.textContent = `${item.name} (Size: ${
      item.size || "N/A"
    }) - N${item.price.toFixed(2)}`;
    select.appendChild(option);
  });
}

let currentCart = [];

function handleAddToCart(e) {
  e.preventDefault();
  try {
    const itemValue = document.getElementById("sale-item").value;
    if (!itemValue) throw new Error("Please select an item.");
    const [itemName, itemSize] = itemValue.split("|");
    const quantity = parseInt(document.getElementById("sale-quantity").value);
    // Removed customerName input reference as it is now prompted on completeSale
    const item = storage
      .getItems()
      .find((i) => i.name === itemName && i.size === itemSize);

    if (!item) {
      throw new Error("Selected item not found in inventory.");
    }

    validateSaleInput(itemName, quantity, item.quantity);

    currentCart.push({
      name: item.name,
      size: item.size,
      quantity,
      price: item.price,
      total: item.price * quantity,
    });

    updateCartDisplay();
    e.target.reset();
  } catch (error) {
    alert(error.message);
  }
}

function updateCartDisplay() {
  const tbody = document.getElementById("cart-items");
  const totalElement = document.getElementById("cart-total");
  tbody.innerHTML = "";

  let total = 0;
  currentCart.forEach((item) => {
    total += item.total;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.name}</td>
      <td>${item.size || ""}</td>
      <td>${item.quantity}</td>
      <td>N${item.price.toFixed(2)}</td>
      <td>N${item.total.toFixed(2)}</td>
    `;
    tbody.appendChild(tr);
  });

  totalElement.textContent = `N${total.toFixed(2)}`;
}

window.completeSale = function () {
  try {
    if (currentCart.length === 0) {
      throw new Error("Cart is empty. Add items to complete the sale.");
    }

    // Read customer name
    const customerNameInput = document.getElementById("customer-name");
    let customerName = customerNameInput ? customerNameInput.value.trim() : "";

    // If no customer name, prompt for it
    if (!customerName) {
      customerName = prompt("Please enter Customer Name:");
      if (!customerName || customerName.trim() === "") {
        throw new Error("Customer name is required to complete the sale.");
      }
      customerName = customerName.trim();
    }

    // Update inventory
    currentCart.forEach((item) => {
      storage.updateItemQuantity(item.name, item.size, -item.quantity);
    });

    // Record sale
    const sale = {
      items: currentCart,
      total: currentCart.reduce((sum, item) => sum + item.total, 0),
      timestamp: new Date().toISOString(),
      customerName: customerName,
    };

    storage.recordSale(sale);
    currentCart = [];
    printReceipt();
    updateCartDisplay();
    refreshInventoryTable();
    reports.updateCharts();
    showReceipt(sale, customerName);
    // printReceipt();

    // Clear customer name input after sale completion
    if (customerNameInput) {
      customerNameInput.value = "";
    }
  } catch (error) {
    alert(error.message);
  }
};

window.showReceipt = function (sale, customerName) {
  const receiptContent = document.getElementById("receipt-content");
  const date = new Date(sale.timestamp);

  let receipt = `
    STOCKPILOT RECEIPT
    ------------------------------
    Customer Name: ${customerName || sale.customerName || "Guest"}
    Date: ${date.toLocaleDateString()} ${date.toLocaleTimeString()}
    ------------------------------
    
    Items:
  `;

  sale.items.forEach((item) => {
    receipt += `
    ${item.name} (Size: ${item.size || "N/A"})
    ${item.quantity} x N${item.price.toFixed(2)} = N${item.total.toFixed(2)}`;
  });

  receipt += `
    ------------------------------
    Total: N${sale.total.toFixed(2)}
    
    Thank you for the patronage☺️\n    Hope to see you next time🌾!
  `;

  receiptContent.innerHTML = receipt;

  const receiptModal = new bootstrap.Modal(
    document.getElementById("receiptModal"),
    {
      backdrop: "static",
      keyboard: false,
    }
  );

  receiptModal.show();
  document
    .getElementById("receiptModal")
    .addEventListener("shown.bs.modal", function () {
      document.querySelector("#receiptModal .btn-primary").focus();
    });
};

window.printReceipt = function () {
  window.print();
};

window.deleteItem = async function (itemName, size) {
  console.log("deleteItem called for", itemName, size);
  try {
    const video = document.getElementById("user-camera");
    const canvas = document.getElementById("snapshot-canvas");
    const context = canvas.getContext("2d");

    // Request access to front camera
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user" },
      audio: false,
    });

    video.srcObject = stream;
    video.style.display = "block";

    // Wait for video to be ready
    await new Promise((resolve) => {
      video.onloadedmetadata = () => {
        resolve();
      };
    });

    // Set canvas size to video size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Get image data URL (base64)
    const imageDataUrl = canvas.toDataURL("image/png");

    // Stop video stream
    stream.getTracks().forEach((track) => track.stop());
    video.style.display = "none";

    // Save deleted item record with timestamp
    const deletedItems = JSON.parse(localStorage.getItem("deletedItems")) || [];
    const timestamp = new Date().toISOString();
    const items = storage.getItems();
    const deletedItem = items.find(
      (i) => i.name === itemName && i.size === size
    );
    if (deletedItem) {
      deletedItems.push({
        ...deletedItem,
        deletedAt: timestamp,
        snapshot: imageDataUrl,
      });
      localStorage.setItem("deletedItems", JSON.stringify(deletedItems));
    }

    // Confirm deletion
    if (confirm("Are you sure you want to delete this item?")) {
      storage.deleteItem(itemName, size);
      refreshInventoryTable();
      refreshSaleItems();
      refreshDeletedItemsTable();
      console.log("Item deleted:", itemName, size);
    }
  } catch (error) {
    console.warn("Camera access denied or error occurred. Deleting without snapshot.", error);
    if (confirm("Camera access denied or error occurred. Delete item without snapshot?")) {
      storage.deleteItem(itemName, size);
      refreshInventoryTable();
      refreshSaleItems();
      refreshDeletedItemsTable();
      console.log("Item deleted without snapshot:", itemName, size);
    }
  }
};

// Function to refresh deleted items table in reports section
function refreshDeletedItemsTable() {
  const deletedItems = JSON.parse(localStorage.getItem("deletedItems")) || [];
  const tbody = document.querySelector("#deleted-items-table tbody");
  tbody.innerHTML = "";

  if (deletedItems.length === 0) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td colspan="6" style="text-align: center; color: #666;">No deleted items</td>`;
    tbody.appendChild(tr);
    return;
  }

  deletedItems.forEach((item) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.name}</td>
      <td>${item.size || ""}</td>
      <td>N${item.price.toFixed(2)}</td>
      <td>${item.quantity}</td>
      <td>${new Date(item.deletedAt).toLocaleString()}</td>
      <td>
        ${
          item.snapshot
            ? `<img src="${item.snapshot}" alt="Snapshot" style="max-width: 100px; max-height: 80px; cursor: pointer;" onclick="window.open('${item.snapshot}', '_blank')" />`
            : "No snapshot"
        }
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Initialize deleted items table on page load and when reports section is shown
document.addEventListener("DOMContentLoaded", () => {
  refreshDeletedItemsTable();
  const reportsTabButton = document.getElementById("reportsTabButton");
  if (reportsTabButton) {
    reportsTabButton.addEventListener("click", () => {
      refreshDeletedItemsTable();
    });
  }
});

// Send deleted items report via email using mailto link
document.addEventListener("DOMContentLoaded", () => {
  const sendEmailBtn = document.getElementById("sendDeletedItemsEmail");
  if (sendEmailBtn) {
    sendEmailBtn.addEventListener("click", () => {
      const deletedItems =
        JSON.parse(localStorage.getItem("deletedItems")) || [];
      if (deletedItems.length === 0) {
        alert("No deleted items to send.");
        return;
      }

      let emailBody = "Deleted Items Report:%0D%0A%0D%0A";
      deletedItems.forEach((item, index) => {
        emailBody += `${index + 1}. Name: ${item.name}, Size: ${
          item.size || ""
        }, Price: N${item.price.toFixed(2)}, Quantity: ${
          item.quantity
        }, Deleted At: ${new Date(item.deletedAt).toLocaleString()}%0D%0A`;
      });

      const email = "mojjam07@gmail.com"; // Replace with actual recipient email
      const subject = encodeURIComponent("Deleted Items Report");
      const body = encodeURIComponent(emailBody);

      window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
      // Clear deleted items after sending email
      localStorage.removeItem("deletedItems");
      refreshDeletedItemsTable();
    });
  }
});

window.showInventory = function () {
  localStorage.setItem("currentSection", "inventory");
  document.getElementById("inventory-section").style.display = "block";
  document.getElementById("sales-section").style.display = "none";
  document.getElementById("reports-section").style.display = "none";
};

window.showSales = function () {
  localStorage.setItem("currentSection", "sales");
  document.getElementById("inventory-section").style.display = "none";
  document.getElementById("sales-section").style.display = "block";
  document.getElementById("reports-section").style.display = "none";
};

window.showReports = function () {
  localStorage.setItem("currentSection", "reports");
  document.getElementById("inventory-section").style.display = "none";
  document.getElementById("sales-section").style.display = "none";
  document.getElementById("reports-section").style.display = "block";

  initCharts();
  reports.updateCharts();
  reports.updateSalesSummaryTable(
    JSON.parse(localStorage.getItem("sales")) || []
  );
};

// On page load, show the last viewed section or default to inventory
document.addEventListener("DOMContentLoaded", () => {
  const currentSection = localStorage.getItem("currentSection") || "inventory";
  if (currentSection === "inventory") {
    window.showInventory();
  } else if (currentSection === "sales") {
    window.showSales();
  } else if (currentSection === "reports") {
    window.showReports();
  } else {
    // If stored section is unknown, default to inventory
    window.showInventory();
  }
});

function initCharts() {
  const topProductsCtx = document
    .getElementById("topProductsChart")
    .getContext("2d");
  if (topProductsChartInstance) {
    topProductsChartInstance.destroy();
  }
  topProductsChartInstance = new Chart(topProductsCtx, {
    type: chartConfigs.topProducts.type,
    data: {
      labels: [],
      datasets: [
        {
          label: "Quantity Sold",
          data: [],
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderColor: "rgba(54, 162, 235, 1)",
          borderWidth: 1,
        },
      ],
    },
    options: chartConfigs.topProducts.options,
  });

  const salesTrendCtx = document
    .getElementById("salesTrendChart")
    .getContext("2d");
  if (salesTrendChartInstance) {
    salesTrendChartInstance.destroy();
  }
  salesTrendChartInstance = new Chart(salesTrendCtx, {
    type: chartConfigs.salesTrend.type,
    data: {
      labels: [],
      datasets: [
        {
          label: "Sales",
          data: [],
          fill: false,
          borderColor: "rgb(75, 192, 192)",
          tension: 0.1,
        },
      ],
    },
    options: chartConfigs.salesTrend.options,
  });

  const inventoryCtx = document
    .getElementById("inventoryChart")
    .getContext("2d");
  if (inventoryChartInstance) {
    inventoryChartInstance.destroy();
  }
  inventoryChartInstance = new Chart(inventoryCtx, {
    type: chartConfigs.inventory.type,
    data: {
      labels: [],
      datasets: [
        {
          label: "Inventory",
          data: [],
          backgroundColor: [
            "rgba(255, 99, 132, 0.2)",
            "rgba(54, 162, 235, 0.2)",
            "rgba(255, 206, 86, 0.2)",
            "rgba(75, 192, 192, 0.2)",
            "rgba(153, 102, 255, 0.2)",
          ],
          borderColor: [
            "rgba(255, 99, 132, 1)",
            "rgba(54, 162, 235, 1)",
            "rgba(255, 206, 86, 1)",
            "rgba(75, 192, 192, 1)",
            "rgba(153, 102, 255, 1)",
          ],
          borderWidth: 1,
        },
      ],
    },
    options: chartConfigs.inventory.options,
  });

  const revenueCtx = document.getElementById("revenueChart").getContext("2d");
  if (revenueChartInstance) {
    revenueChartInstance.destroy();
  }
  revenueChartInstance = new Chart(revenueCtx, {
    type: chartConfigs.revenue.type,
    data: {
      labels: [],
      datasets: [
        {
          label: "Revenue",
          data: [],
          backgroundColor: [
            "rgba(255, 99, 132, 0.2)",
            "rgba(54, 162, 235, 0.2)",
            "rgba(255, 206, 86, 0.2)",
            "rgba(75, 192, 192, 0.2)",
            "rgba(153, 102, 255, 0.2)",
          ],
          borderColor: [
            "rgba(255, 99, 132, 1)",
            "rgba(54, 162, 235, 1)",
            "rgba(255, 206, 86, 1)",
            "rgba(75, 192, 192, 1)",
            "rgba(153, 102, 255, 1)",
          ],
          borderWidth: 1,
        },
      ],
    },
    options: chartConfigs.revenue.options,
  });
}