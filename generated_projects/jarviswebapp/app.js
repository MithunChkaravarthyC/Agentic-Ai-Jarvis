const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('canvas') });
renderer.setSize(window.innerWidth, window.innerHeight);

const currentRot = new THREE.Vector3(0, 0, 0);
const targetRot = new THREE.Vector3(0, 0, 0);
const lerpFactor = 0.05;

const ambientLight = new THREE.AmbientLight(0x101010);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
directionalLight.position.set(1, 1, 1);
scene.add(directionalLight);

const material = new THREE.MeshPhysicalMaterial({
    roughness: 0.15,
    metalness: 0.85,
    clearcoat: 1.0,
    transmission: 0.6,
    color: 0x00ffff
});

const torusKnot = new THREE.TorusKnotGeometry(0.5, 0.2, 100, 16);
const torusKnotMesh = new THREE.Mesh(torusKnot, material);
scene.add(torusKnotMesh);

const icosahedronGeometry = new THREE.IcosahedronGeometry(1, 4);
const icosahedronMesh = new THREE.Mesh(icosahedronGeometry, material);
scene.add(icosahedronMesh);

const ribbons = [];
for (let i = 0; i < 10; i++) {
    const ribbonGeometry = new THREE.BufferGeometry();
    const ribbonPoints = [];
    for (let j = 0; j < 100; j++) {
        ribbonPoints.push(new THREE.Vector3(
            Math.sin(j * 0.1) * Math.cos(i * 0.1),
            Math.sin(j * 0.1) * Math.sin(i * 0.1),
            Math.cos(j * 0.1)
        ));
    }
    ribbonGeometry.setFromPoints(ribbonPoints);
    const ribbonMesh = new THREE.Line(ribbonGeometry, material);
    scene.add(ribbonMesh);
    ribbons.push(ribbonMesh);
}

const particleCount = 1500;
const particles = new THREE.BufferGeometry();
const positions = new Float32Array(particleCount * 3);
for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 10;
    positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
    positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
}
particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
const particleMaterial = new THREE.PointsMaterial({ color: 0xffffff, size: 0.02 });
const particleCloud = new THREE.Points(particles, particleMaterial);
scene.add(particleCloud);

camera.position.z = 5;

const clock = new THREE.Clock();
let wireframe = false;

document.getElementById('wireframeToggle').addEventListener('click', () => {
    wireframe = !wireframe;
    torusKnotMesh.material.wireframe = wireframe;
    icosahedronMesh.material.wireframe = wireframe;
    for (const ribbon of ribbons) {
        ribbon.material.wireframe = wireframe;
    }
});

document.getElementById('particleSlider').addEventListener('input', (e) => {
    particleCount = e.target.value;
    positions.length = particleCount * 3;
    for (let i = 0; i < particleCount; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 10;
        positions[i * 3 + 1] = (Math.random() - 0.5) * 10;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
});

document.getElementById('themeSwitcher').addEventListener('click', () => {
    const body = document.body;
    if (body.style.backgroundColor === '#050508') {
        body.style.backgroundColor = '#1e1e1e';
        body.style.color = '#ffffff';
    } else {
        body.style.backgroundColor = '#050508';
        body.style.color = '#ffffff';
    }
});

function animate() {
    const delta = clock.getDelta();
    currentRot.x += (targetRot.x - currentRot.x) * lerpFactor * delta;
    currentRot.y += (targetRot.y - currentRot.y) * lerpFactor * delta;
    currentRot.z += (targetRot.z - currentRot.z) * lerpFactor * delta;

    torusKnotMesh.rotation.set(currentRot.x, currentRot.y, currentRot.z);
    icosahedronMesh.rotation.set(currentRot.x, currentRot.y, currentRot.z);
    for (const ribbon of ribbons) {
        ribbon.rotation.set(currentRot.x, currentRot.y, currentRot.z);
    }

    const mouse = new THREE.Vector2();
    document.addEventListener('mousemove', (e) => {
        mouse.x = (e.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(e.clientY / window.innerHeight) * 2 + 1;
    });

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(scene.children);
    if (intersects.length > 0) {
        targetRot.x += intersects[0].point.y * 0.01;
        targetRot.y += intersects[0].point.x * 0.01;
        targetRot.z += intersects[0].point.z * 0.01;
    }

    const particleSystem = new THREE.PointsMaterial({ color: 0xffffff, size: 0.02 });
    const particleCloud = new THREE.Points(particles, particleSystem);
    scene.add(particleCloud);

    renderer.render(scene, camera);
    requestAnimationFrame(animate);
}

animate();