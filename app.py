import streamlit as st
import os
import re
import json
import httpx
import asyncio
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Three.js Scene Generator",
    page_icon="🎮",
    layout="wide"
)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "current_scene" not in st.session_state:
    st.session_state.current_scene = None
if "debug_info" not in st.session_state:
    st.session_state.debug_info = {}
if "raw_prompt" not in st.session_state:
    st.session_state.raw_prompt = ""
if "enhanced_prompt" not in st.session_state:
    st.session_state.enhanced_prompt = ""

# Pre-built scenes (keeping the existing code)
def get_rabbit_turtle_scene():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rabbit and Turtle Running on a Hill</title>
        <style>
            body { margin: 0; overflow: hidden; }
            #info {
                position: absolute;
                top: 10px;
                width: 100%;
                text-align: center;
                color: white;
                font-family: Arial, sans-serif;
                pointer-events: none;
                text-shadow: 1px 1px 1px black;
            }
        </style>
    </head>
    <body>
        <div id="info">Rabbit and Turtle Running on a Hill - Use mouse to navigate</div>
        <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
        <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
        <script>
            // Create a scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x87CEEB); // Sky blue background

            // Create a camera
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 5, 10);
            camera.lookAt(0, 0, 0);

            // Create a renderer
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            document.body.appendChild(renderer.domElement);

            // Add orbit controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;

            // Add ambient light
            const ambientLight = new THREE.AmbientLight(0x404040);
            scene.add(ambientLight);

            // Create a directional light
            const light = new THREE.DirectionalLight(0xffffff, 1);
            light.position.set(0, 10, 5);
            light.castShadow = true;
            light.shadow.mapSize.width = 2048;
            light.shadow.mapSize.height = 2048;
            scene.add(light);

            // Create a hill
            const hillGeometry = new THREE.CylinderGeometry(8, 8, 2, 32, 1, false);
            const hillMaterial = new THREE.MeshPhongMaterial({ color: 0x7CFC00 });
            const hill = new THREE.Mesh(hillGeometry, hillMaterial);
            hill.position.y = -1;
            hill.receiveShadow = true;
            scene.add(hill);

            // Create a path around the hill
            const pathGeometry = new THREE.TorusGeometry(6, 0.3, 16, 100);
            const pathMaterial = new THREE.MeshPhongMaterial({ color: 0x8B4513 });
            const path = new THREE.Mesh(pathGeometry, pathMaterial);
            path.rotation.x = Math.PI / 2;
            path.position.y = 0.05;
            path.receiveShadow = true;
            scene.add(path);

            // Create a rabbit using basic geometries
            function createRabbit() {
                const rabbit = new THREE.Group();
                
                // Rabbit body
                const bodyGeometry = new THREE.SphereGeometry(0.5, 16, 16);
                const bodyMaterial = new THREE.MeshPhongMaterial({ color: 0xFFFFFF });
                const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
                body.castShadow = true;
                rabbit.add(body);
                
                // Rabbit head
                const headGeometry = new THREE.SphereGeometry(0.3, 16, 16);
                const headMaterial = new THREE.MeshPhongMaterial({ color: 0xFFFFFF });
                const head = new THREE.Mesh(headGeometry, headMaterial);
                head.position.set(0, 0.4, 0.3);
                head.castShadow = true;
                rabbit.add(head);
                
                // Rabbit ears
                const earGeometry = new THREE.CylinderGeometry(0.05, 0.05, 0.5, 12);
                const earMaterial = new THREE.MeshPhongMaterial({ color: 0xFFCCCC });
                
                const leftEar = new THREE.Mesh(earGeometry, earMaterial);
                leftEar.position.set(-0.1, 0.7, 0.3);
                leftEar.rotation.set(0, 0, -0.2);
                leftEar.castShadow = true;
                rabbit.add(leftEar);
                
                const rightEar = new THREE.Mesh(earGeometry, earMaterial);
                rightEar.position.set(0.1, 0.7, 0.3);
                rightEar.rotation.set(0, 0, 0.2);
                rightEar.castShadow = true;
                rabbit.add(rightEar);
                
                // Rabbit tail
                const tailGeometry = new THREE.SphereGeometry(0.15, 16, 16);
                const tailMaterial = new THREE.MeshPhongMaterial({ color: 0xFFFFFF });
                const tail = new THREE.Mesh(tailGeometry, tailMaterial);
                tail.position.set(0, 0, -0.5);
                tail.castShadow = true;
                rabbit.add(tail);
                
                // Rabbit legs
                const legGeometry = new THREE.CylinderGeometry(0.05, 0.05, 0.4, 12);
                const legMaterial = new THREE.MeshPhongMaterial({ color: 0xFFFFFF });
                
                const frontLeftLeg = new THREE.Mesh(legGeometry, legMaterial);
                frontLeftLeg.position.set(-0.2, -0.4, 0.2);
                frontLeftLeg.castShadow = true;
                rabbit.add(frontLeftLeg);
                
                const frontRightLeg = new THREE.Mesh(legGeometry, legMaterial);
                frontRightLeg.position.set(0.2, -0.4, 0.2);
                frontRightLeg.castShadow = true;
                rabbit.add(frontRightLeg);
                
                const backLeftLeg = new THREE.Mesh(legGeometry, legMaterial);
                backLeftLeg.position.set(-0.2, -0.4, -0.2);
                backLeftLeg.castShadow = true;
                rabbit.add(backLeftLeg);
                
                const backRightLeg = new THREE.Mesh(legGeometry, legMaterial);
                backRightLeg.position.set(0.2, -0.4, -0.2);
                backRightLeg.castShadow = true;
                rabbit.add(backRightLeg);
                
                return rabbit;
            }

            // Create a turtle using basic geometries
            function createTurtle() {
                const turtle = new THREE.Group();
                
                // Turtle shell
                const shellGeometry = new THREE.SphereGeometry(0.5, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2);
                const shellMaterial = new THREE.MeshPhongMaterial({ color: 0x006400 });
                const shell = new THREE.Mesh(shellGeometry, shellMaterial);
                shell.rotation.x = Math.PI / 2;
                shell.castShadow = true;
                turtle.add(shell);
                
                // Turtle head
                const headGeometry = new THREE.SphereGeometry(0.2, 16, 16);
                const headMaterial = new THREE.MeshPhongMaterial({ color: 0x8B4513 });
                const head = new THREE.Mesh(headGeometry, headMaterial);
                head.position.set(0, 0, 0.6);
                head.castShadow = true;
                turtle.add(head);
                
                // Turtle legs
                const legGeometry = new THREE.CylinderGeometry(0.08, 0.08, 0.3, 12);
                const legMaterial = new THREE.MeshPhongMaterial({ color: 0x8B4513 });
                
                const frontLeftLeg = new THREE.Mesh(legGeometry, legMaterial);
                frontLeftLeg.position.set(-0.3, 0, 0.3);
                frontLeftLeg.rotation.x = Math.PI / 2;
                frontLeftLeg.castShadow = true;
                turtle.add(frontLeftLeg);
                
                const frontRightLeg = new THREE.Mesh(legGeometry, legMaterial);
                frontRightLeg.position.set(0.3, 0, 0.3);
                frontRightLeg.rotation.x = Math.PI / 2;
                frontRightLeg.castShadow = true;
                turtle.add(frontRightLeg);
                
                const backLeftLeg = new THREE.Mesh(legGeometry, legMaterial);
                backLeftLeg.position.set(-0.3, 0, -0.3);
                backLeftLeg.rotation.x = Math.PI / 2;
                backLeftLeg.castShadow = true;
                turtle.add(backLeftLeg);
                
                const backRightLeg = new THREE.Mesh(legGeometry, legMaterial);
                backRightLeg.position.set(0.3, 0, -0.3);
                backRightLeg.rotation.x = Math.PI / 2;
                backRightLeg.castShadow = true;
                turtle.add(backRightLeg);
                
                return turtle;
            }

            // Create and position the rabbit and turtle
            const rabbit = createRabbit();
            rabbit.position.set(-4, 0.5, 0);
            rabbit.scale.set(0.8, 0.8, 0.8);
            scene.add(rabbit);

            const turtle = createTurtle();
            turtle.position.set(-2, 0.3, 0);
            turtle.scale.set(0.8, 0.8, 0.8);
            scene.add(turtle);

            // Animation variables
            let rabbitAngle = 0;
            let turtleAngle = Math.PI / 4; // Start the turtle at a different position
            const rabbitSpeed = 0.03;
            const turtleSpeed = 0.01;
            let rabbitHop = 0;

            // Handle window resize
            window.addEventListener('resize', function() {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });

            // Animation loop
            function animate() {
                requestAnimationFrame(animate);

                // Update controls
                controls.update();

                // Update rabbit position - move faster in a circle
                rabbitAngle += rabbitSpeed;
                rabbit.position.x = Math.sin(rabbitAngle) * 6;
                rabbit.position.z = Math.cos(rabbitAngle) * 6;
                rabbit.rotation.y = -rabbitAngle - Math.PI / 2;
                
                // Make the rabbit hop
                rabbitHop += 0.1;
                rabbit.position.y = 0.5 + Math.abs(Math.sin(rabbitHop)) * 0.3;

                // Update turtle position - move slower in a circle
                turtleAngle += turtleSpeed;
                turtle.position.x = Math.sin(turtleAngle) * 6;
                turtle.position.z = Math.cos(turtleAngle) * 6;
                turtle.rotation.y = -turtleAngle - Math.PI / 2;

                // Render the scene
                renderer.render(scene, camera);
            }
            animate();
        </script>
    </body>
    </html>
    """

def get_solar_system_scene():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Solar System Simulation</title>
        <style>
            body { margin: 0; overflow: hidden; }
            #info {
                position: absolute;
                top: 10px;
                width: 100%;
                text-align: center;
                color: white;
                font-family: Arial, sans-serif;
                pointer-events: none;
                text-shadow: 1px 1px 1px black;
            }
        </style>
    </head>
    <body>
        <div id="info">Solar System - Use mouse to navigate</div>
        <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
        <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
        <script>
            // Create scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x000000);
            
            // Create camera
            const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 20, 50);
            camera.lookAt(0, 0, 0);
            
            // Create renderer
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            
            // Add orbit controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Create stars
            function createStars() {
                const starsGeometry = new THREE.BufferGeometry();
                const starsMaterial = new THREE.PointsMaterial({
                    color: 0xFFFFFF,
                    size: 0.7,
                    sizeAttenuation: false
                });
                
                const starsVertices = [];
                for (let i = 0; i < 5000; i++) {
                    const x = THREE.MathUtils.randFloatSpread(2000);
                    const y = THREE.MathUtils.randFloatSpread(2000);
                    const z = THREE.MathUtils.randFloatSpread(2000);
                    starsVertices.push(x, y, z);
                }
                
                starsGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starsVertices, 3));
                const stars = new THREE.Points(starsGeometry, starsMaterial);
                scene.add(stars);
            }
            
            // Create a textured sphere
            function createPlanet(radius, texturePath, x, y, z) {
                const geometry = new THREE.SphereGeometry(radius, 32, 32);
                const material = new THREE.MeshPhongMaterial({
                    color: 0xFFFFFF,
                    shininess: 5
                });
                
                // Use color instead of texture since we're not loading external textures
                if (texturePath === 'sun') {
                    material.color.set(0xFDB813);
                    material.emissive.set(0xFDB813);
                    material.emissiveIntensity = 0.5;
                } else if (texturePath === 'mercury') {
                    material.color.set(0x93764E);
                } else if (texturePath === 'venus') {
                    material.color.set(0xE7CDBA);
                } else if (texturePath === 'earth') {
                    material.color.set(0x2E6F99);
                } else if (texturePath === 'mars') {
                    material.color.set(0xC1440E);
                } else if (texturePath === 'jupiter') {
                    material.color.set(0xC88B3A);
                } else if (texturePath === 'saturn') {
                    material.color.set(0xEAD6B8);
                } else if (texturePath === 'uranus') {
                    material.color.set(0xC9EDF5);
                } else if (texturePath === 'neptune') {
                    material.color.set(0x3D52CF);
                }
                
                const planet = new THREE.Mesh(geometry, material);
                planet.position.set(x, y, z);
                return planet;
            }
            
            // Create Saturn's rings
            function createSaturnRings(innerRadius, outerRadius) {
                const ringsGeometry = new THREE.RingGeometry(innerRadius, outerRadius, 64);
                const ringsMaterial = new THREE.MeshBasicMaterial({
                    color: 0xF0E9E1,
                    side: THREE.DoubleSide,
                    transparent: true,
                    opacity: 0.7
                });
                const rings = new THREE.Mesh(ringsGeometry, ringsMaterial);
                rings.rotation.x = Math.PI / 2;
                return rings;
            }
            
            // Create sun with light
            const sun = createPlanet(5, 'sun', 0, 0, 0);
            scene.add(sun);
            
            // Add light from the sun
            const sunLight = new THREE.PointLight(0xFFFFFF, 2, 300);
            sunLight.position.set(0, 0, 0);
            scene.add(sunLight);
            
            // Add ambient light
            const ambientLight = new THREE.AmbientLight(0x333333);
            scene.add(ambientLight);
            
            // Create planets
            const mercury = createPlanet(0.5, 'mercury', 10, 0, 0);
            scene.add(mercury);
            mercury.userData = { orbitRadius: 10, orbitSpeed: 0.04, rotationSpeed: 0.004 };
            
            const venus = createPlanet(0.9, 'venus', 15, 0, 0);
            scene.add(venus);
            venus.userData = { orbitRadius: 15, orbitSpeed: 0.015, rotationSpeed: 0.002 };
            
            const earth = createPlanet(1, 'earth', 20, 0, 0);
            scene.add(earth);
            earth.userData = { orbitRadius: 20, orbitSpeed: 0.01, rotationSpeed: 0.02 };
            
            const mars = createPlanet(0.7, 'mars', 25, 0, 0);
            scene.add(mars);
            mars.userData = { orbitRadius: 25, orbitSpeed: 0.008, rotationSpeed: 0.018 };
            
            const jupiter = createPlanet(3, 'jupiter', 35, 0, 0);
            scene.add(jupiter);
            jupiter.userData = { orbitRadius: 35, orbitSpeed: 0.002, rotationSpeed: 0.04 };
            
            const saturn = createPlanet(2.5, 'saturn', 45, 0, 0);
            scene.add(saturn);
            saturn.userData = { orbitRadius: 45, orbitSpeed: 0.0009, rotationSpeed: 0.038 };
            
            // Add rings to Saturn
            const saturnRings = createSaturnRings(3, 5);
            saturn.add(saturnRings);
            
            const uranus = createPlanet(1.8, 'uranus', 52, 0, 0);
            scene.add(uranus);
            uranus.userData = { orbitRadius: 52, orbitSpeed: 0.0004, rotationSpeed: 0.03 };
            
            const neptune = createPlanet(1.7, 'neptune', 58, 0, 0);
            scene.add(neptune);
            neptune.userData = { orbitRadius: 58, orbitSpeed: 0.0001, rotationSpeed: 0.032 };
            
            // Add stars to the background
            createStars();
            
            // Handle window resize
            window.addEventListener('resize', function() {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                
                // Update controls
                controls.update();
                
                // Rotate sun
                sun.rotation.y += 0.001;
                
                // Update planet positions and rotations
                const planets = [mercury, venus, earth, mars, jupiter, saturn, uranus, neptune];
                
                planets.forEach(planet => {
                    // Update planet rotation
                    planet.rotation.y += planet.userData.rotationSpeed;
                    
                    // Update planet orbital position
                    const angle = Date.now() * 0.001 * planet.userData.orbitSpeed;
                    const radius = planet.userData.orbitRadius;
                    planet.position.x = Math.cos(angle) * radius;
                    planet.position.z = Math.sin(angle) * radius;
                });
                
                // Render the scene
                renderer.render(scene, camera);
            }
            
            // Start the animation loop
            animate();
        </script>
    </body>
    </html>
    """

def get_forest_scene():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Forest Scene</title>
        <style>
            body { margin: 0; overflow: hidden; }
            #info {
                position: absolute;
                top: 10px;
                width: 100%;
                text-align: center;
                color: white;
                font-family: Arial, sans-serif;
                pointer-events: none;
                text-shadow: 1px 1px 1px black;
            }
        </style>
    </head>
    <body>
        <div id="info">Forest Scene - Use mouse to navigate</div>
        <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
        <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
        <script>
            // Create scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x87CEEB);
            
            // Create camera
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(0, 5, 15);
            camera.lookAt(0, 0, 0);
            
            // Create renderer
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            document.body.appendChild(renderer.domElement);
            
            // Add orbit controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.maxPolarAngle = Math.PI / 2;
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
            scene.add(ambientLight);
            
            const dirLight = new THREE.DirectionalLight(0xFFFFFF, 1);
            dirLight.position.set(10, 10, 10);
            dirLight.castShadow = true;
            dirLight.shadow.mapSize.width = 2048;
            dirLight.shadow.mapSize.height = 2048;
            dirLight.shadow.camera.near = 0.5;
            dirLight.shadow.camera.far = 50;
            dirLight.shadow.camera.left = -20;
            dirLight.shadow.camera.right = 20;
            dirLight.shadow.camera.top = 20;
            dirLight.shadow.camera.bottom = -20;
            scene.add(dirLight);
            
            // Create ground
            const groundGeometry = new THREE.PlaneGeometry(50, 50);
            const groundMaterial = new THREE.MeshStandardMaterial({
                color: 0x458B00,
                roughness: 0.8
            });
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);
            
            // Create lake
            const lakeGeometry = new THREE.CircleGeometry(5, 32);
            const lakeMaterial = new THREE.MeshStandardMaterial({
                color: 0x4682B4,
                roughness: 0.2,
                metalness: 0.8
            });
            const lake = new THREE.Mesh(lakeGeometry, lakeMaterial);
            lake.rotation.x = -Math.PI / 2;
            lake.position.set(-5, 0.01, 2);
            scene.add(lake);
            
            // Create tree function
            function createTree(x, z) {
                const tree = new THREE.Group();
                
                // Tree trunk
                const trunkGeometry = new THREE.CylinderGeometry(0.2, 0.3, 1.5, 8);
                const trunkMaterial = new THREE.MeshStandardMaterial({
                    color: 0x8B4513,
                    roughness: 0.9
                });
                const trunk = new THREE.Mesh(trunkGeometry, trunkMaterial);
                trunk.position.y = 0.75;
                trunk.castShadow = true;
                trunk.receiveShadow = true;
                tree.add(trunk);
                
                // Tree foliage
                const foliageGeometry = new THREE.ConeGeometry(1, 2, 8);
                const foliageMaterial = new THREE.MeshStandardMaterial({
                    color: 0x228B22,
                    roughness: 0.8
                });
                
                const foliage1 = new THREE.Mesh(foliageGeometry, foliageMaterial);
                foliage1.position.y = 2;
                foliage1.castShadow = true;
                tree.add(foliage1);
                
                const foliage2 = new THREE.Mesh(foliageGeometry, foliageMaterial);
                foliage2.position.y = 2.6;
                foliage2.scale.set(0.8, 0.8, 0.8);
                foliage2.castShadow = true;
                tree.add(foliage2);
                
                const foliage3 = new THREE.Mesh(foliageGeometry, foliageMaterial);
                foliage3.position.y = 3.1;
                foliage3.scale.set(0.6, 0.6, 0.6);
                foliage3.castShadow = true;
                tree.add(foliage3);
                
                tree.position.set(x, 0, z);
                return tree;
            }
            
            // Create multiple trees
            for (let i = 0; i < 30; i++) {
                const x = THREE.MathUtils.randFloatSpread(40);
                const z = THREE.MathUtils.randFloatSpread(40);
                
                // Don't place trees in the lake
                const distanceToLake = Math.sqrt(Math.pow(x + 5, 2) + Math.pow(z - 2, 2));
                if (distanceToLake > 5) {
                    const scale = 0.5 + Math.random() * 1.5;
                    const tree = createTree(x, z);
                    tree.scale.set(scale, scale, scale);
                    scene.add(tree);
                }
            }
            
            // Create bird
            function createBird() {
                const bird = new THREE.Group();
                
                // Bird body
                const bodyGeometry = new THREE.SphereGeometry(0.2, 16, 16);
                const bodyMaterial = new THREE.MeshStandardMaterial({
                    color: 0xE74C3C,
                    roughness: 0.8
                });
                const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
                body.castShadow = true;
                bird.add(body);
                
                // Bird head
                const headGeometry = new THREE.SphereGeometry(0.12, 16, 16);
                const headMaterial = new THREE.MeshStandardMaterial({
                    color: 0xE74C3C,
                    roughness: 0.8
                });
                const head = new THREE.Mesh(headGeometry, headMaterial);
                head.position.set(0.15, 0.08, 0);
                head.castShadow = true;
                bird.add(head);
                
                // Bird wings
                const wingGeometry = new THREE.PlaneGeometry(0.3, 0.15);
                const wingMaterial = new THREE.MeshStandardMaterial({
                    color: 0xE74C3C,
                    roughness: 0.8,
                    side: THREE.DoubleSide
                });
                
                const leftWing = new THREE.Mesh(wingGeometry, wingMaterial);
                leftWing.position.set(0, 0.1, 0.15);
                leftWing.rotation.y = Math.PI / 2;
                leftWing.castShadow = true;
                bird.add(leftWing);
                
                const rightWing = new THREE.Mesh(wingGeometry, wingMaterial);
                rightWing.position.set(0, 0.1, -0.15);
                rightWing.rotation.y = Math.PI / 2;
                rightWing.castShadow = true;
                bird.add(rightWing);
                
                // Bird tail
                const tailGeometry = new THREE.PlaneGeometry(0.15, 0.1);
                const tailMaterial = new THREE.MeshStandardMaterial({
                    color: 0xE74C3C,
                    roughness: 0.8,
                    side: THREE.DoubleSide
                });
                const tail = new THREE.Mesh(tailGeometry, tailMaterial);
                tail.position.set(-0.2, 0, 0);
                tail.rotation.y = Math.PI / 2;
                tail.castShadow = true;
                bird.add(tail);
                
                return bird;
            }
            
            // Create multiple birds
            const birds = [];
            for (let i = 0; i < 10; i++) {
                const bird = createBird();
                const x = THREE.MathUtils.randFloatSpread(30);
                const y = 5 + Math.random() * 5;
                const z = THREE.MathUtils.randFloatSpread(30);
                bird.position.set(x, y, z);
                bird.userData = {
                    speed: 0.02 + Math.random() * 0.05,
                    direction: new THREE.Vector3(
                        THREE.MathUtils.randFloatSpread(2),
                        THREE.MathUtils.randFloatSpread(1),
                        THREE.MathUtils.randFloatSpread(2)
                    ).normalize(),
                    wingDirection: 1,
                    wingSpeed: 0.2
                };
                birds.push(bird);
                scene.add(bird);
            }
            
            // Handle window resize
            window.addEventListener('resize', function() {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                
                // Update controls
                controls.update();
                
                // Animate birds
                birds.forEach(bird => {
                    // Move the bird
                    bird.position.x += bird.userData.direction.x * bird.userData.speed;
                    bird.position.y += bird.userData.direction.y * bird.userData.speed;
                    bird.position.z += bird.userData.direction.z * bird.userData.speed;
                    
                    // Rotate bird to face direction of movement
                    bird.lookAt(
                        bird.position.x + bird.userData.direction.x,
                        bird.position.y + bird.userData.direction.y,
                        bird.position.z + bird.userData.direction.z
                    );
                    
                    // Flap wings
                    bird.children[2].rotation.z += bird.userData.wingDirection * bird.userData.wingSpeed;
                    bird.children[3].rotation.z -= bird.userData.wingDirection * bird.userData.wingSpeed;
                    
                    if (Math.abs(bird.children[2].rotation.z) > 1) {
                        bird.userData.wingDirection *= -1;
                    }
                    
                    // Check if bird reaches the boundary
                    const bounds = 20;
                    if (
                        Math.abs(bird.position.x) > bounds ||
                        bird.position.y < 2 ||
                        bird.position.y > 15 ||
                        Math.abs(bird.position.z) > bounds
                    ) {
                        // Change direction
                        bird.userData.direction.set(
                            -bird.userData.direction.x + THREE.MathUtils.randFloatSpread(0.5),
                            -bird.userData.direction.y * 0.5 + THREE.MathUtils.randFloatSpread(0.5),
                            -bird.userData.direction.z + THREE.MathUtils.randFloatSpread(0.5)
                        ).normalize();
                    }
                });
                
                // Render the scene
                renderer.render(scene, camera);
            }
            
            // Start animation
            animate();
        </script>
    </body>
    </html>
    """

# Get API key (using environment variable rather than secrets for simplicity)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# NEW: Prompt enhancement function
async def enhance_prompt(basic_prompt):
    """Takes a simple prompt and expands it with detailed Three.js specifications"""
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        system_prompt = """You are an expert in Three.js scene creation. Your task is to expand simple scene descriptions into detailed technical specifications that can be implemented in Three.js.

For any simple scene description, generate a highly detailed specification that covers:

1. Scene elements with precise geometries, materials, and positioning
2. Lighting setup with multiple light sources, shadows, and ambient lighting
3. Animation details for all moving elements
4. Camera settings and controls
5. Interactive elements and behaviors
6. Background and environmental details
7. Advanced visual effects where appropriate

Your output should be extremely detailed and technical, similar to a professional game developer's specification document. Include specific Three.js classes, methods, and techniques."""
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 2000,
            "temperature": 0.2,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"""Take this simple scene description:
                
"{basic_prompt}"
                
Expand it into a highly detailed Three.js technical specification with precise details about geometries, materials, lighting, animations, and interactions. Be extremely specific and thorough, describing every element in detail.
                
Format the response as a detailed technical brief that a Three.js developer would follow to implement the scene."""}
            ]
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=data,
                headers=headers
            )
            
            if response.status_code != 200:
                return basic_prompt, f"Error enhancing prompt: {response.status_code}"
            
            response_data = response.json()
            
            if "content" in response_data and len(response_data["content"]) > 0:
                enhanced_prompt = response_data["content"][0]["text"]
                return enhanced_prompt, None
            else:
                return basic_prompt, "No content in response"
    
    except Exception as e:
        return basic_prompt, f"Exception enhancing prompt: {str(e)}"

# Direct approach to API call with better debugging
async def call_anthropic_api(prompt):
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Improved system prompt with more detailed guidance
        system_prompt = """You are an expert in Three.js 3D scene creation.

Your task is to generate a complete, standalone HTML document with an interactive Three.js scene based on the user's description.

Create a fully detailed scene with:

1. Complex geometries broken down into component parts (not just basic shapes)
2. Group objects for composite entities (like characters, vehicles, buildings)
3. Detailed materials with appropriate properties (roughness, metalness, etc.)
4. Multiple light sources with shadows and proper intensity
5. Dynamic animations that bring the scene to life
6. Camera controls that allow exploring the scene
7. Proper scaling and positioning of all elements
8. A sky/background that fits the scene's theme
9. Proper coding structure with well-named functions and variables
10. Performance optimizations like object instancing where appropriate

When creating objects:
- Use groups and subgroups for complex objects
- Add fine details to make objects recognizable
- Use appropriate materials with realistic properties
- Position objects thoughtfully in the scene

For animations:
- Create smooth, natural movements
- Use sine/cosine for organic motion
- Add small random variations for realism
- Animate multiple properties (position, rotation, scale)

Implement everything as a single, complete HTML file using Three.js version 0.137.0.
Do not use external assets or textures - create everything programmatically.
Include ONLY the code with no explanations."""
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"Create a complete Three.js scene with: {prompt}. Return ONLY HTML code with no explanations. Make it visually impressive with detailed geometries and animations."}
            ]
        }
        
        # Store request data for debugging
        debug_info = {
            "request": data,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=data,
                headers=headers
            )
            
            # Store raw response for debugging
            debug_info["status_code"] = response.status_code
            debug_info["response_headers"] = dict(response.headers)
            
            if response.status_code != 200:
                debug_info["error"] = f"API error: {response.status_code} - {response.text}"
                return None, debug_info
            
            response_data = response.json()
            debug_info["response"] = response_data
            
            if "content" in response_data and len(response_data["content"]) > 0:
                response_text = response_data["content"][0]["text"]
                return response_text, debug_info
            else:
                debug_info["error"] = "No content in response"
                return None, debug_info
    
    except Exception as e:
        debug_info = {
            "error": f"Exception: {str(e)}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return None, debug_info

# Improved code extraction
def extract_html_from_response(response_text):
    # First, try to find complete HTML document using standard markers
    html_pattern = r"<!DOCTYPE html>[\s\S]*?<\/html>"
    html_matches = re.search(html_pattern, response_text, re.IGNORECASE)
    
    if html_matches:
        return html_matches.group(0)
    
    # If no complete document found, try to find HTML within code blocks
    code_block_pattern = r"```(?:html)?([\s\S]*?)```"
    code_matches = re.search(code_block_pattern, response_text)
    
    if code_matches:
        code = code_matches.group(1).strip()
        
        # Check if the extracted code already contains HTML structure
        if code.strip().startswith("<!DOCTYPE") or code.strip().startswith("<html"):
            return code
        
        # Otherwise wrap it with HTML structure
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Generated Three.js Scene</title>
            <style>
                body {{ margin: 0; overflow: hidden; }}
                #info {{
                    position: absolute;
                    top: 10px;
                    width: 100%;
                    text-align: center;
                    color: white;
                    font-family: Arial, sans-serif;
                    pointer-events: none;
                    text-shadow: 1px 1px 1px black;
                }}
            </style>
        </head>
        <body>
            <div id="info">Generated Three.js Scene - Use mouse to navigate</div>
            <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
            <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
            {code}
        </body>
        </html>
        """
    
    # If all else fails, try to extract any code-like content
    # Look for JavaScript-like content with typical Three.js patterns
    js_patterns = [
        r"const scene = new THREE\.Scene\(\);",
        r"new THREE\.(\w+)\(",
        r"renderer\.render\(scene, camera\);"
    ]
    
    for pattern in js_patterns:
        if re.search(pattern, response_text):
            # Found some Three.js code, wrap it properly
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Generated Three.js Scene</title>
                <style>
                    body {{ margin: 0; overflow: hidden; }}
                    #info {{
                        position: absolute;
                        top: 10px;
                        width: 100%;
                        text-align: center;
                        color: white;
                        font-family: Arial, sans-serif;
                        pointer-events: none;
                        text-shadow: 1px 1px 1px black;
                    }}
                </style>
            </head>
            <body>
                <div id="info">Generated Three.js Scene - Use mouse to navigate</div>
                <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
                <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
                <script>
                {response_text}
                </script>
            </body>
            </html>
            """
    
    # Last resort fallback - just wrap the entire response
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Generated Three.js Scene</title>
        <style>
            body {{ margin: 0; overflow: hidden; }}
            #info {{
                position: absolute;
                top: 10px;
                width: 100%;
                text-align: center;
                color: white;
                font-family: Arial, sans-serif;
                pointer-events: none;
                text-shadow: 1px 1px 1px black;
            }}
        </style>
    </head>
    <body>
        <div id="info">Generated Three.js Scene - Use mouse to navigate</div>
        <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
        <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
        <script>
        // Scene setup
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer();
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);

        // Controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        camera.position.set(0, 5, 10);
        controls.update();

        // Lights
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        scene.add(ambientLight);
        
        const dirLight = new THREE.DirectionalLight(0xffffff, 1);
        dirLight.position.set(5, 10, 7.5);
        dirLight.castShadow = true;
        scene.add(dirLight);
        
        // Parse and attempt to create objects from the response
        try {{
            {response_text}
        }} catch (e) {{
            console.error("Error processing response:", e);
            // Create a fallback object
            const geometry = new THREE.SphereGeometry(2, 32, 32);
            const material = new THREE.MeshPhongMaterial({{ color: 0xff0000 }});
            const sphere = new THREE.Mesh(geometry, material);
            sphere.castShadow = true;
            scene.add(sphere);
        }}
        
        // Animation
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}
        animate();
        
        // Handle window resize
        window.addEventListener('resize', function() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
        </script>
    </body>
    </html>
    """

# NEW: Get custom scene with prompt enhancement
async def get_custom_scene_with_enhancement(basic_prompt):
    """Generate a Three.js scene using two-step process with prompt enhancement"""
    
    # Step 1: Enhance the basic prompt
    enhanced_prompt, enhance_error = await enhance_prompt(basic_prompt)
    
    # Store both prompts for debugging
    st.session_state.raw_prompt = basic_prompt
    st.session_state.enhanced_prompt = enhanced_prompt
    
    if enhance_error:
        st.warning(f"Warning: Using basic prompt because enhancement failed: {enhance_error}")
    
    # Step 2: Call the API with the enhanced prompt
    response_text, debug_info = await call_anthropic_api(enhanced_prompt)
    
    # Store debug info
    st.session_state.debug_info = debug_info
    
    if response_text:
        # Extract HTML from response
        html_content = extract_html_from_response(response_text)
        return html_content, response_text, enhanced_prompt
    else:
        return None, None, enhanced_prompt

# Main app
st.title("🎮 Three.js Scene Generator")

# Create tabs for preset and custom scenes
tab1, tab2, tab3 = st.tabs(["Preset Scenes", "Custom Scene Generator", "Debug Info"])

with tab1:
    st.subheader("Select a Pre-built Scene")
    
    preset_options = {
        "Rabbit & Turtle": get_rabbit_turtle_scene,
        "Solar System": get_solar_system_scene,
        "Forest Scene": get_forest_scene
    }
    
    selected_preset = st.selectbox(
        "Choose a scene:",
        list(preset_options.keys())
    )
    
    if st.button("Load Preset Scene", key="load_preset"):
        scene_html = preset_options[selected_preset]()
        st.session_state.current_scene = {
            "prompt": selected_preset,
            "html": scene_html,
            "is_preset": True
        }
        st.success(f"Loaded {selected_preset} scene!")

with tab2:
    st.subheader("Generate Custom Scene")
    
    with st.form("custom_scene_form"):
        user_prompt = st.text_area(
            "Describe your 3D scene:",
            placeholder="A futuristic city with neon buildings and flying vehicles",
            height=100
        )
        
        # Checkbox to view enhanced prompt before generation
        show_enhanced = st.checkbox("Show enhanced prompt before generation")
        
        submitted = st.form_submit_button("Generate Custom Scene")
        
        if submitted and user_prompt:
            if show_enhanced:
                # Just show the enhanced prompt without generating
                with st.spinner("Enhancing your prompt..."):
                    enhanced_prompt, enhance_error = asyncio.run(enhance_prompt(user_prompt))
                    if enhance_error:
                        st.error(f"Error enhancing prompt: {enhance_error}")
                    else:
                        st.session_state.raw_prompt = user_prompt
                        st.session_state.enhanced_prompt = enhanced_prompt
                        
                        st.subheader("Enhanced Prompt")
                        st.write(enhanced_prompt)
                        
                        if st.button("Continue with this enhanced prompt"):
                            with st.spinner("Generating your 3D scene... (this may take up to a minute)"):
                                # Call API with enhanced prompt
                                html_content, full_response = asyncio.run(call_anthropic_api(enhanced_prompt))
                                
                                if html_content:
                                    # Extract HTML
                                    final_html = extract_html_from_response(html_content)
                                    
                                    # Save current scene to state
                                    st.session_state.current_scene = {
                                        "prompt": user_prompt,
                                        "enhanced_prompt": enhanced_prompt,
                                        "html": final_html, 
                                        "full_response": full_response,
                                        "is_preset": False
                                    }
                                    st.success("Scene generated successfully!")
                                else:
                                    st.error("Failed to generate scene. See Debug tab for details.")
            else:
                # Generate directly with enhanced prompt
                with st.spinner("Generating your 3D scene with enhanced details... (this may take up to 2 minutes)"):
                    # Use the two-step process
                    html_content, full_response, enhanced_prompt = asyncio.run(get_custom_scene_with_enhancement(user_prompt))
                    
                    if html_content:
                        # Save current scene to state
                        st.session_state.current_scene = {
                            "prompt": user_prompt,
                            "enhanced_prompt": enhanced_prompt,
                            "html": html_content, 
                            "full_response": full_response,
                            "is_preset": False
                        }
                        st.success("Scene generated successfully!")
                    else:
                        st.error("Failed to generate scene. See Debug tab for details.")

with tab3:
    st.subheader("Debug Information")
    
    # Show prompt comparison
    if "raw_prompt" in st.session_state and "enhanced_prompt" in st.session_state:
        st.subheader("Prompt Enhancement")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Original Prompt")
            st.info(st.session_state.raw_prompt)
        
        with col2:
            st.write("Enhanced Prompt")
            st.success(st.session_state.enhanced_prompt)
    
    # Show API debug info
    if "debug_info" in st.session_state and st.session_state.debug_info:
        st.subheader("API Debug Info")
        debug_info = st.session_state.debug_info
        
        with st.expander("Request Details"):
            if "request" in debug_info:
                st.json(debug_info["request"])
        
        with st.expander("Response Details"):
            if "status_code" in debug_info:
                st.write(f"Status Code: {debug_info['status_code']}")
            
            if "error" in debug_info:
                st.error(f"Error: {debug_info['error']}")
            
            if "response" in debug_info:
                # Show a simplified version to avoid overwhelming the UI
                simplified_response = {
                    "model": debug_info["response"].get("model", ""),
                    "usage": debug_info["response"].get("usage", {}),
                    "content_length": len(str(debug_info["response"].get("content", [])))
                }
                st.json(simplified_response)

# Display current scene if available
if st.session_state.current_scene:
    scene = st.session_state.current_scene
    
    st.subheader(f"Scene: {scene['prompt']}")
    
    # Show enhanced prompt if available
    if "enhanced_prompt" in scene and not scene.get("is_preset", False):
        with st.expander("View Enhanced Prompt"):
            st.write(scene["enhanced_prompt"])
    
    # Render the Three.js scene
    st.components.v1.html(scene["html"], height=600)
    
    # Show HTML code and download button
    with st.expander("View HTML Code"):
        st.code(scene["html"], language="html")
    
    st.download_button(
        label="Download HTML",
        data=scene["html"],
        file_name="threejs_scene.html",
        mime="text/html"
    )
    
    # Show full response for custom scenes
    if not scene.get("is_preset", False) and "full_response" in scene:
        with st.expander("View Full API Response"):
            st.text_area("Response", scene["full_response"], height=200)

st.markdown("---")
st.markdown("""
### Instructions

1. **Preset Scenes**: Choose from pre-built scenes in the first tab
2. **Custom Scenes**: Describe your own scene in the second tab
   - Optionally check "Show enhanced prompt" to review the detailed prompt before generation
3. **Debug Info**: View prompts and API details in the third tab
4. **Interact** with any scene using your mouse:
   - Left-click + drag: Rotate the camera
   - Right-click + drag: Pan the camera
   - Scroll: Zoom in/out
5. **Download**: Save the HTML to open in your browser

### About Prompt Enhancement

The prompt enhancer transforms simple descriptions into detailed technical specifications, leading to more sophisticated scenes with:
- Complex geometries instead of basic shapes
- Detailed materials and lighting
- More realistic animations
- Better organized scene elements

This two-step process helps bridge the gap between simple descriptions and highly detailed Three.js implementations.
""")
