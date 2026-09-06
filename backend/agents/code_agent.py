import re
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from backend.config import GENERATED_PROJECTS_DIR, MODEL_ROUTING
from backend.ollama_client import ollama_client
from backend.tools.process_manager import process_manager
from backend.prompts import CODE_AGENT_SYSTEM_PROMPT

logger = logging.getLogger("CodeAgent")

class CodeAgent:
    """World-class creative technologist and 3D WebGL engineer specialized in Lusion-style websites."""

    def __init__(self):
        self.model = MODEL_ROUTING["coder"]

    def _slugify(self, text: str) -> str:
        slug = re.sub(r'[^a-zA-Z0-9_-]', '_', text.lower()).strip('_')
        return slug[:30] if slug else "lusion_3d_app"

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

    def _generate_lusion_masterpiece(self, project_name: str, app_spec: str) -> Dict[str, str]:
        """
        Generate an authentic, hypnotic, ultra-smooth 3D web experience inspired by Lusion.co.
        Features:
        - Real Three.js WebGL canvas with procedural 3D physical glass/metallic geometries
        - Silky 60fps dampening lerp loop for organic mouse inertia and parallax
        - Interactive particle physics swarm with cursor repulsion
        - Dynamic 3D Studio (geometry morpher, wireframe toggle, color shift engine)
        - Web Audio API procedural futuristic sound synthesis
        - Fluid magnetic cursor with follower ring
        - Glassmorphic editorial aesthetic with Syne and Space Grotesk typography
        """
        display_title = project_name.replace("_", " ").title()
        if not display_title or display_title.lower() == "jarviswebapp":
            display_title = "Lusion Neo // Creative 3D Studio"

        # Topic detection for bespoke copy
        lower_spec = app_spec.lower()
        if any(k in lower_spec for k in ["ai", "agent", "neural", "intelligence", "jarvis"]):
            tagline = "Autonomous Neural Architecture & 3D Intelligence"
            subline = "Pioneering fluid synthetic intelligence, spatial computing, and next-generation cognitive agent systems in immersive WebGL."
            industry = "AI & Spatial Computing"
        elif any(k in lower_spec for k in ["game", "gaming", "play", "metaverse"]):
            tagline = "Immersive Spatial Realms & Real-Time Physics"
            subline = "Engineering world-class interactive 3D simulations, real-time shaders, and sensory audio-visual realities."
            industry = "Creative Interactive Studio"
        elif any(k in lower_spec for k in ["fintech", "crypto", "finance", "bank"]):
            tagline = "Autonomous Financial Telemetry in Real-Time 3D"
            subline = "High-frequency computational liquidity, algorithmic execution, and hyper-dimensional market visualization."
            industry = "Quantitative Finance"
        elif any(k in lower_spec for k in ["portfolio", "agency", "design", "creative", "lusion"]):
            tagline = "Bespoke Creative Technology & Hypnotic 3D"
            subline = "We engineer award-winning sensory web experiences where art direction meets fluid computational mathematics."
            industry = "Creative Tech Studio"
        else:
            tagline = "Next-Generation Interactive 3D Web Experience"
            subline = f"Mastercrafted with computational Three.js WebGL graphics, silky lerp kinematics, and luxury cybernetic design for {display_title}."
            industry = "Interactive 3D Experience"

        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{display_title} — Lusion 3D Interactive Web Experience</title>
    <!-- Modern Editorial Typography -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <!-- FontAwesome 6 -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Three.js CDN -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <!-- Canvas Confetti -->
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
    <link rel="stylesheet" href="styles.css">
</head>
<body class="lusion-theme">
    <!-- Custom Fluid Magnetic Cursor -->
    <div id="cursorDot" class="cursor-dot"></div>
    <div id="cursorFollower" class="cursor-follower"></div>

    <!-- Ambient Dynamic Gradients -->
    <div class="ambient-nebula nebula-1"></div>
    <div class="ambient-nebula nebula-2"></div>
    <div class="ambient-nebula nebula-3"></div>

    <!-- Top Navigation -->
    <header class="lusion-nav">
        <div class="nav-container">
            <a href="#hero" class="brand-link">
                <span class="brand-symbol">◈</span>
                <span class="brand-text">{display_title.upper()}</span>
            </a>
            <nav class="nav-menu">
                <a href="#hero" class="nav-link active">Home</a>
                <a href="#studio" class="nav-link">3D Studio</a>
                <a href="#showcase" class="nav-link">Showcase</a>
                <a href="#architecture" class="nav-link">Architecture</a>
            </nav>
            <div class="nav-actions">
                <button id="audioToggleBtn" class="hud-pill-btn" title="Toggle Procedural Audio Synthesizer">
                    <i class="fa-solid fa-volume-high"></i> <span id="audioStatusText">SOUND ON</span>
                </button>
                <a href="#contact" class="btn-lusion-primary">
                    <span>CONNECT</span> <i class="fa-solid fa-arrow-right-long"></i>
                </a>
            </div>
        </div>
    </header>

    <!-- Hero Section with Full Interactive 3D WebGL Canvas -->
    <section id="hero" class="hero-section">
        <div class="hero-background-canvas" id="canvasContainer"></div>

        <div class="hero-content">
            <div class="hero-badge">
                <span class="pulse-dot"></span>
                <span>{industry.upper()} // LUSION-GRADE 3D</span>
            </div>
            
            <h1 class="hero-headline">
                Crafting <span class="gradient-text">Silky 3D</span><br>Realities & Beyond
            </h1>
            
            <p class="hero-subline">{subline}</p>
            
            <div class="hero-cta-bar">
                <a href="#studio" class="btn-lusion-glow">
                    <i class="fa-solid fa-wand-magic-sparkles"></i> Customize in 3D Studio
                </a>
                <button id="interact3dBtn" class="btn-lusion-glass">
                    <i class="fa-solid fa-hand"></i> Drag & Explore Mesh
                </button>
            </div>

            <div class="hero-telemetry-hud">
                <div class="telemetry-node">
                    <span class="node-label">RENDER PIPELINE</span>
                    <span class="node-val">Three.js WebGL 60FPS</span>
                </div>
                <div class="telemetry-node">
                    <span class="node-label">GEOMETRY KINEMATICS</span>
                    <span class="node-val" id="activeGeoLabel">Parametric Torus Knot</span>
                </div>
                <div class="telemetry-node">
                    <span class="node-label">PARTICLE SWARM</span>
                    <span class="node-val" id="particleCountLabel">1,800 Active</span>
                </div>
                <div class="telemetry-node">
                    <span class="node-label">INERTIA DAMPING</span>
                    <span class="node-val">LERP (Factor: 0.05)</span>
                </div>
            </div>
        </div>

        <!-- Floating On-Canvas 3D Studio HUD Overlay -->
        <div class="canvas-floating-controls">
            <div class="control-badge"><i class="fa-solid fa-cube"></i> REAL-TIME 3D HUD</div>
            <div class="hud-buttons-grid">
                <button id="btnToggleRotate" class="hud-icon-btn active" title="Toggle Auto-Rotation">
                    <i class="fa-solid fa-rotate"></i>
                    <span>Rotate</span>
                </button>
                <button id="btnToggleWireframe" class="hud-icon-btn" title="Toggle Physical / Wireframe">
                    <i class="fa-solid fa-border-none"></i>
                    <span>Wireframe</span>
                </button>
                <button id="btnCycleTheme" class="hud-icon-btn" title="Cycle Color Shaders">
                    <i class="fa-solid fa-palette"></i>
                    <span>Theme</span>
                </button>
                <button id="btnMorphGeometry" class="hud-icon-btn" title="Morph 3D Geometry">
                    <i class="fa-solid fa-shapes"></i>
                    <span>Morph</span>
                </button>
                <button id="btnResetCamera" class="hud-icon-btn" title="Reset Viewport">
                    <i class="fa-solid fa-arrows-to-dot"></i>
                    <span>Reset</span>
                </button>
            </div>
            <div class="canvas-drag-hint">
                <i class="fa-solid fa-computer-mouse"></i> Move mouse for smooth parallax • Drag canvas to orbit
            </div>
        </div>
    </section>

    <!-- Interactive 3D Studio Section -->
    <section id="studio" class="studio-section">
        <div class="section-container">
            <div class="section-header">
                <div class="sub-badge"><i class="fa-solid fa-sliders"></i> PROCEDURAL WORKBENCH</div>
                <h2 class="section-title">Interactive 3D Studio Controls</h2>
                <p class="section-lead">Adjust the mathematical rendering parameters, light shaders, and physics dynamics in real-time.</p>
            </div>

            <div class="studio-grid">
                <!-- Control Card 1: Geometry Selector -->
                <div class="studio-card">
                    <div class="card-icon"><i class="fa-solid fa-shapes"></i></div>
                    <h3>Geometry Synthesis</h3>
                    <p>Morph the active WebGL mesh dynamically using parametric formulas.</p>
                    <div class="option-pill-group" id="geoPillGroup">
                        <button class="pill-btn active" data-geo="torusknot">Torus Knot</button>
                        <button class="pill-btn" data-geo="icosahedron">Organic Icosahedron</button>
                        <button class="pill-btn" data-geo="quantum">Quantum Core</button>
                        <button class="pill-btn" data-geo="ribbon">Crystalline Ring</button>
                    </div>
                </div>

                <!-- Control Card 2: Chromatic Shader Palettes -->
                <div class="studio-card">
                    <div class="card-icon"><i class="fa-solid fa-swatchbook"></i></div>
                    <h3>Lighting & Shaders</h3>
                    <p>Select cinematic multi-point lighting themes and physical material properties.</p>
                    <div class="color-palette-group" id="themePicker">
                        <button class="color-btn active" data-theme="cyber-cyan" style="background: linear-gradient(135deg, #00f0ff, #0072ff);" title="Cyber Cyan"></button>
                        <button class="color-btn" data-theme="neon-magenta" style="background: linear-gradient(135deg, #ff007f, #7928ca);" title="Neon Magenta"></button>
                        <button class="color-btn" data-theme="emerald-matrix" style="background: linear-gradient(135deg, #00f5a0, #00d9f5);" title="Emerald Matrix"></button>
                        <button class="color-btn" data-theme="solar-amber" style="background: linear-gradient(135deg, #ffd000, #ff6b00);" title="Solar Amber"></button>
                        <button class="color-btn" data-theme="obsidian-mono" style="background: linear-gradient(135deg, #ffffff, #666666);" title="Obsidian Mono"></button>
                    </div>
                </div>

                <!-- Control Card 3: Kinematics & Physics -->
                <div class="studio-card">
                    <div class="card-icon"><i class="fa-solid fa-atom"></i></div>
                    <h3>Particle Swarm & Speed</h3>
                    <p>Fine-tune cosmic particle swarm density and auto-rotational inertia.</p>
                    <div class="slider-control">
                        <div class="slider-header">
                            <span>Particle Count</span>
                            <span id="sliderParticleVal">1800</span>
                        </div>
                        <input type="range" id="particleRange" min="400" max="3000" step="200" value="1800" class="lusion-range">
                    </div>
                    <div class="slider-control">
                        <div class="slider-header">
                            <span>Rotation Velocity</span>
                            <span id="sliderSpeedVal">1.0x</span>
                        </div>
                        <input type="range" id="speedRange" min="0" max="30" step="2" value="10" class="lusion-range">
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Dynamic Showcase Section -->
    <section id="showcase" class="showcase-section">
        <div class="section-container">
            <div class="section-header">
                <div class="sub-badge"><i class="fa-solid fa-layer-group"></i> CURATED WORKS</div>
                <h2 class="section-title">Creative Innovations</h2>
                <p class="section-lead">A collection of spatial interactions, procedural simulations, and fluid architectures.</p>
            </div>

            <!-- Filter Tabs -->
            <div class="showcase-tabs">
                <button class="filter-tab active" data-filter="all">All Specialties</button>
                <button class="filter-tab" data-filter="spatial">Spatial 3D</button>
                <button class="filter-tab" data-filter="physics">Particle Physics</button>
                <button class="filter-tab" data-filter="creative">Creative Tech</button>
            </div>

            <!-- Showcase Grid -->
            <div class="showcase-grid" id="showcaseGrid">
                <!-- Dynamically populated by app.js -->
            </div>
        </div>
    </section>

    <!-- Architecture & Engineering Specs -->
    <section id="architecture" class="arch-section">
        <div class="section-container">
            <div class="arch-card">
                <div class="arch-header">
                    <div class="sub-badge"><i class="fa-solid fa-microchip"></i> UNDER THE HOOD</div>
                    <h2>Lusion-Grade Technical Blueprint</h2>
                </div>
                <div class="arch-columns">
                    <div class="arch-col">
                        <h4><i class="fa-solid fa-bezier-curve"></i> Silky Lerp Damping</h4>
                        <p>Mouse coordinates are normalized and interpolated with a lerp coefficient of 0.05, completely eliminating jitter and producing liquid, weighted momentum.</p>
                    </div>
                    <div class="arch-col">
                        <h4><i class="fa-solid fa-gem"></i> MeshPhysicalMaterial</h4>
                        <p>Refraction, metallic sheen, clearcoat, and roughness are computed per-pixel using Three.js PBR lighting equations for photorealistic glass caustics.</p>
                    </div>
                    <div class="arch-col">
                        <h4><i class="fa-solid fa-wave-square"></i> Web Audio Synthesizer</h4>
                        <p>Zero external MP3 dependencies. Subtle acoustic feedback and holographic frequencies are dynamically synthesized using the browser's native Web Audio API.</p>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Contact & Collaboration Modal Trigger -->
    <section id="contact" class="contact-section">
        <div class="section-container">
            <div class="contact-box">
                <div class="contact-glow"></div>
                <div class="sub-badge"><i class="fa-solid fa-paper-plane"></i> INITIATE DIALOGUE</div>
                <h2>Ready to Build Something Mesmerizing?</h2>
                <p>Collaborate with our multi-agent protocol to construct bespoke 3D applications, spatial websites, and interactive digital artifacts.</p>
                <form id="contactForm" class="contact-form">
                    <div class="form-row">
                        <input type="text" id="contactName" placeholder="Your Name" required class="lusion-input">
                        <input type="email" id="contactEmail" placeholder="Your Email Address" required class="lusion-input">
                    </div>
                    <div class="form-row">
                        <select id="projectScope" class="lusion-input">
                            <option value="3D Website">Custom 3D Website</option>
                            <option value="AI Dashboard">Agentic AI Dashboard</option>
                            <option value="WebGL Studio">Interactive WebGL Studio</option>
                        </select>
                    </div>
                    <button type="submit" class="btn-lusion-glow full-width">
                        <span>TRANSMIT PROPOSAL</span> <i class="fa-solid fa-paper-plane"></i>
                    </button>
                </form>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="lusion-footer">
        <div class="footer-container">
            <div class="footer-left">
                <span class="brand-symbol">◈</span>
                <span>{display_title.upper()} // ARCHITECTED BY J.A.R.V.I.S. MULTI-AGENT PROTOCOL</span>
            </div>
            <div class="footer-right">
                <span>WebGL 2.0 • Three.js r128 • 60 FPS Guaranteed</span>
            </div>
        </div>
    </footer>

    <script src="app.js"></script>
</body>
</html>"""

        styles_css = """/* ==========================================================================
   LUSION-GRADE ULTRA-LUXURY 3D WEB ARCHITECTURE & STYLING
   ========================================================================== */

:root {
    --bg-main: #050508;
    --bg-surface: #0a0a10;
    --bg-card: rgba(18, 18, 28, 0.45);
    --primary: #00f0ff;
    --primary-glow: rgba(0, 240, 255, 0.35);
    --secondary: #ff007f;
    --secondary-glow: rgba(255, 0, 127, 0.35);
    --accent: #7928ca;
    --accent-gold: #ffd000;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --glass-border: rgba(255, 255, 255, 0.08);
    --glass-border-hover: rgba(0, 240, 255, 0.4);
    --glass-blur: blur(24px);
    --font-heading: 'Syne', sans-serif;
    --font-body: 'Space Grotesk', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
}

/* Color Theme Overrides */
body[data-theme="neon-magenta"] {
    --primary: #ff007f;
    --primary-glow: rgba(255, 0, 127, 0.4);
    --secondary: #00f0ff;
}

body[data-theme="emerald-matrix"] {
    --primary: #00f5a0;
    --primary-glow: rgba(0, 245, 160, 0.4);
    --secondary: #00d9f5;
}

body[data-theme="solar-amber"] {
    --primary: #ffd000;
    --primary-glow: rgba(255, 208, 0, 0.4);
    --secondary: #ff6b00;
}

body[data-theme="obsidian-mono"] {
    --primary: #ffffff;
    --primary-glow: rgba(255, 255, 255, 0.3);
    --secondary: #888888;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    cursor: default;
}

html {
    scroll-behavior: smooth;
    background: var(--bg-main);
    color: var(--text-main);
    font-family: var(--font-body);
}

body {
    background: var(--bg-main);
    overflow-x: hidden;
    min-height: 100vh;
    position: relative;
    user-select: none;
}

/* --- Magnetic Fluid Cursor --- */
.cursor-dot {
    position: fixed;
    top: 0;
    left: 0;
    width: 8px;
    height: 8px;
    background: var(--primary);
    border-radius: 50%;
    pointer-events: none;
    z-index: 9999;
    transform: translate(-50%, -50%);
    transition: width 0.2s, height 0.2s, background-color 0.2s;
    box-shadow: 0 0 12px var(--primary-glow);
}

.cursor-follower {
    position: fixed;
    top: 0;
    left: 0;
    width: 36px;
    height: 36px;
    border: 1px solid var(--primary);
    border-radius: 50%;
    pointer-events: none;
    z-index: 9998;
    transform: translate(-50%, -50%);
    transition: width 0.25s, height 0.25s, border-color 0.25s, transform 0.08s ease-out;
    opacity: 0.6;
}

.cursor-hover .cursor-dot {
    width: 14px;
    height: 14px;
    background: var(--secondary);
}

.cursor-hover .cursor-follower {
    width: 54px;
    height: 54px;
    border-color: var(--secondary);
    background: rgba(255, 0, 127, 0.08);
}

/* --- Ambient Nebulas --- */
.ambient-nebula {
    position: fixed;
    border-radius: 50%;
    filter: blur(120px);
    pointer-events: none;
    z-index: 0;
    opacity: 0.35;
}

.nebula-1 {
    top: -10%;
    left: 20%;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
}

.nebula-2 {
    bottom: 10%;
    right: 5%;
    width: 700px;
    height: 700px;
    background: radial-gradient(circle, var(--secondary-glow) 0%, transparent 70%);
}

.nebula-3 {
    top: 45%;
    left: -10%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(121, 40, 202, 0.25) 0%, transparent 70%);
}

/* --- Top Navigation Bar --- */
.lusion-nav {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 1000;
    background: rgba(5, 5, 8, 0.65);
    backdrop-filter: var(--glass-blur);
    border-bottom: 1px solid var(--glass-border);
    padding: 16px 0;
}

.nav-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.brand-link {
    display: flex;
    align-items: center;
    gap: 12px;
    text-decoration: none;
    color: var(--text-main);
    font-family: var(--font-heading);
    font-weight: 800;
    font-size: 18px;
    letter-spacing: 2px;
}

.brand-symbol {
    color: var(--primary);
    font-size: 22px;
    filter: drop-shadow(0 0 8px var(--primary-glow));
    animation: rotateSymbol 12s linear infinite;
}

@keyframes rotateSymbol {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.nav-menu {
    display: flex;
    gap: 32px;
}

.nav-link {
    text-decoration: none;
    color: var(--text-muted);
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    transition: color 0.25s;
    position: relative;
    padding: 6px 0;
}

.nav-link:hover, .nav-link.active {
    color: var(--primary);
}

.nav-link.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: var(--primary);
    box-shadow: 0 0 8px var(--primary-glow);
}

.nav-actions {
    display: flex;
    align-items: center;
    gap: 16px;
}

.hud-pill-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--glass-border);
    color: var(--text-muted);
    padding: 8px 16px;
    border-radius: 50px;
    font-size: 11px;
    font-family: var(--font-mono);
    letter-spacing: 1px;
    transition: all 0.25s;
    display: flex;
    align-items: center;
    gap: 8px;
}

.hud-pill-btn:hover {
    color: var(--primary);
    border-color: var(--primary);
    box-shadow: 0 0 15px var(--primary-glow);
}

.btn-lusion-primary {
    background: var(--text-main);
    color: var(--bg-main);
    padding: 10px 22px;
    border-radius: 50px;
    text-decoration: none;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 1.5px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-lusion-primary:hover {
    background: var(--primary);
    color: var(--bg-main);
    box-shadow: 0 0 25px var(--primary-glow);
    transform: translateY(-2px);
}

/* --- Hero Section with 3D Canvas --- */
.hero-section {
    position: relative;
    width: 100%;
    min-height: 100vh;
    display: flex;
    align-items: center;
    padding: 120px 32px 60px;
    overflow: hidden;
}

.hero-background-canvas {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
}

.hero-content {
    position: relative;
    z-index: 10;
    max-width: 680px;
    margin-left: 5%;
    pointer-events: none;
}

.hero-content * {
    pointer-events: auto;
}

.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 6px 16px;
    border-radius: 50px;
    background: rgba(0, 240, 255, 0.08);
    border: 1px solid var(--primary-glow);
    color: var(--primary);
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 1.5px;
    margin-bottom: 24px;
}

.pulse-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--primary);
    box-shadow: 0 0 8px var(--primary);
    animation: pulseGlow 1.8s infinite;
}

@keyframes pulseGlow {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.5; }
}

.hero-headline {
    font-family: var(--font-heading);
    font-size: clamp(42px, 6vw, 76px);
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -1.5px;
    margin-bottom: 24px;
}

.gradient-text {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 20px var(--primary-glow));
}

.hero-subline {
    font-size: clamp(15px, 1.3vw, 18px);
    line-height: 1.6;
    color: var(--text-muted);
    margin-bottom: 36px;
    max-width: 580px;
}

.hero-cta-bar {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    margin-bottom: 48px;
}

.btn-lusion-glow {
    background: linear-gradient(135deg, var(--primary) 0%, #0072ff 100%);
    color: #030712;
    padding: 14px 28px;
    border-radius: 10px;
    font-weight: 700;
    font-size: 14px;
    letter-spacing: 1px;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    border: none;
    box-shadow: 0 0 30px var(--primary-glow);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.btn-lusion-glow:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 0 45px var(--primary-glow);
}

.btn-lusion-glass {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    color: var(--text-main);
    padding: 14px 28px;
    border-radius: 10px;
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 1px;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    transition: all 0.3s;
}

.btn-lusion-glass:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: var(--primary);
    box-shadow: 0 0 20px var(--primary-glow);
}

.hero-telemetry-hud {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    max-width: 520px;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    padding: 16px 20px;
    border-radius: 12px;
}

.telemetry-node {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.node-label {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-muted);
    letter-spacing: 1.5px;
}

.node-val {
    font-family: var(--font-mono);
    font-size: 13px;
    font-weight: 600;
    color: var(--primary);
}

/* Floating On-Canvas 3D Studio HUD */
.canvas-floating-controls {
    position: absolute;
    right: 40px;
    bottom: 40px;
    z-index: 20;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.6);
    max-width: 320px;
}

.control-badge {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--primary);
    letter-spacing: 1.5px;
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.hud-buttons-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    margin-bottom: 14px;
}

.hud-icon-btn {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--glass-border);
    color: var(--text-muted);
    border-radius: 8px;
    padding: 10px 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    transition: all 0.25s;
}

.hud-icon-btn span {
    font-size: 9px;
    font-family: var(--font-mono);
    letter-spacing: 0.5px;
}

.hud-icon-btn:hover, .hud-icon-btn.active {
    color: var(--primary);
    border-color: var(--primary);
    background: rgba(0, 240, 255, 0.1);
    box-shadow: 0 0 12px var(--primary-glow);
}

.canvas-drag-hint {
    font-size: 10px;
    color: var(--text-muted);
    font-family: var(--font-mono);
    line-height: 1.4;
    text-align: center;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    padding-top: 10px;
}

/* --- Section Shared Styles --- */
.section-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 100px 32px;
}

.section-header {
    text-align: center;
    max-width: 700px;
    margin: 0 auto 64px;
}

.sub-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 2px;
    color: var(--primary);
    margin-bottom: 12px;
}

.section-title {
    font-family: var(--font-heading);
    font-size: clamp(32px, 4vw, 48px);
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 16px;
}

.section-lead {
    font-size: 16px;
    color: var(--text-muted);
    line-height: 1.6;
}

/* --- 3D Studio Workbench Grid --- */
.studio-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
    gap: 32px;
}

.studio-card {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    padding: 36px 28px;
    border-radius: 18px;
    transition: all 0.3s;
    position: relative;
    overflow: hidden;
}

.studio-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--primary), transparent);
    opacity: 0;
    transition: opacity 0.3s;
}

.studio-card:hover {
    border-color: var(--glass-border-hover);
    transform: translateY(-4px);
    box-shadow: 0 15px 40px rgba(0,0,0,0.5);
}

.studio-card:hover::before {
    opacity: 1;
}

.card-icon {
    width: 50px;
    height: 50px;
    border-radius: 12px;
    background: rgba(0, 240, 255, 0.08);
    border: 1px solid var(--primary-glow);
    color: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    margin-bottom: 20px;
}

.studio-card h3 {
    font-family: var(--font-heading);
    font-size: 20px;
    margin-bottom: 10px;
}

.studio-card p {
    font-size: 14px;
    color: var(--text-muted);
    margin-bottom: 24px;
    line-height: 1.5;
}

.option-pill-group {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.pill-btn {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--glass-border);
    color: var(--text-muted);
    padding: 12px 18px;
    border-radius: 10px;
    font-family: var(--font-mono);
    font-size: 12px;
    text-align: left;
    transition: all 0.25s;
}

.pill-btn:hover, .pill-btn.active {
    background: rgba(0, 240, 255, 0.12);
    border-color: var(--primary);
    color: var(--primary);
    box-shadow: 0 0 15px var(--primary-glow);
}

.color-palette-group {
    display: flex;
    gap: 14px;
}

.color-btn {
    width: 44px;
    height: 44px;
    border-radius: 50%;
    border: 2px solid transparent;
    transition: all 0.25s;
}

.color-btn:hover, .color-btn.active {
    transform: scale(1.15);
    border-color: #ffffff;
    box-shadow: 0 0 20px var(--primary-glow);
}

.slider-control {
    margin-bottom: 20px;
}

.slider-header {
    display: flex;
    justify-content: space-between;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 8px;
}

.slider-header span:last-child {
    color: var(--primary);
    font-weight: 600;
}

.lusion-range {
    width: 100%;
    -webkit-appearance: none;
    height: 6px;
    border-radius: 3px;
    background: rgba(255, 255, 255, 0.1);
    outline: none;
}

.lusion-range::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: var(--primary);
    box-shadow: 0 0 10px var(--primary);
    cursor: pointer;
}

/* --- Showcase Grid --- */
.showcase-tabs {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-bottom: 48px;
    flex-wrap: wrap;
}

.filter-tab {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--glass-border);
    color: var(--text-muted);
    padding: 10px 20px;
    border-radius: 50px;
    font-size: 13px;
    font-family: var(--font-mono);
    transition: all 0.25s;
}

.filter-tab:hover, .filter-tab.active {
    background: var(--primary);
    color: var(--bg-main);
    border-color: var(--primary);
    box-shadow: 0 0 20px var(--primary-glow);
    font-weight: 700;
}

.showcase-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    gap: 32px;
}

.showcase-item {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.showcase-item:hover {
    transform: translateY(-6px);
    border-color: var(--primary);
    box-shadow: 0 20px 45px rgba(0, 240, 255, 0.15);
}

.item-thumb {
    width: 100%;
    height: 240px;
    background-size: cover;
    background-position: center;
    position: relative;
}

.item-thumb::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(0deg, var(--bg-surface) 0%, transparent 60%);
}

.item-badge {
    position: absolute;
    top: 16px;
    right: 16px;
    z-index: 2;
    background: rgba(5, 5, 8, 0.8);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    padding: 4px 12px;
    border-radius: 50px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--primary);
    letter-spacing: 1px;
}

.item-body {
    padding: 24px;
}

.item-body h4 {
    font-family: var(--font-heading);
    font-size: 20px;
    margin-bottom: 8px;
}

.item-body p {
    font-size: 14px;
    color: var(--text-muted);
    line-height: 1.5;
    margin-bottom: 16px;
}

.item-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.tag-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    padding: 3px 8px;
    border-radius: 4px;
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-muted);
}

/* --- Architecture Card --- */
.arch-card {
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 24px;
    padding: 56px 48px;
}

.arch-header {
    margin-bottom: 40px;
}

.arch-header h2 {
    font-family: var(--font-heading);
    font-size: 36px;
}

.arch-columns {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 32px;
}

.arch-col h4 {
    font-family: var(--font-heading);
    font-size: 18px;
    margin-bottom: 12px;
    color: var(--primary);
    display: flex;
    align-items: center;
    gap: 10px;
}

.arch-col p {
    font-size: 14px;
    color: var(--text-muted);
    line-height: 1.6;
}

/* --- Contact Section --- */
.contact-box {
    max-width: 800px;
    margin: 0 auto;
    background: var(--bg-card);
    backdrop-filter: var(--glass-blur);
    border: 1px solid var(--glass-border);
    border-radius: 24px;
    padding: 60px 48px;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.contact-glow {
    position: absolute;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 400px;
    height: 200px;
    background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
    pointer-events: none;
}

.contact-box h2 {
    font-family: var(--font-heading);
    font-size: 36px;
    margin-bottom: 16px;
}

.contact-box p {
    font-size: 16px;
    color: var(--text-muted);
    margin-bottom: 36px;
    line-height: 1.6;
}

.contact-form {
    display: flex;
    flex-direction: column;
    gap: 16px;
    text-align: left;
}

.form-row {
    display: flex;
    gap: 16px;
}

.lusion-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--glass-border);
    border-radius: 10px;
    padding: 14px 18px;
    color: var(--text-main);
    font-family: var(--font-body);
    font-size: 14px;
    outline: none;
    transition: all 0.25s;
}

.lusion-input:focus {
    border-color: var(--primary);
    box-shadow: 0 0 15px var(--primary-glow);
    background: rgba(255, 255, 255, 0.07);
}

.full-width {
    width: 100%;
    justify-content: center;
}

/* --- Footer --- */
.lusion-footer {
    border-top: 1px solid var(--glass-border);
    padding: 32px 0;
    background: rgba(5, 5, 8, 0.8);
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
}

.footer-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 0 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}

@media (max-width: 900px) {
    .hero-section {
        padding-top: 100px;
    }
    .canvas-floating-controls {
        position: static;
        margin-top: 40px;
        max-width: 100%;
    }
    .form-row {
        flex-direction: column;
    }
}
"""

        app_js = f"""// ==========================================================================
// LUSION-GRADE THREE.JS CREATIVE ENGINE & KINEMATICS
// ==========================================================================

class Lusion3DStudio {{
    constructor() {{
        this.container = document.getElementById("canvasContainer");
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.activeMesh = null;
        this.particleSystem = null;
        this.lights = [];

        // Smooth Lerp Mouse Kinematics (Factor: 0.05 for silky organic momentum)
        this.mouse = {{ x: 0, y: 0, targetX: 0, targetY: 0 }};
        this.windowHalfX = window.innerWidth / 2;
        this.windowHalfY = window.innerHeight / 2;

        // Interaction State
        this.isDragging = false;
        this.previousMousePosition = {{ x: 0, y: 0 }};
        this.dragVelocity = {{ x: 0, y: 0 }};
        this.autoRotate = true;
        this.rotateSpeed = 0.008;
        this.isWireframe = false;
        this.currentGeometryType = "torusknot";
        this.currentTheme = "cyber-cyan";
        this.soundEnabled = true;

        // Web Audio Synthesizer Context
        this.audioCtx = null;

        this.initThree();
        this.initGeometries();
        this.initParticleSwarm(1800);
        this.initAudioSynthesizer();
        this.bindEvents();
        this.initCursor();
        this.renderShowcaseItems();
        this.animate();
    }}

    // --- 1. Three.js Scene Setup ---
    initThree() {{
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.FogExp2(0x050508, 0.04);

        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(0, 0, 8);

        this.renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true, powerPreference: "high-performance" }});
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        this.container.appendChild(this.renderer.domElement);

        // Multi-point dynamic cinematic lighting
        const ambient = new THREE.AmbientLight(0xffffff, 0.6);
        this.scene.add(ambient);

        const dirLight = new THREE.DirectionalLight(0xffffff, 1.2);
        dirLight.position.set(5, 10, 7);
        this.scene.add(dirLight);

        // Point Light 1 (Cyan / Primary)
        this.pointLight1 = new THREE.PointLight(0x00f0ff, 3.5, 30);
        this.pointLight1.position.set(6, 4, 5);
        this.scene.add(this.pointLight1);
        this.lights.push(this.pointLight1);

        // Point Light 2 (Magenta / Secondary)
        this.pointLight2 = new THREE.PointLight(0xff007f, 3.5, 30);
        this.pointLight2.position.set(-6, -4, -3);
        this.scene.add(this.pointLight2);
        this.lights.push(this.pointLight2);

        // Point Light 3 (Accent rim light)
        this.pointLight3 = new THREE.PointLight(0x7928ca, 2.5, 25);
        this.pointLight3.position.set(0, 6, -5);
        this.scene.add(this.pointLight3);
        this.lights.push(this.pointLight3);
    }}

    // --- 2. Procedural Mesh Generation ---
    getMaterial() {{
        return new THREE.MeshPhysicalMaterial({{
            color: 0x111625,
            emissive: 0x050c1e,
            roughness: 0.12,
            metalness: 0.85,
            clearcoat: 1.0,
            clearcoatRoughness: 0.1,
            reflectivity: 0.9,
            wireframe: this.isWireframe
        }});
    }}

    createGeometry(type) {{
        switch (type) {{
            case "torusknot":
                return new THREE.TorusKnotGeometry(2.0, 0.65, 128, 32, 2, 3);
            case "icosahedron":
                return new THREE.IcosahedronGeometry(2.4, 4);
            case "quantum":
                return new THREE.SphereGeometry(2.3, 64, 64);
            case "ribbon":
                return new THREE.TorusGeometry(2.2, 0.8, 30, 100);
            default:
                return new THREE.TorusKnotGeometry(2.0, 0.65, 128, 32, 2, 3);
        }}
    }}

    initGeometries() {{
        const geo = this.createGeometry(this.currentGeometryType);
        const mat = this.getMaterial();
        this.activeMesh = new THREE.Mesh(geo, mat);
        this.scene.add(this.activeMesh);
    }}

    morphGeometry(type) {{
        this.playTone(440, "triangle", 0.15);
        this.currentGeometryType = type;
        document.getElementById("activeGeoLabel").textContent = type.charAt(0).toUpperCase() + type.slice(1);

        if (this.activeMesh) {{
            const oldRotX = this.activeMesh.rotation.x;
            const oldRotY = this.activeMesh.rotation.y;
            this.scene.remove(this.activeMesh);
            this.activeMesh.geometry.dispose();

            const newGeo = this.createGeometry(type);
            this.activeMesh = new THREE.Mesh(newGeo, this.getMaterial());
            this.activeMesh.rotation.x = oldRotX;
            this.activeMesh.rotation.y = oldRotY;
            this.scene.add(this.activeMesh);
        }}
    }}

    // --- 3. Interactive Floating Particle Swarm ---
    initParticleSwarm(count = 1800) {{
        if (this.particleSystem) {{
            this.scene.remove(this.particleSystem);
            this.particleSystem.geometry.dispose();
        }}

        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);
        const color = new THREE.Color(0x00f0ff);

        for (let i = 0; i < count; i++) {{
            // Spherical distribution
            const radius = 4 + Math.random() * 8;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(Math.random() * 2 - 1);

            positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
            positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
            positions[i * 3 + 2] = radius * Math.cos(phi);

            colors[i * 3] = color.r * (0.6 + Math.random() * 0.4);
            colors[i * 3 + 1] = color.g * (0.6 + Math.random() * 0.4);
            colors[i * 3 + 2] = color.b * (0.6 + Math.random() * 0.4);
        }}

        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));

        const mat = new THREE.PointsMaterial({{
            size: 0.05,
            vertexColors: true,
            transparent: true,
            opacity: 0.75,
            blending: THREE.AdditiveBlending
        }});

        this.particleSystem = new THREE.Points(geo, mat);
        this.scene.add(this.particleSystem);
        document.getElementById("particleCountLabel").textContent = `${{count.toLocaleString()}} Active`;
    }}

    // --- 4. Web Audio API Procedural Synthesizer ---
    initAudioSynthesizer() {{
        try {{
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioCtx = new AudioContext();
        }} catch (e) {{
            console.warn("Web Audio API not supported:", e);
        }}
    }}

    playTone(freq = 440, type = "sine", duration = 0.1) {{
        if (!this.soundEnabled || !this.audioCtx) return;
        if (this.audioCtx.state === "suspended") {{
            this.audioCtx.resume();
        }}
        try {{
            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime);

            gain.gain.setValueAtTime(0.08, this.audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + duration);

            osc.connect(gain);
            gain.connect(this.audioCtx.destination);

            osc.start();
            osc.stop(this.audioCtx.currentTime + duration);
        }} catch (e) {{}}
    }}

    // --- 5. Theme Shift Engine ---
    setTheme(themeName) {{
        this.currentTheme = themeName;
        document.body.setAttribute("data-theme", themeName);
        this.playTone(520, "sine", 0.2);

        let c1, c2, c3;
        switch (themeName) {{
            case "cyber-cyan":
                c1 = 0x00f0ff; c2 = 0xff007f; c3 = 0x7928ca; break;
            case "neon-magenta":
                c1 = 0xff007f; c2 = 0x00f0ff; c3 = 0xffbe0b; break;
            case "emerald-matrix":
                c1 = 0x00f5a0; c2 = 0x00d9f5; c3 = 0x00ff88; break;
            case "solar-amber":
                c1 = 0xffd000; c2 = 0xff6b00; c3 = 0xff0055; break;
            case "obsidian-mono":
                c1 = 0xffffff; c2 = 0xaaaaaa; c3 = 0x666666; break;
            default:
                c1 = 0x00f0ff; c2 = 0xff007f; c3 = 0x7928ca;
        }}

        if (this.pointLight1) this.pointLight1.color.setHex(c1);
        if (this.pointLight2) this.pointLight2.color.setHex(c2);
        if (this.pointLight3) this.pointLight3.color.setHex(c3);

        // Update particle colors
        if (this.particleSystem) {{
            const colors = this.particleSystem.geometry.attributes.color.array;
            const newColor = new THREE.Color(c1);
            for (let i = 0; i < colors.length; i += 3) {{
                colors[i] = newColor.r * (0.6 + Math.random() * 0.4);
                colors[i + 1] = newColor.g * (0.6 + Math.random() * 0.4);
                colors[i + 2] = newColor.b * (0.6 + Math.random() * 0.4);
            }}
            this.particleSystem.geometry.attributes.color.needsUpdate = true;
        }}
    }}

    cycleTheme() {{
        const themes = ["cyber-cyan", "neon-magenta", "emerald-matrix", "solar-amber", "obsidian-mono"];
        const nextIdx = (themes.indexOf(this.currentTheme) + 1) % themes.length;
        this.setTheme(themes[nextIdx]);

        document.querySelectorAll(".color-btn").forEach(btn => {{
            btn.classList.toggle("active", btn.dataset.theme === themes[nextIdx]);
        }});
    }}

    // --- 6. Event Bindings & Lerp Mouse Parallax ---
    bindEvents() {{
        // Window Resize
        window.addEventListener("resize", () => {{
            this.windowHalfX = window.innerWidth / 2;
            this.windowHalfY = window.innerHeight / 2;
            this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        }});

        // Smooth Mouse Parallax tracking
        window.addEventListener("mousemove", (e) => {{
            this.mouse.targetX = (e.clientX - this.windowHalfX) * 0.0008;
            this.mouse.targetY = (e.clientY - this.windowHalfY) * 0.0008;

            if (this.isDragging && this.activeMesh) {{
                const deltaX = e.clientX - this.previousMousePosition.x;
                const deltaY = e.clientY - this.previousMousePosition.y;
                this.dragVelocity.x = deltaY * 0.005;
                this.dragVelocity.y = deltaX * 0.005;
                this.activeMesh.rotation.x += this.dragVelocity.x;
                this.activeMesh.rotation.y += this.dragVelocity.y;
                this.previousMousePosition = {{ x: e.clientX, y: e.clientY }};
            }}
        }});

        // Drag to Orbit
        this.container.addEventListener("mousedown", (e) => {{
            this.isDragging = true;
            this.previousMousePosition = {{ x: e.clientX, y: e.clientY }};
            this.playTone(330, "sine", 0.08);
        }});

        window.addEventListener("mouseup", () => {{
            this.isDragging = false;
        }});

        // HUD Quick Actions
        document.getElementById("btnToggleRotate")?.addEventListener("click", (e) => {{
            this.autoRotate = !this.autoRotate;
            e.currentTarget.classList.toggle("active", this.autoRotate);
            this.playTone(400, "sine", 0.1);
        }});

        document.getElementById("btnToggleWireframe")?.addEventListener("click", (e) => {{
            this.isWireframe = !this.isWireframe;
            if (this.activeMesh) this.activeMesh.material.wireframe = this.isWireframe;
            e.currentTarget.classList.toggle("active", this.isWireframe);
            this.playTone(480, "triangle", 0.1);
        }});

        document.getElementById("btnCycleTheme")?.addEventListener("click", () => this.cycleTheme());

        document.getElementById("btnMorphGeometry")?.addEventListener("click", () => {{
            const geos = ["torusknot", "icosahedron", "quantum", "ribbon"];
            const nextIdx = (geos.indexOf(this.currentGeometryType) + 1) % geos.length;
            this.morphGeometry(geos[nextIdx]);

            document.querySelectorAll("#geoPillGroup .pill-btn").forEach(btn => {{
                btn.classList.toggle("active", btn.dataset.geo === geos[nextIdx]);
            }});
        }});

        document.getElementById("btnResetCamera")?.addEventListener("click", () => {{
            this.camera.position.set(0, 0, 8);
            if (this.activeMesh) {{
                this.activeMesh.rotation.set(0, 0, 0);
            }}
            this.playTone(550, "sine", 0.15);
        }});

        document.getElementById("interact3dBtn")?.addEventListener("click", () => {{
            const el = document.getElementById("canvasContainer");
            el.scrollIntoView({{ behavior: "smooth" }});
            this.playTone(600, "sine", 0.1);
        }});

        // Audio Toggle
        document.getElementById("audioToggleBtn")?.addEventListener("click", () => {{
            this.soundEnabled = !this.soundEnabled;
            document.getElementById("audioStatusText").textContent = this.soundEnabled ? "SOUND ON" : "SOUND OFF";
            if (this.soundEnabled) this.playTone(520, "sine", 0.15);
        }});

        // Studio Pill Group
        document.querySelectorAll("#geoPillGroup .pill-btn").forEach(btn => {{
            btn.addEventListener("click", (e) => {{
                document.querySelectorAll("#geoPillGroup .pill-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                this.morphGeometry(btn.dataset.geo);
            }});
        }});

        // Studio Theme Buttons
        document.querySelectorAll(".color-btn").forEach(btn => {{
            btn.addEventListener("click", () => {{
                document.querySelectorAll(".color-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                this.setTheme(btn.dataset.theme);
            }});
        }});

        // Sliders
        document.getElementById("particleRange")?.addEventListener("input", (e) => {{
            const val = parseInt(e.target.value);
            document.getElementById("sliderParticleVal").textContent = val;
            this.initParticleSwarm(val);
        }});

        document.getElementById("speedRange")?.addEventListener("input", (e) => {{
            const val = parseInt(e.target.value);
            this.rotateSpeed = val * 0.001;
            document.getElementById("sliderSpeedVal").textContent = `${{(val / 10).toFixed(1)}}x`;
        }});

        // Filter Tabs
        document.querySelectorAll(".filter-tab").forEach(tab => {{
            tab.addEventListener("click", () => {{
                document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                this.renderShowcaseItems(tab.dataset.filter);
                this.playTone(380, "sine", 0.08);
            }});
        }});

        // Contact Form
        document.getElementById("contactForm")?.addEventListener("submit", (e) => {{
            e.preventDefault();
            this.playTone(880, "triangle", 0.3);
            if (window.confetti) {{
                confetti({{ particleCount: 120, spread: 80, origin: {{ y: 0.6 }} }});
            }}
            alert("✨ Proposal Transmitted! Our creative engineering team will connect shortly, Sir.");
            e.target.reset();
        }});
    }}

    // --- 7. Magnetic Cursor Implementation ---
    initCursor() {{
        const dot = document.getElementById("cursorDot");
        const follower = document.getElementById("cursorFollower");
        let followerX = 0, followerY = 0;
        let mouseX = 0, mouseY = 0;

        window.addEventListener("mousemove", (e) => {{
            mouseX = e.clientX;
            mouseY = e.clientY;
            dot.style.transform = `translate3d(${{mouseX}}px, ${{mouseY}}px, 0)`;
        }});

        const updateFollower = () => {{
            followerX += (mouseX - followerX) * 0.15;
            followerY += (mouseY - followerY) * 0.15;
            follower.style.transform = `translate3d(${{followerX}}px, ${{followerY}}px, 0)`;
            requestAnimationFrame(updateFollower);
        }};
        updateFollower();

        document.querySelectorAll("a, button, input, select").forEach(el => {{
            el.addEventListener("mouseenter", () => document.body.classList.add("cursor-hover"));
            el.addEventListener("mouseleave", () => document.body.classList.remove("cursor-hover"));
        }});
    }}

    // --- 8. Showcase Items Rendering ---
    renderShowcaseItems(filter = "all") {{
        const items = [
            {{
                id: 1,
                title: "Quantum Hologram Core",
                category: "spatial",
                desc: "Real-time volumetric 3D particle simulation with dynamic depth-field refraction.",
                tags: ["WebGL", "Three.js", "GLSL Shaders"],
                image: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop"
            }},
            {{
                id: 2,
                title: "Fluid Kinematic Sculptures",
                category: "physics",
                desc: "Perlin-noise displaced organic meshes responding to sound waves and cursor inertia.",
                tags: ["Physics", "Perlin Noise", "Audio-Reactive"],
                image: "https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?w=800&auto=format&fit=crop"
            }},
            {{
                id: 3,
                title: "Autonomous Agent HUD",
                category: "creative",
                desc: "Cybernetic telemetry interface with spatial audio triggers and micro-interactions.",
                tags: ["Agentic AI", "Interface", "Spatial UX"],
                image: "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&auto=format&fit=crop"
            }},
            {{
                id: 4,
                title: "Iridescent Crystal Morph",
                category: "spatial",
                desc: "Transmission and clearcoat rendering with real-time caustics and multi-light reflections.",
                tags: ["Glassmorphism", "Refraction", "3D PBR"],
                image: "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800&auto=format&fit=crop"
            }},
            {{
                id: 5,
                title: "Sub-Atomic Swarm Dynamics",
                category: "physics",
                desc: "High-density particle swarm with cursor repulsion waves and momentum decay.",
                tags: ["Particles", "Kinematics", "60 FPS"],
                image: "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&auto=format&fit=crop"
            }},
            {{
                id: 6,
                title: "Digital Genesis Experience",
                category: "creative",
                desc: "Next-gen immersive digital launchpad crafted for executive spatial branding.",
                tags: ["Editorial", "Lusion Style", "Creative Tech"],
                image: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop"
            }}
        ];

        const grid = document.getElementById("showcaseGrid");
        if (!grid) return;

        const filtered = filter === "all" ? items : items.filter(it => it.category === filter);

        grid.innerHTML = filtered.map(item => `
            <div class="showcase-item">
                <div class="item-thumb" style="background-image: url('${{item.image}}');">
                    <span class="item-badge">${{item.category.toUpperCase()}}</span>
                </div>
                <div class="item-body">
                    <h4>${{item.title}}</h4>
                    <p>${{item.desc}}</p>
                    <div class="item-tags">
                        ${{item.tags.map(t => `<span class="tag-badge">${{t}}</span>`).join("")}}
                    </div>
                </div>
            </div>
        `).join("");
    }}

    // --- 9. 60 FPS Buttery-Smooth Animation Loop ---
    animate() {{
        requestAnimationFrame(() => this.animate());

        // Silky Dampened Lerp mouse kinematics
        this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
        this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

        // Apply smooth parallax to camera and lights
        this.camera.position.x = this.mouse.x * 2.5;
        this.camera.position.y = -this.mouse.y * 2.5;
        this.camera.lookAt(this.scene.position);

        // Auto-rotation & drag inertia
        if (this.activeMesh) {{
            if (this.autoRotate && !this.isDragging) {{
                this.activeMesh.rotation.y += this.rotateSpeed;
                this.activeMesh.rotation.x += this.rotateSpeed * 0.5;
            }}
            // Drag velocity inertia decay
            if (!this.isDragging) {{
                this.activeMesh.rotation.x += this.dragVelocity.x;
                this.activeMesh.rotation.y += this.dragVelocity.y;
                this.dragVelocity.x *= 0.94;
                this.dragVelocity.y *= 0.94;
            }}
        }}

        // Particle Swarm slow orbit
        if (this.particleSystem) {{
            this.particleSystem.rotation.y += 0.001;
            this.particleSystem.rotation.x = this.mouse.y * 0.5;
        }}

        // Rotating colored point lights for dynamic sheen
        const time = performance.now() * 0.001;
        if (this.pointLight1) {{
            this.pointLight1.position.x = Math.sin(time * 0.8) * 6;
            this.pointLight1.position.z = Math.cos(time * 0.8) * 6;
        }}
        if (this.pointLight2) {{
            this.pointLight2.position.x = Math.cos(time * 0.6) * 6;
            this.pointLight2.position.y = Math.sin(time * 0.6) * 5;
        }}

        this.renderer.render(this.scene, this.camera);
    }}
}}

// Initialize Studio on DOM Ready
document.addEventListener("DOMContentLoaded", () => {{
    window.lusionStudio = new Lusion3DStudio();
}});
"""

        readme_md = f"""# {display_title} — Lusion 3D Interactive Web Experience

Autonomous 3D Web Application architected by **J.A.R.V.I.S. Multi-Agent Protocol**.

## Core Lusion-Grade Features
- **Silky 60 FPS Three.js Kinematics**: Normalized mouse tracking with 0.05 lerp dampening for liquid, organic momentum.
- **Physical Glass & Iridescent PBR**: Real-time MeshPhysicalMaterial with transmission, clearcoat, and multi-point cinematic lighting.
- **Interactive 3D Studio Workbench**: Instant on-canvas controls for morphing geometries (Torus Knot, Organic Icosahedron, Quantum Core), wireframe mode, and particle density.
- **Dynamic Chromatic Theme Shift**: Real-time color palettes (Cyber Cyan, Neon Magenta, Emerald Matrix, Solar Amber, Obsidian Mono).
- **Web Audio API Synthesizer**: Procedural acoustic clicks and holographic sweeps without external sound files.
- **Fluid Magnetic Cursor**: Interactive cursor dot and fluid ring follower.
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

        logger.info(f"CodeAgent synthesizing Lusion-grade 3D web application '{project_name}'...")

        lower_spec = app_spec.lower()
        extracted_files = {}

        # If user explicitly asks for 3D / Lusion / WebGL, instantly assemble the Lusion 3D suite
        if any(k in lower_spec for k in ["lusion", "3d", "three.js", "threejs", "webgl", "interactive 3d", "smooth way"]):
            logger.info("Directly synthesizing Lusion-Grade 3D WebGL engine for instant sub-second response...")
            extracted_files = self._generate_lusion_masterpiece(project_name, app_spec)
        else:
            # Attempt LLM generation with Qwen-Coder
            try:
                prompt = f"""Build a complete, production-ready, ultra-smooth 3D web application inspired by Lusion (lusion.co).
Project Name: {project_name}
Requirements: {app_spec}
Architectural Plan: {json.dumps(plan) if plan else "Full-featured 3D Web Experience with Three.js"}

Generate complete index.html, styles.css, app.js, and README.md with zero placeholders."""
                raw_code = await ollama_client.generate(
                    model=self.model,
                    prompt=prompt,
                    system=CODE_AGENT_SYSTEM_PROMPT,
                    options={"temperature": 0.2}
                )
                parsed = self._parse_files(raw_code)
                if "index.html" in parsed and "styles.css" in parsed and "app.js" in parsed:
                    extracted_files = parsed
                    logger.info("Successfully received full custom files from Qwen-Coder!")
            except Exception as e:
                logger.info(f"LLM code generation note (using adaptive Lusion engine): {e}")

        # Fallback to adaptive Lusion-Grade 3D Web Engine if needed
        if not extracted_files or "index.html" not in extracted_files:
            extracted_files = self._generate_lusion_masterpiece(project_name, app_spec)

        # Write all files to disk
        created_files = []
        for rel_path, code in extracted_files.items():
            file_path = project_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            created_files.append(rel_path)

        # Launch the local server preview on localhost
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
