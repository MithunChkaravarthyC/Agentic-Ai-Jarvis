// =========================================================
// 3D CAKE & LUXURY SHOP ENGINE (Three.js + Cart + Customizer)
// =========================================================

// --- 1. Product Catalog Database ---
const PRODUCTS = [
    {
        id: "cake-1",
        title: "Belgian Dark Truffle Royal",
        category: "signature",
        price: 899,
        tag: "Bestseller",
        desc: "70% Single-origin Belgian ganache layered with moist chocolate sponge and edible 24K gold foil.",
        image: "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=600&auto=format&fit=crop"
    },
    {
        id: "cake-2",
        title: "Red Velvet Berry Supreme",
        category: "signature",
        price: 799,
        tag: "Chef Special",
        desc: "Velvety crimson sponge layered with whipped Philadelphia cream cheese and fresh raspberries.",
        image: "https://images.unsplash.com/photo-1535141192574-5d4897c13136?w=600&auto=format&fit=crop"
    },
    {
        id: "cake-3",
        title: "Salted Caramel Biscoff Crunch",
        category: "signature",
        price: 949,
        tag: "Trending",
        desc: "Lotus Biscoff mousse, crushed speculoos crumble, and artisanal Himalayan salted caramel.",
        image: "https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=600&auto=format&fit=crop"
    },
    {
        id: "cake-4",
        title: "Madagascar Strawberry Gateau",
        category: "signature",
        price: 749,
        tag: "Fresh Summer",
        desc: "Infused with pure Bourbon vanilla bean and topped with fresh organic Mahabaleshwar strawberries.",
        image: "https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=600&auto=format&fit=crop"
    },
    {
        id: "cup-1",
        title: "Golden Ferrero Cupcakes (Set of 6)",
        category: "cupcakes",
        price: 499,
        tag: "Popular",
        desc: "Decadent Nutella-stuffed chocolate cupcakes topped with whole Ferrero Rocher & roasted hazelnuts.",
        image: "https://images.unsplash.com/photo-1587668178277-295251f900ce?w=600&auto=format&fit=crop"
    },
    {
        id: "cup-2",
        title: "Matcha Pistachio Blossom (Set of 6)",
        category: "cupcakes",
        price: 549,
        tag: "Exotic",
        desc: "Kyoto ceremonial matcha cream with roasted Iranian pistachios and white chocolate glaze.",
        image: "https://images.unsplash.com/photo-1576618148400-f54bed99fcfd?w=600&auto=format&fit=crop"
    },
    {
        id: "pas-1",
        title: "French Butter Croissant Box",
        category: "pastries",
        price: 399,
        tag: "Flaky & Crisp",
        desc: "AOP Charentes-Poitou French butter laminated 72 times for the ultimate honeycomb flakiness.",
        image: "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=600&auto=format&fit=crop"
    },
    {
        id: "pas-2",
        title: "Parisian Macarons Carousel (12 Pcs)",
        category: "pastries",
        price: 699,
        tag: "Luxury Gift",
        desc: "Almond meringue shells filled with pistachio, lavender honey, salted butter caramel, and dark cacao.",
        image: "https://images.unsplash.com/photo-1569864358642-9d1684040f43?w=600&auto=format&fit=crop"
    },
    {
        id: "wed-1",
        title: "Grand Victorian Wedding Tower",
        category: "wedding",
        price: 4999,
        tag: "Bespoke 3D",
        desc: "Four exquisite tiers with handcrafted edible sugar roses, pearls, and customizable flavor profiles.",
        image: "https://images.unsplash.com/photo-1535254973040-607b474cb50d?w=600&auto=format&fit=crop"
    }
];

// --- 2. Shopping Cart State ---
let cart = JSON.parse(localStorage.getItem("jarvis_shop_cart")) || [];

function saveCart() {
    localStorage.setItem("jarvis_shop_cart", JSON.stringify(cart));
    updateCartUI();
}

function addToCart(item) {
    const existing = cart.find(c => c.id === item.id);
    if (existing) {
        existing.qty += 1;
    } else {
        cart.push({ ...item, qty: 1 });
    }
    saveCart();
    showToast(`Added "${item.title}" to cart!`);
}

function updateQty(id, delta) {
    const idx = cart.findIndex(c => c.id === id);
    if (idx !== -1) {
        cart[idx].qty += delta;
        if (cart[idx].qty <= 0) {
            cart.splice(idx, 1);
        }
    }
    saveCart();
}

function updateCartUI() {
    const badge = document.getElementById("cartCountBadge");
    const itemsList = document.getElementById("cartItemsList");
    const subtotalEl = document.getElementById("cartSubtotal");
    const taxEl = document.getElementById("cartTax");
    const totalEl = document.getElementById("cartGrandTotal");
    const modalTotal = document.getElementById("modalTotalPayable");

    const totalCount = cart.reduce((sum, item) => sum + item.qty, 0);
    badge.textContent = totalCount;

    if (cart.length === 0) {
        itemsList.innerHTML = `
            <div style="text-align:center; padding: 40px 10px; color:#64748b;">
                <i class="fa-solid fa-basket-shopping" style="font-size:40px; margin-bottom:12px; color:#334155;"></i>
                <p>Your cart is empty.</p>
                <span style="font-size:12px;">Add handcrafted cakes from our menu.</span>
            </div>
        `;
        subtotalEl.textContent = "₹0.00";
        taxEl.textContent = "₹0.00";
        totalEl.textContent = "₹0.00";
        if (modalTotal) modalTotal.textContent = "₹0.00";
        return;
    }

    let subtotal = 0;
    itemsList.innerHTML = cart.map(item => {
        const itemTotal = item.price * item.qty;
        subtotal += itemTotal;
        return `
            <div class="cart-item-card">
                <img src="${item.image}" alt="${item.title}" class="cart-item-img">
                <div class="cart-item-details">
                    <div class="cart-item-title">${item.title}</div>
                    <div class="cart-item-price">₹${item.price}</div>
                </div>
                <div class="cart-qty-ctrls">
                    <button class="cart-qty-btn" onclick="updateQty('${item.id}', -1)">-</button>
                    <span>${item.qty}</span>
                    <button class="cart-qty-btn" onclick="updateQty('${item.id}', 1)">+</button>
                </div>
            </div>
        `;
    }).join("");

    const tax = Math.round(subtotal * 0.05);
    const grandTotal = subtotal + tax;

    subtotalEl.textContent = `₹${subtotal.toLocaleString()}`;
    taxEl.textContent = `₹${tax.toLocaleString()}`;
    totalEl.textContent = `₹${grandTotal.toLocaleString()}`;
    if (modalTotal) modalTotal.textContent = `₹${grandTotal.toLocaleString()}`;
}

function showToast(message) {
    const toast = document.getElementById("toastNotification");
    const text = document.getElementById("toastMessage");
    text.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3000);
}

// --- 3. Render Product Catalog ---
function renderProducts(category = "all", searchQuery = "") {
    const grid = document.getElementById("productGrid");
    const filtered = PRODUCTS.filter(p => {
        const matchCat = category === "all" || p.category === category;
        const matchSearch = p.title.toLowerCase().includes(searchQuery.toLowerCase()) || p.desc.toLowerCase().includes(searchQuery.toLowerCase());
        return matchCat && matchSearch;
    });

    if (filtered.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 40px; color:#94a3b8;">No cakes found matching your search.</div>`;
        return;
    }

    grid.innerHTML = filtered.map(p => `
        <div class="product-card">
            <div class="product-img-wrapper">
                <img src="${p.image}" alt="${p.title}" class="product-img" loading="lazy">
                <span class="product-tag">${p.tag}</span>
            </div>
            <div class="product-info">
                <h3 class="product-title">${p.title}</h3>
                <p class="product-desc">${p.desc}</p>
                <div class="product-meta">
                    <span class="product-price">₹${p.price}</span>
                    <button class="btn-add-cart" onclick='addToCart(${JSON.stringify(p)})'>
                        <i class="fa-solid fa-plus"></i> Add
                    </button>
                </div>
            </div>
        </div>
    `).join("");
}

// --- 4. Interactive Three.js 3D Cake Canvas ---
let scene, camera, renderer, cakeGroup, particlesGroup;
let isAutoRotating = true;
let currentFlavorColor = 0xfbbf24;

function initHero3DScene() {
    const container = document.getElementById("threejsCanvasContainer");
    if (!container || !window.THREE) return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 3, 7);

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const goldSpotLight = new THREE.SpotLight(0xfbbf24, 2.5);
    goldSpotLight.position.set(5, 8, 5);
    goldSpotLight.castShadow = true;
    scene.add(goldSpotLight);

    const cyanRimLight = new THREE.PointLight(0x00f0ff, 2.0, 10);
    cyanRimLight.position.set(-5, 2, -3);
    scene.add(cyanRimLight);

    // Cake 3D Geometry
    cakeGroup = new THREE.Group();

    // Plate / Stand
    const plateGeo = new THREE.CylinderGeometry(2.3, 2.1, 0.12, 48);
    const plateMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.8, roughness: 0.2 });
    const plate = new THREE.Mesh(plateGeo, plateMat);
    plate.position.y = -1.2;
    cakeGroup.add(plate);

    // Tier 1 (Bottom)
    const tier1Geo = new THREE.CylinderGeometry(1.8, 1.8, 0.9, 48);
    const cakeMat1 = new THREE.MeshStandardMaterial({ color: 0x3d2314, roughness: 0.4, metalness: 0.1 });
    const tier1 = new THREE.Mesh(tier1Geo, cakeMat1);
    tier1.position.y = -0.7;
    cakeGroup.add(tier1);

    // Frosting Ring 1
    const frost1Geo = new THREE.TorusGeometry(1.82, 0.08, 16, 48);
    const frostMat = new THREE.MeshStandardMaterial({ color: currentFlavorColor, roughness: 0.1, metalness: 0.3 });
    const frost1 = new THREE.Mesh(frost1Geo, frostMat);
    frost1.rotation.x = Math.PI / 2;
    frost1.position.y = -0.25;
    cakeGroup.add(frost1);

    // Tier 2 (Middle)
    const tier2Geo = new THREE.CylinderGeometry(1.3, 1.3, 0.8, 48);
    const cakeMat2 = new THREE.MeshStandardMaterial({ color: 0x541212, roughness: 0.4 });
    const tier2 = new THREE.Mesh(tier2Geo, cakeMat2);
    tier2.position.y = 0.15;
    cakeGroup.add(tier2);

    // Tier 3 (Top)
    const tier3Geo = new THREE.CylinderGeometry(0.8, 0.8, 0.7, 48);
    const cakeMat3 = new THREE.MeshStandardMaterial({ color: 0xf5eedc, roughness: 0.3 });
    const tier3 = new THREE.Mesh(tier3Geo, cakeMat3);
    tier3.position.y = 0.9;
    cakeGroup.add(tier3);

    // Crown Cherries / Berries on Top
    for (let i = 0; i < 6; i++) {
        const angle = (i / 6) * Math.PI * 2;
        const berryGeo = new THREE.SphereGeometry(0.12, 16, 16);
        const berryMat = new THREE.MeshStandardMaterial({ color: 0xd90429, roughness: 0.2, metalness: 0.1 });
        const berry = new THREE.Mesh(berryGeo, berryMat);
        berry.position.set(Math.cos(angle) * 0.55, 1.32, Math.sin(angle) * 0.55);
        cakeGroup.add(berry);
    }

    // Floating Candle / Sparkle on Top
    const candleGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.4, 16);
    const candleMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
    const candle = new THREE.Mesh(candleGeo, candleMat);
    candle.position.y = 1.45;
    cakeGroup.add(candle);

    const flameGeo = new THREE.ConeGeometry(0.08, 0.2, 16);
    const flameMat = new THREE.MeshBasicMaterial({ color: 0xffa500 });
    const flame = new THREE.Mesh(flameGeo, flameMat);
    flame.position.y = 1.7;
    cakeGroup.add(flame);

    scene.add(cakeGroup);

    // Floating Gold Particles
    particlesGroup = new THREE.Group();
    const partGeo = new THREE.BufferGeometry();
    const partCount = 70;
    const posArray = new Float32Array(partCount * 3);

    for (let i = 0; i < partCount * 3; i += 3) {
        posArray[i] = (Math.random() - 0.5) * 8;
        posArray[i + 1] = (Math.random() - 0.5) * 6;
        posArray[i + 2] = (Math.random() - 0.5) * 6;
    }

    partGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const partMat = new THREE.PointsMaterial({ size: 0.07, color: 0xfbbf24, transparent: true, opacity: 0.8 });
    const particleMesh = new THREE.Points(partGeo, partMat);
    particlesGroup.add(particleMesh);
    scene.add(particlesGroup);

    // Mouse Parallax Interaction
    let mouseX = 0, mouseY = 0;
    let targetRotationX = 0, targetRotationY = 0;
    let isDragging = false;
    let previousMousePosition = { x: 0, y: 0 };

    container.addEventListener('mousedown', () => isDragging = true);
    window.addEventListener('mouseup', () => isDragging = false);

    container.addEventListener('mousemove', (e) => {
        const rect = container.getBoundingClientRect();
        mouseX = ((e.clientX - rect.left) / width) * 2 - 1;
        mouseY = -(((e.clientY - rect.top) / height) * 2 - 1);

        if (isDragging) {
            const deltaX = e.clientX - previousMousePosition.x;
            const deltaY = e.clientY - previousMousePosition.y;
            cakeGroup.rotation.y += deltaX * 0.01;
            cakeGroup.rotation.x += deltaY * 0.01;
        }
        previousMousePosition = { x: e.clientX, y: e.clientY };
    });

    // Animation Loop
    function animate() {
        requestAnimationFrame(animate);

        if (isAutoRotating && !isDragging) {
            cakeGroup.rotation.y += 0.01;
        }

        particlesGroup.rotation.y += 0.002;
        flame.scale.y = 0.8 + Math.sin(Date.now() * 0.01) * 0.3;

        camera.position.x += (mouseX * 0.5 - camera.position.x) * 0.05;
        camera.position.y += (3 + mouseY * 0.3 - camera.position.y) * 0.05;
        camera.lookAt(0, 0, 0);

        renderer.render(scene, camera);
    }
    animate();

    // Resize Handler
    window.addEventListener('resize', () => {
        const w = container.clientWidth;
        const h = container.clientHeight;
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        renderer.setSize(w, h);
    });

    // Controls
    document.getElementById("rotateToggleBtn")?.addEventListener("click", () => {
        isAutoRotating = !isAutoRotating;
    });

    const flavors = [0xfbbf24, 0xf43f5e, 0x00f0ff, 0x10b981, 0xa855f7];
    let flavorIdx = 0;
    document.getElementById("frostingColorBtn")?.addEventListener("click", () => {
        flavorIdx = (flavorIdx + 1) % flavors.length;
        frostMat.color.setHex(flavors[flavorIdx]);
        goldSpotLight.color.setHex(flavors[flavorIdx]);
    });

    document.getElementById("sparkleEffectBtn")?.addEventListener("click", () => {
        if (window.confetti) {
            confetti({ particleCount: 50, spread: 60, origin: { y: 0.6 } });
        }
    });
}

// --- 5. 3D Customizer Logic ---
function initCustomizer() {
    const tierPills = document.querySelectorAll("#tierOptions .pill");
    const flavorSelect = document.getElementById("flavorSelect");
    const checkboxes = document.querySelectorAll('.check-container input[type="checkbox"]');
    const totalDisplay = document.getElementById("customizerTotalDisplay");
    const form = document.getElementById("cakeCustomizerForm");

    let baseTierPrice = 0;
    let selectedTier = "1 Tier (1 kg)";

    tierPills.forEach(pill => {
        pill.addEventListener("click", () => {
            tierPills.forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            baseTierPrice = parseInt(pill.dataset.price, 10);
            selectedTier = pill.textContent.split('+')[0].trim();
            calcTotal();
        });
    });

    flavorSelect?.addEventListener("change", calcTotal);
    checkboxes.forEach(cb => cb.addEventListener("change", calcTotal));

    function calcTotal() {
        let total = 899 + baseTierPrice; // base starting price
        const flavorPrice = parseInt(flavorSelect.options[flavorSelect.selectedIndex].dataset.price, 10) || 0;
        total += flavorPrice;

        checkboxes.forEach(cb => {
            if (cb.checked) {
                total += parseInt(cb.dataset.price, 10) || 0;
            }
        });

        totalDisplay.textContent = `₹${total.toLocaleString()}`;
        return total;
    }

    form?.addEventListener("submit", (e) => {
        e.preventDefault();
        const finalPrice = calcTotal();
        const flavorName = flavorSelect.value;
        const msg = document.getElementById("cakeMessageInput").value.trim();

        const customItem = {
            id: "custom-" + Date.now(),
            title: `Custom ${selectedTier} — ${flavorName}`,
            price: finalPrice,
            category: "custom",
            tag: "Bespoke 3D",
            desc: msg ? `Inscription: "${msg}"` : "Handcrafted to your custom specifications.",
            image: "https://images.unsplash.com/photo-1535254973040-607b474cb50d?w=600&auto=format&fit=crop"
        };

        addToCart(customItem);
        if (window.confetti) {
            confetti({ particleCount: 70, spread: 70, origin: { y: 0.7 } });
        }
        document.getElementById("cartDrawer").classList.add("open");
    });
}

// --- 6. Event Bindings & Init ---
document.addEventListener("DOMContentLoaded", () => {
    renderProducts();
    updateCartUI();
    initHero3DScene();
    initCustomizer();

    // Filter Tab switching
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            renderProducts(btn.dataset.category, document.getElementById("menuSearchInput").value);
        });
    });

    // Search Box
    document.getElementById("menuSearchInput")?.addEventListener("input", (e) => {
        const activeTab = document.querySelector(".tab-btn.active");
        renderProducts(activeTab ? activeTab.dataset.category : "all", e.target.value);
    });

    // Cart Drawer Open / Close
    const drawer = document.getElementById("cartDrawer");
    document.getElementById("cartToggleBtn")?.addEventListener("click", () => drawer.classList.add("open"));
    document.getElementById("closeCartBtn")?.addEventListener("click", () => drawer.classList.remove("open"));
    document.getElementById("cartOverlay")?.addEventListener("click", () => drawer.classList.remove("open"));

    // Checkout Modal
    const modal = document.getElementById("checkoutModal");
    document.getElementById("checkoutBtn")?.addEventListener("click", () => {
        if (cart.length === 0) {
            alert("Please add items to your cart before proceeding.");
            return;
        }
        drawer.classList.remove("open");
        modal.classList.add("active");
    });

    document.getElementById("closeModalBtn")?.addEventListener("click", () => modal.classList.remove("active"));

    // Payment Form Submit (Celebration)
    document.getElementById("paymentForm")?.addEventListener("submit", (e) => {
        e.preventDefault();
        modal.classList.remove("active");
        if (window.confetti) {
            confetti({ particleCount: 150, spread: 100, origin: { y: 0.5 } });
        }
        alert("🎉 Payment Authorized! Your mastercrafted order has been placed. Thank you, Sir!");
        cart = [];
        saveCart();
    });
});
