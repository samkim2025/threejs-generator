import streamlit as st

# Set page config
st.set_page_config(
    page_title="Three.js Scene Generator",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Title
st.title("Three.js Scene Generator")
st.markdown("Generate 3D scenes using Three.js")

# HTML content for Three.js app
html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Three.js Scene Generator</title>
    <style>
        body { 
            margin: 0; 
            font-family: Arial, sans-serif;
            overflow: hidden;
        }
        #app {
            width: 100vw;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        #scene-container {
            flex-grow: 1;
            position: relative;
        }
        canvas { 
            display: block; 
            width: 100%;
            height: 100%;
        }
        #controls {
            padding: 10px;
            background-color: #f0f0f0;
            border-top: 1px solid #ccc;
        }
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
        button {
            padding: 8px 12px;
            margin-right: 8px;
            border: none;
            border-radius: 4px;
            background-color: #4285f4;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #3367d6;
        }
        textarea {
            width: 100%;
            padding: 8px;
            margin-bottom: 8px;
            border-radius: 4px;
            border: 1px solid #ccc;
        }
    </style>
</head>
<body>
    <div id="app">
        <div id="scene-container">
            <div id="info">Generated Three.js Scene - Use mouse to navigate</div>
        </div>
        <div id="controls">
            <button id="solar-system-btn">Load Solar System</button>
            <button id="generate-btn">Generate Custom Scene</button>
            <textarea id="prompt-input" placeholder="Describe your 3D scene..." rows="3"></textarea>
        </div>
    </div>

    <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>

    <script>
        // Scene setup
        let scene, camera, renderer, controls;
        let currentAnimation = null;

        function initScene() {
            // Clear previous animation if exists
            if (currentAnimation) {
                cancelAnimationFrame(currentAnimation);
            }

            // Remove existing renderer if exists
            const container = document.getElementById('scene-container');
            if (renderer) {
                container.removeChild(renderer.domElement);
            }

            // Create new scene
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
            
            renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.shadowMap.enabled = true;
            container.appendChild(renderer.domElement);
            
            // Add controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Handle window resize
            window.addEventListener('resize', () => {
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            });
        }

        // Create the Solar System scene
        function createSolarSystem() {
            initScene();
            scene.background = new THREE.Color(0x000000);
            
            // Set camera position
            camera.position.set(0, 20, 50);
            camera.lookAt(0, 0, 0);
            
            // Add ambient light
            const ambientLight = new THREE.AmbientLight(0x333333);
            scene.add(ambientLight);
            
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
            function createPlanet(radius, color, x, y, z, emissive = false) {
                const geometry = new THREE.SphereGeometry(radius, 32, 32);
                const material = new THREE.MeshPhongMaterial({
                    color: color,
                    shininess: 5
                });
                
                if (emissive) {
                    material.emissive = new THREE.Color(color);
                    material.emissiveIntensity = 0.5;
                }
                
                const planet = new THREE.Mesh(geometry, material);
                planet.position.set(x, y, z);
                scene.add(planet);
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
            const sun = createPlanet(5, 0xFDB813, 0, 0, 0, true);
            
            // Add light from the sun
            const sunLight = new THREE.PointLight(0xFFFFFF, 2, 300);
            sunLight.position.set(0, 0, 0);
            scene.add(sunLight);
            
            // Create planets
            const mercury = createPlanet(0.5, 0x93764E, 10, 0, 0);
            mercury.userData = { orbitRadius: 10, orbitSpeed: 0.04, rotationSpeed: 0.004 };
            
            const venus = createPlanet(0.9, 0xE7CDBA, 15, 0, 0);
            venus.userData = { orbitRadius: 15, orbitSpeed: 0.015, rotationSpeed: 0.002 };
            
            const earth = createPlanet(1, 0x2E6F99, 20, 0, 0);
            earth.userData = { orbitRadius: 20, orbitSpeed: 0.01, rotationSpeed: 0.02 };
            
            const mars = createPlanet(0.7, 0xC1440E, 25, 0, 0);
            mars.userData = { orbitRadius: 25, orbitSpeed: 0.008, rotationSpeed: 0.018 };
            
            const jupiter = createPlanet(3, 0xC88B3A, 35, 0, 0);
            jupiter.userData = { orbitRadius: 35, orbitSpeed: 0.002, rotationSpeed: 0.04 };
            
            const saturn = createPlanet(2.5, 0xEAD6B8, 45, 0, 0);
            saturn.userData = { orbitRadius: 45, orbitSpeed: 0.0009, rotationSpeed: 0.038 };
            
            // Add rings to Saturn
            const saturnRings = createSaturnRings(3, 5);
            saturn.add(saturnRings);
            
            const uranus = createPlanet(1.8, 0xC9EDF5, 52, 0, 0);
            uranus.userData = { orbitRadius: 52, orbitSpeed: 0.0004, rotationSpeed: 0.03 };
            
            const neptune = createPlanet(1.7, 0x3D52CF, 58, 0, 0);
            neptune.userData = { orbitRadius: 58, orbitSpeed: 0.0001, rotationSpeed: 0.032 };
            
            // Add stars to the background
            createStars();
            
            // Animation function
            function animate() {
                currentAnimation = requestAnimationFrame(animate);
                
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
        }

        // Create a scene programmatically based on the prompt
        function createCustomScene(prompt) {
            initScene();
            
            // Set a sky blue background
            scene.background = new THREE.Color(0x87CEEB);
            
            // Set camera position
            camera.position.set(0, 2, 5);
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(3, 5, 3);
            directionalLight.castShadow = true;
            scene.add(directionalLight);
            
            // Example: Creating a programmatic rabbit and turtle scene
            if (prompt.toLowerCase().includes("rabbit") && prompt.toLowerCase().includes("turtle")) {
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
                
                // Create rabbit programmatically
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
                
                // Create turtle programmatically
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
                
                // Animation function
                function animate() {
                    currentAnimation = requestAnimationFrame(animate);
                    
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
                
                // Start animation
                animate();
            } else {
                // Generic fallback for other prompts
                
                // Add a ground
                const groundGeometry = new THREE.PlaneGeometry(20, 20);
                const groundMaterial = new THREE.MeshPhongMaterial({ color: 0x9b7653 });
                const ground = new THREE.Mesh(groundGeometry, groundMaterial);
                ground.rotation.x = -Math.PI / 2;
                ground.position.y = -1;
                ground.receiveShadow = true;
                scene.add(ground);
                
                // Add some random objects based on the prompt
                const objects = [];
                
                for (let i = 0; i < 10; i++) {
                    let object;
                    const x = Math.random() * 16 - 8;
                    const z = Math.random() * 16 - 8;
                    const y = 0;
                    const size = 0.5 + Math.random() * 1;
                    
                    // Create different shapes based on words in the prompt
                    if (prompt.toLowerCase().includes("cube") || i % 4 === 0) {
                        const geometry = new THREE.BoxGeometry(size, size, size);
                        const material = new THREE.MeshPhongMaterial({ color: Math.random() * 0xffffff });
                        object = new THREE.Mesh(geometry, material);
                    } else if (prompt.toLowerCase().includes("sphere") || i % 4 === 1) {
                        const geometry = new THREE.SphereGeometry(size/2, 16, 16);
                        const material = new THREE.MeshPhongMaterial({ color: Math.random() * 0xffffff });
                        object = new THREE.Mesh(geometry, material);
                    } else if (prompt.toLowerCase().includes("cylinder") || i % 4 === 2) {
                        const geometry = new THREE.CylinderGeometry(size/2, size/2, size, 16);
                        const material = new THREE.MeshPhongMaterial({ color: Math.random() * 0xffffff });
                        object = new THREE.Mesh(geometry, material);
                    } else {
                        const geometry = new THREE.ConeGeometry(size/2, size, 16);
                        const material = new THREE.MeshPhongMaterial({ color: Math.random() * 0xffffff });
                        object = new THREE.Mesh(geometry, material);
                    }
                    
                    object.position.set(x, y + size/2, z);
                    object.castShadow = true;
                    object.receiveShadow = true;
                    objects.push(object);
                    scene.add(object);
                }
                
                // Animation function
                function animate() {
                    currentAnimation = requestAnimationFrame(animate);
                    
                    // Animate objects
                    objects.forEach((object, index) => {
                        object.rotation.x += 0.01;
                        object.rotation.y += 0.01;
                        object.position.y = Math.max(object.geometry.parameters.height/2, 
                                                   object.position.y + Math.sin((Date.now() + index * 100) * 0.001) * 0.01);
                    });
                    
                    // Update controls
                    controls.update();
                    
                    // Render the scene
                    renderer.render(scene, camera);
                }
                
                // Start animation
                animate();
            }
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            // Start with solar system on page load
            createSolarSystem();
            
            // Set up button event listeners
            document.getElementById('solar-system-btn').addEventListener('click', createSolarSystem);
            
            document.getElementById('generate-btn').addEventListener('click', () => {
                const prompt = document.getElementById('prompt-input').value;
                if (prompt) {
                    createCustomScene(prompt);
                    document.getElementById('info').textContent = prompt;
                } else {
                    alert('Please enter a description for your scene');
                }
            });
        });
    </script>
</body>
</html>
"""

# Render the HTML content
st.components.v1.html(html_content, height=800)
