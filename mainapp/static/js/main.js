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

// Inventory Section: Add stock item with image upload
const addItemForm = document.getElementById('add-item-form');
if (addItemForm) {
    addItemForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Check authentication first
        if (!isAuthenticated()) {
            alert('You must be logged in to add items.');
            window.location.href = '/login/';
            return;
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
        }
    });
}

// Fetch and display stock items
async function fetchStockItems() {
    if (!isAuthenticated()) {
        console.log('User not authenticated');
        const container = document.getElementById('inventory-cards');
        if (container) {
            container.innerHTML = '<p>Please <a href="/login/">log in</a> to view inventory items.</p>';
        }
        return;
    }
    
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
                <p>Price: ₦${item.price}</p>
                <p>Quantity: ${item.quantity}</p>
                <button class="btn btn-sm btn-danger" onclick="deleteStockItem(${item.id})">Delete</button>
            </div>
        `;
        container.appendChild(card);
    });
}

// Delete stock item
async function deleteStockItem(id) {
    if (!isAuthenticated()) {
        alert('You must be logged in to delete items.');
        window.location.href = '/login/';
        return;
    }
    
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
    if (!isAuthenticated()) return;
    
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
        
        if (quantity <= 0) {
            alert('Quantity must be positive.');
            return;
        }
        
        if (quantity > availableStock) {
            alert(`Only ${availableStock} items available in stock.`);
            return;
        }
        
        // Add to cart
        cart.push({ item_name, size, price, quantity });
        updateCartDisplay();
        saleItemSelect.selectedIndex = 0;
        quantityInput.value = '';
    });
}

const completeSaleBtn = document.getElementById('complete-sale-btn');
if (completeSaleBtn) {
    completeSaleBtn.addEventListener('click', async () => {
        if (!isAuthenticated()) {
            alert('You must be logged in to complete sales.');
            window.location.href = '/login/';
            return;
        }
        
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
                cart = [];
                updateCartDisplay();
                // Refresh stock items to update quantities
                fetchStockItems();
                loadSaleItems();
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
});

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