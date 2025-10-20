// Get CSRF token from cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Get CSRF token
const csrftoken = getCookie('csrftoken');

// Helper function to check authentication consistently
function isAuthenticated() {
    // Check if auth_token cookie exists
    const authToken = getCookie('auth_token');
    return authToken !== null && authToken !== '';
}

// Helper function to verify authentication with server
async function verifyAuthentication() {
    try {
        const response = await fetch('/api/verify-auth/', {
            method: 'GET',
            credentials: 'include',
        });
        return response.ok;
    } catch (error) {
        console.error('Error verifying authentication:', error);
        return false;
    }
}

const addItemForm = document.getElementById('add-item-form');
if (addItemForm) {
    addItemForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Disable submit button to prevent multiple submissions
        const submitButton = addItemForm.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Adding...';
        }

        // Verify authentication with server
        const isAuthValid = await verifyAuthentication();
        if (!isAuthValid) {
            alert('Your session has expired. Please log in again.');
            window.location.href = '/login/';
            return;
        }

        const item_name = document.getElementById('item-name').value.trim();
        const size = document.getElementById('item-size').value.trim();
        const price = parseFloat(document.getElementById('item-price').value);
        const quantity = parseInt(document.getElementById('item-quantity').value);
        const imageInput = document.getElementById('item-image');
        const imageFile = imageInput.files[0];

        const formData = new FormData();
        formData.append('item_name', item_name);
        formData.append('size', size);
        formData.append('price', price);
        formData.append('quantity', quantity);
        if (imageFile) {
            formData.append('image', imageFile);
        }

        try {
            const response = await fetch('/api/stockitems/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
                credentials: 'include',
                body: formData,
            });

            if (response.status === 401 || response.status === 403) {
                alert('Authentication failed. Please log in again.');
                window.location.href = '/login/';
                return;
            }

            const data = await response.json();
            if (response.ok) {
                alert('Item added successfully.');
                addItemForm.reset();
                fetchStockItems();
            } else {
                alert('Failed to add item: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error adding item:', error);
            alert('Error adding item: ' + error.message);
        } finally {
            // Re-enable submit button
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = 'Add Item';
            }
        }
    });
}

// Fetch and display stock items
async function fetchStockItems() {
    try {
        const response = await fetch('/api/stockitems/', {
            method: 'GET',
            credentials: 'include',
        });
        
        if (response.ok) {
            const data = await response.json();
            displayStockItems(data);
        } else if (response.status === 401 || response.status === 403) {
            console.error('Authentication failed');
            const container = document.getElementById('inventory-cards');
            if (container) {
                container.innerHTML = '<p>Authentication expired. Please <a href="/login/">log in again</a>.</p>';
            }
        } else {
            console.error('Failed to fetch stock items');
            const container = document.getElementById('inventory-cards');
            if (container) {
                container.innerHTML = '<p>Error loading inventory items.</p>';
            }
        }
    } catch (error) {
        console.error('Error fetching stock items:', error);
        const container = document.getElementById('inventory-cards');
        if (container) {
            container.innerHTML = '<p>Error loading inventory items.</p>';
        }
    }
}

// Display stock items in inventory-cards container
function displayStockItems(items) {
    const container = document.getElementById('inventory-cards');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (items.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">No stock items found.</p>';
        return;
    }
    
        items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'inventory-card';
            card.innerHTML = `
                <img src="${item.image_url || '/static/images/stockpilot.png'}" alt="${item.item_name}" class="inventory-card-image" />
                <div class="inventory-card-details">
                    <h4>${item.item_name}</h4>
                    <p>Size: ${item.size}</p>
                    <p class="price">Price: ₦${parseFloat(item.price).toFixed(2)}</p>
                    <p>Quantity: ${item.quantity}</p>
                    <div style="display: flex; justify-content: space-between; gap: 10px;">
                        <button class="btn btn-sm btn-primary" onclick="deleteStockItem(${item.id})">Delete</button>
                        <button class="btn btn-sm btn-primary" onclick="openUpdateModal(${item.id}, ${item.quantity}, ${item.price})">Edit</button>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
}

// Open the update modal and populate fields
window.openUpdateModal = function openUpdateModal(id, quantity, price) {
    const modal = document.getElementById('updateStockModal');
    const itemIdInput = document.getElementById('update-item-id');
    const quantityInput = document.getElementById('update-item-quantity');
    const priceInput = document.getElementById('update-item-price');

    if (!modal || !itemIdInput || !quantityInput || !priceInput) return;

    itemIdInput.value = id;
    quantityInput.value = quantity;
    priceInput.value = price;

    modal.style.display = 'block';
}

// Close the update modal
const closeUpdateModalBtn = document.getElementById('closeUpdateModal');
if (closeUpdateModalBtn) {
    closeUpdateModalBtn.addEventListener('click', () => {
        const modal = document.getElementById('updateStockModal');
        if (modal) {
            modal.style.display = 'none';
        }
    });
}

// Handle update form submission
const updateStockForm = document.getElementById('update-stock-form');
if (updateStockForm) {
    updateStockForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const id = document.getElementById('update-item-id').value;
        const quantity = parseInt(document.getElementById('update-item-quantity').value);
        const price = parseFloat(document.getElementById('update-item-price').value);

        if (!id || isNaN(quantity) || isNaN(price)) {
            alert('Please enter valid quantity and price.');
            return;
        }

        try {
            const response = await fetch(`/api/stockitems/${id}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                credentials: 'include',
                body: JSON.stringify({ quantity, price }),
            });

            if (response.ok) {
                alert('Stock item updated successfully.');
                const modal = document.getElementById('updateStockModal');
                if (modal) {
                    modal.style.display = 'none';
                }
                fetchStockItems();
            } else if (response.status === 401 || response.status === 403) {
                alert('Authentication failed. Please log in again.');
                window.location.href = '/login/';
            } else {
                const data = await response.json();
                alert('Failed to update item: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error updating stock item:', error);
            alert('Error updating stock item: ' + error.message);
        }
    });
}

window.deleteStockItem = async function deleteStockItem(id) {
    if (!confirm('Are you sure you want to delete this item?')) return;
    
    try {
        const response = await fetch(`/api/stockitems/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            credentials: 'include',
        });
        
        if (response.ok) {
            alert('Item deleted successfully.');
            fetchStockItems();
        } else if (response.status === 401 || response.status === 403) {
            alert('Authentication failed. Please log in again.');
            window.location.href = '/login/';
        } else {
            alert('Failed to delete item.');
        }
    } catch (error) {
        console.error('Error deleting item:', error);
        alert('Error deleting item: ' + error.message);
    }
}

// Sales Section: Manage cart and record sale
const saleForm = document.getElementById('sale-form');
const cartItemsContainer = document.getElementById('cart-items');
const cartTotalDisplay = document.getElementById('cart-total');

let cart = [];

function updateCartDisplay() {
    if (!cartItemsContainer || !cartTotalDisplay) return;
    cartItemsContainer.innerHTML = '';
    if (cart.length === 0) {
        const tr = document.createElement('tr');
        tr.innerHTML = '<td colspan="5" style="text-align: center; color: #666;">Cart is empty</td>';
        cartItemsContainer.appendChild(tr);
        cartTotalDisplay.textContent = '₦0.00';
        return;
    }
    let total = 0;
    cart.forEach(item => {
        const tr = document.createElement('tr');
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        tr.innerHTML = `
            <td>${item.item_name}</td>
            <td>${item.size}</td>
            <td>${item.quantity}</td>
            <td>₦${item.price.toFixed(2)}</td>
            <td>₦${itemTotal.toFixed(2)}</td>
        `;
        cartItemsContainer.appendChild(tr);
    });
    cartTotalDisplay.textContent = `₦${total.toFixed(2)}`;
}

// Load available items for sale
async function loadSaleItems() {
    try {
        const response = await fetch('/api/stockitems/', {
            method: 'GET',
            credentials: 'include',
        });
        
        if (response.ok) {
            const items = await response.json();
            const saleItemSelect = document.getElementById('sale-item');
            if (saleItemSelect) {
                saleItemSelect.innerHTML = '<option value="">Select an item...</option>';
                items.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.id;
                    option.textContent = `${item.item_name} - ${item.size} (₦${item.price}) - Stock: ${item.quantity}`;
                    option.dataset.price = item.price;
                    option.dataset.name = item.item_name;
                    option.dataset.size = item.size;
                    option.dataset.stock = item.quantity;
                    saleItemSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading sale items:', error);
    }
}

    if (saleForm) {
        saleForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const saleItemSelect = document.getElementById('sale-item');
            const quantityInput = document.getElementById('sale-quantity');
            const selectedOption = saleItemSelect.options[saleItemSelect.selectedIndex];
            
            if (!selectedOption || !selectedOption.value || !quantityInput.value) {
                alert('Please select an item and enter quantity.');
                return;
            }
            
            const item_name = selectedOption.dataset.name;
            const size = selectedOption.dataset.size;
            const price = parseFloat(selectedOption.dataset.price);
            const quantity = parseInt(quantityInput.value);
            const availableStock = parseInt(selectedOption.dataset.stock);
            const itemId = selectedOption.value;

            if (quantity <= 0) {
                alert('Quantity must be positive.');
                return;
            }

            // Calculate current quantity of this item already in cart
            let cartQty = 0;
            cart.forEach(c => {
                if (c.id == itemId) cartQty += c.quantity;
            });

            if (quantity + cartQty > availableStock) {
                alert(`Only ${availableStock - cartQty} items available in stock.`);
                return;
            }

            // Add to cart
            cart.push({ item_name, size, price, quantity, id: itemId, stock: availableStock });
            updateCartDisplay();
            saleItemSelect.selectedIndex = 0;
            quantityInput.value = '';
        });
    }

const completeSaleBtn = document.getElementById('complete-sale-btn');
if (completeSaleBtn) {
    completeSaleBtn.addEventListener('click', async () => {
        if (cart.length === 0) {
            alert('Cart is empty.');
            return;
        }
        
        const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
        const customerName = prompt('Enter customer name:') || '';
        
        try {
            const response = await fetch('/api/record_sale/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken,
                },
                credentials: 'include',
                body: JSON.stringify({ items: cart, total, customerName }),
            });
            
            if (response.status === 401 || response.status === 403) {
                alert('Authentication failed. Please log in again.');
                window.location.href = '/login/';
                return;
            }
            
            const data = await response.json();
            if (response.ok) {
                alert('Sale recorded successfully.');
                // Update stock quantities by decrementing based on cart items
                for (const item of cart) {
                    try {
                        // Calculate new quantity after sale
                        const newQuantity = Math.max(0, item.stock - item.quantity);
                        const updateResponse = await fetch(`/api/stockitems/${item.id}/`, {
                            method: 'PATCH',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': csrftoken,
                            },
                            credentials: 'include',
                            body: JSON.stringify({ quantity: newQuantity.toString() }),
                        });
                        if (!updateResponse.ok) {
                            console.error(`Failed to update stock for item ID ${item.id}`);
                        }
                    } catch (updateError) {
                        console.error(`Error updating stock for item ID ${item.id}:`, updateError);
                    }
                }
                // Print receipt before clearing the cart
                printReceipt(cart, total, customerName);
                cart = [];
                updateCartDisplay();
                // Refresh stock items to update quantities
                fetchStockItems();
                loadSaleItems();
                // Refresh sales report section if it exists
                fetchSalesSummary();
            } else {
                alert('Failed to record sale: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error recording sale:', error);
            alert('Error recording sale: ' + error.message);
        }
    });
}

// On page load, fetch stock items and load sale items
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('inventory-cards')) {
        fetchStockItems();
    }
    if (document.getElementById('sale-item')) {
        loadSaleItems();
    }
    if (document.getElementById('deleted-items-table')) {
        fetchDeletedItems();
    }
    if (document.getElementById('sales-summary-table')) {
        fetchSalesSummary();
    }
});

// Fetch and display sales summary in reports section
async function fetchSalesSummary() {
    try {
        const response = await fetch('/api/sales-summary/', {
            method: 'GET',
            credentials: 'include',
        });

        if (response.ok) {
            const sales = await response.json();
            displaySalesSummary(sales);
        } else if (response.status === 401 || response.status === 403) {
            console.error('Authentication failed while fetching sales summary');
            const tableBody = document.querySelector('#sales-summary-table tbody');
            if (tableBody) {
                tableBody.innerHTML = '<tr><td colspan="4">Authentication expired. Please <a href="/login/">log in again</a>.</td></tr>';
            }
        } else {
            console.error('Failed to fetch sales summary');
            const tableBody = document.querySelector('#sales-summary-table tbody');
            if (tableBody) {
                tableBody.innerHTML = '<tr><td colspan="4">Error loading sales summary.</td></tr>';
            }
        }
    } catch (error) {
        console.error('Error fetching sales summary:', error);
        const tableBody = document.querySelector('#sales-summary-table tbody');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="4">Error loading sales summary.</td></tr>';
        }
    }
}

// Clear all sales records
const clearSalesBtn = document.getElementById('clearSalesBtn');
if (clearSalesBtn) {
    clearSalesBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to delete all sales records?')) return;

        try {
            const response = await fetch('/api/clear-sales/', {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
            });

            if (response.ok) {
                alert('All sales records deleted.');
                fetchSalesSummary();
            } else {
                alert('Failed to delete sales records.');
            }
        } catch (error) {
            console.error('Error deleting sales records:', error);
            alert('Error deleting sales records: ' + error.message);
        }
    });
}

// Clear all deleted items records
const clearDeletedBtn = document.getElementById('clearDeletedBtn');
if (clearDeletedBtn) {
    clearDeletedBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to delete all deleted items records?')) return;

        try {
            const response = await fetch('/api/clear-deleted-items/', {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'X-CSRFToken': csrftoken,
                },
            });

            if (response.ok) {
                alert('All deleted items records deleted.');
                fetchDeletedItems();
            } else {
                alert('Failed to delete deleted items records.');
            }
        } catch (error) {
            console.error('Error deleting deleted items records:', error);
            alert('Error deleting deleted items records: ' + error.message);
        }
    });
}

// Display sales summary in reports section table
function displaySalesSummary(sales) {
    const tableBody = document.querySelector('#sales-summary-table tbody');
    if (!tableBody) return;

    if (sales.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; color: #666;">No sales data available</td></tr>';
        return;
    }

    tableBody.innerHTML = '';
    sales.forEach(sale => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${sale.id}</td>
            <td>${new Date(sale.timestamp).toLocaleString()}</td>
            <td>₦${sale.total.toFixed(2)}</td>
            <td><button class="btn btn-sm btn-primary" onclick="viewSaleDetails(${sale.id})">View</button></td>
        `;
        tableBody.appendChild(tr);
    });
}

// Print receipt function
function printReceipt(cart, total, customerName) {
    let receiptWindow = window.open('', 'Print Receipt', 'width=300,height=600');
    let receiptContent = `
        <html>
        <head>
            <title>POS Receipt</title>
            <style>
                body {
                    font-family: monospace;
                    font-size: 12px;
                    width: 280px;
                    padding: 10px;
                }
                h2, h3, p {
                    text-align: center;
                    margin: 5px 0;
                }
                .line {
                    border-top: 1px dashed #000;
                    margin: 5px 0;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 2px 5px;
                    text-align: left;
                }
                th {
                    border-bottom: 1px solid #000;
                }
                .right {
                    text-align: right;
                }
            </style>
        </head>
        <body>
            <h2>StockPilot Store</h2>
            <p>Customer: ${customerName}</p>
            <p>${new Date().toLocaleString()}</p>
            <div class="line"></div>
            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Qty</th>
                        <th class="right">Price</th>
                        <th class="right">Total</th>
                    </tr>
                </thead>
                <tbody>
    `;

    if (!cart || cart.length === 0) {
        receiptContent += `
            <tr>
                <td colspan="4" style="text-align: center; color: #666;">No items in cart</td>
            </tr>
        `;
    } else {
        cart.forEach(item => {
            const itemTotal = item.price * item.quantity;
            receiptContent += `
                <tr>
                    <td>${item.item_name} (${item.size || ''})</td>
                    <td>${item.quantity}</td>
                    <td class="right">₦${item.price.toFixed(2)}</td>
                    <td class="right">₦${itemTotal.toFixed(2)}</td>
                </tr>
            `;
        });
    }

    receiptContent += `
                </tbody>
            </table>
            <div class="line"></div>
            <h3>Total: ₦${total.toFixed(2)}</h3>
            <p style="text-align: center;">Thank you for your purchase!</p>
        </body>
        </html>
    `;

    receiptWindow.document.write(receiptContent);
    receiptWindow.document.close();
    receiptWindow.focus();
    receiptWindow.print();
    // Close the window after printing is done
    receiptWindow.addEventListener('afterprint', () => receiptWindow.close());
}

// Print receipt from sale record
function printReceiptFromSale(sale) {
    let receiptWindow = window.open('', 'Print Receipt', 'width=300,height=600');
    let receiptContent = `
        <html>
        <head>
            <title>POS Receipt</title>
            <style>
                body {
                    font-family: monospace;
                    font-size: 12px;
                    width: 280px;
                    padding: 10px;
                }
                h2, h3, p {
                    text-align: center;
                    margin: 5px 0;
                }
                .line {
                    border-top: 1px dashed #000;
                    margin: 5px 0;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                }
                th, td {
                    padding: 2px 5px;
                    text-align: left;
                }
                th {
                    border-bottom: 1px solid #000;
                }
                .right {
                    text-align: right;
                }
            </style>
        </head>
        <body>
            <h2>StockPilot Store</h2>
            <p>Customer: ${sale.customer_name || 'N/A'}</p>
            <p>${new Date(sale.timestamp).toLocaleString()}</p>
            <div class="line"></div>
            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Qty</th>
                        <th class="right">Price</th>
                        <th class="right">Total</th>
                    </tr>
                </thead>
                <tbody>
    `;

    if (!sale.items || sale.items.length === 0) {
        receiptContent += `
            <tr>
                <td colspan="4" style="text-align: center; color: #666;">No items in sale</td>
            </tr>
        `;
    } else {
        sale.items.forEach(item => {
            const itemTotal = item.price * item.quantity;
            receiptContent += `
                <tr>
                    <td>${item.item_name} (${item.size || ''})</td>
                    <td>${item.quantity}</td>
                    <td class="right">₦${item.price.toFixed(2)}</td>
                    <td class="right">₦${itemTotal.toFixed(2)}</td>
                </tr>
            `;
        });
    }

    receiptContent += `
                </tbody>
            </table>
            <div class="line"></div>
            <h3>Total: ₦${sale.total.toFixed(2)}</h3>
            <p style="text-align: center;">Thank you for your purchase!</p>
        </body>
        </html>
    `;

    receiptWindow.document.write(receiptContent);
    receiptWindow.document.close();
    receiptWindow.focus();
    receiptWindow.print();
    // Close the window after printing is done
    receiptWindow.addEventListener('afterprint', () => receiptWindow.close());
}

window.viewSaleDetails = async function viewSaleDetails(saleId) {
    try {
        const response = await fetch(`/api/sales-summary/${saleId}/`, {
            method: 'GET',
            credentials: 'include',
        });

        if (response.ok) {
            const sale = await response.json();
            printReceiptFromSale(sale);
        } else if (response.status === 401 || response.status === 403) {
            alert('Authentication failed. Please log in again.');
            window.location.href = '/login/';
        } else {
            alert('Failed to fetch sale details.');
        }
    } catch (error) {
        console.error('Error fetching sale details:', error);
        alert('Error fetching sale details: ' + error.message);
    }
};

// Fetch and display deleted items in reports section
async function fetchDeletedItems() {
    try {
        const response = await fetch('/api/deleted-items/', {
            method: 'GET',
            credentials: 'include',
        });

        if (response.ok) {
            const deletedItems = await response.json();
            displayDeletedItems(deletedItems);
        } else if (response.status === 401 || response.status === 403) {
            console.error('Authentication failed while fetching deleted items');
            const tableBody = document.querySelector('#deleted-items-table tbody');
            if (tableBody) {
                tableBody.innerHTML = '<tr><td colspan="6">Authentication expired. Please <a href="/login/">log in again</a>.</td></tr>';
            }
        } else {
            console.error('Failed to fetch deleted items');
            const tableBody = document.querySelector('#deleted-items-table tbody');
            if (tableBody) {
                tableBody.innerHTML = '<tr><td colspan="6">Error loading deleted items.</td></tr>';
            }
        }
    } catch (error) {
        console.error('Error fetching deleted items:', error);
        const tableBody = document.querySelector('#deleted-items-table tbody');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="6">Error loading deleted items.</td></tr>';
        }
    }
}

// Display deleted items in the reports section table
function displayDeletedItems(items) {
    const tableBody = document.querySelector('#deleted-items-table tbody');
    if (!tableBody) return;

    if (items.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #666;">No deleted items</td></tr>';
        return;
    }

    tableBody.innerHTML = '';
    items.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.item_name}</td>
            <td>${item.size || ''}</td>
            <td>₦${parseFloat(item.price).toFixed(2)}</td>
            <td>${item.quantity}</td>
            <td>${new Date(item.deleted_at).toLocaleString()}</td>
            <td>${item.snapshot ? '<a href="' + item.snapshot + '" target="_blank">View</a>' : ''}</td>
        `;
        tableBody.appendChild(tr);
    });
}

// Modify deleteStockItem to refresh deleted items after deletion
window.deleteStockItem = async function deleteStockItem(id) {
    if (!confirm('Are you sure you want to delete this item?')) return;
    
    try {
        const response = await fetch(`/api/stockitems/${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrftoken,
            },
            credentials: 'include',
        });
        
        if (response.ok) {
            alert('Item deleted successfully.');
            fetchStockItems();
            fetchDeletedItems();  // Refresh deleted items in reports section
        } else if (response.status === 401 || response.status === 403) {
            alert('Authentication failed. Please log in again.');
            window.location.href = '/login/';
        } else {
            alert('Failed to delete item.');
        }
    } catch (error) {
        console.error('Error deleting item:', error);
        alert('Error deleting item: ' + error.message);
    }
}

// Navigation functions to show/hide sections
function showInventory(event) {
    if (event) event.preventDefault();
    document.getElementById('inventory-section').style.display = 'block';
    document.getElementById('sales-section').style.display = 'none';
    document.getElementById('reports-section').style.display = 'none';
    fetchStockItems();
}

function showSales(event) {
    if (event) event.preventDefault();
    document.getElementById('inventory-section').style.display = 'none';
    document.getElementById('sales-section').style.display = 'block';
    document.getElementById('reports-section').style.display = 'none';
    loadSaleItems();
}

function showReports(event) {
    if (event) event.preventDefault();
    document.getElementById('inventory-section').style.display = 'none';
    document.getElementById('sales-section').style.display = 'none';
    document.getElementById('reports-section').style.display = 'block';
}

window.showInventory = showInventory;
window.showSales = showSales;
window.showReports = showReports;