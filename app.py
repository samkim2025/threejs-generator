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

# Example prompts for the scene generator
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

# Enhanced prompt function using explicit examples
async def enhanc
