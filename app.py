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
if "active_page" not in st.session_state:
    st.session_state.active_page = "generator"  # Default to generator page

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
    # Create a unique ID for the scene
    scene_id = f"scene_{int(time.time())}"
    
    st.session_state.history.append({
        "id": scene_id,
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

def get_solar_system_demo():
    """Return the solar system demo scene."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Procedural Solar System</title>
      <style>
        body {
          margin: 0;
          overflow: hidden;
          background-color: #000;
        }
        canvas {
          width: 100%;
          height: 100%;
          display: block;
        }
        .info {
          position: absolute;
          top: 10px;
          left: 10px;
          color: white;
          font-family: Arial, sans-serif;
          padding: 10px;
          background-color: rgba(0, 0, 0, 0.5);
          border-radius: 5px;
          font-size: 14px;
          z-index: 100;
        }
        .planet-label {
          position: absolute;
          color: white;
          font-family: Arial, sans-serif;
          font-size: 12px;
          padding: 2px 5px;
          background-color: rgba(0, 0, 0, 0.5);
          border-radius: 3px;
          pointer-events: none;
          display: none;
        }
      </style>
    </head>
    <body>
      <div class="info">Solar System<br>Use mouse to rotate, scroll to zoom</div>
      <div id="planetLabel" class="planet-label"></div>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
      <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
      <script>
        // Scene setup
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040);
        scene.add(ambientLight);
        const pointLight = new THREE.PointLight(0xffffff, 2, 300);
        scene.add(pointLight);

        // Camera controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        camera.position.set(0, 50, 150);
        controls.update();

        // Procedural texture generation
        function createCanvasTexture(width, height, drawFunction) {
          const canvas = document.createElement('canvas');
          canvas.width = width;
          canvas.height = height;
          const ctx = canvas.getContext('2d');
          drawFunction(ctx, width, height);
          return new THREE.CanvasTexture(canvas);
        }

        // Generate star field texture
        function generateStarfieldTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            ctx.fillStyle = 'black';
            ctx.fillRect(0, 0, width, height);
            
            // Add stars
            ctx.fillStyle = 'white';
            for (let i = 0; i < 1000; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const radius = Math.random() * 1.5;
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
            }
            
            // Add some colored stars
            const colors = ['rgba(255,200,200,0.8)', 'rgba(200,200,255,0.8)', 'rgba(255,255,200,0.8)'];
            for (let i = 0; i < 100; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const radius = Math.random() * 1.8 + 0.5;
              ctx.fillStyle = colors[Math.floor(Math.random() * colors.length)];
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
            }
          });
        }

        // Sun texture - fiery with solar flares
        function generateSunTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Create radial gradient for the sun
            const gradient = ctx.createRadialGradient(
              width/2, height/2, 0,
              width/2, height/2, width/2
            );
            
            gradient.addColorStop(0, '#ffff80');
            gradient.addColorStop(0.2, '#ffdd00');
            gradient.addColorStop(0.4, '#ff8800');
            gradient.addColorStop(0.6, '#ff4400');
            gradient.addColorStop(1, '#ff2200');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, width, height);
            
            // Add solar flares
            for (let i = 0; i < 15; i++) {
              const angle = Math.random() * Math.PI * 2;
              const length = Math.random() * width/4 + width/10;
              const startX = width/2 + Math.cos(angle) * (width/2 - 10);
              const startY = height/2 + Math.sin(angle) * (height/2 - 10);
              const endX = width/2 + Math.cos(angle) * (width/2 + length);
              const endY = height/2 + Math.sin(angle) * (height/2 + length);
              
              const flareGradient = ctx.createLinearGradient(startX, startY, endX, endY);
              flareGradient.addColorStop(0, 'rgba(255, 255, 0, 0.7)');
              flareGradient.addColorStop(1, 'rgba(255, 100, 0, 0)');
              
              ctx.beginPath();
              ctx.moveTo(startX, startY);
              ctx.lineTo(endX, endY);
              ctx.lineWidth = 5 + Math.random() * 15;
              ctx.strokeStyle = flareGradient;
              ctx.stroke();
            }
            
            // Add sun spots
            ctx.fillStyle = 'rgba(80, 30, 0, 0.3)';
            for (let i = 0; i < 8; i++) {
              const angle = Math.random() * Math.PI * 2;
              const distance = Math.random() * width/3;
              const x = width/2 + Math.cos(angle) * distance;
              const y = height/2 + Math.sin(angle) * distance;
              const radius = 5 + Math.random() * 15;
              
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
            }
          });
        }

        // Mercury - rocky, cratered
        function generateMercuryTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Base color - rocky gray-brown
            ctx.fillStyle = '#a0928b';
            ctx.fillRect(0, 0, width, height);
            
            // Add darker patches
            for (let i = 0; i < 20; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const radius = Math.random() * width/6 + width/10;
              
              const gradient = ctx.createRadialGradient(
                x, y, 0,
                x, y, radius
              );
              
              gradient.addColorStop(0, 'rgba(90, 85, 70, 0.4)');
              gradient.addColorStop(1, 'rgba(90, 85, 70, 0)');
              
              ctx.fillStyle = gradient;
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
            }
            
            // Add craters
            for (let i = 0; i < 300; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const radius = Math.random() * 5 + 1;
              
              ctx.fillStyle = Math.random() > 0.5 ? '#887775' : '#b5a9a4';
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
              
              // Add crater rim highlight
              ctx.strokeStyle = '#c5b9b4';
              ctx.lineWidth = 0.5;
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.stroke();
            }
          });
        }

        // Venus - yellowish with swirling clouds
        function generateVenusTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Base color - yellowish
            ctx.fillStyle = '#e6c587';
            ctx.fillRect(0, 0, width, height);
            
            // Add swirling clouds
            for (let i = 0; i < 10; i++) {
              const centerX = width / 2;
              const centerY = height / 2;
              
              ctx.strokeStyle = 'rgba(255, 240, 200, 0.3)';
              ctx.lineWidth = 10 + Math.random() * 20;
              
              // Create swirls
              ctx.beginPath();
              for (let angle = 0; angle < Math.PI * 8; angle += 0.1) {
                const radius = (width/3) * (1 - angle/(Math.PI * 10)) + Math.random() * 20;
                const x = centerX + Math.cos(angle) * radius;
                const y = centerY + Math.sin(angle) * radius;
                
                if (angle === 0) {
                  ctx.moveTo(x, y);
                } else {
                  ctx.lineTo(x, y);
                }
              }
              ctx.stroke();
            }
            
            // Add atmospheric haze
            ctx.fillStyle = 'rgba(240, 218, 180, 0.3)';
            ctx.fillRect(0, 0, width, height);
          });
        }

        // Earth - blue oceans, green/brown land, white clouds
        function generateEarthTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Blue oceans as base
            ctx.fillStyle = '#1a66b2';
            ctx.fillRect(0, 0, width, height);
            
            // Generate continents
            const numContinents = 7;
            for (let i = 0; i < numContinents; i++) {
              const centerX = Math.random() * width;
              const centerY = Math.random() * height;
              const baseSize = width / 6;
              
              // Continent color - green to brown
              const greenValue = 100 + Math.floor(Math.random() * 60);
              const redValue = 140 + Math.floor(Math.random() * 40);
              ctx.fillStyle = `rgb(${redValue}, ${greenValue}, 50)`;
              
              // Draw landmass with random blob shape
              ctx.beginPath();
              const numPoints = 15;
              for (let j = 0; j <= numPoints; j++) {
                const angle = (j / numPoints) * Math.PI * 2;
                const radius = baseSize * (0.5 + Math.random() * 0.8);
                const x = centerX + Math.cos(angle) * radius;
                const y = centerY + Math.sin(angle) * radius;
                
                if (j === 0) {
                  ctx.moveTo(x, y);
                } else {
                  ctx.lineTo(x, y);
                }
              }
              ctx.closePath();
              ctx.fill();
            }
            
            // Add clouds
            ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
            for (let i = 0; i < 20; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const radius = Math.random() * width/8 + width/20;
              
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
            }
            
            // Add polar ice caps
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            // North pole
            ctx.beginPath();
            ctx.ellipse(width/2, height/10, width/3, height/6, 0, 0, Math.PI * 2);
            ctx.fill();
            // South pole
            ctx.beginPath();
            ctx.ellipse(width/2, height - height/10, width/3, height/6, 0, 0, Math.PI * 2);
            ctx.fill();
          });
        }

        // Mars - reddish with darker features
        function generateMarsTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Base reddish color
            ctx.fillStyle = '#c1572f';
            ctx.fillRect(0, 0, width, height);
            
            // Add darker regions
            for (let i = 0; i < 8; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const radius = Math.random() * width/4 + width/8;
              
              const gradient = ctx.createRadialGradient(
                x, y, 0,
                x, y, radius
              );
              
              gradient.addColorStop(0, 'rgba(100, 40, 20, 0.5)');
              gradient.addColorStop(1, 'rgba(100, 40, 20, 0)');
              
              ctx.fillStyle = gradient;
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
            }
            
            // Add polar caps
            ctx.fillStyle = 'rgba(255, 240, 230, 0.7)';
            // North pole
            ctx.beginPath();
            ctx.ellipse(width/2, height/8, width/4, height/8, 0, 0, Math.PI * 2);
            ctx.fill();
            // South pole
            ctx.beginPath();
            ctx.ellipse(width/2, height - height/8, width/4, height/8, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // Add craters
            for (let i = 0; i < 200; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const radius = Math.random() * 3 + 1;
              
              ctx.fillStyle = '#a4472f';
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
            }
          });
        }

        // Jupiter - banded with Great Red Spot
        function generateJupiterTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Base color
            ctx.fillStyle = '#ebd39a';
            ctx.fillRect(0, 0, width, height);
            
            // Add bands
            const bands = [
              { y: height * 0.1, color: 'rgba(184, 140, 50, 0.8)', thickness: height * 0.08 },
              { y: height * 0.3, color: 'rgba(240, 200, 150, 0.7)', thickness: height * 0.1 },
              { y: height * 0.5, color: 'rgba(184, 140, 50, 0.8)', thickness: height * 0.1 },
              { y: height * 0.7, color: 'rgba(240, 200, 150, 0.7)', thickness: height * 0.1 },
              { y: height * 0.9, color: 'rgba(184, 140, 50, 0.8)', thickness: height * 0.08 }
            ];
            
            // Draw bands
            bands.forEach(band => {
              ctx.fillStyle = band.color;
              ctx.fillRect(0, band.y - band.thickness/2, width, band.thickness);
              
              // Add details to each band
              ctx.fillStyle = 'rgba(210, 180, 120, 0.3)';
              for (let i = 0; i < 10; i++) {
                const x = Math.random() * width;
                const y = band.y - band.thickness/2 + Math.random() * band.thickness;
                const spotWidth = Math.random() * width/6 + width/10;
                const spotHeight = Math.random() * band.thickness/2 + band.thickness/4;
                
                ctx.beginPath();
                ctx.ellipse(x, y, spotWidth, spotHeight, 0, 0, Math.PI * 2);
                ctx.fill();
              }
            });
            
            // Add Great Red Spot
            const spotX = width * 0.7;
            const spotY = height * 0.3;
            const spotWidth = width * 0.2;
            const spotHeight = height * 0.08;
            
            ctx.fillStyle = '#bf4040';
            ctx.beginPath();
            ctx.ellipse(spotX, spotY, spotWidth, spotHeight, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // Add highlight to Great Red Spot
            ctx.fillStyle = 'rgba(255, 100, 100, 0.3)';
            ctx.beginPath();
            ctx.ellipse(spotX - spotWidth * 0.2, spotY - spotHeight * 0.2, spotWidth * 0.7, spotHeight * 0.7, 0, 0, Math.PI * 2);
            ctx.fill();
          });
        }

        // Saturn - similar to Jupiter but more muted
        function generateSaturnTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Base color - pale yellow
            ctx.fillStyle = '#e6dcb3';
            ctx.fillRect(0, 0, width, height);
            
            // Add bands
            const bands = [
              { y: height * 0.15, color: 'rgba(200, 180, 120, 0.6)', thickness: height * 0.1 },
              { y: height * 0.35, color: 'rgba(220, 200, 150, 0.5)', thickness: height * 0.1 },
              { y: height * 0.55, color: 'rgba(200, 180, 120, 0.6)', thickness: height * 0.1 },
              { y: height * 0.75, color: 'rgba(220, 200, 150, 0.5)', thickness: height * 0.1 },
              { y: height * 0.9, color: 'rgba(200, 180, 120, 0.6)', thickness: height * 0.08 }
            ];
            
            // Draw bands
            bands.forEach(band => {
              ctx.fillStyle = band.color;
              ctx.fillRect(0, band.y - band.thickness/2, width, band.thickness);
              
              // Add details to each band
              ctx.fillStyle = 'rgba(190, 170, 110, 0.3)';
              for (let i = 0; i < 8; i++) {
                const x = Math.random() * width;
                const y = band.y - band.thickness/2 + Math.random() * band.thickness;
                const spotWidth = Math.random() * width/8 + width/12;
                const spotHeight = Math.random() * band.thickness/2 + band.thickness/4;
                
                ctx.beginPath();
                ctx.ellipse(x, y, spotWidth, spotHeight, 0, 0, Math.PI * 2);
                ctx.fill();
              }
            });
            
            // Add subtle storm
            const stormX = width * 0.3;
            const stormY = height * 0.4;
            const stormRadius = width * 0.08;
            
            const stormGradient = ctx.createRadialGradient(
              stormX, stormY, 0,
              stormX, stormY, stormRadius
            );
            
            stormGradient.addColorStop(0, 'rgba(230, 210, 160, 0.8)');
            stormGradient.addColorStop(1, 'rgba(230, 210, 160, 0)');
            
            ctx.fillStyle = stormGradient;
            ctx.beginPath();
            ctx.arc(stormX, stormY, stormRadius, 0, Math.PI * 2);
            ctx.fill();
          });
        }

        // Saturn ring texture
        function generateSaturnRingTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Create transparent background
            ctx.clearRect(0, 0, width, height);
            
            // Create ring gradient
            const gradient = ctx.createRadialGradient(
              width/2, height/2, width/4,
              width/2, height/2, width/2
            );
            
            gradient.addColorStop(0, 'rgba(230, 220, 180, 0.9)');
            gradient.addColorStop(0.2, 'rgba(200, 180, 140, 0.8)');
            gradient.addColorStop(0.4, 'rgba(180, 160, 120, 0.7)');
            gradient.addColorStop(0.6, 'rgba(160, 140, 100, 0.6)');
            gradient.addColorStop(0.8, 'rgba(140, 120, 80, 0.5)');
            gradient.addColorStop(1, 'rgba(120, 100, 60, 0.4)');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, width, height);
            
            // Add ring divisions
            const ringDivisions = [
              { pos: 0.3, width: 0.02 },
              { pos: 0.5, width: 0.04 },
              { pos: 0.7, width: 0.03 },
              { pos: 0.85, width: 0.02 }
            ];
            
            ringDivisions.forEach(div => {
              const radius = width/4 + (width/4) * div.pos;
              const ringWidth = (width/4) * div.width;
              
              ctx.strokeStyle = 'rgba(50, 40, 30, 0.6)';
              ctx.lineWidth = ringWidth;
              ctx.beginPath();
              ctx.arc(width/2, height/2, radius, 0, Math.PI * 2);
              ctx.stroke();
            });
            
            // Add particles to rings
            ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
            for (let i = 0; i < 400; i++) {
              const angle = Math.random() * Math.PI * 2;
              const distance = width/4 + Math.random() * (width/4);
              const x = width/2 + Math.cos(angle) * distance;
              const y = height/2 + Math.sin(angle) * distance;
              const size = Math.random() * 1.5 + 0.5;
              
              ctx.beginPath();
              ctx.arc(x, y, size, 0, Math.PI * 2);
              ctx.fill();
            }
          });
        }

        // Uranus - light blue-green
        function generateUranusTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Create base gradient
            const gradient = ctx.createRadialGradient(
              width/2, height/2, 0,
              width/2, height/2, width/2
            );
            
            gradient.addColorStop(0, '#b1e5ee');
            gradient.addColorStop(0.7, '#77a5b5');
            gradient.addColorStop(1, '#5f8a9a');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, width, height);
            
            // Add subtle bands
            const bands = [
              { y: height * 0.25, color: 'rgba(160, 210, 220, 0.3)', thickness: height * 0.1 },
              { y: height * 0.5, color: 'rgba(120, 180, 190, 0.3)', thickness: height * 0.12 },
              { y: height * 0.75, color: 'rgba(160, 210, 220, 0.3)', thickness: height * 0.1 }
            ];
            
            bands.forEach(band => {
              ctx.fillStyle = band.color;
              ctx.fillRect(0, band.y - band.thickness/2, width, band.thickness);
            });
            
            // Add a few subtle clouds
            ctx.fillStyle = 'rgba(170, 230, 240, 0.2)';
            for (let i = 0; i < 8; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const cloudWidth = Math.random() * width/8 + width/12;
              const cloudHeight = Math.random() * height/20 + height/40;
              
              ctx.beginPath();
              ctx.ellipse(x, y, cloudWidth, cloudHeight, 0, 0, Math.PI * 2);
              ctx.fill();
            }
          });
        }

        // Neptune - darker blue
        function generateNeptuneTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Create base gradient
            const gradient = ctx.createRadialGradient(
              width/2, height/2, 0,
              width/2, height/2, width/2
            );
            
            gradient.addColorStop(0, '#3e69b3');
            gradient.addColorStop(0.7, '#2a4580');
            gradient.addColorStop(1, '#1a2850');
            
            ctx.fillStyle = gradient;
            ctx.fillRect(0, 0, width, height);
            
            // Add subtle bands
            const bands = [
              { y: height * 0.3, color: 'rgba(70, 120, 180, 0.3)', thickness: height * 0.15 },
              { y: height * 0.6, color: 'rgba(40, 80, 130, 0.3)', thickness: height * 0.12 },
              { y: height * 0.85, color: 'rgba(70, 120, 180, 0.3)', thickness: height * 0.1 }
            ];
            
            bands.forEach(band => {
              ctx.fillStyle = band.color;
              ctx.fillRect(0, band.y - band.thickness/2, width, band.thickness);
            });
            
            // Add Great Dark Spot
            const spotX = width * 0.6;
            const spotY = height * 0.4;
            const spotWidth = width * 0.15;
            const spotHeight = height * 0.08;
            
            ctx.fillStyle = 'rgba(10, 30, 60, 0.7)';
            ctx.beginPath();
            ctx.ellipse(spotX, spotY, spotWidth, spotHeight, 0, 0, Math.PI * 2);
            ctx.fill();
            
            // Add smaller storms and clouds
            ctx.fillStyle = 'rgba(100, 150, 220, 0.3)';
            for (let i = 0; i < 12; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const cloudWidth = Math.random() * width/12 + width/24;
              const cloudHeight = Math.random() * height/25 + height/50;
              
              ctx.beginPath();
              ctx.ellipse(x, y, cloudWidth, cloudHeight, Math.random() * Math.PI, 0, Math.PI * 2);
              ctx.fill();
            }
          });
        }

        // Moon texture
        function generateMoonTexture(size) {
          return createCanvasTexture(size, size, (ctx, width, height) => {
            // Base color - grayish
            ctx.fillStyle = '#aaa9ad';
            ctx.fillRect(0, 0, width, height);
            
            // Add darker and lighter patches
            for (let i = 0; i < 30; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const radius = Math.random() * width/8 + width/16;
              
              const gradient = ctx.createRadialGradient(
                x, y, 0,
                x, y, radius
              );
              
              if (Math.random() > 0.5) {
                // Darker patch (maria)
                gradient.addColorStop(0, 'rgba(70, 70, 80, 0.5)');
                gradient.addColorStop(1, 'rgba(70, 70, 80, 0)');
              } else {
                // Lighter patch (highlands)
                gradient.addColorStop(0, 'rgba(200, 200, 210, 0.4)');
                gradient.addColorStop(1, 'rgba(200, 200, 210, 0)');
              }
              
              ctx.fillStyle = gradient;
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
            }
            
            // Add craters
            for (let i = 0; i < 300; i++) {
              const x = Math.random() * width;
              const y = Math.random() * height;
              const radius = Math.random() * 5 + 1;
              
              // Crater
              ctx.fillStyle = '#8a8a8a';
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.fill();
              
              // Crater rim highlight
              ctx.strokeStyle = '#c5c5c5';
              ctx.lineWidth = 0.5;
              ctx.beginPath();
              ctx.arc(x, y, radius, 0, Math.PI * 2);
              ctx.stroke();
            }
          });
        }

        // Create sun
        const sunGeometry = new THREE.SphereGeometry(10, 64, 64);
        const sunTexture = generateSunTexture(512);
        const sunMaterial = new THREE.MeshBasicMaterial({ 
          map: sunTexture,
          emissive: 0xffdd00,
          emissiveMap: sunTexture,
          emissiveIntensity: 0.5
        });
        const sun = new THREE.Mesh(sunGeometry, sunMaterial);
        scene.add(sun);

        // Add sun glow effect
        const sunGlowGeometry = new THREE.SphereGeometry(13, 32, 32);
        const sunGlowMaterial = new THREE.MeshBasicMaterial({
          color: 0xffdd00,
          transparent: true,
          opacity: 0.2,
          side: THREE.BackSide
        });
        const sunGlow = new THREE.Mesh(sunGlowGeometry, sunGlowMaterial);
        scene.add(sunGlow);

        // Helper function to create a planet
        function createPlanet(radius, textureFn, distance, name, tilt = 0, ringConfig = null) {
          const geometry = new THREE.SphereGeometry(radius, 32, 32);
          const texture = textureFn(256);
          const material = new THREE.MeshLambertMaterial({ map: texture });
          const planet = new THREE.Mesh(geometry, material);
          planet.userData.name = name;
          
          // Create orbit
          const orbitGeometry = new THREE.RingGeometry(distance - 0.1, distance + 0.1, 64);
          const orbitMaterial = new THREE.MeshBasicMaterial({ 
            color: 0x444444, 
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.3
          });
          const orbit = new THREE.Mesh(orbitGeometry, orbitMaterial);
          orbit.rotation.x = Math.PI / 2;
          scene.add(orbit);
          
          // Create planetary system
          const planetSystem = new THREE.Object3D();
          scene.add(planetSystem);
          
          // Create orbit path
          const planetOrbit = new THREE.Object3D();
          planetSystem.add(planetOrbit);
          
          // Add planet to orbit
          planetOrbit.add(planet);
          planet.position.x = distance;
          
          // Tilt the planet
          planet.rotation.x = tilt * Math.PI / 180;
          
          // Add rings if configured (e.g., for Saturn)
          if (ringConfig) {
            const { innerRadius, outerRadius } = ringConfig;
            const ringGeometry = new THREE.RingGeometry(innerRadius, outerRadius, 64);
            const ringTexture = generateSaturnRingTexture(256);
            const ringMaterial = new THREE.MeshBasicMaterial({ 
              map: ringTexture,
              side: THREE.DoubleSide,
              transparent: true,
              opacity: 0.9
            });
            const ring = new THREE.Mesh(ringGeometry, ringMaterial);
            ring.rotation.x = Math.PI / 2;
            planet.add(ring);
          }
          
          return { planet, planetSystem, planetOrbit, name, distance };
        }

        // Create planets
        const planets = [
          createPlanet(0.8, generateMercuryTexture, 20, "Mercury", 0.01),
          createPlanet(1.5, generateVenusTexture, 30, "Venus", 177.4),
          createPlanet(1.6, generateEarthTexture, 40, "Earth", 23.5),
          createPlanet(1.2, generateMarsTexture, 50, "Mars", 25.2),
          createPlanet(4.0, generateJupiterTexture, 65, "Jupiter", 3.1),
          createPlanet(3.5, generateSaturnTexture, 80, "Saturn", 26.7, {
            innerRadius: 4,
            outerRadius: 7
          }),
          createPlanet(2.5, generateUranusTexture, 95, "Uranus", 97.8),
          createPlanet(2.3, generateNeptuneTexture, 110, "Neptune", 28.3)
        ];
        
        // Add Earth's moon
        const moonGeometry = new THREE.SphereGeometry(0.4, 24, 24);
        const moonTexture = generateMoonTexture(128);
        const moonMaterial = new THREE.MeshLambertMaterial({
          map: moonTexture
        });
        const moon = new THREE.Mesh(moonGeometry, moonMaterial);
        moon.userData.name = "Moon";
        
        const moonOrbit = new THREE.Object3D();
        planets[2].planet.add(moonOrbit);
        moonOrbit.add(moon);
        moon.position.x = 3;

        // Add starfield background (replaces individual stars with a skybox)
        const starfieldGeometry = new THREE.SphereGeometry(400, 32, 32);
        const starfieldTexture = generateStarfieldTexture(1024);
        const starfieldMaterial = new THREE.MeshBasicMaterial({
          map: starfieldTexture,
          side: THREE.BackSide
        });
        const starfield = new THREE.Mesh(starfieldGeometry, starfieldMaterial);
        scene.add(starfield);

        // Planet labeling
        const planetLabel = document.getElementById('planetLabel');
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        
        function onMouseMove(event) {
          mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
          mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
          
          raycaster.setFromCamera(mouse, camera);
          
          // Get all meshes to check for intersection
          const meshes = planets.map(p => p.planet);
          meshes.push(moon);
          meshes.push(sun);
          
          const intersects = raycaster.intersectObjects(meshes);
          
          if (intersects.length > 0) {
            const object = intersects[0].object;
            const name = object.userData.name;
            
            if (name) {
              planetLabel.textContent = name;
              planetLabel.style.display = 'block';
              planetLabel.style.left = event.clientX + 10 + 'px';
              planetLabel.style.top = event.clientY + 10 + 'px';
            }
          } else {
            planetLabel.style.display = 'none';
          }
        }
        
        window.addEventListener('mousemove', onMouseMove, false);

        // Animation
        let time = 0;
        function animate() {
          requestAnimationFrame(animate);
          time += 0.005;
          
          // Make the sun pulse slightly
          const pulseFactor = 1 + Math.sin(time * 2) * 0.03;
          sunGlow.scale.set(pulseFactor, pulseFactor, pulseFactor);
          
          // Rotate planets around the sun
          planets.forEach((planet, index) => {
            // Different speeds based on distance
            const speed = 0.005 / (0.5 + index * 0.2);
            planet.planetSystem.rotation.y += speed;
            
            // Rotate planets on their axes
            planet.planet.rotation.y += 0.01 / (index * 0.2 + 0.5);
          });
          
          // Rotate moon around Earth
          if (moonOrbit) {
            moonOrbit.rotation.y += 0.02;
            moon.rotation.y += 0.01;
          }
          
          // Rotate sun
          sun.rotation.y += 0.002;
          
          renderer.render(scene, camera);
        }

        // Handle window resize
        window.addEventListener('resize', () => {
          camera.aspect = window.innerWidth / window.innerHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // Start animation
        animate();
      </script>
    </body>
    </html>
    """

def render_enhanced_sidebar():
    """Display an enhanced sidebar with navigation and history."""
    # Add title with fancy icon
    st.sidebar.markdown("# 🚀 Three.js Explorer")
    
    # Page navigation
    st.sidebar.markdown("## 📋 Navigation")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("🎮 Generator", use_container_width=True):
            st.session_state.active_page = "generator"
            st.rerun()
    with col2:
        if st.button("🌌 Demo Scene", use_container_width=True):
            st.session_state.active_page = "demo"
            st.rerun()
    
    # Add separator
    st.sidebar.markdown("---")
    
    # History section
    st.sidebar.markdown("## 📜 Scene History")
    
    if not st.session_state.history:
        st.sidebar.info("No scenes in history yet. Generate some scenes to see them here!")
    else:
        for i, item in enumerate(st.session_state.history):
            scene_title = item["prompt"]
            if len(scene_title) > 35:
                scene_title = scene_title[:32] + "..."
                
            col1, col2 = st.sidebar.columns([3, 1])
            with col1:
                if st.button(f"{scene_title}", key=f"history_{i}", use_container_width=True):
                    st.session_state.current_scene = item
                    st.session_state.active_page = "generator"  # Switch to generator page when loading history
                    st.rerun()
            with col2:
                # Add a delete button for each history item
                if st.button("🗑️", key=f"delete_{i}", help="Delete from history"):
                    st.session_state.history.pop(i)
                    # If we deleted the current scene, reset it
                    if st.session_state.current_scene and \
                       st.session_state.current_scene.get("id", "") == item.get("id", ""):
                        st.session_state.current_scene = None
                    st.rerun()
    
    # Add clear history button
    if st.session_state.history:
        if st.sidebar.button("Clear History", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    
    # Add helpful tips at the bottom
    with st.sidebar.expander("💡 Tips & Tricks", expanded=False):
        st.markdown("""
        - Use specific descriptions for better results
        - Try generating landscapes, space scenes, or abstract art
        - View the solar system demo for inspiration
        - Check the code tab to learn Three.js techniques
        - Downloaded scenes work in any browser
        """)

# Generator page content
def show_generator_page():
    """Show the main scene generator page."""
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
                        "id": f"scene_{int(time.time())}",
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
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="Download HTML",
                        data=html_content,
                        file_name="threejs_scene.html",
                        mime="text/html",
                        use_container_width=True
                    )
                with col2:
                    # Add a button to view the scene in full-screen
                    st.markdown(
                        f'<a href="data:text/html;base64,{base64.b64encode(html_content.encode()).decode()}" target="_blank" style="text-decoration:none; width:100%;">'
                        f'<div style="background-color:#4CAF50; padding:10px; color:white; text-align:center; border-radius:4px; cursor:pointer; width:100%;">View Full Screen</div>'
                        f'</a>', 
                        unsafe_allow_html=True
                    )
        
        with tab2:
            st.text_area("Full AI Response", value=scene.get("full_response", ""), height=400)
        
        with tab3:
            st.write("Debug Information")
            st.json({
                "id": scene.get("id", ""),
                "code_type": scene.get("code_type", ""),
                "timestamp": scene.get("timestamp", ""),
                "html_length": len(scene.get("html", "")),
                "contains_three.js": "three.js" in scene.get("html", "").lower(),
                "contains_orbitcontrols": "orbitcontrols" in scene.get("html", "").lower()
            })
            
            if st.button("Force Reload Scene"):
                st.rerun()
    
    # Instructions and tips at the bottom
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
        - If a scene doesn't load, try clicking "Force Reload Scene"
        - If you see errors, check the "Debug" tab for more information
        - Some complex scenes may take longer to generate and load
        """)

# Demo page content
def show_demo_page():
    """Show the solar system demo page."""
    st.title("🌌 Solar System Demo")
    st.write("An interactive procedural solar system created with Three.js")
    
    # Description
    with st.expander("About this demo", expanded=True):
        st.markdown("""
        This procedural solar system demo showcases what's possible with Three.js. Key features:
        
        - **Procedurally generated textures** for all planets and the sun
        - **Realistic orbital mechanics** with different rotation speeds
        - **Interactive controls**: rotate, pan, and zoom to explore
        - **Planet labels** appear when you hover over objects
        - **Physical accuracy**: relative planet sizes, orbits, and tilts
        
        This is a great example of what can be created with Three.js for science visualization, education, or games.
        Hover over any planet to see its name!
        """)
    
    # Render the solar system demo
    render_threejs_scene(get_solar_system_demo(), height=700)
    
    # Features explanation
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Technical Features")
        st.markdown("""
        - Canvas-based procedural texture generation
        - Complex nested 3D transformations
        - Dynamic lighting and materials
        - Raycasting for interactive object selection
        - Custom shader effects for the sun's glow
        - Responsive design that works on all devices
        """)
    
    with col2:
        st.subheader("How to Use This Demo")
        st.markdown("""
        - **Click and drag** to orbit around the scene
        - **Right-click and drag** to pan
        - **Scroll** to zoom in and out
        - **Hover** over any planet to see its name
        - **Wait** to see planets orbit around the sun
        - Observe Saturn's rings and Earth's moon
        """)
    
    # Button to view source code
    with st.expander("View Source Code", expanded=False):
        st.code(get_solar_system_demo(), language="html")
        
        st.download_button(
            label="Download Solar System Demo",
            data=get_solar_system_demo(),
            file_name="solar_system.html",
            mime="text/html"
        )

# Main app logic
def main():
    """Main app function to control page flow."""
    # Render the enhanced sidebar
    render_enhanced_sidebar()
    
    # Show the appropriate page based on active_page state
    if st.session_state.active_page == "generator":
        show_generator_page()
    elif st.session_state.active_page == "demo":
        show_demo_page()

# Run the app
if __name__ == "__main__":
    main()
