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
    st.session_state.history.append({
        "prompt": prompt,
        "html": html_content,
        "timestamp": timestamp
    })

# Main sidebar
with st.sidebar:
    st.title("🎮 Scene History")
    
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history):
            if st.button(f"Scene {i+1}: {item['prompt'][:30]}...", key=f"history_{i}"):
                st.session_state.current_scene = item
    else:
        st.info("Your generated scenes will appear here")
    
    if st.button("WebGL Test Scene"):
        test_html = create_test_scene()
        st.session_state.current_scene = {
            "prompt": "Test Scene with Rotating Cube",
            "html": test_html,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# Main content
st.title("🎮 AI Three.js Scene Generator")
st.write("Enter a description and get a 3D scene generated with Three.js")

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
                # Save current scene to state
                st.session_state.current_scene = {
                    "prompt": user_prompt,
                    "html": html_content,
                    "full_response": full_response,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Add to history
                add_to_history(user_prompt, html_content)
                
                st.success("Scene generated successfully!")
            else:
                st.error("Failed to generate Three.js code. Please try a different description.")

# Display current scene if available
if st.session_state.current_scene:
    scene = st.session_state.current_scene
    
    st.subheader(f"Scene: {scene['prompt']}")
    
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
