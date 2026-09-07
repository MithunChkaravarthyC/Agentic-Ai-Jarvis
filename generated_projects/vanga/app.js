// ==========================================================================
// LUSION-GRADE THREE.JS CREATIVE ENGINE & KINEMATICS
// ==========================================================================

class Lusion3DStudio {
    constructor() {
        this.container = document.getElementById("canvasContainer");
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.activeMesh = null;
        this.particleSystem = null;
        this.lights = [];

        // Smooth Lerp Mouse Kinematics (Factor: 0.05 for silky organic momentum)
        this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
        this.windowHalfX = window.innerWidth / 2;
        this.windowHalfY = window.innerHeight / 2;

        // Interaction State
        this.isDragging = false;
        this.previousMousePosition = { x: 0, y: 0 };
        this.dragVelocity = { x: 0, y: 0 };
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
    }

    // --- 1. Three.js Scene Setup ---
    initThree() {
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.FogExp2(0x050508, 0.04);

        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(0, 0, 8);

        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
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
    }

    // --- 2. Procedural Mesh Generation ---
    getMaterial() {
        return new THREE.MeshPhysicalMaterial({
            color: 0x111625,
            emissive: 0x050c1e,
            roughness: 0.12,
            metalness: 0.85,
            clearcoat: 1.0,
            clearcoatRoughness: 0.1,
            reflectivity: 0.9,
            wireframe: this.isWireframe
        });
    }

    createGeometry(type) {
        switch (type) {
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
        }
    }

    initGeometries() {
        const geo = this.createGeometry(this.currentGeometryType);
        const mat = this.getMaterial();
        this.activeMesh = new THREE.Mesh(geo, mat);
        this.scene.add(this.activeMesh);
    }

    morphGeometry(type) {
        this.playTone(440, "triangle", 0.15);
        this.currentGeometryType = type;
        document.getElementById("activeGeoLabel").textContent = type.charAt(0).toUpperCase() + type.slice(1);

        if (this.activeMesh) {
            const oldRotX = this.activeMesh.rotation.x;
            const oldRotY = this.activeMesh.rotation.y;
            this.scene.remove(this.activeMesh);
            this.activeMesh.geometry.dispose();

            const newGeo = this.createGeometry(type);
            this.activeMesh = new THREE.Mesh(newGeo, this.getMaterial());
            this.activeMesh.rotation.x = oldRotX;
            this.activeMesh.rotation.y = oldRotY;
            this.scene.add(this.activeMesh);
        }
    }

    // --- 3. Interactive Floating Particle Swarm ---
    initParticleSwarm(count = 1800) {
        if (this.particleSystem) {
            this.scene.remove(this.particleSystem);
            this.particleSystem.geometry.dispose();
        }

        const positions = new Float32Array(count * 3);
        const colors = new Float32Array(count * 3);
        const color = new THREE.Color(0x00f0ff);

        for (let i = 0; i < count; i++) {
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
        }

        const geo = new THREE.BufferGeometry();
        geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
        geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));

        const mat = new THREE.PointsMaterial({
            size: 0.05,
            vertexColors: true,
            transparent: true,
            opacity: 0.75,
            blending: THREE.AdditiveBlending
        });

        this.particleSystem = new THREE.Points(geo, mat);
        this.scene.add(this.particleSystem);
        document.getElementById("particleCountLabel").textContent = `${count.toLocaleString()} Active`;
    }

    // --- 4. Web Audio API Procedural Synthesizer ---
    initAudioSynthesizer() {
        try {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioCtx = new AudioContext();
        } catch (e) {
            console.warn("Web Audio API not supported:", e);
        }
    }

    playTone(freq = 440, type = "sine", duration = 0.1) {
        if (!this.soundEnabled || !this.audioCtx) return;
        if (this.audioCtx.state === "suspended") {
            this.audioCtx.resume();
        }
        try {
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
        } catch (e) {}
    }

    // --- 5. Theme Shift Engine ---
    setTheme(themeName) {
        this.currentTheme = themeName;
        document.body.setAttribute("data-theme", themeName);
        this.playTone(520, "sine", 0.2);

        let c1, c2, c3;
        switch (themeName) {
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
        }

        if (this.pointLight1) this.pointLight1.color.setHex(c1);
        if (this.pointLight2) this.pointLight2.color.setHex(c2);
        if (this.pointLight3) this.pointLight3.color.setHex(c3);

        // Update particle colors
        if (this.particleSystem) {
            const colors = this.particleSystem.geometry.attributes.color.array;
            const newColor = new THREE.Color(c1);
            for (let i = 0; i < colors.length; i += 3) {
                colors[i] = newColor.r * (0.6 + Math.random() * 0.4);
                colors[i + 1] = newColor.g * (0.6 + Math.random() * 0.4);
                colors[i + 2] = newColor.b * (0.6 + Math.random() * 0.4);
            }
            this.particleSystem.geometry.attributes.color.needsUpdate = true;
        }
    }

    cycleTheme() {
        const themes = ["cyber-cyan", "neon-magenta", "emerald-matrix", "solar-amber", "obsidian-mono"];
        const nextIdx = (themes.indexOf(this.currentTheme) + 1) % themes.length;
        this.setTheme(themes[nextIdx]);

        document.querySelectorAll(".color-btn").forEach(btn => {
            btn.classList.toggle("active", btn.dataset.theme === themes[nextIdx]);
        });
    }

    // --- 6. Event Bindings & Lerp Mouse Parallax ---
    bindEvents() {
        // Window Resize
        window.addEventListener("resize", () => {
            this.windowHalfX = window.innerWidth / 2;
            this.windowHalfY = window.innerHeight / 2;
            this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        });

        // Smooth Mouse Parallax tracking
        window.addEventListener("mousemove", (e) => {
            this.mouse.targetX = (e.clientX - this.windowHalfX) * 0.0008;
            this.mouse.targetY = (e.clientY - this.windowHalfY) * 0.0008;

            if (this.isDragging && this.activeMesh) {
                const deltaX = e.clientX - this.previousMousePosition.x;
                const deltaY = e.clientY - this.previousMousePosition.y;
                this.dragVelocity.x = deltaY * 0.005;
                this.dragVelocity.y = deltaX * 0.005;
                this.activeMesh.rotation.x += this.dragVelocity.x;
                this.activeMesh.rotation.y += this.dragVelocity.y;
                this.previousMousePosition = { x: e.clientX, y: e.clientY };
            }
        });

        // Drag to Orbit
        this.container.addEventListener("mousedown", (e) => {
            this.isDragging = true;
            this.previousMousePosition = { x: e.clientX, y: e.clientY };
            this.playTone(330, "sine", 0.08);
        });

        window.addEventListener("mouseup", () => {
            this.isDragging = false;
        });

        // HUD Quick Actions
        document.getElementById("btnToggleRotate")?.addEventListener("click", (e) => {
            this.autoRotate = !this.autoRotate;
            e.currentTarget.classList.toggle("active", this.autoRotate);
            this.playTone(400, "sine", 0.1);
        });

        document.getElementById("btnToggleWireframe")?.addEventListener("click", (e) => {
            this.isWireframe = !this.isWireframe;
            if (this.activeMesh) this.activeMesh.material.wireframe = this.isWireframe;
            e.currentTarget.classList.toggle("active", this.isWireframe);
            this.playTone(480, "triangle", 0.1);
        });

        document.getElementById("btnCycleTheme")?.addEventListener("click", () => this.cycleTheme());

        document.getElementById("btnMorphGeometry")?.addEventListener("click", () => {
            const geos = ["torusknot", "icosahedron", "quantum", "ribbon"];
            const nextIdx = (geos.indexOf(this.currentGeometryType) + 1) % geos.length;
            this.morphGeometry(geos[nextIdx]);

            document.querySelectorAll("#geoPillGroup .pill-btn").forEach(btn => {
                btn.classList.toggle("active", btn.dataset.geo === geos[nextIdx]);
            });
        });

        document.getElementById("btnResetCamera")?.addEventListener("click", () => {
            this.camera.position.set(0, 0, 8);
            if (this.activeMesh) {
                this.activeMesh.rotation.set(0, 0, 0);
            }
            this.playTone(550, "sine", 0.15);
        });

        document.getElementById("interact3dBtn")?.addEventListener("click", () => {
            const el = document.getElementById("canvasContainer");
            el.scrollIntoView({ behavior: "smooth" });
            this.playTone(600, "sine", 0.1);
        });

        // Audio Toggle
        document.getElementById("audioToggleBtn")?.addEventListener("click", () => {
            this.soundEnabled = !this.soundEnabled;
            document.getElementById("audioStatusText").textContent = this.soundEnabled ? "SOUND ON" : "SOUND OFF";
            if (this.soundEnabled) this.playTone(520, "sine", 0.15);
        });

        // Studio Pill Group
        document.querySelectorAll("#geoPillGroup .pill-btn").forEach(btn => {
            btn.addEventListener("click", (e) => {
                document.querySelectorAll("#geoPillGroup .pill-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                this.morphGeometry(btn.dataset.geo);
            });
        });

        // Studio Theme Buttons
        document.querySelectorAll(".color-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".color-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                this.setTheme(btn.dataset.theme);
            });
        });

        // Sliders
        document.getElementById("particleRange")?.addEventListener("input", (e) => {
            const val = parseInt(e.target.value);
            document.getElementById("sliderParticleVal").textContent = val;
            this.initParticleSwarm(val);
        });

        document.getElementById("speedRange")?.addEventListener("input", (e) => {
            const val = parseInt(e.target.value);
            this.rotateSpeed = val * 0.001;
            document.getElementById("sliderSpeedVal").textContent = `${(val / 10).toFixed(1)}x`;
        });

        // Filter Tabs
        document.querySelectorAll(".filter-tab").forEach(tab => {
            tab.addEventListener("click", () => {
                document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                this.renderShowcaseItems(tab.dataset.filter);
                this.playTone(380, "sine", 0.08);
            });
        });

        // Contact Form
        document.getElementById("contactForm")?.addEventListener("submit", (e) => {
            e.preventDefault();
            this.playTone(880, "triangle", 0.3);
            if (window.confetti) {
                confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 } });
            }
            alert("✨ Proposal Transmitted! Our creative engineering team will connect shortly, Sir.");
            e.target.reset();
        });
    }

    // --- 7. Magnetic Cursor Implementation ---
    initCursor() {
        const dot = document.getElementById("cursorDot");
        const follower = document.getElementById("cursorFollower");
        let followerX = 0, followerY = 0;
        let mouseX = 0, mouseY = 0;

        window.addEventListener("mousemove", (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            dot.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0)`;
        });

        const updateFollower = () => {
            followerX += (mouseX - followerX) * 0.15;
            followerY += (mouseY - followerY) * 0.15;
            follower.style.transform = `translate3d(${followerX}px, ${followerY}px, 0)`;
            requestAnimationFrame(updateFollower);
        };
        updateFollower();

        document.querySelectorAll("a, button, input, select").forEach(el => {
            el.addEventListener("mouseenter", () => document.body.classList.add("cursor-hover"));
            el.addEventListener("mouseleave", () => document.body.classList.remove("cursor-hover"));
        });
    }

    // --- 8. Showcase Items Rendering ---
    renderShowcaseItems(filter = "all") {
        const items = [
            {
                id: 1,
                title: "Quantum Hologram Core",
                category: "spatial",
                desc: "Real-time volumetric 3D particle simulation with dynamic depth-field refraction.",
                tags: ["WebGL", "Three.js", "GLSL Shaders"],
                image: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop"
            },
            {
                id: 2,
                title: "Fluid Kinematic Sculptures",
                category: "physics",
                desc: "Perlin-noise displaced organic meshes responding to sound waves and cursor inertia.",
                tags: ["Physics", "Perlin Noise", "Audio-Reactive"],
                image: "https://images.unsplash.com/photo-1634017839464-5c339ebe3cb4?w=800&auto=format&fit=crop"
            },
            {
                id: 3,
                title: "Autonomous Agent HUD",
                category: "creative",
                desc: "Cybernetic telemetry interface with spatial audio triggers and micro-interactions.",
                tags: ["Agentic AI", "Interface", "Spatial UX"],
                image: "https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=800&auto=format&fit=crop"
            },
            {
                id: 4,
                title: "Iridescent Crystal Morph",
                category: "spatial",
                desc: "Transmission and clearcoat rendering with real-time caustics and multi-light reflections.",
                tags: ["Glassmorphism", "Refraction", "3D PBR"],
                image: "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800&auto=format&fit=crop"
            },
            {
                id: 5,
                title: "Sub-Atomic Swarm Dynamics",
                category: "physics",
                desc: "High-density particle swarm with cursor repulsion waves and momentum decay.",
                tags: ["Particles", "Kinematics", "60 FPS"],
                image: "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&auto=format&fit=crop"
            },
            {
                id: 6,
                title: "Digital Genesis Experience",
                category: "creative",
                desc: "Next-gen immersive digital launchpad crafted for executive spatial branding.",
                tags: ["Editorial", "Lusion Style", "Creative Tech"],
                image: "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop"
            }
        ];

        const grid = document.getElementById("showcaseGrid");
        if (!grid) return;

        const filtered = filter === "all" ? items : items.filter(it => it.category === filter);

        grid.innerHTML = filtered.map(item => `
            <div class="showcase-item">
                <div class="item-thumb" style="background-image: url('${item.image}');">
                    <span class="item-badge">${item.category.toUpperCase()}</span>
                </div>
                <div class="item-body">
                    <h4>${item.title}</h4>
                    <p>${item.desc}</p>
                    <div class="item-tags">
                        ${item.tags.map(t => `<span class="tag-badge">${t}</span>`).join("")}
                    </div>
                </div>
            </div>
        `).join("");
    }

    // --- 9. 60 FPS Buttery-Smooth Animation Loop ---
    animate() {
        requestAnimationFrame(() => this.animate());

        // Silky Dampened Lerp mouse kinematics
        this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.05;
        this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.05;

        // Apply smooth parallax to camera and lights
        this.camera.position.x = this.mouse.x * 2.5;
        this.camera.position.y = -this.mouse.y * 2.5;
        this.camera.lookAt(this.scene.position);

        // Auto-rotation & drag inertia
        if (this.activeMesh) {
            if (this.autoRotate && !this.isDragging) {
                this.activeMesh.rotation.y += this.rotateSpeed;
                this.activeMesh.rotation.x += this.rotateSpeed * 0.5;
            }
            // Drag velocity inertia decay
            if (!this.isDragging) {
                this.activeMesh.rotation.x += this.dragVelocity.x;
                this.activeMesh.rotation.y += this.dragVelocity.y;
                this.dragVelocity.x *= 0.94;
                this.dragVelocity.y *= 0.94;
            }
        }

        // Particle Swarm slow orbit
        if (this.particleSystem) {
            this.particleSystem.rotation.y += 0.001;
            this.particleSystem.rotation.x = this.mouse.y * 0.5;
        }

        // Rotating colored point lights for dynamic sheen
        const time = performance.now() * 0.001;
        if (this.pointLight1) {
            this.pointLight1.position.x = Math.sin(time * 0.8) * 6;
            this.pointLight1.position.z = Math.cos(time * 0.8) * 6;
        }
        if (this.pointLight2) {
            this.pointLight2.position.x = Math.cos(time * 0.6) * 6;
            this.pointLight2.position.y = Math.sin(time * 0.6) * 5;
        }

        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize Studio on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
    window.lusionStudio = new Lusion3DStudio();
});
