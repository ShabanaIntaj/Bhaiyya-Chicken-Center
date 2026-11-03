
const API_BASE = "http://127.0.0.1:8000";

let products = [];

let cart = [];

try {
    cart = JSON.parse(localStorage.getItem("bhaiyyaCart")) || [];
} catch (error) {
    cart = [];
}

// Format prices in Indian Rupees
function formatPrice(price) {
    return "₹" + Number(price || 0).toLocaleString("en-IN", {
        maximumFractionDigits: 2
    });
}

// Safely display text received from the backend
function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, function (char) {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };
        return entities[char];
    });
}

// Load products from your existing FastAPI backend
async function loadProducts() {
    const productList = document.getElementById("product-list");
    const message = document.getElementById("product-message");

    productList.innerHTML =
        '<div class="loading-message">Loading fresh products...</div>';
    message.textContent = "";

    try {
        const response = await fetch(`${API_BASE}/products/`);

        if (!response.ok) {
            throw new Error("Could not load products.");
        }

        const data = await response.json();

        // Supports either a direct array or an object containing products
        products = Array.isArray(data)
            ? data
            : (data.products || data.items || []);

        displayProducts();
    } catch (error) {
        productList.innerHTML = `
            <div class="empty-message">
                Products could not be loaded yet.
                Please check that the backend is running.
            </div>
        `;

        message.textContent =
            "If the backend is running, the browser may be blocking the connection (CORS). We can fix that next.";
        console.error("Product loading error:", error);
    }
}

// Display products as cards
function displayProducts() {
    const productList = document.getElementById("product-list");

    if (!products.length) {
        productList.innerHTML = `
            <div class="empty-message">
                No products available yet.
            </div>
        `;
        return;
    }

    productList.innerHTML = products.map(function (product) {
        const id = product.id ?? product.product_id;
        
        const name = product.name ?? product.product_name ?? "Chicken Cut";
        const price = Number(
            product.selling_price ?? product.price ?? 0
        );

        const available =
            product.is_available ??
            product.available ??
            product.is_active ??
            true;

        const image = product.image_url ?? product.image_path ?? "";
        const description = product.description ?? "Fresh chicken cut";

        const imageHTML = image
            ? `<img src="${escapeHTML(image)}" alt="${escapeHTML(name)}"
                    onerror="this.parentElement.innerHTML='🍗'">`
            : "🍗";

        return `
            <article class="product-card">
                <div class="product-image">${imageHTML}</div>

                <div class="product-info">
                    <h3>${escapeHTML(name)}</h3>
                    <p>${escapeHTML(description)}</p>

                    <div class="product-price">
                        ${formatPrice(price)}
                        <small> / as listed</small>
                    </div>

                    <span class="availability ${available ? "" : "unavailable"}">
                        ${available ? "Available" : "Currently unavailable"}
                    </span>

                    <button
                        class="add-button"
                        data-product-id="${escapeHTML(String(id))}"
                        ${available ? "" : "disabled"}>
                         ${available ? "＋ Add to Cart" : "Unavailable"}
                    </button>
                </div>
            </article>
        `;
    }).join("");

    productList.querySelectorAll(".add-button").forEach(function (button) {
    button.addEventListener("click", function () {
        addToCart(button.dataset.productId);
    });
});
}

// Add one product to the cart
function addToCart(productId) {
    const product = products.find(function (item) {
        return String(item.id ?? item.product_id) === String(productId);
    });

    if (!product) return;

    const available =
        product.is_available ??
        product.available ??
        product.is_active ??
        true;

    if (!available) {
        alert("This product is currently unavailable.");
        return;
    }

    const id = String(product.id ?? product.product_id);
    const existingItem = cart.find(function (item) {
        return item.id === id;
    });

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            id: id,
            name: product.name ?? product.product_name ?? "Chicken Cut",
            price: Number(product.selling_price ?? product.price ?? 0),
            quantity: 1
        });
    }

    updateCart();
}

// Change the quantity of an item
function changeQuantity(productId, change) {
    const item = cart.find(function (product) {
        return product.id === String(productId);
    });

    if (!item) return;

    item.quantity += change;

    if (item.quantity <= 0) {
        cart = cart.filter(function (product) {
            return product.id !== String(productId);
        });
    }

    updateCart();
}

// Calculate the total
function getCartTotal() {
    return cart.reduce(function (total, item) {
        return total + item.price * item.quantity;
    }, 0);
}

// Update the cart count and contents
function updateCart() {

    localStorage.setItem("bhaiyyaCart", JSON.stringify(cart));

    const count = cart.reduce(function (total, item) {
        return total + item.quantity;
    }, 0);

    document.getElementById("cart-count").textContent = count;

    const cartItems = document.getElementById("cart-items");
    const cartTotal = document.getElementById("cart-total");

    if (!cart.length) {
        cartItems.innerHTML = "<p>Your cart is empty.</p>";
    } else {
        cartItems.innerHTML = cart.map(function (item) {
            return `
                <div class="cart-row">
                    <div>
                        <strong>${escapeHTML(item.name)}</strong>
                        <small>${formatPrice(item.price)} each</small>
                        <small>Subtotal: ${formatPrice(item.price * item.quantity)}</small>
                    </div>

                    <div class="quantity-controls">
                        <button onclick="changeQuantity('${item.id}', -1)">−</button>
                        <span>${item.quantity}</span>
                        <button onclick="changeQuantity('${item.id}', 1)">+</button>
                    </div>
                </div>
            `;
        }).join("");
    }

    cartTotal.textContent = "Total: " + formatPrice(getCartTotal());
}

// Open the cart
function showCart() {
    document.getElementById("cart-modal").classList.remove("hidden");
    document.getElementById("cart-message").textContent = "";
    updateCart();
}

// Close the cart
function closeCart() {
    document.getElementById("cart-modal").classList.add("hidden");
}

// Close the cart when clicking outside its panel
document.getElementById("cart-modal").addEventListener("click", function (event) {
    if (event.target === this) {
        closeCart();
    }
});

// Load products when the page opens
document.addEventListener("DOMContentLoaded", function () {
    updateCart();
    loadProducts();
});

// Proceed to checkout
function proceedToCheckout() {

    if (cart.length === 0) {
        alert("Please add products to your cart first.");
        return;
    }

    alert("Checkout page will be available soon!");
}




// Close Checkout
function closeCheckout() {

    document.getElementById("checkout-modal")
        .classList.add("hidden");
}
