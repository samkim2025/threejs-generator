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

# Include prebuilt scenes
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

# Get API key from environment variable
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

# Direct API call function for scene generation
async def generate_scene(prompt):
    """Generate Three.js scene HTML directly from a prompt"""
    try:
        # Debug logging
        st.session_state.debug_info["generation_attempt"] = True
        st.session_state.debug_info["generation_prompt"] = prompt
        
        # Log the length of the prompt
        st.session_state.debug_info["prompt_length"] = len(prompt)
        
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Simplified system prompt to focus on generating working HTML
        system_prompt = """You are an expert in Three.js 3D scene creation. Create a complete standalone HTML document with Three.js that implements the described scene.

Include:
- All Three.js imports (use version 0.137.0 from unpkg CDN)
- Complete HTML, CSS, and JavaScript
- Scene setup with camera, renderer, and lighting
- Orbit controls for user interaction
- All described objects and animations
- Proper shadows and materials
- Window resize handling

Focus on creating a working, visually appealing scene that runs in a browser.
Return ONLY the complete HTML document with no explanations or markdown.
"""
        
        # Format a direct prompt asking for HTML
        message = f"""Create a complete Three.js scene based on this specification:

{prompt}

Return ONLY the complete HTML document with embedded JavaScript. No explanations or markdown.
Make sure to include all Three.js imports from the CDN.
"""
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4000,
            "temperature": 0.2, 
            "system": system_prompt,
            "messages": [{"role": "user", "content": message}]
        }
        
        st.session_state.debug_info["request"] = data
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                json=data,
                headers=headers
            )
            
            st.session_state.debug_info["status_code"] = response.status_code
            
            if response.status_code != 200:
                error_msg = f"API error: {response.status_code} - {response.text}"
                st.session_state.debug_info["error"] = error_msg
                return None, error_msg
            
            response_data = response.json()
            st.session_state.debug_info["response_received"] = True
            
            if "content" in response_data and len(response_data["content"]) > 0:
                content = response_data["content"][0]["text"]
                st.session_state.debug_info["content_length"] = len(content)
                return content, None
            else:
                error_msg = "No content in response"
                st.session_state.debug_info["error"] = error_msg
                return None, error_msg
    
    except Exception as e:
        error_msg = f"Exception during scene generation: {str(e)}"
        st.session_state.debug_info["error"] = error_msg
        return None, error_msg

# Simplified HTML extraction for direct responses
def extract_html(response_text):
    """Extract HTML content from response text, with better debugging"""
    
    st.session_state.debug_info["extraction_attempted"] = True
    
    # Step 1: Look for complete HTML document
    html_pattern = r"<!DOCTYPE html>[\s\S]*?<\/html>"
    match = re.search(html_pattern, response_text, re.IGNORECASE)
    
    if match:
        st.session_state.debug_info["extraction_method"] = "complete_html"
        return match.group(0)
    
    # Step 2: Look for HTML within code blocks
    code_pattern = r"```(?:html)?\s*(<!DOCTYPE[\s\S]*?<\/html>)\s*```"
    match = re.search(code_pattern, response_text, re.IGNORECASE)
    
    if match:
        st.session_state.debug_info["extraction_method"] = "code_block_html"
        return match.group(1)
    
    # Step 3: Look for just the content between <html> tags
    html_tags_pattern = r"<html[\s\S]*?<\/html>"
    match = re.search(html_tags_pattern, response_text, re.IGNORECASE)
    
    if match:
        html_content = match.group(0)
        st.session_state.debug_info["extraction_method"] = "html_tags"
        return f"<!DOCTYPE html>\n{html_content}"
    
    # If we couldn't find valid HTML, log and return a fallback
    st.session_state.debug_info["extraction_method"] = "fallback"
    st.session_state.debug_info["raw_response"] = response_text[:500] + "..." # Log beginning of response
    
    # Create a fallback HTML with basic scene
    return create_fallback_html(response_text)

# Create fallback HTML that might work with the given content
def create_fallback_html(content):
    """Create fallback HTML that attempts to use any JavaScript content from the response"""
    
    # Look for JavaScript-like content with common Three.js patterns
    js_content = ""
    
    # Try to extract what looks like JavaScript
    js_patterns = [
        r"const scene = new THREE\.Scene\(\);[\s\S]*?renderer\.render\(scene, camera\);",
        r"function animate\(\)[\s\S]*?animate\(\);",
        r"new THREE\.([A-Za-z]+)[\s\S]*?;"
    ]
    
    for pattern in js_patterns:
        matches = re.findall(pattern, content)
        if matches:
            for match in matches:
                if isinstance(match, str) and len(match) > 20:  # Avoid tiny fragments
                    js_content += match + "\n"
    
    # If we found nothing, use a minimal scene with a spinning cube
    if not js_content:
        js_content = """
        // Create scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x87CEEB);
        
        // Create camera
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        camera.position.set(0, 5, 10);
        
        // Create renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = true;
        document.body.appendChild(renderer.domElement);
        
        // Add controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        
        // Add lights
        const ambient = new THREE.AmbientLight(0x404040);
        scene.add(ambient);
        
        const light = new THREE.DirectionalLight(0xffffff);
        light.position.set(10, 10, 10);
        light.castShadow = true;
        scene.add(light);
        
        // Add a cube
        const geometry = new THREE.BoxGeometry(2, 2, 2);
        const material = new THREE.MeshStandardMaterial({ color: 0x00ff00 });
        const cube = new THREE.Mesh(geometry, material);
        cube.castShadow = true;
        scene.add(cube);
        
        // Add a floor
        const floorGeometry = new THREE.PlaneGeometry(20, 20);
        const floorMaterial = new THREE.MeshStandardMaterial({ color: 0xcccccc });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = -1;
        floor.receiveShadow = true;
        scene.add(floor);
        
        // Animation
        function animate() {
            requestAnimationFrame(animate);
            cube.rotation.x += 0.01;
            cube.rotation.y += 0.01;
            controls.update();
            renderer.render(scene, camera);
        }
        animate();
        
        // Handle resize
        window.addEventListener('resize', function() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        """
    
    # Create the complete HTML
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Three.js Generated Scene</title>
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
        try {{
            {js_content}
        }} catch (error) {{
            console.error("Error in generated code:", error);
            
            // Create a fallback scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0xff0000);
            
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 5;
            
            const renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            
            const geometry = new THREE.BoxGeometry(1, 1, 1);
            const material = new THREE.MeshBasicMaterial({{ color: 0xffffff }});
            const cube = new THREE.Mesh(geometry, material);
            scene.add(cube);
            
            function animate() {{
                requestAnimationFrame(animate);
                cube.rotation.x += 0.01;
                cube.rotation.y += 0.01;
                renderer.render(scene, camera);
            }}
            animate();
        }}
        </script>
    </body>
    </html>
    """

# Main app
st.title("🎮 Three.js Scene Generator")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Preset Scenes", "Custom Scene Generator", "Debug Info"])

with tab1:
    st.subheader("Select a Pre-built Scene")
    
    preset_options = {
        "Rabbit & Turtle": get_rabbit_turtle_scene,
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
        
        # Add a debug mode option
        debug_mode = st.checkbox("Debug Mode (shows all steps)")
        
        submitted = st.form_submit_button("Generate Custom Scene")
        
        if submitted and user_prompt:
            # Clear previous debug info
            st.session_state.debug_info = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with st.spinner("Step 1: Enhancing your prompt..."):
                # Start with enhancing the prompt
                enhanced_prompt, enhance_error = asyncio.run(enhance_prompt(user_prompt))
                
                if enhance_error:
                    st.warning(f"Warning: Prompt enhancement had an issue: {enhance_error}")
                    st.session_state.debug_info["enhance_error"] = enhance_error
                    enhanced_prompt = user_prompt  # Fallback to original prompt
                
                # Store prompts
                st.session_state.raw_prompt = user_prompt
                st.session_state.enhanced_prompt = enhanced_prompt
                
                if debug_mode:
                    st.success("Prompt enhanced successfully!")
                    st.write("Enhanced Prompt:")
                    st.write(enhanced_prompt)
            
            # Generate the scene
            with st.spinner("Step 2: Generating Three.js scene..."):
                # Direct generation approach
                response_text, generation_error = asyncio.run(generate_scene(enhanced_prompt))
                
                if generation_error:
                    st.error(f"Error generating scene: {generation_error}")
                    st.session_state.debug_info["generation_error"] = generation_error
                elif not response_text or len(response_text) < 100:
                    st.error("Received empty or incomplete response")
                    st.session_state.debug_info["generation_error"] = "Empty or incomplete response"
                else:
                    st.session_state.debug_info["response_text_preview"] = response_text[:500] + "..."
                    
                    # Extract HTML content
                    html_content = extract_html(response_text)
                    
                    if debug_mode:
                        st.success("Scene generated!")
                        
                        # Show a preview of the HTML content
                        with st.expander("Preview of HTML (first 1000 characters)"):
                            st.code(html_content[:1000] + "...", language="html")
                    
                    # Save current scene
                    st.session_state.current_scene = {
                        "prompt": user_prompt,
                        "enhanced_prompt": enhanced_prompt,
                        "html": html_content, 
                        "full_response": response_text,
                        "is_preset": False
                    }
                    
                    if debug_mode:
                        st.success("HTML extracted and saved")
                    else:
                        st.success("Scene generated successfully!")

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
    
    # Show detailed debug info
    if "debug_info" in st.session_state and st.session_state.debug_info:
        st.subheader("Process Debug Info")
        
        # Format the debug info in a more readable way
        debug_info = st.session_state.debug_info
        
        # Show critical errors first
        if "generation_error" in debug_info:
            st.error(f"Generation Error: {debug_info['generation_error']}")
        
        if "enhance_error" in debug_info:
            st.warning(f"Enhancement Error: {debug_info['enhance_error']}")
        
        # Process timeline
        timeline_items = []
        
        if "timestamp" in debug_info:
            timeline_items.append(("Process Started", debug_info["timestamp"]))
        
        if "generation_attempt" in debug_info:
            timeline_items.append(("Generation Attempted", "Yes"))
        
        if "response_received" in debug_info:
            timeline_items.append(("API Response Received", "Yes"))
        
        if "extraction_attempted" in debug_info:
            timeline_items.append(("HTML Extraction Attempted", "Yes"))
        
        if "extraction_method" in debug_info:
            timeline_items.append(("Extraction Method", debug_info["extraction_method"]))
        
        # Show timeline
        if timeline_items:
            st.write("Processing Timeline:")
            for item, value in timeline_items:
                st.write(f"- {item}: {value}")
        
        # Other debug info
        other_keys = [k for k in debug_info.keys() if k not in ["timestamp", "request", "response", 
                                                               "generation_error", "enhance_error",
                                                               "raw_response", "response_text_preview",
                                                               "generation_attempt", "response_received",
                                                               "extraction_attempted", "extraction_method"]]
        
        if other_keys:
            st.write("Other Debug Information:")
            for key in other_keys:
                st.write(f"- {key}: {debug_info[key]}")
        
        # Show raw response data if available
        if "raw_response" in debug_info:
            with st.expander("Raw Response Preview"):
                st.text(debug_info["raw_response"])
                
        if "response_text_preview" in debug_info:
            with st.expander("Generated Response Preview"):
                st.text(debug_info["response_text_preview"])

# Display current scene if available
if st.session_state.current_scene:
    scene = st.session_state.current_scene
    
    st.subheader(f"Scene: {scene['prompt']}")
    
    # Show enhanced prompt if available
    if "enhanced_prompt" in scene and not scene.get("is_preset", False):
        with st.expander("View Enhanced Prompt"):
            st.write(scene["enhanced_prompt"])
    
    # Render the Three.js scene
    try:
        st.components.v1.html(scene["html"], height=600)
    except Exception as e:
        st.error(f"Error rendering scene: {str(e)}")
        st.warning("Displaying raw HTML instead - save and open in a browser to view properly")
        st.code(scene["html"], language="html")
    
    # Show HTML code and download button
    with st.expander("View HTML Code"):
        st.code(scene["html"], language="html")
    
    # Download button
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

# Instructions
st.markdown("---")
st.markdown("""
### Instructions

1. **Preset Scenes**: Select a pre-built scene in the first tab
2. **Custom Scenes**: Describe your own scene in the second tab
   - Enable debug mode to see more details about each step
   - If the scene doesn't display properly, download the HTML and open in a browser
3. **Debug Info**: View detailed process information in the third tab
4. **Interact** with scenes using your mouse:
   - Left-click + drag: Rotate the camera
   - Right-click + drag: Pan the camera
   - Scroll: Zoom in/out

### Troubleshooting Tips

If you encounter issues:
1. Try simpler scene descriptions
2. Check the Debug tab for specific errors
3. Download the HTML file and open it directly in a browser
4. Enable debug mode to see intermediate steps

**Technical Note**: Three.js scenes sometimes work better when run locally in a browser, especially complex ones.
""")
