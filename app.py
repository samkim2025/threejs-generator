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

# Pre-built scenes (only solar system)
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

# Get API key (using environment variable rather than secrets for simplicity)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Prompt enhancement function
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
        
        # Improved system prompt with more directive guidance
        system_prompt = """You are an expert in Three.js 3D scene creation.

Your task is to generate a working, standalone HTML document with a Three.js scene based on the user's description.

Important requirements:
1. The output must be a COMPLETE and VALID HTML document
2. Include the necessary Three.js library and OrbitControls
3. Create a scene that works without external resources
4. Implement the scene exactly as described by the user
5. Include proper camera controls, lighting, and animation
6. Make sure all code is properly closed and syntactically correct

DO NOT include explanations or markdown - ONLY output the full HTML document.
DO NOT truncate your response - I need the COMPLETE HTML file.
Your response should START with <!DOCTYPE html> and END with </html>."""
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"""Create a complete Three.js scene based on this description: {prompt}

Return ONLY a working HTML document (not HTML fragments).
Do not include any explanation or markdown formatting.
The document should include ALL necessary scripts, styles, and code.
It must be a COMPLETE, STANDALONE HTML file that I can save and run directly in a browser.

Your response must start with <!DOCTYPE html> and contain a complete, working Three.js scene."""}
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

# Improved HTML extraction - focusing on getting a complete document
def extract_html_from_response(response_text):
    # Look for complete HTML document
    html_pattern = r"<!DOCTYPE html>[\s\S]*?<\/html>"
    html_matches = re.search(html_pattern, response_text, re.IGNORECASE)
    
    if html_matches:
        return html_matches.group(0)
    
    # If no complete document, look for code blocks
    code_block_pattern = r"```(?:html)?([\s\S]*?)```"
    code_matches = re.findall(code_block_pattern, response_text)
    
    if code_matches:
        # Check if any code block contains complete HTML
        for code in code_matches:
            code = code.strip()
            if code.lower().startswith("<!doctype html>") or code.lower().startswith("<html"):
                # This looks like a complete HTML document
                return code
        
        # If no complete HTML found in code blocks, use the first block and wrap it
        html_content = code_matches[0].strip()
        
        # If it contains script tag but no HTML structure, wrap it properly
        if "<script>" in html_content and not (html_content.lower().startswith("<!doctype") or html_content.lower().startswith("<html")):
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
                {html_content}
            </body>
            </html>
            """
        else:
            return html_content
    
    # If we still don't have HTML, look for Three.js specific code in the response
    if "new THREE." in response_text:
        # Extract all text from response and wrap it in a proper document
        js_code = response_text.strip()
        
        # Ensure it's wrapped in script tags if not already
        if not js_code.startswith("<script>"):
            js_code = f"<script>\n{js_code}\n</script>"
        
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
            {js_code}
        </body>
        </html>
        """
    
    # Last resort fallback - create a basic scene template with a message
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
        <div id="info">Generated Three.js Scene - Could not parse response properly</div>
        <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
        <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
        <script>
        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x335577);
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
        
        // Fallback object with user prompt text
        const geometry = new THREE.BoxGeometry(5, 1, 5);
        const material = new THREE.MeshPhongMaterial({{ color: 0xff4444 }});
        const cube = new THREE.Mesh(geometry, material);
        cube.castShadow = true;
        cube.position.y = 0.5;
        scene.add(cube);
        
        // Add text showing the scene couldn't be generated
        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 256;
        const context = canvas.getContext('2d');
        context.fillStyle = '#ffffff';
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.font = 'Bold 36px Arial';
        context.fillStyle = '#000000';
        context.textAlign = 'center';
        context.fillText('Scene generation error', canvas.width/2, canvas.height/2 - 20);
        context.font = '24px Arial';
        context.fillText('See debug info for details', canvas.width/2, canvas.height/2 + 20);
        
        const texture = new THREE.CanvasTexture(canvas);
        const textGeometry = new THREE.PlaneGeometry(4, 2);
        const textMaterial = new THREE.MeshBasicMaterial({{ map: texture, side: THREE.DoubleSide }});
        const textMesh = new THREE.Mesh(textGeometry, textMaterial);
        textMesh.position.set(0, 2, 0);
        scene.add(textMesh);
        
        // Animation loop
        function animate() {{
            requestAnimationFrame(animate);
            cube.rotation.y += 0.01;
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

# Get custom scene with prompt enhancement
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
    st.subheader("Solar System Preset")
    
    # Only including the Solar System preset option
    if st.button("Load Solar System Scene", key="load_preset"):
        scene_html = get_solar_system_scene()
        st.session_state.current_scene = {
            "prompt": "Solar System",
            "html": scene_html,
            "is_preset": True
        }
        st.success("Loaded Solar System scene!")

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
                                response_text, debug_info = asyncio.run(call_anthropic_api(enhanced_prompt))
                                
                                if response_text:
                                    # Extract HTML
                                    final_html = extract_html_from_response(response_text)
                                    
                                    # Save current scene to state
                                    st.session_state.current_scene = {
                                        "prompt": user_prompt,
                                        "enhanced_prompt": enhanced_prompt,
                                        "html": final_html, 
                                        "full_response": response_text,
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

1. **Preset Scene**: Load the Solar System preset from the first tab
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
