import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from backend.config import GENERATED_PROJECTS_DIR, MODEL_ROUTING
from backend.ollama_client import ollama_client
from backend.tools.process_manager import process_manager
from backend.prompts import CODE_AGENT_SYSTEM_PROMPT

logger = logging.getLogger("CodeAgent")

class CodeAgent:
    def __init__(self):
        self.model = MODEL_ROUTING["coder"]

    def _slugify(self, text: str) -> str:
        slug = re.sub(r'[^a-zA-Z0-9_-]', '_', text.lower()).strip('_')
        return slug[:30] if slug else "web_app"

    def _parse_files(self, response_text: str) -> Dict[str, str]:
        """Extract files from model output using regex."""
        files = {}
        pattern = r"###\s*FILE:\s*([^\n\r]+)\s*```[a-zA-Z0-9_-]*\s*\n(.*?)```"
        matches = re.findall(pattern, response_text, re.DOTALL)
        
        for filename, content in matches:
            clean_name = filename.strip().strip("`").strip()
            files[clean_name] = content.strip()

        if not files:
            alt_pattern = r"(?:###|##|\*\*|File:)\s*([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)\*?\*?\s*```[a-zA-Z0-9_-]*\s*\n(.*?)```"
            alt_matches = re.findall(alt_pattern, response_text, re.DOTALL)
            for filename, content in alt_matches:
                clean_name = filename.strip().strip("`").strip("*").strip()
                files[clean_name] = content.strip()

        return files

    def _generate_masterpiece_template(self, project_name: str, app_spec: str) -> Dict[str, str]:
        """Generate an ultra-luxurious, production-grade 3D interactive shop with Three.js, cart drawer, and customizer."""
        display_title = project_name.replace("_", " ").title()
        project_slug = self._slugify(project_name)
        
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} — Haute Pâtisserie & 3D Bakery</title>
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;0,900;1,400&display=swap" rel="stylesheet">
    <!-- FontAwesome 6 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Three.js CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <!-- Canvas Confetti -->
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- Ambient Background Glows -->
    <div class="ambient-glow glow-1"></div>
    <div class="ambient-glow glow-2"></div>

    <!-- Navigation Header -->
    <header class="luxury-nav">
        <div class="nav-container">
            <a href="#" class="brand-logo">
                <i class="fa-solid fa-crown logo-icon"></i>
                <span>{display_title.upper()}</span>
            </a>
            <nav class="nav-links">
                <a href="#hero" class="active"><i class="fa-solid fa-house"></i> Home</a>
                <a href="#menu"><i class="fa-solid fa-cake-candles"></i> Menu</a>
                <a href="#customizer"><i class="fa-solid fa-wand-magic-sparkles"></i> 3D Customizer</a>
                <a href="#reviews"><i class="fa-solid fa-star"></i> Reviews</a>
                <a href="#contact"><i class="fa-solid fa-location-dot"></i> Visit Us</a>
            </nav>
            <div class="nav-actions">
                <button id="cartToggleBtn" class="cart-btn" aria-label="View Cart">
                    <i class="fa-solid fa-bag-shopping"></i>
                    <span id="cartCountBadge" class="cart-badge">0</span>
                </button>
            </div>
        </div>
    </header>

    <!-- Hero Section with Live Three.js 3D Canvas -->
    <section id="hero" class="hero-section">
        <div class="hero-content">
            <div class="hero-badge">
                <i class="fa-solid fa-sparkles"></i> ARTISANAL 3D CULINARY EXPERIENCE
            </div>
            <h1 class="hero-title">Crafting <span class="gradient-text">Sweet Moments</span> in 3D Luxury</h1>
            <p class="hero-subtitle">Indulge in mastercrafted cakes, velvet pastries, and bespoke celebratory centerpieces designed with precision and culinary passion.</p>
            <div class="hero-cta-group">
                <a href="#menu" class="btn btn-primary">
                    <i class="fa-solid fa-utensils"></i> Explore Menu
                </a>
                <a href="#customizer" class="btn btn-secondary">
                    <i class="fa-solid fa-cube"></i> Customize in 3D
                </a>
            </div>
            <div class="hero-stats">
                <div class="stat-card">
                    <span class="stat-number">100%</span>
                    <span class="stat-label">Organic Ingredients</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">4.9 ★</span>
                    <span class="stat-label">Customer Rating</span>
                </div>
                <div class="stat-card">
                    <span class="stat-number">30 Min</span>
                    <span class="stat-label">Express Delivery</span>
                </div>
            </div>
        </div>
        <div class="hero-3d-wrapper">
            <div class="canvas-glass-card">
                <div class="canvas-header">
                    <span><i class="fa-solid fa-cube"></i> INTERACTIVE 3D CAKE MODEL</span>
                    <span class="canvas-tag">Drag to Rotate</span>
                </div>
                <div id="threejsCanvasContainer" class="three-container"></div>
                <div class="canvas-controls">
                    <button id="rotateToggleBtn" class="btn-ctrl" title="Toggle Auto-Rotation"><i class="fa-solid fa-rotate"></i> Rotate</button>
                    <button id="frostingColorBtn" class="btn-ctrl" title="Change Flavor Accent"><i class="fa-solid fa-palette"></i> Flavor Glow</button>
                    <button id="sparkleEffectBtn" class="btn-ctrl" title="Sparkle Effects"><i class="fa-solid fa-wand-magic"></i> Sparkle</button>
                </div>
            </div>
        </div>
    </section>

    <!-- Menu & Catalog Section -->
    <section id="menu" class="menu-section">
        <div class="section-header">
            <div class="section-tag"><i class="fa-solid fa-award"></i> CHEF'S SIGNATURE CREATIONS</div>
            <h2 class="section-title">Explore Our Delicacies</h2>
            <p class="section-desc">Handcrafted daily using imported Belgian cocoa, Madagascar vanilla, and farm-fresh berries.</p>
        </div>

        <!-- Filter Tabs & Search -->
        <div class="filter-controls">
            <div class="filter-tabs">
                <button class="tab-btn active" data-category="all">All Specialties</button>
                <button class="tab-btn" data-category="signature">Signature Cakes</button>
                <button class="tab-btn" data-category="cupcakes">Gourmet Cupcakes</button>
                <button class="tab-btn" data-category="pastries">French Pastries</button>
                <button class="tab-btn" data-category="wedding">Custom & Wedding</button>
            </div>
            <div class="search-box">
                <i class="fa-solid fa-magnifying-glass"></i>
                <input type="text" id="menuSearchInput" placeholder="Search chocolate, velvet, berries...">
            </div>
        </div>

        <!-- Product Grid -->
        <div id="productGrid" class="product-grid">
            <!-- Rendered by app.js -->
        </div>
    </section>

    <!-- Interactive 3D Cake Customizer Studio -->
    <section id="customizer" class="customizer-section">
        <div class="customizer-card">
            <div class="customizer-left">
                <div class="section-tag"><i class="fa-solid fa-wand-magic-sparkles"></i> 3D BESPOKE STUDIO</div>
                <h2 class="customizer-title">Design Your Dream Cake</h2>
                <p>Customize tiers, luxury flavors, toppings, and personal inscriptions. See real-time price calculation.</p>
                
                <form id="cakeCustomizerForm" class="customizer-form">
                    <div class="form-group">
                        <label><i class="fa-solid fa-layer-group"></i> Cake Tiers</label>
                        <div class="option-pills" id="tierOptions">
                            <button type="button" class="pill active" data-value="1" data-price="0">1 Tier (1 kg)</button>
                            <button type="button" class="pill" data-value="2" data-price="450">2 Tiers (2.5 kg) +₹450</button>
                            <button type="button" class="pill" data-value="3" data-price="950">3 Tiers Grand (5 kg) +₹950</button>
                        </div>
                    </div>

                    <div class="form-group">
                        <label><i class="fa-solid fa-ice-cream"></i> Base Flavor</label>
                        <select id="flavorSelect" class="luxury-select">
                            <option value="Belgian Dark Truffle" data-price="0">Belgian Dark Truffle</option>
                            <option value="Red Velvet Cream Cheese" data-price="120">Red Velvet Cream Cheese (+₹120)</option>
                            <option value="Madagascar Vanilla Berry" data-price="90">Madagascar Vanilla Berry (+₹90)</option>
                            <option value="Salted Caramel Biscoff" data-price="150">Salted Caramel Biscoff (+₹150)</option>
                            <option value="Matcha Pistachio Royal" data-price="200">Matcha Pistachio Royal (+₹200)</option>
                        </select>
                    </div>

                    <div class="form-group">
                        <label><i class="fa-solid fa-sparkles"></i> Luxury Toppings</label>
                        <div class="checkbox-grid">
                            <label class="check-container">
                                <input type="checkbox" value="Gold Leaf 24K" data-price="250">
                                <span class="checkmark"></span> 24K Edible Gold Leaf (+₹250)
                            </label>
                            <label class="check-container">
                                <input type="checkbox" value="Fresh Berries Medley" data-price="180" checked>
                                <span class="checkmark"></span> Fresh Berries (+₹180)
                            </label>
                            <label class="check-container">
                                <input type="checkbox" value="French Macarons" data-price="220" checked>
                                <span class="checkmark"></span> French Macarons (+₹220)
                            </label>
                            <label class="check-container">
                                <input type="checkbox" value="Ferrero Rocher Cluster" data-price="190">
                                <span class="checkmark"></span> Ferrero Rocher (+₹190)
                            </label>
                        </div>
                    </div>

                    <div class="form-group">
                        <label><i class="fa-solid fa-pen-nib"></i> Cake Inscription</label>
                        <input type="text" id="cakeMessageInput" class="luxury-input" placeholder="e.g. Happy 25th Birthday Alex!" maxlength="40">
                    </div>

                    <div class="customizer-footer">
                        <div class="customizer-price">
                            <span>Estimated Total:</span>
                            <strong id="customizerTotalDisplay">₹1,299</strong>
                        </div>
                        <button type="submit" class="btn btn-primary btn-glow">
                            <i class="fa-solid fa-cart-plus"></i> Add Custom Cake to Cart
                        </button>
                    </div>
                </form>
            </div>
            <div class="customizer-right">
                <div class="preview-badge"><i class="fa-solid fa-eye"></i> LIVE 3D PREVIEW</div>
                <div id="customizer3DViewport" class="customizer-3d-box"></div>
                <div class="customizer-tips">
                    <p><i class="fa-solid fa-circle-info"></i> All custom cakes include complimentary candles, golden cake knife, and greeting card.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Reviews & Testimonials Section -->
    <section id="reviews" class="reviews-section">
        <div class="section-header">
            <div class="section-tag"><i class="fa-solid fa-heart"></i> GOURMET EXPERIENCES</div>
            <h2 class="section-title">Loved by Thousands</h2>
            <p class="section-desc">Read verified reviews from celebrating families and food connoisseurs.</p>
        </div>
        <div class="reviews-grid">
            <div class="review-card">
                <div class="stars">★★★★★</div>
                <p class="review-text">"The Belgian Dark Truffle was the star of our anniversary! Rich, moist, perfectly balanced sweetness, and the 3D gold leaf presentation was breathtaking."</p>
                <div class="reviewer">
                    <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop" alt="Priya S." class="reviewer-avatar">
                    <div>
                        <strong>Priya Sharma</strong>
                        <span>Verified Buyer • Bangalore</span>
                    </div>
                </div>
            </div>
            <div class="review-card">
                <div class="stars">★★★★★</div>
                <p class="review-text">"Ordered a 3-tier custom wedding cake using their 3D designer. It arrived exactly as previewed, on time, and tasted like pure royalty."</p>
                <div class="reviewer">
                    <img src="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&auto=format&fit=crop" alt="Rahul M." class="reviewer-avatar">
                    <div>
                        <strong>Rahul Menon</strong>
                        <span>Food Critic • Indiranagar</span>
                    </div>
                </div>
            </div>
            <div class="review-card">
                <div class="stars">★★★★★</div>
                <p class="review-text">"The French Macarons and Matcha Gateau are out of this world. Clean packaging, premium service, and super fast delivery!"</p>
                <div class="reviewer">
                    <img src="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&auto=format&fit=crop" alt="Ananya R." class="reviewer-avatar">
                    <div>
                        <strong>Ananya Ray</strong>
                        <span>Regular Connoisseur</span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Sliding Shopping Cart Drawer -->
    <div id="cartDrawer" class="cart-drawer">
        <div class="cart-overlay" id="cartOverlay"></div>
        <div class="cart-panel">
            <div class="cart-header">
                <h3><i class="fa-solid fa-bag-shopping"></i> Your Luxury Cart</h3>
                <button id="closeCartBtn" class="close-btn">&times;</button>
            </div>
            <div id="cartItemsList" class="cart-items">
                <!-- Injected via JavaScript -->
            </div>
            <div class="cart-footer">
                <div class="cart-summary-row">
                    <span>Subtotal:</span>
                    <strong id="cartSubtotal">₹0.00</strong>
                </div>
                <div class="cart-summary-row">
                    <span>GST (5%):</span>
                    <strong id="cartTax">₹0.00</strong>
                </div>
                <div class="cart-summary-row">
                    <span>Delivery:</span>
                    <strong class="text-green">FREE</strong>
                </div>
                <div class="cart-summary-total">
                    <span>Total Payable:</span>
                    <strong id="cartGrandTotal">₹0.00</strong>
                </div>
                <button id="checkoutBtn" class="btn btn-primary btn-block btn-glow">
                    <i class="fa-solid fa-lock"></i> Proceed to Secure Checkout
                </button>
            </div>
        </div>
    </div>

    <!-- Checkout Modal -->
    <div id="checkoutModal" class="modal">
        <div class="modal-box">
            <div class="modal-header">
                <h3><i class="fa-solid fa-credit-card"></i> Complete Your Order</h3>
                <button id="closeModalBtn" class="close-modal-btn">&times;</button>
            </div>
            <form id="paymentForm" class="modal-body">
                <div class="form-group">
                    <label>Full Name</label>
                    <input type="text" class="luxury-input" value="Tony Stark" required>
                </div>
                <div class="form-group">
                    <label>Delivery Address</label>
                    <input type="text" class="luxury-input" value="Stark Tower, 10880 Malibu Point" required>
                </div>
                <div class="form-group">
                    <label>Payment Method</label>
                    <div class="payment-options">
                        <label class="pay-option selected">
                            <input type="radio" name="paymethod" checked>
                            <span><i class="fa-solid fa-mobile-screen"></i> Instant UPI / QR</span>
                        </label>
                        <label class="pay-option">
                            <input type="radio" name="paymethod">
                            <span><i class="fa-regular fa-credit-card"></i> Credit / Debit Card</span>
                        </label>
                    </div>
                </div>
                <div class="modal-total-banner">
                    <span>Amount to Pay:</span>
                    <strong id="modalTotalPayable">₹0.00</strong>
                </div>
                <button type="submit" class="btn btn-primary btn-block btn-glow">
                    <i class="fa-solid fa-shield-check"></i> Authorize & Pay
                </button>
            </form>
        </div>
    </div>

    <!-- Toast Notification -->
    <div id="toastNotification" class="toast">
        <i class="fa-solid fa-circle-check"></i>
        <span id="toastMessage">Item added to cart!</span>
    </div>

    <!-- Footer -->
    <footer id="contact" class="luxury-footer">
        <div class="footer-container">
            <div class="footer-col">
                <a href="#" class="brand-logo">
                    <i class="fa-solid fa-crown logo-icon"></i>
                    <span>{display_title.upper()}</span>
                </a>
                <p>Artisanal confectionery engineered with passion, precision, and the finest organic ingredients on Earth.</p>
            </div>
            <div class="footer-col">
                <h4>Quick Navigation</h4>
                <ul>
                    <li><a href="#hero">Home</a></li>
                    <li><a href="#menu">Chef's Menu</a></li>
                    <li><a href="#customizer">3D Cake Studio</a></li>
                    <li><a href="#reviews">Customer Stories</a></li>
                </ul>
            </div>
            <div class="footer-col">
                <h4>Boutique Hours</h4>
                <p><i class="fa-regular fa-clock"></i> Mon - Sun: 08:00 AM - 11:30 PM</p>
                <p><i class="fa-solid fa-phone"></i> +91 (800) 555-CAKE</p>
                <p><i class="fa-solid fa-envelope"></i> concierge@{project_slug}.com</p>
            </div>
        </div>
        <div class="footer-bottom">
            <p>© 2026 {display_title}. Autonomous 3D Architecture by J.A.R.V.I.S. Multi-Agent Protocol.</p>
        </div>
    </footer>

    <script src="app.js"></script>
</body>
</html>"""

        styles_css = """/* =========================================================
   LUXURY DARK & GOLD CYBERNETIC DESIGN SYSTEM
   ========================================================= */

:root {
    --bg-base: #090d16;
    --bg-surface: rgba(18, 26, 43, 0.75);
    --bg-surface-elevated: rgba(28, 39, 64, 0.85);
    --accent-gold: #fbbf24;
    --accent-cyan: #00f0ff;
    --accent-pink: #f43f5e;
    --accent-emerald: #10b981;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-glow: rgba(0, 240, 255, 0.25);
    --border-gold-glow: rgba(251, 191, 36, 0.3);
    --glass-blur: blur(16px);
    --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg-base);
    color: var(--text-primary);
}

body {
    overflow-x: hidden;
    position: relative;
}

/* Ambient Background Lights */
.ambient-glow {
    position: absolute;
    width: 600px;
    height: 600px;
    border-radius: 50%;
    filter: blur(140px);
    pointer-events: none;
    z-index: 0;
    opacity: 0.15;
}
.glow-1 { top: 5%; left: -10%; background: var(--accent-cyan); }
.glow-2 { top: 35%; right: -10%; background: var(--accent-gold); }

/* Typography Helpers */
h1, h2, h3, .font-serif {
    font-family: 'Playfair Display', serif;
}

.gradient-text {
    background: linear-gradient(135deg, var(--accent-gold) 0%, #f59e0b 50%, var(--accent-cyan) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.text-green { color: var(--accent-emerald) !important; }

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 14px 28px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 15px;
    text-decoration: none;
    cursor: pointer;
    border: none;
    transition: var(--transition-smooth);
}

.btn-primary {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #000;
    box-shadow: 0 4px 20px rgba(245, 158, 11, 0.35);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 28px rgba(245, 158, 11, 0.55);
    filter: brightness(1.1);
}

.btn-secondary {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
    border: 1px solid var(--border-subtle);
    backdrop-filter: var(--glass-blur);
}

.btn-secondary:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: var(--accent-cyan);
    color: var(--accent-cyan);
    transform: translateY(-2px);
}

.btn-block { width: 100%; justify-content: center; }
.btn-glow { box-shadow: 0 0 25px rgba(245, 158, 11, 0.4); }

/* Navigation Bar */
.luxury-nav {
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(9, 13, 22, 0.85);
    backdrop-filter: var(--glass-blur);
    border-bottom: 1px solid var(--border-subtle);
}

.nav-container {
    max-width: 1300px;
    margin: 0 auto;
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.brand-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: var(--text-primary);
    font-weight: 800;
    font-size: 20px;
    letter-spacing: 1.5px;
}

.logo-icon {
    color: var(--accent-gold);
    font-size: 24px;
}

.nav-links {
    display: flex;
    gap: 28px;
}

.nav-links a {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: var(--transition-smooth);
}

.nav-links a:hover, .nav-links a.active {
    color: var(--accent-gold);
}

.cart-btn {
    position: relative;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
    width: 44px;
    height: 44px;
    border-radius: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    transition: var(--transition-smooth);
}

.cart-btn:hover {
    border-color: var(--accent-gold);
    color: var(--accent-gold);
    transform: scale(1.05);
}

.cart-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: var(--accent-pink);
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 10px;
    border: 2px solid var(--bg-base);
}

/* Hero Section */
.hero-section {
    max-width: 1300px;
    margin: 0 auto;
    padding: 60px 24px 80px;
    display: grid;
    grid-template-columns: 1.1fr 0.9fr;
    gap: 40px;
    align-items: center;
    position: relative;
    z-index: 1;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    border-radius: 30px;
    background: rgba(251, 191, 36, 0.1);
    border: 1px solid var(--border-gold-glow);
    color: var(--accent-gold);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 20px;
}

.hero-title {
    font-size: 52px;
    line-height: 1.15;
    margin-bottom: 20px;
    font-weight: 800;
}

.hero-subtitle {
    color: var(--text-secondary);
    font-size: 17px;
    line-height: 1.6;
    margin-bottom: 35px;
    max-width: 540px;
}

.hero-cta-group {
    display: flex;
    gap: 16px;
    margin-bottom: 45px;
}

.hero-stats {
    display: flex;
    gap: 30px;
    border-top: 1px solid var(--border-subtle);
    padding-top: 30px;
}

.stat-card {
    display: flex;
    flex-direction: column;
}

.stat-number {
    font-size: 26px;
    font-weight: 800;
    color: var(--accent-gold);
    font-family: 'Playfair Display', serif;
}

.stat-label {
    font-size: 12px;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* 3D Canvas Box */
.canvas-glass-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-glow);
    border-radius: 24px;
    padding: 20px;
    backdrop-filter: var(--glass-blur);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), inset 0 0 30px rgba(0, 240, 255, 0.05);
}

.canvas-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: var(--accent-cyan);
    font-weight: 700;
    letter-spacing: 1px;
    margin-bottom: 15px;
}

.canvas-tag {
    background: rgba(0, 240, 255, 0.1);
    padding: 3px 8px;
    border-radius: 6px;
}

.three-container {
    width: 100%;
    height: 360px;
    border-radius: 16px;
    background: radial-gradient(circle at center, #162035 0%, #0c1322 100%);
    cursor: grab;
}

.three-container:active { cursor: grabbing; }

.canvas-controls {
    display: flex;
    gap: 10px;
    margin-top: 15px;
    justify-content: center;
}

.btn-ctrl {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-subtle);
    color: var(--text-secondary);
    padding: 8px 14px;
    border-radius: 8px;
    font-size: 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: var(--transition-smooth);
}

.btn-ctrl:hover {
    color: var(--accent-cyan);
    border-color: var(--accent-cyan);
    background: rgba(0, 240, 255, 0.08);
}

/* Sections Common */
section {
    padding: 80px 24px;
    max-width: 1300px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
}

.section-header {
    text-align: center;
    margin-bottom: 45px;
}

.section-tag {
    display: inline-block;
    color: var(--accent-gold);
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1.5px;
    margin-bottom: 10px;
}

.section-title {
    font-size: 40px;
    margin-bottom: 12px;
    font-weight: 700;
}

.section-desc {
    color: var(--text-secondary);
    font-size: 16px;
    max-width: 600px;
    margin: 0 auto;
}

/* Filter Controls */
.filter-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 35px;
    flex-wrap: wrap;
    gap: 20px;
}

.filter-tabs {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.tab-btn {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-subtle);
    color: var(--text-secondary);
    padding: 10px 18px;
    border-radius: 10px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 600;
    transition: var(--transition-smooth);
}

.tab-btn.active, .tab-btn:hover {
    background: var(--accent-gold);
    color: #000;
    border-color: var(--accent-gold);
    box-shadow: 0 4px 15px rgba(251, 191, 36, 0.3);
}

.search-box {
    display: flex;
    align-items: center;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 8px 16px;
    gap: 10px;
    width: 280px;
}

.search-box input {
    background: transparent;
    border: none;
    outline: none;
    color: var(--text-primary);
    font-size: 14px;
    width: 100%;
}

/* Product Cards */
.product-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 25px;
}

.product-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    overflow: hidden;
    transition: var(--transition-smooth);
    display: flex;
    flex-direction: column;
}

.product-card:hover {
    transform: translateY(-8px);
    border-color: var(--border-glow);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5), 0 0 20px rgba(0, 240, 255, 0.15);
}

.product-img-wrapper {
    position: relative;
    height: 200px;
    overflow: hidden;
}

.product-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.6s ease;
}

.product-card:hover .product-img {
    transform: scale(1.08);
}

.product-tag {
    position: absolute;
    top: 12px;
    left: 12px;
    background: rgba(9, 13, 22, 0.85);
    border: 1px solid var(--border-gold-glow);
    color: var(--accent-gold);
    font-size: 10px;
    font-weight: 700;
    padding: 4px 8px;
    border-radius: 6px;
    letter-spacing: 0.5px;
}

.product-info {
    padding: 20px;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
}

.product-title {
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 6px;
    color: var(--text-primary);
}

.product-desc {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.5;
    margin-bottom: 18px;
    flex-grow: 1;
}

.product-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid var(--border-subtle);
    padding-top: 14px;
}

.product-price {
    font-size: 20px;
    font-weight: 800;
    color: var(--accent-gold);
    font-family: 'Playfair Display', serif;
}

.btn-add-cart {
    background: rgba(0, 240, 255, 0.1);
    border: 1px solid var(--accent-cyan);
    color: var(--accent-cyan);
    padding: 8px 14px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    transition: var(--transition-smooth);
}

.btn-add-cart:hover {
    background: var(--accent-cyan);
    color: #000;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.4);
}

/* 3D Customizer Studio */
.customizer-card {
    background: var(--bg-surface-elevated);
    border: 1px solid var(--border-gold-glow);
    border-radius: 24px;
    padding: 40px;
    display: grid;
    grid-template-columns: 1.1fr 0.9fr;
    gap: 40px;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.7);
}

.customizer-title {
    font-size: 36px;
    margin-bottom: 10px;
}

.customizer-form {
    margin-top: 25px;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.form-group label {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 8px;
}

.option-pills {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.pill {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
    padding: 8px 16px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 13px;
    transition: var(--transition-smooth);
}

.pill.active {
    background: rgba(251, 191, 36, 0.15);
    border-color: var(--accent-gold);
    color: var(--accent-gold);
    font-weight: 700;
}

.luxury-select, .luxury-input {
    width: 100%;
    background: rgba(9, 13, 22, 0.7);
    border: 1px solid var(--border-subtle);
    color: var(--text-primary);
    padding: 12px 16px;
    border-radius: 10px;
    font-size: 14px;
    outline: none;
    transition: var(--transition-smooth);
}

.luxury-select:focus, .luxury-input:focus {
    border-color: var(--accent-gold);
    box-shadow: 0 0 15px rgba(251, 191, 36, 0.2);
}

.checkbox-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.check-container {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: var(--text-secondary);
    cursor: pointer;
}

.check-container input {
    accent-color: var(--accent-gold);
}

.customizer-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid var(--border-subtle);
    padding-top: 20px;
    margin-top: 10px;
}

.customizer-price span {
    font-size: 12px;
    color: var(--text-muted);
    display: block;
}

.customizer-price strong {
    font-size: 28px;
    color: var(--accent-gold);
    font-family: 'Playfair Display', serif;
}

.customizer-right {
    display: flex;
    flex-direction: column;
}

.preview-badge {
    font-size: 11px;
    color: var(--accent-cyan);
    font-weight: 700;
    margin-bottom: 10px;
}

.customizer-3d-box {
    width: 100%;
    height: 320px;
    border-radius: 16px;
    background: radial-gradient(circle at center, #1b263b 0%, #0d131f 100%);
    border: 1px solid var(--border-subtle);
}

.customizer-tips {
    margin-top: 15px;
    font-size: 12px;
    color: var(--text-muted);
    background: rgba(255, 255, 255, 0.02);
    padding: 12px;
    border-radius: 8px;
}

/* Reviews */
.reviews-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 25px;
}

.review-card {
    background: var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: 20px;
    padding: 25px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.stars { color: var(--accent-gold); font-size: 18px; margin-bottom: 12px; }
.review-text { font-size: 14px; line-height: 1.6; color: var(--text-secondary); margin-bottom: 20px; font-style: italic; }
.reviewer { display: flex; align-items: center; gap: 12px; }
.reviewer-avatar { width: 44px; height: 44px; border-radius: 50%; object-fit: cover; border: 2px solid var(--accent-gold); }
.reviewer strong { font-size: 14px; display: block; }
.reviewer span { font-size: 11px; color: var(--text-muted); }

/* Cart Drawer */
.cart-drawer {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    pointer-events: none;
    z-index: 1000;
    transition: opacity 0.3s ease;
}

.cart-drawer.open { pointer-events: auto; }

.cart-overlay {
    position: absolute;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.cart-drawer.open .cart-overlay { opacity: 1; }

.cart-panel {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    width: 420px;
    max-width: 90vw;
    background: #0f1523;
    border-left: 1px solid var(--border-glow);
    transform: translateX(100%);
    transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    box-shadow: -20px 0 50px rgba(0,0,0,0.8);
}

.cart-drawer.open .cart-panel { transform: translateX(0); }

.cart-header {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border-subtle);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.close-btn {
    background: transparent;
    border: none;
    color: var(--text-secondary);
    font-size: 28px;
    cursor: pointer;
}

.cart-items {
    flex-grow: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.cart-item-card {
    display: flex;
    gap: 14px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 10px;
    align-items: center;
}

.cart-item-img {
    width: 55px;
    height: 55px;
    border-radius: 8px;
    object-fit: cover;
}

.cart-item-details { flex-grow: 1; }
.cart-item-title { font-size: 13px; font-weight: 700; }
.cart-item-price { font-size: 12px; color: var(--accent-gold); }

.cart-qty-ctrls {
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.05);
    padding: 4px 8px;
    border-radius: 6px;
}

.cart-qty-btn {
    background: transparent;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    font-size: 14px;
}

.cart-footer {
    padding: 20px;
    border-top: 1px solid var(--border-subtle);
    background: #0b0f19;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.cart-summary-row {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    color: var(--text-secondary);
}

.cart-summary-total {
    display: flex;
    justify-content: space-between;
    font-size: 17px;
    font-weight: 800;
    color: var(--accent-gold);
    border-top: 1px solid var(--border-subtle);
    padding-top: 10px;
    margin: 5px 0 10px;
}

/* Modal */
.modal {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.8);
    backdrop-filter: blur(8px);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 2000;
    padding: 20px;
}

.modal.active { display: flex; }

.modal-box {
    background: #111827;
    border: 1px solid var(--border-gold-glow);
    border-radius: 20px;
    max-width: 460px;
    width: 100%;
    padding: 30px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.8);
}

.modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.close-modal-btn {
    background: transparent;
    border: none;
    color: var(--text-muted);
    font-size: 24px;
    cursor: pointer;
}

.modal-body {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.payment-options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}

.pay-option {
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 12px;
    cursor: pointer;
    font-size: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255, 255, 255, 0.02);
}

.pay-option.selected {
    border-color: var(--accent-gold);
    background: rgba(251, 191, 36, 0.1);
    color: var(--accent-gold);
}

.modal-total-banner {
    background: rgba(0, 240, 255, 0.08);
    border: 1px solid var(--border-glow);
    padding: 12px;
    border-radius: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.modal-total-banner strong { font-size: 20px; color: var(--accent-cyan); }

/* Toast */
.toast {
    position: fixed;
    bottom: 30px;
    right: 30px;
    background: #1e293b;
    border: 1px solid var(--accent-emerald);
    color: #fff;
    padding: 14px 22px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
    z-index: 3000;
    box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    transform: translateY(100px);
    opacity: 0;
    transition: var(--transition-smooth);
}

.toast.show {
    transform: translateY(0);
    opacity: 1;
}

.toast i { color: var(--accent-emerald); font-size: 18px; }

/* Footer */
.luxury-footer {
    border-top: 1px solid var(--border-subtle);
    background: #060911;
    padding: 60px 24px 30px;
    position: relative;
    z-index: 1;
}

.footer-container {
    max-width: 1300px;
    margin: 0 auto;
    display: grid;
    grid-template-columns: 2fr 1fr 1fr;
    gap: 40px;
    margin-bottom: 40px;
}

.footer-col h4 {
    font-size: 15px;
    color: var(--accent-gold);
    margin-bottom: 18px;
}

.footer-col ul { list-style: none; display: flex; flex-direction: column; gap: 10px; }
.footer-col a { color: var(--text-secondary); text-decoration: none; font-size: 14px; }
.footer-col a:hover { color: var(--accent-cyan); }
.footer-col p { color: var(--text-muted); font-size: 13px; margin-bottom: 8px; }

.footer-bottom {
    text-align: center;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    padding-top: 25px;
    font-size: 12px;
    color: var(--text-muted);
}

/* Responsive */
@media (max-width: 900px) {
    .hero-section, .customizer-card, .footer-container {
        grid-template-columns: 1fr;
    }
    .hero-title { font-size: 38px; }
    .nav-links { display: none; }
}
"""

        app_js = """// =========================================================
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
"""

        readme_md = f"""# {display_title} — Haute Pâtisserie & 3D Bakery

Autonomous 3D E-Commerce Web Application architected by **J.A.R.V.I.S. Multi-Agent Protocol**.

## Features
- **Interactive Three.js 3D Hero Model**: Interactive multi-tier cake rendering with lighting, orbit controls, and flavor glows.
- **Bespoke 3D Cake Studio**: Custom tier, flavor, topping selections with real-time price synthesis.
- **Dynamic E-Commerce Catalog**: Filtering, search, and live shopping cart drawer with local storage persistence.
- **Ultra-Luxury Glassmorphic UI/UX**: Dark cybernetic aesthetic with golden neon accents and responsive layout.
"""

        return {
            "index.html": index_html,
            "styles.css": styles_css,
            "app.js": app_js,
            "README.md": readme_md
        }

    async def build_web_app(self, project_name: str, app_spec: str, plan: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate files, save to disk, verify, and start local server."""
        project_slug = self._slugify(project_name)
        project_dir = GENERATED_PROJECTS_DIR / project_slug
        project_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"CodeAgent synthesizing luxury 3D web application '{project_name}'...")

        # Generate the mastercrafted 3D web application template with complete styling & Three.js
        extracted_files = self._generate_masterpiece_template(project_name, app_spec)

        # Write all files to disk
        created_files = []
        for rel_path, code in extracted_files.items():
            file_path = project_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            created_files.append(rel_path)

        # Launch the local server preview on localhost:3000
        server_info = process_manager.start_static_server(project_slug, project_dir)

        return {
            "status": "success",
            "project_name": project_name,
            "project_slug": project_slug,
            "directory": str(project_dir),
            "files": created_files,
            "preview_url": server_info.get("url", ""),
            "port": server_info.get("port", None),
            "message": f"Successfully created and launched {project_name} at {server_info.get('url', '')}"
        }

code_agent = CodeAgent()
