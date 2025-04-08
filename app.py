import streamlit as st
import os
import httpx
import re
import asyncio
from datetime import datetime

# Page configuration 
st.set_page_config(page_title="Three.js Generator", layout="wide")

# Initialize session state
if "history" not in st.session_state:
    st.session_state.history = []
if "current_scene" not in st.session_state:
    st.session_state.current_scene = None

# API key handling
def get_api_key():
    try:
        return st.secrets.get("ANTHROPIC_API_KEY", "")
    except:
        return os.getenv("ANTHROPIC_API_KEY", "")

ANTHROPIC_API_KEY = get_api_key()
if not ANTHROPIC_API_KEY:
    st.error("ANTHROPIC_API_KEY is not set.")
    st.stop()

# Fixed minimal Three.js scene that's guaranteed to work in Streamlit
def create_minimal_scene():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Basic Three.js</title>
        <style>
            body { margin: 0; padding: 0; overflow: hidden; }
            #info { 
                position: absolute; 
                top: 10px; 
                width: 100%; 
                text-align: center; 
                color: white; 
                font-family: Arial;
                pointer-events: none;
                text-shadow: 1px 1px 1px black;
            }
        </style>
    </head>
    <body>
        <div id="info">Basic WebGL Cube - If you see this, WebGL is working!</div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script>
            // This is a very minimal Three.js example designed to work in Streamlit
            
            // Ensure the DOM is loaded before proceeding
            document.addEventListener("DOMContentLoaded", init);
            
            // Init will be called when DOM is ready
            function init() {
                console.log("Initializing Three.js scene");
                
                // Create scene
                const scene = new THREE.Scene();
                scene.background = new THREE.Color(0x333333);
                
                // Create camera
                const camera = new THREE.PerspectiveCamera(
                    75, 
                    window.innerWidth / window.innerHeight, 
                    0.1, 
                    1000
                );
                camera.position.z = 5;
                
                // Create renderer
                const renderer = new THREE.WebGLRenderer({ antialias: true });
                renderer.setSize(window.innerWidth, window.innerHeight);
                document.body.appendChild(renderer.domElement);
                
                // Create a cube
                const geometry = new THREE.BoxGeometry(1, 1, 1);
                const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
                const cube = new THREE.Mesh(geometry, material);
                scene.add(cube);
                
                // Animation loop
                function animate() {
                    requestAnimationFrame(animate);
                    cube.rotation.x += 0.01;
                    cube.rotation.y += 0.01;
                    renderer.render(scene, camera);
                }
                
                // Start animation
                animate();
                
                // Handle window resize
                window.addEventListener('resize', () => {
                    camera.aspect = window.innerWidth / window.innerHeight;
                    camera.updateProjectionMatrix();
                    renderer.setSize(window.innerWidth, window.innerHeight);
                });
                
                console.log("Three.js scene initialized");
            }
            
            // Alternative init in case DOMContentLoaded already fired
            if (document.readyState === "complete" || document.readyState === "interactive") {
                console.log("DOM already loaded, initializing immediately");
                setTimeout(init, 1);
            }
        </script>
    </body>
    </html>
    """

# Simple Claude API call function
async def call_claude_api(prompt):
    try:
        headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": "You are an expert in Three.js. Create complete, standalone Three.js code based on the description.",
            "messages": [
                {"role": "user", "content": f"Create a Three.js scene with: {prompt}"}
            ]
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post("https://api.anthropic.com/v1/messages", json=data, headers=headers)
            response.raise_for_status()
            return response.json()["content"][0]["text"]
    except Exception as e:
        return f"Error: {str(e)}"

# Extract code from Claude's response
def extract_code(response_text):
    html_pattern = r"```(?:html)(.*?)```"
    html_matches = re.findall(html_pattern, response_text, re.DOTALL)
    
    if html_matches:
        return html_matches[0].strip()
    
    js_pattern = r"```(?:javascript|js)(.*?)```"
    js_matches = re.findall(js_pattern, response_text, re.DOTALL)
    
    if js_matches:
        js_code = js_matches[0].strip()
        # Wrap JS in HTML
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>body {{ margin: 0; }}</style>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        </head>
        <body>
            <script>{js_code}</script>
        </body>
        </html>
        """
    
    return ""

# Generate Three.js scene
def generate_scene(prompt):
    try:
        response_text = asyncio.run(call_claude_api(prompt))
        code = extract_code(response_text)
        return code, response_text
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return "", f"Error: {str(e)}"

# Main UI
st.title("🎮 AI Three.js Scene Generator")

# Test basic Three.js rendering
st.subheader("Test WebGL Compatibility")
if st.button("Run WebGL Test"):
    minimal_scene = create_minimal_scene()
    st.components.v1.html(minimal_scene, height=300)

with st.form("generator_form"):
    user_prompt = st.text_area(
        "Describe your 3D scene:",
        placeholder="A simple rotating cube with colorful materials",
        height=100
    )
    
    submitted = st.form_submit_button("Generate Scene")
    
    if submitted and user_prompt:
        with st.spinner("Generating scene..."):
            code, response = generate_scene(user_prompt)
            
            if code:
                st.session_state.current_scene = {
                    "prompt": user_prompt,
                    "code": code,
                    "response": response,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                st.success("Scene generated!")
            else:
                st.error("Failed to generate scene")

# Display current scene
if st.session_state.current_scene:
    scene = st.session_state.current_scene
    st.subheader(f"Scene: {scene['prompt']}")
    
    # Try to render the scene using iframe with specific settings
    st.components.v1.html(scene["code"], height=500, scrolling=True)
    
    # Display tabs for code and response
    tab1, tab2 = st.tabs(["Generated HTML", "AI Response"])
    
    with tab1:
        st.code(scene["code"], language="html")
        st.download_button(
            "Download HTML",
            scene["code"],
            file_name="threejs_scene.html",
            mime="text/html"
        )
    
    with tab2:
        st.text_area("Full Response", scene["response"], height=300)

# Add a direct download option for minimal scene
st.markdown("---")
st.markdown("### Troubleshooting")
st.markdown("If you can't see the 3D scene, download and open the file directly in your browser:")
if st.download_button(
    "Download Basic WebGL Test",
    create_minimal_scene(),
    file_name="minimal_threejs.html",
    mime="text/html"
):
    st.info("Open the downloaded file in your browser to test WebGL support")
