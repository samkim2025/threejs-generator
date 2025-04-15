import streamlit as st
import anthropic
import os
import re
import json
import base64
from dotenv import load_dotenv
import time

# Load environment variables (for local development)
load_dotenv()

# Get API key (will use secrets in Streamlit Cloud)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or st.secrets.get("ANTHROPIC_API_KEY", "")

if not ANTHROPIC_API_KEY:
    st.error("ANTHROPIC_API_KEY is not set. Please add it to your Streamlit secrets.")
    st.stop()

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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

def extract_code(response_text):
    """Extract Three.js code from Claude's response with improved regex."""
    # First, check if there's a complete HTML document
    html_doc_pattern = r"<!DOCTYPE html>[\s\S]*?<html[\s\S]*?</html>"
    html_doc_match = re.search(html_doc_pattern, response_text, re.IGNORECASE)
    
    if html_doc_match:
        return html_doc_match.group(0), "html"
    
    # Try to extract HTML code blocks with triple backticks
    html_pattern = r"```(?:html)?(.*?)```"
    html_matches = re.findall(html_pattern, response_text, re.DOTALL)
    
    if html_matches:
        for match in html_matches:
            # Check if it contains core HTML elements
            if "<html" in match.lower() and "</html>" in match.lower():
                return match.strip(), "html"
    
    # Then try JavaScript code blocks
    js_pattern = r"```(?:javascript|js)(.*?)```"
    js_matches = re.findall(js_pattern, response_text, re.DOTALL)
    
    if js_matches:
        return js_matches[0].strip(), "js"
    
    # Fallback: try to find any code block
    generic_pattern = r"```(.*?)```"
    generic_matches = re.findall(generic_pattern, response_text, re.DOTALL)
    
    if generic_matches:
        # Try to determine if it's HTML or JS
        for match in generic_matches:
            if "<html" in match.lower() or "<script" in match.lower():
                return match.strip(), "html"
            elif "three.js" in match.lower() or "new THREE." in match:
                return match.strip(), "js"
        
        # If we can't determine, return the first block
        return generic_matches[0].strip(), "generic"
    
    # Last resort: try to find anything that looks like a complete HTML document
    if "<!DOCTYPE html>" in response_text or "<html>" in response_text:
        start_idx = max(response_text.find("<!DOCTYPE html>"), response_text.find("<html>"))
        end_idx = response_text.find("</html>", start_idx)
        if end_idx > start_idx:
            return response_text[start_idx:end_idx+7], "html"
    
    return "", ""

def create_html_with_code(threejs_code, code_type):
    """Create complete HTML with improved Three.js code integration."""
    # If the code already contains a complete HTML document, return it as is
    if code_type == "html" and ("<html" in threejs_code.lower() and "</html>" in threejs_code.lower()):
        # Ensure all Three.js dependencies are correctly loaded
        if "three@" not in threejs_code:
            # Add the latest Three.js if not present
            threejs_code = threejs_code.replace(
                "</head>", 
                '<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>\n</head>'
            )
        
        if "OrbitControls" not in threejs_code and "controls/OrbitControls.js" not in threejs_code:
            # Add OrbitControls if not present
            threejs_code = threejs_code.replace(
                '</head>',
                '<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>\n</head>'
            )
        
        return threejs_code
    
    # If we have JavaScript code, wrap it in a complete HTML document
    if code_type in ["js", "generic"]:
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Generated Three.js Scene</title>
            <style>
                body {{ margin: 0; padding: 0; overflow: hidden; }}
                canvas {{ width: 100%; height: 100%; display: block; }}
                #loading {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                          display: flex; justify-content: center; align-items: center;
                          background-color: rgba(0,0,0,0.7); color: white; font-family: Arial; 
                          font-size: 24px; z-index: 1000; }}
            </style>
            <!-- Import Three.js libraries -->
            <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
        </head>
        <body>
            <div id="loading">Loading 3D Scene...</div>
            <script>
            // Wait for Three.js to load
            window.addEventListener('load', function() {{
                {threejs_code}
                
                // Remove loading screen when scene is ready
                document.getElementById('loading').style.display = 'none';
            }});
            
            // Error handling
            window.addEventListener('error', function(e) {{
                console.error('Three.js error:', e);
                document.getElementById('loading').innerHTML = 'Error loading scene.<br>See console for details.';
                document.getElementById('loading').style.backgroundColor = 'rgba(255,0,0,0.7)';
            }});
            </script>
        </body>
        </html>
        """
    
    # If we have nothing usable, return a meaningful error page
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Scene Generation Error</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding-top: 50px; }
            .error { color: red; margin: 20px; }
        </style>
    </head>
    <body>
        <h1>Scene Generation Error</h1>
        <p class="error">No valid Three.js code was found in the AI response.</p>
        <p>Please try again with a more detailed description or check the AI Response tab for more information.</p>
    </body>
    </html>
    """

def add_to_history(prompt, html_content):
    """Add a generated scene to history."""
    st.session_state.history.append({
        "prompt": prompt,
        "html": html_content,
        "timestamp": st.session_state.get("current_timestamp", "")
    })

def render_threejs_scene(html_content, height=600):
    """Render the Three.js scene in an iframe with improved error handling."""
    # Use Base64 encoding to ensure all content is properly loaded in the iframe
    encoded_content = base64.b64encode(html_content.encode()).decode()
    
    iframe_html = f"""
    <iframe 
        srcdoc="{html_content.replace('"', '&quot;')}" 
        width="100%" 
        height="{height}" 
        style="border:none; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" 
        allow="accelerometer; camera; fullscreen; gyroscope; microphone; xr-spatial-tracking"
        sandbox="allow-scripts allow-same-origin"
    ></iframe>
    """
    
    st.components.v1.html(iframe_html, height=height+10, scrolling=False)

def generate_threejs_code(prompt):
    """Generate Three.js code using Claude API with improved prompt."""
    system_prompt = """You are an expert in Three.js, WebGL, and 3D web development. 
    Your task is to create complete, standalone Three.js code based on the user's description.
    
    REQUIREMENTS FOR YOUR RESPONSE:
    1. Your response MUST contain a SINGLE complete HTML document with embedded Three.js code.
    2. The HTML document MUST be enclosed within ```html``` and ``` tags for proper extraction.
    3. The document MUST contain all necessary scripts and CSS inline, requiring no external files.
    
    TECHNICAL REQUIREMENTS:
    1. Import Three.js and OrbitControls from CDN (use Three.js version 0.160.0)
    2. Set up a proper canvas, scene, camera, renderer, and lighting
    3. Create the 3D objects described with appropriate materials and textures
    4. Include animations and OrbitControls for user interaction
    5. Handle window resizing correctly
    6. Include error handling for texture/model loading
    7. Use only features compatible with modern browsers
    8. Add detailed code comments explaining key aspects
    
    CRITICAL CONSTRAINTS:
    - For textures and models, only use CDN URLs or basic procedural textures
    - Use requestAnimationFrame for animations
    - ALL code must be self-contained in a single HTML file
    - Include responsive design to handle window resizing
    - Make sure OrbitControls are properly configured
    
    Example of correctly formatted response:
    ```html
    <!DOCTYPE html>
    <html>
    <head>
        <title>Three.js Scene</title>
        <!-- Imports and CSS here -->
    </head>
    <body>
        <script>
            // Three.js code here
        </script>
    </body>
    </html>
    ```
    
    Ensure your entire response can be extracted and run directly in a browser with no modifications.
    """
    
    try:
        response = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"Create a Three.js scene with the following description: {prompt}. Make it visually interesting with good lighting and materials."}
            ]
        )
        code, code_type = extract_code(response.content[0].text)
        return code, code_type, response.content[0].text
    except Exception as e:
        st.error(f"Error generating code: {str(e)}")
        return "", "", f"Error: {str(e)}"

def display_scene_container():
    """Create a container for displaying the Three.js scene with proper styling."""
    container = st.container()
    container.markdown("""
    <style>
    .scene-container {
        background-color: #f0f0f0;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 20px;
    }
    </style>
    <div class="scene-container">
    <h3>Interactive 3D Scene</h3>
    <p>Use mouse to interact: Left-click & drag to rotate, right-click & drag to pan, scroll to zoom</p>
    </div>
    """, unsafe_allow_html=True)
    return container

# Add a testing feature for pre-made scenes
def get_test_scene():
    """Return a pre-made Three.js scene for testing renderer."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Test Three.js Scene</title>
        <style>
            body { margin: 0; overflow: hidden; }
            canvas { width: 100%; height: 100%; display: block; }
        </style>
        <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.160.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <script>
            // Set up scene
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x87CEEB);
            
            // Set up camera
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 5;
            
            // Set up renderer
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.body.appendChild(renderer.domElement);
            
            // Add controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            
            // Add light
            const light = new THREE.DirectionalLight(0xffffff, 1);
            light.position.set(1, 1, 1);
            scene.add(light);
            
            const ambientLight = new THREE.AmbientLight(0x404040);
            scene.add(ambientLight);
            
            // Create a rotating cube
            const geometry = new THREE.BoxGeometry();
            const material = new THREE.MeshStandardMaterial({ 
                color: 0x00ff00,
                metalness: 0.3,
                roughness: 0.4
            });
            const cube = new THREE.Mesh(geometry, material);
            scene.add(cube);
            
            // Handle window resize
            window.addEventListener('resize', () => {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
            
            // Animation loop
            function animate() {
                requestAnimationFrame(animate);
                cube.rotation.x += 0.01;
                cube.rotation.y += 0.01;
                controls.update();
                renderer.render(scene, camera);
            }
            animate();
        </script>
    </body>
    </html>
    """

# Sidebar
with st.sidebar:
    st.title("🎮 Scene Generator")
    
    # Test scene button
    if st.button("Load Test Scene"):
        test_html = get_test_scene()
        st.session_state.current_scene = {
            "prompt": "Test Scene with Rotating Cube",
            "html": test_html,
            "code": test_html,
            "code_type": "html",
            "full_response": "Test scene - not generated by AI",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    st.divider()
    st.subheader("📜 Scene History")
    
    if st.session_state.history:
        for i, item in enumerate(st.session_state.history):
            if st.button(f"Scene {i+1}: {item['prompt'][:25]}...", key=f"history_{i}"):
                st.session_state.current_scene = item
    else:
        st.info("Your generated scenes will appear here")

# Main content
st.title("🎮 AI Three.js Scene Generator")
st.write("Enter a description and get a 3D scene generated with Three.js")

# Input form
with st.form("scene_generator_form"):
    user_prompt = st.text_area(
        "Describe your 3D scene:", 
        placeholder="Describe your Three.js scene here! For example: A forest with trees, a flowing river, and birds flying overhead",
        height=150
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        submitted = st.form_submit_button("Generate 3D Scene", use_container_width=True)
    with col2:
        example_button = st.form_submit_button("Use Random Example", use_container_width=True)
    with col3:
        advanced_options = st.checkbox("Advanced Options")
    
    if advanced_options:
        st.write("Advanced generation options:")
        temperature = st.slider("Creativity (Temperature)", min_value=0.0, max_value=1.0, value=0.2, step=0.1)
        model_choice = st.selectbox("Claude Model", ["claude-3-opus-20240229", "claude-3-sonnet-20240229"])
    else:
        temperature = 0.2
        model_choice = "claude-3-opus-20240229"
    
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
        with st.spinner("Generating your 3D scene... (this may take up to 30 seconds)"):
            st.session_state.current_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Show temporary loading message
            loading_placeholder = st.empty()
            loading_placeholder.info("Getting creative with your scene description...")
            
            # Call Claude API with selected model and temperature
            code, code_type, full_response = generate_threejs_code(user_prompt)
            
            if code:
                loading_placeholder.info("Preparing your 3D scene...")
                
                html_content = create_html_with_code(code, code_type)
                
                # Save current scene to state
                st.session_state.current_scene = {
                    "prompt": user_prompt,
                    "html": html_content,
                    "code": code,
                    "code_type": code_type,
                    "full_response": full_response,
                    "timestamp": st.session_state.current_timestamp
                }
                
                # Add to history
                add_to_history(user_prompt, html_content)
                
                loading_placeholder.empty()
                st.success("Scene generated successfully!")
            else:
                loading_placeholder.empty()
                st.error("Failed to generate Three.js code. Please try a different description or check the AI Response tab.")

# Display current scene if available
if st.session_state.current_scene:
    scene = st.session_state.current_scene
    
    st.subheader(f"Scene: {scene['prompt']}")
    
    # Create a dedicated container for the 3D scene
    scene_container = display_scene_container()
    with scene_container:
        try:
            render_threejs_scene(scene["html"])
        except Exception as e:
            st.error(f"Error rendering scene: {str(e)}")
            st.warning("The HTML content might contain errors. Check the code in the tabs below.")
    
    # Display code and response
    tab1, tab2, tab3 = st.tabs(["Generated Code", "AI Response", "Debug"])
    
    with tab1:
        st.code(scene.get("code", ""), language="html" if scene.get("code_type") == "html" else "javascript")
        
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
        st.text_area("Full AI Response", value=scene.get("full_response", ""), height=400)
    
    with tab3:
        st.write("Debug Information")
        st.json({
            "code_type": scene.get("code_type", ""),
            "timestamp": scene.get("timestamp", ""),
            "html_length": len(scene.get("html", "")),
            "contains_three.js": "three.js" in scene.get("html", "").lower(),
            "contains_orbitcontrols": "orbitcontrols" in scene.get("html", "").lower()
        })
        
        if st.button("Force Reload Scene"):
            st.experimental_rerun()

# Instructions and tips
st.markdown("---")
with st.expander("📝 Tips for better results", expanded=False):
    st.markdown("""
    ### 💡 Tips for better results
    - Be specific about colors, shapes, materials, and lighting
    - Mention if you want animations or interactions
    - Specify camera position and perspective if important
    - Describe the mood or atmosphere you want to create
    
    ### 🚀 How to interact with the scene
    - Left-click + drag: Rotate the camera
    - Right-click + drag: Pan the camera
    - Scroll: Zoom in/out
    
    ### 🛠️ Troubleshooting
    - If a scene doesn't load, try the "Load Test Scene" button to check if Three.js is working
    - If you see errors, check the "Debug" tab for more information
    - Some complex scenes may take longer to generate and load
    """)
