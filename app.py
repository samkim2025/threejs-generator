import streamlit as st
import os
import re
import json
import httpx
import asyncio
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Three.js Scene Generator",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "current_scene" not in st.session_state:
    st.session_state.current_scene = None

# Get API key from environment or secrets
def get_api_key():
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except:
        return os.getenv("ANTHROPIC_API_KEY", "")

ANTHROPIC_API_KEY = get_api_key()
if not ANTHROPIC_API_KEY:
    st.error("ANTHROPIC_API_KEY is not set. Please add it to your environment or Streamlit secrets.")
    st.stop()

# Extract code from Claude's response
def extract_code(response_text):
    # Try to extract HTML code blocks
    html_pattern = r"```(?:html)(.*?)```"
    html_matches = re.findall(html_pattern, response_text, re.DOTALL)
    
    if html_matches:
        return html_matches[0].strip()
    
    # Then try JavaScript code blocks (and wrap in HTML)
    js_pattern = r"```(?:javascript|js)(.*?)```"
    js_matches = re.findall(js_pattern, response_text, re.DOTALL)
    
    if js_matches:
        js_code = js_matches[0].strip()
        # Create HTML wrapper for JS code
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>AI Generated Three.js Scene</title>
            <style>
                body {{ margin: 0; overflow: hidden; }}
                canvas {{ width: 100%; height: 100%; display: block; }}
                #info {{
                    position: absolute;
                    top: 10px;
                    width: 100%;
                    text-align: center;
                    color: white;
                    font-family: Arial, sans-serif;
                    pointer-events: none;
                    z-index: 100;
                }}
            </style>
        </head>
        <body>
            <div id="info">Generated Three.js Scene - Use mouse to navigate</div>
            <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
            <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
            <script>
            {js_code}
            </script>
        </body>
        </html>
        """
    
    # Finally try to find any code block
    generic_pattern = r"```(.*?)```"
    generic_matches = re.findall(generic_pattern, response_text, re.DOTALL)
    
    if generic_matches:
        code = generic_matches[0].strip()
        if "<html" in code.lower():
            return code
        else:
            # Assume it's JavaScript and wrap it
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>AI Generated Three.js Scene</title>
                <style>
                    body {{ margin: 0; overflow: hidden; }}
                    canvas {{ width: 100%; height: 100%; display: block; }}
                </style>
            </head>
            <body>
                <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
                <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
                <script>
                {code}
                </script>
            </body>
            </html>
            """
    
    return ""

# Make async API call to Claude
async def call_claude_api(prompt):
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # System prompt focused on creating advanced Three.js scenes
        system_prompt = """You are an expert in Three.js, WebGL, and 3D web development.
        Your task is to create complete, standalone Three.js code based on the user's description.
        
        The code must:
        1. Include all necessary Three.js imports (use version 0.137.0 from unpkg CDN)
        2. Set up a proper scene, camera, renderer with shadows enabled
        3. Include OrbitControls for user interaction
        4. Create the described 3D scene with realistic models, materials, and lighting
        5. Add animations and interactivity where appropriate
        6. Implement a day/night cycle if it makes sense for the scene
        7. Add multiple light sources for realistic lighting
        8. Create detailed objects using Three.js geometries (not external models)
        9. Add proper event handlers for window resizing
        10. Use requestAnimationFrame for smooth rendering
        
        Provide your response as a single complete HTML document with embedded JavaScript.
        The code should be production-ready and optimized for performance.
        Do not leave any placeholders or TO-DO comments - implement everything fully.
        Do not use any external libraries other than Three.js and its built-in modules.
        """
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": f"Create a detailed Three.js scene visualization of: {prompt}. The scene should be interactive, visually impressive, and fully implemented with no placeholders."}
            ]
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", json=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            
            if "content" in response_data and len(response_data["content"]) > 0:
                return response_data["content"][0]["text"]
            else:
                return "Error: No content in response"
    except Exception as e:
        return f"Error calling Claude API: {str(e)}"

# Generate Three.js code using Claude
def generate_threejs_code(prompt):
    try:
        response_text = asyncio.run(call_claude_api(prompt))
        
        if response_text.startswith("Error"):
            st.error(response_text)
            return "", response_text
        
        code = extract_code(response_text)
        return code, response_text
    except Exception as e:
        error_msg = f"Error generating code: {str(e)}"
        st.error(error_msg)
        return "", error_msg

# Create a hardcoded test scene to verify WebGL works
def create_test_scene():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Three.js Test Scene</title>
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
                z-index: 100;
                text-shadow: 1px 1px 1px black;
            }
        </style>
    </head>
    <body>
        <div id="info">Three.js Test Scene - Rotating Cube</div>
        <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
        <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
        <script>
            // Create scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x333333);
            
            // Create camera
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.set(3, 3, 3);
            camera.lookAt(0, 0, 0);
            
            // Create renderer
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            document.body.appendChild(renderer.domElement);
            
            // Add orbit controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(5, 5, 5);
            directionalLight.castShadow = true;
            directionalLight.shadow.mapSize.width = 1024;
            directionalLight.shadow.mapSize.height = 1024;
            scene.add(directionalLight);
            
            // Create cube
            const geometry = new THREE.BoxGeometry(1, 1, 1);
            const material = new THREE.MeshPhongMaterial({ 
                color: 0x00ff00,
                shininess: 100
            });
            const cube = new THREE.Mesh(geometry, material);
            cube.castShadow = true;
            cube.receiveShadow = true;
            scene.add(cube);
            
            // Create ground
            const groundGeometry = new THREE.PlaneGeometry(10, 10);
            const groundMaterial = new THREE.MeshPhongMaterial({ 
                color: 0x999999,
                shininess: 0
            });
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            ground.position.y = -0.5;
            ground.receiveShadow = true;
            scene.add(ground);
            
            // Handle window resize
            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                
                // Rotate cube
                cube.rotation.x += 0.01;
                cube.rotation.y += 0.01;
                
                // Update controls
                controls.update();
                
                // Render
                renderer.render(scene, camera);
            }
            
            // Start animation
            animate();
        </script>
    </body>
    </html>
    """

# Add a scene to history
def add_to_history(prompt, html_content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_scene = {
        "prompt": prompt,
        "html": html_content,
        "timestamp": timestamp
    }
    st.session_state.history.append(new_scene)
    return new_scene

# Main sidebar
with st.sidebar:
    st.title("🎮 Scene History")
    
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history):
            if st.button(f"Scene {i+1}: {item['prompt'][:30]}...", key=f"history_{i}"):
                # Ensure all required keys exist
                if "html" not in item:
                    st.error(f"Scene {i+1} is missing HTML content")
                else:
                    st.session_state.current_scene = item
    else:
        st.info("Your generated scenes will appear here")
    
    if st.button("WebGL Test Scene"):
        test_html = create_test_scene()
        test_scene = {
            "prompt": "Test Scene with Rotating Cube",
            "html": test_html,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.current_scene = test_scene

# Fixed scene for rabbits and turtles
def create_rabbit_turtle_scene():
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

# Main content
st.title("🎮 AI Three.js Scene Generator")
st.write("Enter a description and get a 3D scene generated with Three.js")

# Add a fallback for the rabbit and turtle scene
if st.button("Load Rabbit and Turtle Example"):
    rabbit_turtle_html = create_rabbit_turtle_scene()
    rabbit_turtle_scene = {
        "prompt": "A rabbit and a turtle running on a hill",
        "html": rabbit_turtle_html,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    st.session_state.current_scene = rabbit_turtle_scene
    add_to_history("A rabbit and a turtle running on a hill", rabbit_turtle_html)

# Input form
with st.form("scene_generator_form"):
    user_prompt = st.text_area(
        "Describe your 3D scene:",
        placeholder="A rabbit and a turtle running on a hill",
        height=100
    )
    
    col1, col2 = st.columns(2)
    with col1:
        submitted = st.form_submit_button("Generate 3D Scene", use_container_width=True)
    with col2:
        example_button = st.form_submit_button("Use Random Example", use_container_width=True)
    
    # Handle random example
    if example_button:
        examples = [
            "A solar system with planets orbiting around the sun",
            "A forest scene with trees, a lake, and animated birds flying",
            "A futuristic city with neon buildings and flying vehicles",
            "An underwater scene with fish, coral, and bubbles rising to the surface",
            "A mountain landscape with snow-capped peaks and a log cabin"
        ]
        import random
        user_prompt = random.choice(examples)
        submitted = True
    
    if submitted and user_prompt:
        with st.spinner("Generating your 3D scene... (this may take up to a minute)"):
            html_content, full_response = generate_threejs_code(user_prompt)
            
            if html_content:
                # Save current scene to state with all required fields
                new_scene = {
                    "prompt": user_prompt,
                    "html": html_content,
                    "full_response": full_response,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.session_state.current_scene = new_scene
                
                # Add to history
                add_to_history(user_prompt, html_content)
                
                st.success("Scene generated successfully!")
            else:
                st.error("Failed to generate Three.js code. Please try a different description.")

# Display current scene if available
if st.session_state.current_scene:
    scene = st.session_state.current_scene
    
    # Add validation to ensure all required keys exist
    if not isinstance(scene, dict):
        st.error("Invalid scene data structure")
    elif "prompt" not in scene:
        st.error("Scene is missing prompt information")
    elif "html" not in scene:
        st.error("Scene is missing HTML content")
        # Try to load a default scene as a fallback
        scene["html"] = create_test_scene()
    
    # Now it's safe to display the scene
    st.subheader(f"Scene: {scene.get('prompt', 'Unknown')}")
    
    # Render the Three.js scene with sufficient height
    st.components.v1.html(scene["html"], height=600)
    
    # Display tabs for code and response
    tab1, tab2 = st.tabs(["HTML Code", "Full Response"])
    
    with tab1:
        st.code(scene["html"], language="html")
        
        # Download button
        st.download_button(
            label="Download HTML",
            data=scene["html"],
            file_name="threejs_scene.html",
            mime="text/html"
        )
    
    with tab2:
        if "full_response" in scene:
            st.text_area("Full AI Response", value=scene["full_response"], height=400)
        else:
            st.info("Full response not available for this scene")

# Instructions
st.markdown("---")
st.markdown("""
### How to Use This Tool

1. **Enter a Description**: Describe the 3D scene you want to create in detail
2. **Generate**: Click the "Generate 3D Scene" button
3. **Interact**: Use your mouse to navigate the generated scene:
   - Left-click + drag: Rotate the camera
   - Right-click + drag: Pan the camera
   - Scroll: Zoom in/out
4. **Download**: Save the HTML file to open directly in your browser

### Tips for Better Results

- Be specific about what objects you want in the scene
- Mention lighting, colors, and atmosphere
- Describe any animations or movements
- Add details about materials and textures

### Troubleshooting

- If you see a black screen, try the "WebGL Test Scene" button
- Some complex scenes may take longer to load
- Download the HTML to run locally for best performance
""")
