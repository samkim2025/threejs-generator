import streamlit as st
import os
import re
import httpx
import asyncio
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Instant 3D Scene Generator",
    page_icon="🎮",
    layout="wide"
)

# Initialize session state
if "current_scene" not in st.session_state:
    st.session_state.current_scene = None
if "debug_info" not in st.session_state:
    st.session_state.debug_info = {}
if "scene_history" not in st.session_state:
    st.session_state.scene_history = []
if "history_index" not in st.session_state:
    st.session_state.history_index = None

# Get API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Solar System Demo HTML
SOLAR_SYSTEM_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solar System Demo</title>
    <style>
        body { margin: 0; overflow: hidden; }
        canvas { display: block; }
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
    <div id="info">Solar System Demo - Use mouse to navigate</div>
    <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
    <script>
        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x000000);
        
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 30, 100);
        
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);
        
        // Orbit controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        
        // Lights
        const ambientLight = new THREE.AmbientLight(0x202020);
        scene.add(ambientLight);
        
        // Sun light (point light at center)
        const sunLight = new THREE.PointLight(0xffffff, 2, 300);
        scene.add(sunLight);
        
        // Helper function to create a planet
        function createPlanet(radius, color, distance, speed, tilt = 0) {
            const planetGroup = new THREE.Group();
            scene.add(planetGroup);
            
            // Planet
            const planetGeometry = new THREE.SphereGeometry(radius, 32, 32);
            const planetMaterial = new THREE.MeshStandardMaterial({ 
                color: color,
                roughness: 0.7,
                metalness: 0.3
            });
            const planet = new THREE.Mesh(planetGeometry, planetMaterial);
            planetGroup.add(planet);
            
            // Apply tilt
            planet.rotation.x = tilt;
            
            // Orbit
            const orbitGeometry = new THREE.RingGeometry(distance - 0.1, distance + 0.1, 128);
            const orbitMaterial = new THREE.MeshBasicMaterial({ 
                color: 0x444444,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.2
            });
            const orbit = new THREE.Mesh(orbitGeometry, orbitMaterial);
            orbit.rotation.x = Math.PI / 2;
            scene.add(orbit);
            
            return {
                group: planetGroup,
                mesh: planet,
                distance: distance,
                speed: speed,
                angle: Math.random() * Math.PI * 2
            };
        }
        
        // Create the sun
        const sunGeometry = new THREE.SphereGeometry(10, 32, 32);
        const sunMaterial = new THREE.MeshBasicMaterial({ 
            color: 0xffff00,
            emissive: 0xffff00,
            emissiveIntensity: 1
        });
        const sun = new THREE.Mesh(sunGeometry, sunMaterial);
        scene.add(sun);
        
        // Create planets
        const planets = [
            createPlanet(0.8, 0xc88c3c, 20, 0.01), // Mercury
            createPlanet(2, 0xe39e54, 30, 0.008), // Venus
            createPlanet(2.2, 0x3c85c8, 40, 0.006, 0.4), // Earth
            createPlanet(1.2, 0xc85c3c, 50, 0.004), // Mars
            createPlanet(7, 0xc8b93c, 70, 0.002), // Jupiter
            createPlanet(6, 0xc8953c, 90, 0.0015, 0.5), // Saturn
            createPlanet(4, 0x3cc8c8, 110, 0.001), // Uranus
            createPlanet(4, 0x3c3cc8, 130, 0.0008) // Neptune
        ];
        
        // Create Saturn's rings
        const saturnRingGeometry = new THREE.RingGeometry(8, 12, 32);
        const saturnRingMaterial = new THREE.MeshBasicMaterial({ 
            color: 0xc8953c,
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.6
        });
        const saturnRing = new THREE.Mesh(saturnRingGeometry, saturnRingMaterial);
        saturnRing.rotation.x = Math.PI / 2;
        planets[5].mesh.add(saturnRing);
        
        // Create a star field
        const starGeometry = new THREE.BufferGeometry();
        const starMaterial = new THREE.PointsMaterial({
            color: 0xffffff,
            size: 0.5
        });
        
        const starVertices = [];
        for (let i = 0; i < 5000; i++) {
            const x = (Math.random() - 0.5) * 2000;
            const y = (Math.random() - 0.5) * 2000;
            const z = (Math.random() - 0.5) * 2000;
            starVertices.push(x, y, z);
        }
        
        starGeometry.setAttribute('position', new THREE.Float32BufferAttribute(starVertices, 3));
        const stars = new THREE.Points(starGeometry, starMaterial);
        scene.add(stars);
        
        // Create Earth's moon
        const moonGroup = new THREE.Group();
        planets[2].mesh.add(moonGroup);
        
        const moonGeometry = new THREE.SphereGeometry(0.6, 16, 16);
        const moonMaterial = new THREE.MeshStandardMaterial({ 
            color: 0xcccccc,
            roughness: 0.8,
            metalness: 0.1
        });
        const moon = new THREE.Mesh(moonGeometry, moonMaterial);
        moon.position.set(5, 0, 0);
        moonGroup.add(moon);
        
        // Animation
        function animate() {
            requestAnimationFrame(animate);
            
            // Update controls
            controls.update();
            
            // Rotate the sun
            sun.rotation.y += 0.001;
            
            // Update planet positions
            planets.forEach(planet => {
                planet.angle += planet.speed;
                const x = Math.cos(planet.angle) * planet.distance;
                const z = Math.sin(planet.angle) * planet.distance;
                planet.group.position.set(x, 0, z);
                planet.mesh.rotation.y += planet.speed * 10;
            });
            
            // Rotate moon around Earth
            moonGroup.rotation.y += 0.02;
            
            // Render scene
            renderer.render(scene, camera);
        }
        
        // Handle window resize
        window.addEventListener('resize', function() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        
        // Start animation
        animate();
    </script>
</body>
</html>"""

# Example mappings with a lion example for animal scenes
EXAMPLE_MAPPINGS = [
    {
        "simple": "A cool city with many buildings",
        "enhanced": "Create a 3D city scene using Three.js that features a bustling urban environment with skyscrapers, apartment buildings, and smaller shops lining the streets. Incorporate roads with moving cars, traffic lights, and pedestrian crossings to bring the city to life. Add pedestrians walking on sidewalks and crossing the streets to enhance realism. Include street elements such as lampposts, benches, and trees for a more immersive experience. Utilize dynamic lighting to simulate day and night cycles, and implement basic camera controls to allow users to explore the vibrant cityscape from different perspectives."
    },
    {
        "simple": "A lion sitting under a tree in a grassy field",
        "enhanced": "Create a serene 3D scene featuring a golden-maned lion resting under the shade of a tall acacia tree in an expansive grassy savanna. The scene should include a detailed lion constructed from primitive Three.js shapes (spheres, cylinders, and boxes) with a tawny body, distinctive mane, and relaxed posture. The acacia tree should have a thick trunk and a wide, umbrella-like canopy of leaves providing dappled shade. Surrounding them, tall grass should sway gently in a simulated breeze. Implement a day-night cycle with changing lighting conditions, casting realistic shadows across the scene. Allow users to orbit around the scene with camera controls to view the lion and its environment from different angles."
    }
]

# Example HTML for animal scene with lion created from primitives
LION_EXAMPLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lion Under Tree Scene</title>
    <style>
        body { margin: 0; overflow: hidden; }
        canvas { display: block; }
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
    <div id="info">Lion Under Tree - Use mouse to navigate</div>
    <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
    <script>
        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x87CEEB);
        
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 5, 10);
        
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);
        
        // Orbit controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        
        // Lights
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xFFFFFF, 1);
        directionalLight.position.set(5, 8, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 1024;
        directionalLight.shadow.mapSize.height = 1024;
        scene.add(directionalLight);
        
        // Ground
        const groundGeometry = new THREE.PlaneGeometry(100, 100);
        const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x8B4513 });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);
        
        // Grass
        const grassGeometry = new THREE.PlaneGeometry(100, 100, 50, 50);
        const grassMaterial = new THREE.MeshStandardMaterial({ 
            color: 0x7CFC00,
            roughness: 0.8
        });
        const grass = new THREE.Mesh(grassGeometry, grassMaterial);
        grass.rotation.x = -Math.PI / 2;
        grass.position.y = 0.05;
        grass.receiveShadow = true;
        scene.add(grass);
        
        // Tree
        function createTree(x, z) {
            const treeGroup = new THREE.Group();
            
            // Trunk
            const trunkGeometry = new THREE.CylinderGeometry(0.5, 0.8, 5, 8);
            const trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x8B4513 });
            const trunk = new THREE.Mesh(trunkGeometry, trunkMaterial);
            trunk.position.y = 2.5;
            trunk.castShadow = true;
            trunk.receiveShadow = true;
            treeGroup.add(trunk);
            
            // Canopy
            const canopyGeometry = new THREE.SphereGeometry(4, 16, 16);
            const canopyMaterial = new THREE.MeshStandardMaterial({ color: 0x228B22 });
            const canopy = new THREE.Mesh(canopyGeometry, canopyMaterial);
            canopy.position.y = 7;
            canopy.scale.y = 0.7;
            canopy.castShadow = true;
            treeGroup.add(canopy);
            
            treeGroup.position.set(x, 0, z);
            scene.add(treeGroup);
            
            return treeGroup;
        }
        
        const tree = createTree(3, 2);
        
        // Create lion using primitives
        function createLion() {
            const lionGroup = new THREE.Group();
            
            // Body
            const bodyGeometry = new THREE.SphereGeometry(1, 16, 16);
            const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0xC2B280 });
            const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
            body.scale.set(1.2, 1, 1.5);
            body.position.y = 1.1;
            body.castShadow = true;
            lionGroup.add(body);
            
            // Head
            const headGeometry = new THREE.SphereGeometry(0.7, 16, 16);
            const headMaterial = new THREE.MeshStandardMaterial({ color: 0xC2B280 });
            const head = new THREE.Mesh(headGeometry, headMaterial);
            head.position.set(1.2, 1.5, 0);
            head.castShadow = true;
            lionGroup.add(head);
            
            // Mane
            const maneGeometry = new THREE.SphereGeometry(1, 16, 16);
            const maneMaterial = new THREE.MeshStandardMaterial({ color: 0xCD853F });
            const mane = new THREE.Mesh(maneGeometry, maneMaterial);
            mane.position.set(1.2, 1.5, 0);
            mane.scale.set(1.2, 1.2, 1.2);
            mane.castShadow = true;
            lionGroup.add(mane);
            
            // Face
            const snoutGeometry = new THREE.CylinderGeometry(0.2, 0.3, 0.4, 8);
            const snoutMaterial = new THREE.MeshStandardMaterial({ color: 0xD2B48C });
            const snout = new THREE.Mesh(snoutGeometry, snoutMaterial);
            snout.position.set(1.7, 1.4, 0);
            snout.rotation.z = Math.PI / 2;
            snout.castShadow = true;
            lionGroup.add(snout);
            
            // Eyes
            const eyeGeometry = new THREE.SphereGeometry(0.1, 8, 8);
            const eyeMaterial = new THREE.MeshStandardMaterial({ color: 0x000000 });
            
            const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
            leftEye.position.set(1.6, 1.7, 0.3);
            lionGroup.add(leftEye);
            
            const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
            rightEye.position.set(1.6, 1.7, -0.3);
            lionGroup.add(rightEye);
            
            // Legs
            const legGeometry = new THREE.CylinderGeometry(0.2, 0.2, 1, 8);
            const legMaterial = new THREE.MeshStandardMaterial({ color: 0xC2B280 });
            
            const frontLeftLeg = new THREE.Mesh(legGeometry, legMaterial);
            frontLeftLeg.position.set(0.6, 0.5, 0.5);
            frontLeftLeg.castShadow = true;
            lionGroup.add(frontLeftLeg);
            
            const frontRightLeg = new THREE.Mesh(legGeometry, legMaterial);
            frontRightLeg.position.set(0.6, 0.5, -0.5);
            frontRightLeg.castShadow = true;
            lionGroup.add(frontRightLeg);
            
            const backLeftLeg = new THREE.Mesh(legGeometry, legMaterial);
            backLeftLeg.position.set(-0.6, 0.5, 0.5);
            backLeftLeg.castShadow = true;
            lionGroup.add(backLeftLeg);
            
            const backRightLeg = new THREE.Mesh(legGeometry, legMaterial);
            backRightLeg.position.set(-0.6, 0.5, -0.5);
            backRightLeg.castShadow = true;
            lionGroup.add(backRightLeg);
            
            // Tail
            const tailGeometry = new THREE.CylinderGeometry(0.1, 0.15, 1.5, 8);
            const tailMaterial = new THREE.MeshStandardMaterial({ color: 0xC2B280 });
            const tail = new THREE.Mesh(tailGeometry, tailMaterial);
            tail.position.set(-1.5, 1.2, 0);
            tail.rotation.z = Math.PI / 4;
            tail.castShadow = true;
            lionGroup.add(tail);
            
            // Tail tuft
            const tuftGeometry = new THREE.SphereGeometry(0.2, 8, 8);
            const tuftMaterial = new THREE.MeshStandardMaterial({ color: 0x8B4513 });
            const tuft = new THREE.Mesh(tuftGeometry, tuftMaterial);
            tuft.position.set(-2, 1.8, 0);
            tuft.castShadow = true;
            lionGroup.add(tuft);
            
            // Position the lion
            lionGroup.position.set(-2, 0, 0);
            scene.add(lionGroup);
            
            return lionGroup;
        }
        
        const lion = createLion();
        
        // Create grass tufts
        for (let i = 0; i < 200; i++) {
            const tuftGeometry = new THREE.ConeGeometry(0.2, 1, 4);
            const tuftMaterial = new THREE.MeshStandardMaterial({ 
                color: 0x7CFC00,
                side: THREE.DoubleSide
            });
            const tuft = new THREE.Mesh(tuftGeometry, tuftMaterial);
            
            const x = Math.random() * 80 - 40;
            const z = Math.random() * 80 - 40;
            
            // Don't place grass too close to the lion or tree
            const distToLion = Math.sqrt(Math.pow(x - lion.position.x, 2) + Math.pow(z - lion.position.z, 2));
            const distToTree = Math.sqrt(Math.pow(x - tree.position.x, 2) + Math.pow(z - tree.position.z, 2));
            
            if (distToLion > 4 && distToTree > 5) {
                tuft.position.set(x, 0.5, z);
                tuft.rotation.y = Math.random() * Math.PI;
                tuft.castShadow = true;
                scene.add(tuft);
            }
        }
        
        // Day/night cycle
        let time = 0;
        
        // Animation
        function animate() {
            requestAnimationFrame(animate);
            
            // Update controls
            controls.update();
            
            // Update time and day/night cycle
            time += 0.002;
            const daylight = Math.sin(time) * 0.5 + 0.5;
            ambientLight.intensity = 0.1 + daylight * 0.5;
            directionalLight.intensity = daylight;
            
            // Position the sun
            directionalLight.position.x = Math.sin(time) * 10;
            directionalLight.position.y = Math.sin(time) * 5 + 5;
            directionalLight.position.z = Math.cos(time) * 10;
            
            // Change sky color based on time
            const r = 0.5 + daylight * 0.3;
            const g = 0.6 + daylight * 0.4;
            const b = 0.8 + daylight * 0.2;
            scene.background.setRGB(r, g, b);
            
            // Animate lion (subtle breathing)
            lion.children[0].scale.y = 1 + Math.sin(time * 3) * 0.05;
            lion.children[2].scale.y = 1 + Math.sin(time * 3) * 0.05;
            
            // Animate tail
            lion.children[9].rotation.z = Math.PI / 4 + Math.sin(time * 2) * 0.2;
            lion.children[10].position.x = -2 + Math.sin(time * 2) * 0.1;
            lion.children[10].position.y = 1.8 + Math.sin(time * 2) * 0.1;
            
            renderer.render(scene, camera);
        }
        
        // Handle window resize
        window.addEventListener('resize', function() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        
        // Start animation
        animate();
    </script>
</body>
</html>"""

# Enhanced prompt function using explicit examples
async def enhance_prompt(basic_prompt):
    """Transform a basic prompt into a detailed scene description"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    # Build a system prompt with examples
    example_text = ""
    for example in EXAMPLE_MAPPINGS:
        example_text += f"SIMPLE: \"{example['simple']}\"\n"
        example_text += f"ENHANCED: \"{example['enhanced']}\"\n\n"
    
    system_prompt = f"""You transform simple scene descriptions into detailed specifications for 3D visualization.

Here are examples of the exact transformation expected:

{example_text}
Your job is to transform the user's simple prompt into a similar enhanced description that describes:
1. Core visual elements with specific details (shapes, sizes, colors)
2. Movement and animations that bring the scene to life
3. Lighting and atmospheric effects
4. Interactive elements where appropriate
5. Spatial relationships between objects

CRITICALLY IMPORTANT: Always specify that objects should be created using only THREE.js primitive shapes (boxes, spheres, cylinders, etc.) and NOT using external 3D models or resources.

The enhanced description should be 150-250 words and focus entirely on what should appear in the scene."""
    
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 750,
        "temperature": 0.3,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": f"""Transform this simple description:

"{basic_prompt}"

Into a detailed scene description similar to the examples in your instructions.
Focus only on what should appear in the scene and how it should behave.
IMPORTANT: Specify that all objects must be created using THREE.js primitive shapes (boxes, spheres, cylinders, etc.) and NOT using external 3D models."""}
        ]
    }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            json=data,
            headers=headers
        )
        
        if response.status_code != 200:
            return basic_prompt, f"Error: {response.status_code}"
        
        response_data = response.json()
        
        if "content" in response_data and len(response_data["content"]) > 0:
            enhanced_prompt = response_data["content"][0]["text"]
            return enhanced_prompt, None
        else:
            return basic_prompt, "No content in response"

# Scene generator with improved template approach
async def generate_scene(prompt, simple_prompt):
    """Generate a complete Three.js scene from a prompt"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    # Get example mapping that best matches the concept
    best_example = None
    for i, example in enumerate(EXAMPLE_MAPPINGS):
        if any(keyword in simple_prompt.lower() for keyword in example["simple"].lower().split()):
            best_example = example
            best_example_index = i
            break
    
    if not best_example:
        best_example = EXAMPLE_MAPPINGS[0]  # Default to city example
        best_example_index = 0
    
    # Create a system prompt with the full mapping example
    example_html = LION_EXAMPLE_HTML if best_example_index == 1 else """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>3D City Scene</title>
    <style>
        body {
            margin: 0;
            overflow: hidden;
        }
        canvas {
            display: block;
        }
        #info {
            position: absolute;
            top: 10px;
            width: 100%;
            text-align: center;
            color: white;
            font-family: Arial, sans-serif;
            pointer-events: none;
        }
    </style>
</head>
<body>
    <div id="info">3D City Scene - Use mouse to navigate</div>
    <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
    <script>
        // Scene, camera, renderer setup
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);
        
        // Background
        scene.background = new THREE.Color(0x87CEEB);
        
        // Camera and controls
        camera.position.set(30, 30, 30);
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;
        
        // Lights
        const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
        scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(50, 100, 50);
        directionalLight.castShadow = true;
        scene.add(directionalLight);
        
        // Ground
        const groundGeometry = new THREE.PlaneBufferGeometry(200, 200);
        const groundMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        scene.add(ground);
        
        // Buildings
        function createBuilding(x, z, width, height, depth) {
            const buildingGeometry = new THREE.BoxBufferGeometry(width, height, depth);
            const buildingMaterial = new THREE.MeshStandardMaterial({
                color: Math.random() > 0.5 ? 0x808080 : 0xa0a0a0,
                roughness: 0.7
            });
            
            const building = new THREE.Mesh(buildingGeometry, buildingMaterial);
            building.position.set(x, height/2, z);
            building.castShadow = true;
            building.receiveShadow = true;
            scene.add(building);
            
            // Add windows
            if (height > 5) {
                const windowSize = 0.5;
                const windowGeometry = new THREE.PlaneBufferGeometry(windowSize, windowSize);
                const windowMaterial = new THREE.MeshStandardMaterial({
                    color: 0xaaaaff,
                    emissive: 0x555555,
                    emissiveIntensity: 0.2
                });
                
                // Calculate number of windows based on building size
                const windowsPerFloor = Math.max(1, Math.floor(width / 2));
                const floors = Math.max(1, Math.floor(height / 3));
                
                for (let floor = 0; floor < floors; floor++) {
                    for (let i = 0; i < windowsPerFloor; i++) {
                        // Front windows
                        const frontWindow = new THREE.Mesh(windowGeometry, windowMaterial.clone());
                        frontWindow.position.set(
                            x - width/2 + (i + 0.5) * (width / windowsPerFloor),
                            floor * 3 + 1.5,
                            z + depth/2 + 0.01
                        );
                        scene.add(frontWindow);
                        
                        // Back windows
                        const backWindow = new THREE.Mesh(windowGeometry, windowMaterial.clone());
                        backWindow.position.set(
                            x - width/2 + (i + 0.5) * (width / windowsPerFloor),
                            floor * 3 + 1.5,
                            z - depth/2 - 0.01
                        );
                        backWindow.rotation.y = Math.PI;
                        scene.add(backWindow);
                    }
                }
            }
            
            return building;
        }
        
        // Create buildings in a grid
        const buildings = [];
        for (let x = -80; x < 80; x += 20) {
            for (let z = -80; z < 80; z += 20) {
                // Vary building sizes
                const width = 5 + Math.random() * 10;
                const height = 5 + Math.random() * 40;
                const depth = 5 + Math.random() * 10;
                
                // Add random offset to position
                const offsetX = (Math.random() - 0.5) * 10;
                const offsetZ = (Math.random() - 0.5) * 10;
                
                // Create building
                const building = createBuilding(x + offsetX, z + offsetZ, width, height, depth);
                buildings.push(building);
            }
        }
        
        // Create roads
        function createRoad(x1, z1, x2, z2, width) {
            const length = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(z2 - z1, 2));
            const roadGeometry = new THREE.PlaneBufferGeometry(length, width);
            const roadMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 });
            const road = new THREE.Mesh(roadGeometry, roadMaterial);
            
            // Position and rotate to connect the points
            road.position.set((x1 + x2) / 2, 0.01, (z1 + z2) / 2);
            road.rotation.x = -Math.PI / 2;
            road.rotation.z = Math.atan2(z2 - z1, x2 - x1);
            
            road.receiveShadow = true;
            scene.add(road);
            
            return road;
        }
        
        // Create grid of roads
        const roads = [];
        for (let i = -80; i <= 80; i += 20) {
            // Horizontal roads
            createRoad(-80, i, 80, i, 10);
            // Vertical roads
            createRoad(i, -80, i, 80, 10);
        }
        
        // Create cars
        const cars = [];
        function createCar() {
            const car = new THREE.Group();
            
            // Car body
            const bodyGeometry = new THREE.BoxBufferGeometry(2, 0.7, 1);
            const bodyMaterial = new THREE.MeshStandardMaterial({
                color: Math.random() * 0xffffff
            });
            const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
            body.castShadow = true;
            car.add(body);
            
            // Car top
            const topGeometry = new THREE.BoxBufferGeometry(1, 0.5, 0.9);
            const topMaterial = new THREE.MeshStandardMaterial({
                color: 0x333333
            });
            const top = new THREE.Mesh(topGeometry, topMaterial);
            top.position.y = 0.6;
            top.castShadow = true;
            car.add(top);
            
            // wheels
            const wheelGeometry = new THREE.CylinderBufferGeometry(0.3, 0.3, 0.2, 8);
            const wheelMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 });
            
            const wheel1 = new THREE.Mesh(wheelGeometry, wheelMaterial);
            wheel1.position.set(0.7, -0.3, 0.5);
            wheel1.rotation.z = Math.PI / 2;
            car.add(wheel1);
            
            const wheel2 = new THREE.Mesh(wheelGeometry, wheelMaterial);
            wheel2.position.set(0.7, -0.3, -0.5);
            wheel2.rotation.z = Math.PI / 2;
            car.add(wheel2);
            
            const wheel3 = new THREE.Mesh(wheelGeometry, wheelMaterial);
            wheel3.position.set(-0.7, -0.3, 0.5);
            wheel3.rotation.z = Math.PI / 2;
            car.add(wheel3);
            
            const wheel4 = new THREE.Mesh(wheelGeometry, wheelMaterial);
            wheel4.position.set(-0.7, -0.3, -0.5);
            wheel4.rotation.z = Math.PI / 2;
            car.add(wheel4);
            
            // Add to scene
            scene.add(car);
            
            // Random position on a road
            const lane = Math.floor(Math.random() * 9) - 4;
            const randomPos = (Math.random() - 0.5) * 160;
            
            if (Math.random() > 0.5) {
                // Horizontal road
                car.position.set(randomPos, 0.6, lane * 20);
                car.rotation.y = Math.random() > 0.5 ? 0 : Math.PI;
            } else {
                // Vertical road
                car.position.set(lane * 20, 0.6, randomPos);
                car.rotation.y = Math.random() > 0.5 ? Math.PI / 2 : -Math.PI / 2;
            }
            
            // Store direction
            car.userData.direction = car.rotation.y;
            car.userData.speed = 0.1 + Math.random() * 0.1;
            
            return car;
        }
        
        // Create cars
        for (let i = 0; i < 30; i++) {
            cars.push(createCar());
        }
        
        // Animation loop
        function animate() {
            requestAnimationFrame(animate);
            
            // Update car positions
            cars.forEach(car => {
                const speed = car.userData.speed;
                
                // Move car based on its rotation
                if (car.rotation.y === 0) {
                    car.position.x += speed;
                    if (car.position.x > 85) car.position.x = -85;
                } else if (Math.abs(car.rotation.y - Math.PI) < 0.1) {
                    car.position.x -= speed;
                    if (car.position.x < -85) car.position.x = 85;
                } else if (Math.abs(car.rotation.y - Math.PI/2) < 0.1) {
                    car.position.z -= speed;
                    if (car.position.z < -85) car.position.z = 85;
                } else {
                    car.position.z += speed;
                    if (car.position.z > 85) car.position.z = -85;
                }
            });
            
            // Update controls
            controls.update();
            
            // Render scene
            renderer.render(scene, camera);
        }
        
        // Handle window resize
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        
        // Start animation loop
        animate();
    </script>
</body>
</html>"""
    
    system_prompt = f"""You are an expert Three.js developer who creates complete, working 3D web applications.

I'll provide you with a description of a 3D scene. Your task is to generate a SINGLE, COMPLETE HTML file containing a Three.js scene that implements this description.

CRITICALLY IMPORTANT: DO NOT USE EXTERNAL 3D MODELS OR RESOURCES. Create all scene elements using Three.js primitive shapes like BoxGeometry, SphereGeometry, CylinderGeometry, etc.

Here's an example of the transformation from simple prompt to enhanced description to working HTML:

SIMPLE PROMPT: "{best_example['simple']}"

ENHANCED DESCRIPTION: "{best_example['enhanced']}"

WORKING HTML: {example_html}

Now, create a scene based on this description: "{prompt}"

Your output must:
1. Be a COMPLETE HTML document with all necessary Three.js imports
2. Use unpkg.com CDN links for Three.js (version 0.137.0 or newer)
3. Include OrbitControls for camera navigation
4. Have proper lighting, shadows, and camera setup
5. Implement animations that bring the scene to life
6. Create ALL objects using Three.js primitive shapes (NOT GLTFLoader or other model loaders)
7. Include a help message in a #info div to guide users
8. Ensure all code is properly closed and browsers will render the scene correctly

RETURN ONLY THE COMPLETE HTML DOCUMENT."""
    
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 4000,
        "temperature": 0.2,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": f"""Create a complete, working Three.js scene based on this description:

{prompt}

Generate ONLY a complete HTML document with embedded JavaScript. Your HTML must include:
1. Proper <head> section with viewport settings and styles
2. Three.js and OrbitControls imported from unpkg.com (not CloudFlare)
3. A complete scene setup with proper lighting
4. Animated elements to bring the scene to life
5. A help message in a #info div for users
6. Responsive design that works on all screen sizes
7. Create ALL objects using Three.js primitive shapes (NO EXTERNAL MODELS)

DO NOT use GLTFLoader or try to load external 3D models. Build all scene elements directly using Three.js geometry.

Your response should start with <!DOCTYPE html> and end with </html>."""}
        ]
    }
    
    debug_info = {
        "request": {
            "simple_prompt": simple_prompt,
            "enhanced_prompt": prompt,
            "system_prompt_length": len(system_prompt),
            "model": data["model"],
            "max_tokens": data["max_tokens"],
            "temperature": data["temperature"]
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            json=data,
            headers=headers
        )
        
        debug_info["status_code"] = response.status_code
        
        if response.status_code != 200:
            debug_info["error"] = f"API error: {response.status_code} - {response.text}"
            return None, debug_info
        
        response_data = response.json()
        debug_info["response_meta"] = {
            "model": response_data.get("model", ""),
            "usage": response_data.get("usage", {}),
        }
        
        if "content" in response_data and len(response_data["content"]) > 0:
            response_text = response_data["content"][0]["text"]
            # Get just the HTML portion
            html_content = extract_html_from_response(response_text)
            # Ensure it uses reliable CDN URLs
            html_content = fix_cdn_urls(html_content)
            # Remove any GLTFLoader references
            html_content = remove_gltf_loader(html_content)
            debug_info["html_length"] = len(html_content)
            return html_content, debug_info
        else:
            debug_info["error"] = "No content in response"
            return None, debug_info

# Extract HTML from response
def extract_html_from_response(response_text):
    """Extract a complete HTML document from the response text"""
    # Look for a complete HTML document
    html_pattern = r"<!DOCTYPE html>[\s\S]*?<\/html>"
    html_match = re.search(html_pattern, response_text, re.IGNORECASE)
    
    if html_match:
        return html_match.group(0)
    
    # If no match, check for HTML without doctype
    html_pattern = r"<html[\s\S]*?<\/html>"
    html_match = re.search(html_pattern, response_text, re.IGNORECASE)
    
    if html_match:
        return f"<!DOCTYPE html>\n{html_match.group(0)}"
    
    # If still no match, try to extract from code blocks
    code_pattern = r"```(?:html)?\s*([\s\S]*?)\s*```"
    code_matches = re.findall(code_pattern, response_text)
    
    if code_matches:
        # Check each code block for HTML content
        for code in code_matches:
            if "<html" in code.lower() or "<!doctype" in code.lower():
                if code.lower().startswith("<!doctype html>"):
                    return code
                elif code.lower().startswith("<html"):
                    return f"<!DOCTYPE html>\n{code}"
        
        # If no HTML found, use the first code block and wrap it
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated 3D Scene</title>
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
    <div id="info">Generated 3D Scene - Use mouse to navigate</div>
    <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
    <script>
    {code_matches[0]}
    </script>
</body>
</html>"""
    
    # Last resort - create a fallback scene
    return create_fallback_scene()

# Fix CDN URLs to use unpkg.com instead of CloudFlare
def fix_cdn_urls(html_content):
    """Replace CDN URLs with reliable ones from unpkg.com"""
    # Replace CloudFlare Three.js URL
    html_content = re.sub(
        r'(https?:)?\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/three\.js\/[^\/]+\/three\.min\.js',
        'https://unpkg.com/three@0.137.0/build/three.min.js',
        html_content
    )
    
    # Replace CloudFlare OrbitControls URL
    html_content = re.sub(
        r'(https?:)?\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/three\.js\/[^\/]+\/controls\/OrbitControls\.min\.js',
        'https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js',
        html_content
    )
    
    return html_content

# Remove GLTF loader and model loading
def remove_gltf_loader(html_content):
    """Remove GLTFLoader and model loading from the HTML"""
    # Remove GLTFLoader import
    html_content = re.sub(
        r'<script src="[^"]*GLTFLoader[^"]*"><\/script>',
        '',
        html_content
    )
    
    # If GLTFLoader is found, inject the lion example code
    if "GLTFLoader" in html_content or "loader.load(" in html_content:
        html_content = html_content.replace("</body>", """
    <script>
        // Alert about external model attempt
        console.warn("External model loading detected and removed. Using primitive shapes instead.");
        
        // Create lion using primitives
        function createLion() {
            const lionGroup = new THREE.Group();
            
            // Body
            const bodyGeometry = new THREE.SphereGeometry(1, 16, 16);
            const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0xC2B280 });
            const body = new THREE.Mesh(bodyGeometry, bodyMaterial);
            body.scale.set(1.2, 1, 1.5);
            body.position.y = 1.1;
            body.castShadow = true;
            lionGroup.add(body);
            
            // Head
            const headGeometry = new THREE.SphereGeometry(0.7, 16, 16);
            const headMaterial = new THREE.MeshStandardMaterial({ color: 0xC2B280 });
            const head = new THREE.Mesh(headGeometry, headMaterial);
            head.position.set(1.2, 1.5, 0);
            head.castShadow = true;
            lionGroup.add(head);
            
            // Mane
            const maneGeometry = new THREE.SphereGeometry(1, 16, 16);
            const maneMaterial = new THREE.MeshStandardMaterial({ color: 0xCD853F });
            const mane = new THREE.Mesh(maneGeometry, maneMaterial);
            mane.position.set(1.2, 1.5, 0);
            mane.scale.set(1.2, 1.2, 1.2);
            mane.castShadow = true;
            lionGroup.add(mane);
            
            // Face
            const snoutGeometry = new THREE.CylinderGeometry(0.2, 0.3, 0.4, 8);
            const snoutMaterial = new THREE.MeshStandardMaterial({ color: 0xD2B48C });
            const snout = new THREE.Mesh(snoutGeometry, snoutMaterial);
            snout.position.set(1.7, 1.4, 0);
            snout.rotation.z = Math.PI / 2;
            snout.castShadow = true;
            lionGroup.add(snout);
            
            // Eyes
            const eyeGeometry = new THREE.SphereGeometry(0.1, 8, 8);
            const eyeMaterial = new THREE.MeshStandardMaterial({ color: 0x000000 });
            
            const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
            leftEye.position.set(1.6, 1.7, 0.3);
            lionGroup.add(leftEye);
            
            const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
            rightEye.position.set(1.6, 1.7, -0.3);
            lionGroup.add(rightEye);
            
            // Legs
            const legGeometry = new THREE.CylinderGeometry(0.2, 0.2, 1, 8);
            const legMaterial = new THREE.MeshStandardMaterial({ color: 0xC2B280 });
            
            const frontLeftLeg = new THREE.Mesh(legGeometry, legMaterial);
            frontLeftLeg.position.set(0.6, 0.5, 0.5);
            frontLeftLeg.castShadow = true;
            lionGroup.add(frontLeftLeg);
            
            const frontRightLeg = new THREE.Mesh(legGeometry, legMaterial);
            frontRightLeg.position.set(0.6, 0.5, -0.5);
            frontRightLeg.castShadow = true;
            lionGroup.add(frontRightLeg);
            
            const backLeftLeg = new THREE.Mesh(legGeometry, legMaterial);
            backLeftLeg.position.set(-0.6, 0.5, 0.5);
            backLeftLeg.castShadow = true;
            lionGroup.add(backLeftLeg);
            
            const backRightLeg = new THREE.Mesh(legGeometry, legMaterial);
            backRightLeg.position.set(-0.6, 0.5, -0.5);
            backRightLeg.castShadow = true;
            lionGroup.add(backRightLeg);
            
            // Tail
            const tailGeometry = new THREE.CylinderGeometry(0.1, 0.15, 1.5, 8);
            const tailMaterial = new THREE.MeshStandardMaterial({ color: 0xC2B280 });
            const tail = new THREE.Mesh(tailGeometry, tailMaterial);
            tail.position.set(-1.5, 1.2, 0);
            tail.rotation.z = Math.PI / 4;
            tail.castShadow = true;
            lionGroup.add(tail);
            
            // Tail tuft
            const tuftGeometry = new THREE.SphereGeometry(0.2, 8, 8);
            const tuftMaterial = new THREE.MeshStandardMaterial({ color: 0x8B4513 });
            const tuft = new THREE.Mesh(tuftGeometry, tuftMaterial);
            tuft.position.set(-2, 1.8, 0);
            tuft.castShadow = true;
            lionGroup.add(tuft);
            
            // Position the lion
            lionGroup.position.set(-2, 0, 0);
            scene.add(lionGroup);
            
            return lionGroup;
        }
        
        const lion = createLion();
        let animateLion = function(time) {
            // Animate lion (subtle breathing)
            lion.children[0].scale.y = 1 + Math.sin(time * 3) * 0.05;
            lion.children[2].scale.y = 1 + Math.sin(time * 3) * 0.05;
            
            // Animate tail
            lion.children[9].rotation.z = Math.PI / 4 + Math.sin(time * 2) * 0.2;
            lion.children[10].position.x = -2 + Math.sin(time * 2) * 0.1;
            lion.children[10].position.y = 1.8 + Math.sin(time * 2) * 0.1;
        };
        
        // Update the animation function to include lion animation
        const originalAnimateFunction = animate;
        animate = function() {
            let time = Date.now() * 0.001;
            if (typeof animateLion === 'function') {
                animateLion(time);
            }
            originalAnimateFunction();
        };
    </script>
</body>""")
        
        # Also remove any loader.load calls
        html_content = re.sub(
            r'const loader = new THREE\.GLTFLoader\(\);[\s\S]*?loader\.load\([^\)]*\)[^\}]*\}\);',
            '// External model loading removed',
            html_content
        )
    
    return html_content

# Create a fallback scene if all else fails
def create_fallback_scene():
    """Create a basic fallback scene when extraction fails"""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fallback 3D Scene</title>
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
        #error {
            position: absolute;
            bottom: 20px;
            width: 100%;
            text-align: center;
            color: #ff4444;
            font-family: Arial, sans-serif;
            font-weight: bold;
            pointer-events: none;
            text-shadow: 1px 1px 1px black;
        }
    </style>
</head>
<body>
    <div id="info">Fallback 3D Scene</div>
    <div id="error">Scene generation failed - See debug info</div>
    <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
    <script>
    // Create a basic scene with an error message
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x333344);
    
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 5, 10);
    
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);
    
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 7.5);
    scene.add(directionalLight);
    
    // Create a platform
    const platformGeometry = new THREE.CylinderGeometry(5, 5, 0.5, 32);
    const platformMaterial = new THREE.MeshPhongMaterial({ color: 0x888888 });
    const platform = new THREE.Mesh(platformGeometry, platformMaterial);
    platform.position.y = -0.25;
    scene.add(platform);
    
    // Create error message cube
    const cubeGeometry = new THREE.BoxGeometry(3, 3, 3);
    const cubeMaterial = new THREE.MeshPhongMaterial({ color: 0xff4444 });
    const cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
    cube.position.y = 1.5;
    scene.add(cube);
    
    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        cube.rotation.y += 0.01;
        controls.update();
        renderer.render(scene, camera);
    }
    animate();
    
    // Handle window resize
    window.addEventListener('resize', function() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    </script>
</body>
</html>"""

# Complete scene generation pipeline
async def generate_scene_from_prompt(basic_prompt):
    """Complete pipeline: enhance prompt then generate scene"""
    # Step 1: Enhance the prompt with more details
    enhanced_prompt, enhance_error = await enhance_prompt(basic_prompt)
    
    if enhance_error:
        st.warning(f"Warning: Using basic prompt because enhancement failed: {enhance_error}")
        prompt_to_use = basic_prompt
    else:
        prompt_to_use = enhanced_prompt
    
    # Step 2: Generate the scene with the enhanced prompt
    html_content, debug_info = await generate_scene(prompt_to_use, basic_prompt)
    
    # Store both prompts and debug info
    debug_info["original_prompt"] = basic_prompt
    debug_info["enhanced_prompt"] = prompt_to_use
    
    return html_content, debug_info

# Function to save a scene to history
def save_to_history(scene_data):
    # Add timestamp to the scene data
    scene_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add the scene to history
    st.session_state.scene_history.append(scene_data)
    
    # Limit history to last 10 scenes
    if len(st.session_state.scene_history) > 10:
        st.session_state.scene_history = st.session_state.scene_history[-10:]

# Function to load a scene from history
def load_from_history(index):
    if 0 <= index < len(st.session_state.scene_history):
        st.session_state.current_scene = st.session_state.scene_history[index]
        st.session_state.history_index = index
        return True
    return False

# Main app UI
def main():
    # Sidebar for history
    with st.sidebar:
        st.title("Scene History")
        
        if len(st.session_state.scene_history) > 0:
            for i, scene in enumerate(reversed(st.session_state.scene_history)):
                index = len(st.session_state.scene_history) - 1 - i
                
                # Create an expander for each history item
                with st.expander(f"{scene['prompt'][:30]}..." if len(scene['prompt']) > 30 else scene['prompt']):
                    st.write(f"Created: {scene['timestamp']}")
                    if st.button("Load Scene", key=f"load_{index}"):
                        load_from_history(index)
                        st.rerun()
        else:
            st.info("No scenes in history yet. Create a scene to see it here!")
    
    # Main content area
    st.title("🎮 Instant 3D Scene Generator")
    st.write("Describe any scene and see it in 3D instantly!")
    
    # Create tabs for main content
    tab1, tab2, tab3 = st.tabs(["Create Scene", "Solar System Demo", "Scene Details"])
    
    with tab1:
        # Main input form
        with st.form("scene_generator_form"):
            user_prompt = st.text_area(
                "Describe your 3D scene:",
                placeholder="A lion sitting under a tree in a grassy field",
                height=80
            )
            
            generate_button = st.form_submit_button("Generate 3D Scene")
            
            if generate_button and user_prompt:
                with st.spinner("Creating your 3D scene... (this may take up to a minute)"):
                    html_content, debug_info = asyncio.run(generate_scene_from_prompt(user_prompt))
                    
                    if html_content:
                        # Store the current scene
                        scene_data = {
                            "prompt": user_prompt,
                            "enhanced_prompt": debug_info.get("enhanced_prompt", user_prompt),
                            "html": html_content,
                            "debug_info": debug_info
                        }
                        
                        st.session_state.current_scene = scene_data
                        
                        # Add to history
                        save_to_history(scene_data)
                        
                        st.success("Scene generated successfully!")
                    else:
                        st.error("Failed to generate scene. See debug tab for details.")
                        st.session_state.debug_info = debug_info
        
        # Display current scene if available
        if "current_scene" in st.session_state and st.session_state.current_scene:
            scene = st.session_state.current_scene
            
            # Show the scene in an HTML component
            st.components.v1.html(scene["html"], height=600)
            
            # Information about navigating the scene
            st.info("**Navigation:** Left-click + drag to rotate | Right-click + drag to pan | Scroll to zoom")
            
            # Download button
            st.download_button(
                label="Download HTML",
                data=scene["html"],
                file_name="3d_scene.html",
                mime="text/html"
            )
    
    with tab2:
        # Solar System Demo
        st.subheader("Solar System Demo")
        st.write("Explore our solar system in 3D! Use your mouse to navigate around the scene.")
        
        # Display the solar system scene
        st.components.v1.html(SOLAR_SYSTEM_HTML, height=600)
        
        # Information about navigating the scene
        st.info("**Navigation:** Left-click + drag to rotate | Right-click + drag to pan | Scroll to zoom")
        
        # Info about the solar system
        st.write("""
        This demo shows a scale model of our solar system with:
        - The Sun at the center with a yellow glow
        - All eight planets orbiting at different speeds
        - Saturn with its distinctive rings
        - Earth with its moon
        - A starry background
        
        Each planet is created using Three.js primitives and has simple animations to show orbital motion.
        """)
    
    with tab3:
        # Scene details
        if "current_scene" in st.session_state and st.session_state.current_scene:
            scene = st.session_state.current_scene
            
            # Show the prompts
            st.subheader("Prompts")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Original Prompt")
                st.info(scene["prompt"])
            
            with col2:
                st.write("Enhanced Prompt")
                st.success(scene["enhanced_prompt"])
            
            # Show the HTML code
            st.subheader("Generated HTML")
            with st.expander("View HTML Code"):
                st.code(scene["html"], language="html")
            
            # Show debug info
            st.subheader("Debug Information")
            with st.expander("View Debug Info"):
                st.json(scene["debug_info"])
        else:
            st.info("Generate a scene to see details here.")

# Instructions
if __name__ == "__main__":
    main()
