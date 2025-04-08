import streamlit as st
import os
import re
import json
from datetime import datetime
import httpx

# Set page configuration
st.set_page_config(
    page_title="AI Three.js Scene Generator",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if "history" not in st.session_state:
    st.session_state.history = []
if "current_scene" not in st.session_state:
    st.session_state.current_scene = None

# Safer API key handling
def get_api_key():
    """Get API key from environment or secrets."""
    # Try to get from secrets first
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except:
        # Fallback to environment variable
        return os.getenv("ANTHROPIC_API_KEY", "")

ANTHROPIC_API_KEY = get_api_key()

if not ANTHROPIC_API_KEY:
    st.error("ANTHROPIC_API_KEY is not set. Please add it to your Streamlit secrets.")
    st.stop()

def extract_code(response_text):
    """Extract Three.js code from Claude's response."""
    # Try to extract HTML code blocks first
    html_pattern = r"```(?:html)(.*?)```"
    html_matches = re.findall(html_pattern, response_text, re.DOTALL)
    
    if html_matches:
        return html_matches[0].strip(), "html"
    
    # Then try JavaScript code blocks
    js_pattern = r"```(?:javascript|js)(.*?)```"
    js_matches = re.findall(js_pattern, response_text, re.DOTALL)
    
    if js_matches:
        return js_matches[0].strip(), "js"
    
    # Fallback: try to find any code block
    generic_pattern = r"```(.*?)```"
    generic_matches = re.findall(generic_pattern, response_text, re.DOTALL)
    
    if generic_matches:
        return generic_matches[0].strip(), "generic"
    
    return "", ""

async def call_claude_api(prompt):
    """Call Claude API using httpx directly to avoid initialization issues."""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    system_prompt = """You are an expert in Three.js, WebGL, and 3D web development. 
    Your task is to create complete, standalone Three.js code based on the user's description.
    
    The code must:
    1. Include all necessary Three.js imports from CDN (use the latest stable version)
    2. Set up a proper canvas, scene, camera, renderer, and lighting
    3. Create the 3D objects described by the user with appropriate materials and textures
    4. Include smooth animations and camera controls (OrbitControls)
    5. Be complete, error-free, and ready to run in a browser
    6. Use only Three.js code that works in all modern browsers
    7. Include detailed comments explaining key aspects of the implementation
    
    Format your response with a single code block containing complete HTML with the Three.js code embedded.
    The HTML should be a fully functional standalone page that can be saved and run directly in a browser.
    
    Important guidelines:
    - For textures and models, use only URLs that are publicly accessible and stable
    - Make sure all event listeners are properly set up and removed when appropriate
    - Include responsive design to handle window resizing
    - Use requestAnimationFrame for smooth animations
    - Add error handling for texture and model loading
    """
    
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 4000,
        "temperature": 0.2,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": f"Create a Three.js scene with the following description: {prompt}. Make it visually interesting with good lighting and materials."}
        ]
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", json=data, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            
            if "content" in response_data and len(response_data["content"]) > 0:
                return response_data["content"][0]["text"]
            else:
                return "Error: No content in response"
    except Exception as e:
        return f"Error calling Claude API: {str(e)}"

def generate_threejs_code(prompt):
    """Generate Three.js code using Claude API."""
    try:
        import asyncio
        response_text = asyncio.run(call_claude_api(prompt))
        
        if response_text.startswith("Error"):
            st.error(response_text)
            return "", "", response_text
        
        code, code_type = extract_code(response_text)
        return code, code_type, response_text
    except Exception as e:
        error_msg = f"Error generating code: {str(e)}"
        st.error(error_msg)
        return "", "", error_msg

def create_html_with_code(threejs_code, code_type):
    """Create complete HTML with the Three.js code."""
    # If the code already contains <html>, assume it's complete
    if code_type == "html" and "<html" in threejs_code.lower():
        return threejs_code
    
    # If we have JavaScript code, wrap it in HTML with error tracking
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>AI Generated Three.js Scene</title>
        <style>
            body {{ margin: 0; overflow: hidden; }}
            canvas {{ width: 100%; height: 100%; display: block; }}
            #error-display {{
                position: fixed;
                bottom: 10px;
                left: 10px;
                background: rgba(255,0,0,0.7);
                color: white;
                padding: 10px;
                font-family: monospace;
                max-width: 80%;
                z-index: 1000;
                white-space: pre-wrap;
            }}
        </style>
    </head>
    <body>
        <div id="error-display"></div>
        
        <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
        
        <script>
        // Error tracking
        window.addEventListener('error', function(e) {{
            document.getElementById('error-display').innerHTML += '<div>' + e.message + '</div>';
            console.error(e);
        }});
        
        // Check WebGL compatibility
        if (!window.WebGLRenderingContext) {{
            document.getElementById('error-display').innerHTML = 
                '<div>Your browser does not support WebGL, which is required for Three.js</div>';
        }}
        
        // Add a simple cube if no other objects are defined
        function addTestCube(scene) {{
            const geometry = new THREE.BoxGeometry(1, 1, 1);
            const material = new THREE.MeshPhongMaterial({{ color: 0xff0000 }});
            const cube = new THREE.Mesh(geometry, material);
            scene.add(cube);
            return cube;
        }}
        
        try {{
            {threejs_code}
            
            // Check if there's a scene and camera defined, otherwise create minimal ones
            if (typeof scene === 'undefined') {{
                console.log("No scene defined, creating minimal scene");
                window.scene = new THREE.Scene();
                window.camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
                window.renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.body.appendChild(renderer.domElement);
                
                // Add light
                const light = new THREE.DirectionalLight(0xffffff, 1);
                light.position.set(0, 1, 1).normalize();
                scene.add(light);
                
                // Add ambient light
                scene.add(new THREE.AmbientLight(0x404040));
                
                // Add a cube
                const cube = addTestCube(scene);
                
                // Position camera
                camera.position.z = 5;
                
                // Animation loop
                function animate() {{
                    requestAnimationFrame(animate);
                    cube.rotation.x += 0.01;
                    cube.rotation.y += 0.01;
                    renderer.render(scene, camera);
                }}
                animate();
            }}
            
            // Make sure animation is running
            if (typeof animate === 'function' && !window._animationStarted) {{
                window._animationStarted = true;
                animate();
            }}
            
        }} catch(e) {{
            document.getElementById('error-display').innerHTML += '<div>Error: ' + e.message + '</div>';
            console.error(e);
            
            // Create a fallback scene on error
            try {{
                console.log("Creating fallback scene");
                const scene = new THREE.Scene();
                const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
                const renderer = new THREE.WebGLRenderer({{ antialias: true }});
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.body.appendChild(renderer.domElement);
                
                // Add light
                const light = new THREE.DirectionalLight(0xffffff, 1);
                light.position.set(0, 1, 1).normalize();
                scene.add(light);
                
                // Add ambient light
                scene.add(new THREE.AmbientLight(0x404040));
                
                // Add a cube
                const cube = new THREE.Mesh(
                    new THREE.BoxGeometry(1, 1, 1),
                    new THREE.MeshPhongMaterial({{ color: 0xff0000 }})
                );
                scene.add(cube);
                
                // Position camera
                camera.position.z = 5;
                
                // Animation loop
                function animate() {{
                    requestAnimationFrame(animate);
                    cube.rotation.x += 0.01;
                    cube.rotation.y += 0.01;
                    renderer.render(scene, camera);
                }}
                animate();
                
                document.getElementById('error-display').innerHTML += '<div>Fallback scene created</div>';
            }} catch(fallbackError) {{
                document.getElementById('error-display').innerHTML += '<div>Fallback failed: ' + fallbackError.message + '</div>';
            }}
        }}
        </script>
    </body>
    </html>
    """

def test_threejs_scene():
    """Create a simple test Three.js scene."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Three.js Test</title>
        <style>
            body { margin: 0; overflow: hidden; }
            #info { 
                position: absolute; 
                top: 10px; 
                width: 100%; 
                text-align: center; 
                color: white;
                background-color: rgba(0,0,0,0.5);
                padding: 5px;
                font-family: Arial, sans-serif;
            }
        </style>
    </head>
    <body>
        <div id="info">Basic Three.js Test - Rotating Cube</div>
        <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
        <script>
            // Set up scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x333333);
            
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            
            const renderer = new THREE.WebGLRenderer({antialias: true});
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            
            // Add lights
            const ambientLight = new THREE.AmbientLight(0x404040);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(1, 1, 1).normalize();
            scene.add(directionalLight);
            
            // Create a cube
            const geometry = new THREE.BoxGeometry();
            const material = new THREE.MeshPhongMaterial({ 
                color: 0x00ff00,
                shininess: 100
            });
            const cube = new THREE.Mesh(geometry, material);
            scene.add(cube);
            
            camera.position.z = 5;
            
            // Handle window resize
            window.addEventListener('resize', function() {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                cube.rotation.x += 0.01;
                cube.rotation.y += 0.01;
                renderer.render(scene, camera);
            }
            animate();
        </script>
    </body>
    </html>
    """

def add_to_history(prompt, html_content):
    """Add a generated scene to history."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.history.append({
        "prompt": prompt,
        "html": html_content,
        "timestamp": timestamp
    })

def render_threejs_scene(html_content, height=600):
    """Render the Three.js scene in an iframe."""
    # Use streamlit components to render HTML
    st.components.v1.html(html_content, height=height, scrolling=False)

# Sidebar
with st.sidebar:
    st.title("🎮 Scene History")
    
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history):
            if st.button(f"Scene {i+1}: {item['prompt'][:30]}...", key=f"history_{i}"):
                st.session_state.current_scene = item
    else:
        st.info("Your generated scenes will appear here")
    
    # Add a test scene button
    if st.button("Test Basic Three.js"):
        test_html = test_threejs_scene()
        st.session_state.current_scene = {
            "prompt": "Basic Three.js Test",
            "html": test_html,
            "code": "// Basic test scene code",
            "code_type": "js",
            "full_response": "Test scene",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

# Main content
st.title("🎮 AI Three.js Scene Generator")
st.write("Enter a description and get a 3D scene generated with Three.js")

# Debug info 
with st.expander("Debug Info"):
    st.write("This section helps troubleshoot rendering issues")
    st.code("""
    // Browser Compatibility
    - Check if your browser supports WebGL (required for Three.js)
    - Make sure JavaScript is enabled
    
    // Common Issues
    - Black screen: Usually means the scene is created but nothing is visible
    - No renderer: The canvas element might not be properly added to the DOM
    - Camera issues: Objects might be out of view of the camera
    - Error in console: Check browser developer tools (F12) for JavaScript errors
    """)
    
    # WebGL check button
    if st.button("Check WebGL Support"):
        webgl_check = """
        <script>
        function checkWebGL() {
            try {
                var canvas = document.createElement('canvas');
                return !!window.WebGLRenderingContext && 
                    (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'));
            } catch(e) {
                return false;
            }
        }
        document.write(checkWebGL() ? 
            '<div style="color:green;font-weight:bold">WebGL is supported!</div>' : 
            '<div style="color:red;font-weight:bold">WebGL is NOT supported!</div>');
        </script>
        """
        st.components.v1.html(webgl_check, height=50)

# Input form
with st.form("scene_generator_form"):
    user_prompt = st.text_area(
        "Describe your 3D scene:", 
        placeholder="Describe your Three.js scene here! For example: A forest with trees, a flowing river, and birds flying overhead",
        height=150
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        submitted = st.form_submit_button("Generate 3D Scene", use_container_width=True)
    with col2:
        example_button = st.form_submit_button("Use Random Example", use_container_width=True)
    
    # Handle random example
    if example_button:
        examples = [
            "A solar system with textured planets orbiting around the sun",
            "A peaceful forest scene with trees, a lake, and animated birds flying",
            "A futuristic city with neon buildings and flying vehicles",
            "An underwater scene with fish, coral, and bubbles rising to the surface",
            "A mountain landscape with snow-capped peaks and a log cabin"
        ]
        import random
        user_prompt = random.choice(examples)
        submitted = True
    
    if submitted and user_prompt:
        with st.spinner("Generating your 3D scene... (this may take 30-60 seconds)"):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            code, code_type, full_response = generate_threejs_code(user_prompt)
            
            if code:
                html_content = create_html_with_code(code, code_type)
                
                # Save current scene to state
                st.session_state.current_scene = {
                    "prompt": user_prompt,
                    "html": html_content,
                    "code": code,
                    "code_type": code_type,
                    "full_response": full_response,
                    "timestamp": timestamp
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
    
    render_threejs_scene(scene["html"])
    
    # Display code and response
    tab1, tab2, tab3 = st.tabs(["Generated Code", "AI Response", "Rendering Info"])
    
    with tab1:
        st.code(scene.get("code", ""), language="javascript")
        
        # Download button for HTML
        html_content = scene.get("html", "")
        if html_content:
            st.download_button(
                label="Download HTML",
                data=html_content,
                file_name="threejs_scene.html",
                mime="text/html"
            )
    
    with tab2:
        st.text_area("Full AI Response", value=scene.get("full_response", ""), height=400, disabled=True)
    
    with tab3:
        st.markdown("""
        ### Troubleshooting Rendering Issues
        
        If you see a black screen:
        1. Download the HTML and open it directly in your browser
        2. Check browser console (F12 > Console) for errors
        3. Try the 'Test Basic Three.js' button in the sidebar
        
        Common issues:
        - **Camera position**: Objects might be out of view
        - **Missing lights**: Scene might be too dark
        - **Animation not started**: The render loop might not be running
        - **WebGL issues**: Browser might not support specific features
        
        Try adding this to the console to debug camera position:
        ```javascript
        console.log(camera.position);
        ```
        """)
        
        if st.button("Try Simple Cube Render"):
            simple_cube = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>body { margin: 0; }</style>
            </head>
            <body>
                <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
                <script>
                    const scene = new THREE.Scene();
                    const camera = new THREE.PerspectiveCamera(75, window.innerWidth/window.innerHeight, 0.1, 1000);
                    const renderer = new THREE.WebGLRenderer();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                    document.body.appendChild(renderer.domElement);
                    
                    const geometry = new THREE.BoxGeometry();
                    const material = new THREE.MeshBasicMaterial({color: 0x00ff00});
                    const cube = new THREE.Mesh(geometry, material);
                    scene.add(cube);
                    
                    camera.position.z = 5;
                    
                    function animate() {
                        requestAnimationFrame(animate);
                        cube.rotation.x += 0.01;
                        cube.rotation.y += 0.01;
                        renderer.render(scene, camera);
                    }
                    animate();
                </script>
            </body>
            </html>
            """
            st.components.v1.html(simple_cube, height=300)

# Instructions
st.markdown("---")
st.markdown("""
### 🚀 How to use this tool
1. Enter a description of the 3D scene you want to create
2. Click "Generate 3D Scene"
3. The AI will create Three.js code and render the scene
4. Interact with the scene using your mouse:
   - Left-click + drag: Rotate the camera
   - Right-click + drag: Pan the camera
   - Scroll: Zoom in/out

### 💡 Tips for better results
- Be specific about colors, shapes, materials, and lighting
- Mention if you want animations or interactions
- Specify camera position and perspective if important
- Describe the mood or atmosphere you want to create
""")
