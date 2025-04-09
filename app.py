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
if "show_enhanced_complete" not in st.session_state:
    st.session_state.show_enhanced_complete = False
if "current_enhanced_prompt" not in st.session_state:
    st.session_state.current_enhanced_prompt = ""

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

# Modified prompt enhancement function with length constraint
async def enhance_prompt(basic_prompt):
    """Takes a simple prompt and expands it with detailed Three.js specifications"""
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Modified system prompt to request more concise output
        system_prompt = """You are an expert in Three.js scene creation. Your task is to expand simple scene descriptions into technical specifications that can be implemented in Three.js.

For the scene description, provide a focused and concise technical specification that covers:
1. Scene elements with precise geometries, materials, and positioning
2. Lighting setup
3. Animation details
4. Camera settings and controls

Be specific but also efficient with your response length. Focus on the most essential elements that would make this scene work effectively.
Keep your response under 800 words to ensure it doesn't exceed token limits."""
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,  # Limiting the token count
            "temperature": 0.2,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"""Take this simple scene description:
                
"{basic_prompt}"
                
Expand it into a detailed but concise Three.js technical specification that can be implemented efficiently.
Focus on the core elements needed to create this scene.
Keep your response under 800 words."""}
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

# Modified API call with emphasis on conciseness and completeness
async def call_anthropic_api(prompt):
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Modified system prompt focusing on concise, complete output
        system_prompt = """You are an expert in Three.js 3D scene creation.

Your task is to generate a CONCISE, working HTML document with a Three.js scene based on the user's description.

IMPORTANT REQUIREMENTS:
1. Create a MINIMAL but COMPLETE HTML file with less than 250 lines of code
2. Focus on creating a BASIC scene that captures the essence of the request
3. Use simple geometries and techniques - prioritize WORKING code over complexity
4. AVOID complex shaders, excessive objects, or detailed models
5. Make sure your response is COMPLETE with all closing tags and brackets
6. Use Three.js version 0.137.0 and OrbitControls

Your response must:
- START with <!DOCTYPE html> and END with </html>
- Include only the HTML document with no explanations
- Be simple enough to avoid output truncation
- Prioritize completeness over sophistication"""
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 3000,  # Adjusted to handle complete but concise responses
            "temperature": 0.1,  # Lower temperature for more deterministic output
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"""Create a minimal Three.js scene based on this description: {prompt}

Return a COMPLETE and SIMPLE HTML document. Focus on making it work rather than making it complex.
Keep the code under 250 lines total, focusing on the core elements.
Make sure to include proper beginning and ending tags for all HTML elements.

The scene should be minimal but functional, capturing the essence of: "{prompt}"."""}
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

# Improved HTML extraction - focusing on finding a COMPLETE document
def extract_html_from_response(response_text):
    # Look for complete HTML document with doctype
    doctype_pattern = r"<!DOCTYPE html>[\s\S]*?<\/html>"
    doctype_matches = re.search(doctype_pattern, response_text, re.IGNORECASE)
    
    if doctype_matches:
        return doctype_matches.group(0)
    
    # Try looking for HTML without doctype
    html_pattern = r"<html[\s\S]*?<\/html>"
    html_matches = re.search(html_pattern, response_text, re.IGNORECASE)
    
    if html_matches:
        html_content = html_matches.group(0)
        return f"<!DOCTYPE html>\n{html_content}"
    
    # Look for code blocks
    code_block_pattern = r"```(?:html)?([\s\S]*?)```"
    code_matches = re.findall(code_block_pattern, response_text)
    
    if code_matches:
        # Try each code block to find HTML content
        for code in code_matches:
            code = code.strip()
            if "<html" in code.lower() or "<!doctype" in code.lower():
                # This appears to be HTML
                if code.lower().startswith("<!doctype html>"):
                    return code
                elif code.lower().startswith("<html"):
                    return f"<!DOCTYPE html>\n{code}"
                else:
                    # Fragment of HTML - try to identify the structure
                    if "<body" in code and "</body>" in code:
                        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Generated Three.js Scene</title>
    <style>
        body {{ margin: 0; overflow: hidden; }}
    </style>
</head>
{code}
</html>"""
        
        # If we reach here, use the first code block and try to make it complete
        html_content = code_matches[0].strip()
        
        # Check if it contains the Three.js scene setup
        if "new THREE.Scene" in html_content:
            if not html_content.startswith("<script>"):
                html_content = f"<script>\n{html_content}\n</script>"
            
            return f"""<!DOCTYPE html>
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
</html>"""
    
    # Last resort - check if there's any JavaScript THREE.js code in the response
    if "new THREE." in response_text:
        # Extract the JavaScript section, assuming it's the main content
        js_code = response_text.split("new THREE.")[1:]
        js_code = "new THREE." + "new THREE.".join(js_code)
        
        # Wrap with proper HTML structure
        return f"""<!DOCTYPE html>
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
    // Scene setup from API response
    {js_code}
    </script>
</body>
</html>"""
    
    # Fallback template with error message
    return f"""<!DOCTYPE html>
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
    <div id="info">Could not generate proper Three.js scene - See debug info</div>
    <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
    <script>
    // Basic scene setup
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

    // Light
    const light = new THREE.DirectionalLight(0xffffff, 1);
    light.position.set(5, 10, 7.5);
    scene.add(light);
    
    // Error message object
    const geometry = new THREE.BoxGeometry(5, 1, 5);
    const material = new THREE.MeshBasicMaterial({{ color: 0xff4444 }});
    const cube = new THREE.Mesh(geometry, material);
    cube.position.y = 0.5;
    scene.add(cube);
    
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
</html>"""

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
    
    # Check if we're at the review stage for the enhanced prompt
    if st.session_state.show_enhanced_complete:
        st.subheader("Enhanced Prompt")
        st.write(st.session_state.current_enhanced_prompt)
        
        col1, col2 = st.columns(2)
        
        # Button to continue with generation
        with col1:
            if st.button("Generate Scene with this Enhanced Prompt"):
                with st.spinner("Generating your 3D scene... (this may take up to a minute)"):
                    # Call API with enhanced prompt
                    response_text, debug_info = asyncio.run(call_anthropic_api(st.session_state.current_enhanced_prompt))
                    
                    if response_text:
                        # Extract HTML
                        final_html = extract_html_from_response(response_text)
                        
                        # Save current scene to state
                        st.session_state.current_scene = {
                            "prompt": st.session_state.raw_prompt,
                            "enhanced_prompt": st.session_state.current_enhanced_prompt,
                            "html": final_html, 
                            "full_response": response_text,
                            "is_preset": False
                        }
                        # Reset the review stage flag
                        st.session_state.show_enhanced_complete = False
                        st.success("Scene generated successfully!")
                    else:
                        st.error("Failed to generate scene. See Debug tab for details.")
        
        # Button to go back
        with col2:
            if st.button("Back to Prompt"):
                st.session_state.show_enhanced_complete = False
                st.experimental_rerun()
    
    # If not at review stage, show the form
    else:
        with st.form("custom_scene_form"):
            user_prompt = st.text_area(
                "Describe your 3D scene:",
                placeholder="A futuristic city with neon buildings and flying vehicles",
                height=100
            )
            
            # Checkbox to view enhanced prompt before generation
            show_enhanced = st.checkbox("Show enhanced prompt before generation")
            
            submitted = st.form_submit_button("Generate Scene")
            
            if submitted and user_prompt:
                if show_enhanced:
                    # Just show the enhanced prompt without generating
                    with st.spinner("Enhancing your prompt..."):
                        enhanced_prompt, enhance_error = asyncio.run(enhance_prompt(user_prompt))
                        if enhance_error:
                            st.error(f"Error enhancing prompt: {enhance_error}")
                        else:
                            # Store the prompts and set the review flag
                            st.session_state.raw_prompt = user_prompt
                            st.session_state.enhanced_prompt = enhanced_prompt
                            st.session_state.current_enhanced_prompt = enhanced_prompt
                            st.session_state.show_enhanced_complete = True
                            st.experimental_rerun()
                else:
                    # Generate directly with enhanced prompt
                    with st.spinner("Generating your 3D scene... (this may take up to 2 minutes)"):
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
    
    # Add note about token limits
    st.info("### Note about response limits\n\n"
            "The API has token limits that can cause issues with complex scenes. "
            "The system has been modified to request simpler, more concise scenes that are less likely to "
            "be truncated during generation. If you're seeing incomplete scenes, try simpler descriptions.")
    
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
                
                # Show content length information
                if "content" in debug_info["response"] and len(debug_info["response"]["content"]) > 0:
                    content_text = debug_info["response"]["content"][0]["text"]
                    st.write(f"Response content length: {len(content_text)} characters")
                    
                    # Check for signs of truncation
                    if not content_text.strip().endswith("</html>"):
                        st.warning("⚠️ Response appears to be truncated (doesn't end with </html>)")
                    
                    # Show the end of the response for debugging
                    if len(content_text) > 300:
                        st.write("Last 300 characters of response:")
                        st.code(content_text[-300:])

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
   - Keep descriptions simple and concise to avoid token limit issues
   - Optionally check "Show enhanced prompt" to review before generation
3. **Debug Info**: View prompt enhancements and API details in the third tab
4. **Interact** with any scene using your mouse:
   - Left-click + drag: Rotate the camera
   - Right-click + drag: Pan the camera
   - Scroll: Zoom in/out
5. **Download**: Save the HTML to open in your browser

### About Token Limits

This application works with API token limits that can affect scene generation:
- Complex scenes may be truncated if they exceed these limits
- The app has been optimized to generate simpler, complete scenes
- For best results, use concise descriptions focusing on core elements
- Check the Debug tab if your scene doesn't render correctly
""")
