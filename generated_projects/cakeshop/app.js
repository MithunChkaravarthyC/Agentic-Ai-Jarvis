const products = [
    {
        id: 1,
        name: "Chocolate Cake",
        price: 20.99,
        image: "cake1.jpg"
    },
    {
        id: 2,
        name: "Vanilla Cake",
        price: 15.99,
        image: "cake2.jpg"
    },
    {
        id: 3,
        name: "Red Velvet Cake",
        price: 22.99,
        image: "cake3.jpg"
    }
];

const cart = [];

document.addEventListener("DOMContentLoaded", () => {
    const productList = document.getElementById("product-list");
    const cartList = document.getElementById("cart-list");
    const checkoutButton = document.getElementById("checkout");

    // Render products
    products.forEach((product) => {
        const productListItem = document.createElement("li");
        productListItem.innerHTML = `
            <img src="${product.image}" alt="${product.name}">
            <h2>${product.name}</h2>
            <p>$${product.price}</p>
            <button class="add-to-cart" data-product-id="${product.id}">Add to Cart</button>
        `;
        productListItem.addEventListener("click", (e) => {
            const productId = e.target.dataset.productId;
            const product = products.find((product) => product.id === parseInt(productId));
            if (cart.includes(product)) {
                // Remove product from cart
                cart.splice(cart.indexOf(product), 1);
                const cartItem = cartList.querySelector(`[data-product-id="${productId}"]`);
                cartList.removeChild(cartItem);
            } else {
                // Add product to cart
                cart.push(product);
                const cartItem = document.createElement("li");
                cartItem.innerHTML = `
                    <img src="${product.image}" alt="${product.name}">
                    <h2>${product.name}</h2>
                    <p>$${product.price}</p>
                    <button class="remove-from-cart" data-product-id="${product.id}">Remove from Cart</button>
                `;
                cartItem.addEventListener("click", (e) => {
                    const productId = e.target.dataset.productId;
                    cart.splice(cart.indexOf(product), 1);
                    cartList.removeChild(cartItem);
                });
                cartList.appendChild(cartItem);
            }
            renderCart();
        });
        productListItem.querySelector(".add-to-cart").addEventListener("click", (e) => {
            const productId = e.target.dataset.productId;
            const product = products.find((product) => product.id === parseInt(productId));
            cart.push(product);
            const cartItem = document.createElement("li");
            cartItem.innerHTML = `
                <img src="${product.image}" alt="${product.name}">
                <h2>${product.name}</h2>
                <p>$${product.price}</p>
                <button class="remove-from-cart" data-product-id="${product.id}">Remove from Cart</button>
            `;
            cartItem.addEventListener("click", (e) => {
                const productId = e.target.dataset.productId;
                cart.splice(cart.indexOf(product), 1);
                cartList.removeChild(cartItem);
            });
            cartList.appendChild(cartItem);
            renderCart();
        });
        productList.appendChild(productListItem);
    });

    // Render cart
    function renderCart() {
        cartList.innerHTML = "";
        cart.forEach((product) => {
            const cartItem = document.createElement("li");
            cartItem.innerHTML = `
                <img src="${product.image}" alt="${product.name}">
                <h2>${product.name}</h2>
                <p>$${product.price}</p>
                <button class="remove-from-cart" data-product-id="${product.id}">Remove from Cart</button>
            `;
            cartItem.addEventListener("click", (e) => {
                const productId = e.target.dataset.productId;
                cart.splice(cart.indexOf(product), 1);
                cartList.removeChild(cartItem);
            });
            cartList.appendChild(cartItem);
        });
    }

    // Checkout button
    checkoutButton.addEventListener("click", () => {
        alert(`You have ${cart.length} items in your cart. Total cost: $${cart.reduce((acc, product) => acc + product.price, 0).toFixed(2)}`);
    });
});