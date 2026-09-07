import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer();
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

const ambientLight = new THREE.AmbientLight(0x404040);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
directionalLight.position.set(1, 1, 1);
scene.add(directionalLight);

const pointLight1 = new THREE.PointLight(0x00f0ff, 0.5, 100);
pointLight1.position.set(10, 10, 10);
scene.add(pointLight1);

const pointLight2 = new THREE.PointLight(0xff007f, 0.5, 100);
pointLight2.position.set(-10, 10, -10);
scene.add(pointLight2);

const pointLight3 = new THREE.PointLight(0xffbe0b, 0.5, 100);
pointLight3.position.set(0, -10, 0);
scene.add(pointLight3);

const geometry = new THREE.TorusKnotGeometry(1, 0.4, 128, 16);
const material = new THREE.MeshPhysicalMaterial({
    color: 0xff0000,
    roughness: 0.1,
    metalness: 0.9,
    clearcoat: 1.0,
    transmission: 0.5
});
const torusKnot = new THREE.Mesh(geometry, material);
scene.add(torusKnot);

camera.position.z = 5;

const controls = new OrbitControls(camera, renderer.domElement);

let currentRotX = 0;
let currentRotY = 0;
let targetRotX = 0;
let targetRotY = 0;

function animate() {
    requestAnimationFrame(animate);

    currentRotX += (targetRotX - currentRotX) * 0.05;
    currentRotY += (targetRotY - currentRotY) * 0.05;

    torusKnot.rotation.x = currentRotX;
    torusKnot.rotation.y = currentRotY;

    controls.update();
    renderer.render(scene, camera);
}

animate();

window.addEventListener('mousemove', (event) => {
    targetRotX = (event.clientX / window.innerWidth - 0.5) * 0.1;
    targetRotY = (event.clientY / window.innerHeight - 0.5) * 0.1;
});

const cursor = document.createElement('div');
cursor.classList.add('cursor');
document.body.appendChild(cursor);

const hud = document.createElement('div');
hud.classList.add('hud');
hud.innerHTML = `
    <button id="wireframe">Wireframe</button>
    <input type="range" id="particleCount" min="1000" max="3000" value="1500">
    <button id="autoRotate">Auto-Rotate</button>
    <button id="resetCamera">Reset Camera</button>
`;
document.body.appendChild(hud);

document.getElementById('wireframe').addEventListener('click', () => {
    torusKnot.material.wireframe = !torusKnot.material.wireframe;
});

document.getElementById('particleCount').addEventListener('input', (event) => {
    const particleCount = parseInt(event.target.value);
    // Implement particle system here
});

document.getElementById('autoRotate').addEventListener('click', () => {
    controls.autoRotate = !controls.autoRotate;
});

document.getElementById('resetCamera').addEventListener('click', () => {
    camera.position.set(5, 5, 5);
    controls.reset();
});

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});