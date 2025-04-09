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

# Get API key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Improved prompt enhancer with examples
async def enhance_prompt(basic_prompt):
    """Enhance a basic prompt with rich details for 3D scene generation"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    # Significantly improved system prompt with examples and clear direction
    system_prompt = """You are an expert at transforming simple scene descriptions into detailed, vivid scene specifications for 3D visualization.

Your task is to expand basic prompts into rich, detailed scene descriptions, adding significant visual details while maintaining the core concept.

Here are examples of the level of enhancement expected:

BASIC: "A cool city with many buildings"
ENHANCED: "Create a 3D city scene featuring a bustling urban environment with skyscrapers, apartment buildings, and smaller shops lining the streets. Incorporate roads with moving cars, traffic lights, and pedestrian crossings to bring the city to life. Add pedestrians walking on sidewalks and crossing the streets to enhance realism. Include street elements such as lampposts, benches, and trees for a more immersive experience. Utilize dynamic lighting to simulate day and night cycles, and implement basic camera controls to allow users to explore the vibrant cityscape from different perspectives."

BASIC: "A forest with animals"
ENHANCED: "Create a lush 3D forest scene with dense, varied vegetation including tall pine trees, leafy deciduous trees, and undergrowth of ferns and bushes. Populate the forest with wildlife such as deer grazing in clearings, rabbits hopping between bushes, and birds flying overhead or perched on branches. Include a small stream winding through the forest with rocks and fallen logs. Create dappled lighting effects as sunlight filters through the canopy, with particles representing dust or pollen floating in the light beams. Add ambient sounds of rustling leaves, flowing water, and occasional animal calls to complete the immersive forest experience."

BASIC: "A spaceship flying through asteroids"
ENHANCED: "Create a dynamic 3D space scene featuring a sleek, futuristic spaceship navigating through a dense asteroid field. The spaceship should have glowing engines, detailed exterior paneling, and occasional thruster bursts as it maneuvers. Surround it with various sized asteroids - from small rocky debris to massive cratered boulders - all slowly rotating and moving through space. Include distant stars and nebulae as background elements to create depth. Add dramatic lighting effects with the nearest star casting harsh shadows across the spaceship and asteroids. Implement particle effects for engine exhaust and small collisions between asteroids. Allow the camera to follow behind the spaceship as it weaves through this hazardous environment, giving viewers a sense of speed and danger."

Your enhancements should:
1. Add specific visual elements and their attributes (shapes, colors, sizes, materials)
2. Describe environmental details and atmosphere
3. Suggest movement and animations
4. Mention lighting and special effects
5. Describe spatial relationships between objects

The enhancement should be 150-250 words long and focus entirely on visual appearance and behavior, not implementation details."""
    
    data = {
        "model": "claude-3-opus-20240229",  # Using Opus for better enhancement
        "max_tokens": 750,
        "temperature": 0.3,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": f"""Transform this basic 3D scene description:

"{basic_prompt}"

Into a richly detailed scene description similar to the examples in your instructions. 
Make sure to add significant visual details about objects, environment, lighting, movement, and atmosphere.
Focus only on what the scene should look like and how it should behave, not on implementation details."""}
        ]
    }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            json=data,
            headers=headers
        )
        
        if response.status_code != 200:
            return basic_prompt, f"Error: {response.status_code}"
        
        response_data = response.json()
        
        if "content" in response_data and len(response_data["content"]) > 0:
            enhanced_prompt = response_data["content"][0]["text"]
            return enhanced_prompt, None
        else:
            return basic_prompt, "No content in response"

# Scene generator - creates a complete Three.js scene from a prompt
async def generate_scene(prompt):
    """Generate a complete Three.js scene from a prompt"""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    system_prompt = """You are an expert Three.js developer with a specialty in creating complete, working 3D scenes with HTML, CSS, and JavaScript.

Your task is to generate a SINGLE, COMPLETE HTML file containing a Three.js scene based on the user's description. This file will be directly displayed in a web component.

CRITICAL REQUIREMENTS:
1. Your output MUST be a COMPLETE HTML document with <!DOCTYPE html>, <html>, <head>, and <body> tags
2. Include CDN links to Three.js (version 0.137.0 or newer) and OrbitControls
3. Create a responsive scene that works on all screen sizes
4. Use ONLY BufferGeometry (NOT Geometry which is deprecated)
5. Include proper orbit controls for camera navigation
6. Implement simple animations to bring the scene to life
7. Use basic lighting including ambient and directional lights
8. Ensure all code is properly closed with matching brackets and tags
9. Create a scene that works WITHOUT external resources (no external textures, models, etc.)
10. Keep the total code under 300 lines for reliability

YOUR RESPONSE MUST CONTAIN ONLY THE COMPLETE HTML DOCUMENT - NO explanations, NO markdown formatting, NO conversation.
Start with <!DOCTYPE html> and end with </html>."""
    
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 4000,
        "temperature": 0.2,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": f"""Generate a complete, working Three.js scene based on this description:

Description: {prompt}

Generate ONLY the complete HTML document with embedded JavaScript that creates this scene.
- DO NOT use external resources (models, textures, etc.)
- Use minimal, efficient code that will work reliably
- Include THREE.OrbitControls for camera navigation
- Implement simple animations to bring the scene to life
- Ensure the scene is responsive (adapts to window size)
- Use modern Three.js syntax including BufferGeometry (NOT the deprecated Geometry)
- Keep the code under 300 lines total
- Make sure all brackets, parentheses, and HTML tags are properly closed

Return ONLY a complete, working HTML document (no explanations or Markdown).
Your response should start with <!DOCTYPE html> and end with </html>."""}
        ]
    }
    
    debug_info = {
        "request": {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model": data["model"],
            "max_tokens": data["max_tokens"],
            "temperature": data["temperature"]
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            json=data,
            headers=headers
        )
        
        debug_info["status_code"] = response.status_code
        
        if response.status_code != 200:
            debug_info["error"] = f"API error: {response.status_code} - {response.text}"
            return None, debug_info
        
        response_data = response.json()
        debug_info["response_meta"] = {
            "model": response_data.get("model", ""),
            "usage": response_data.get("usage", {}),
        }
        
        if "content" in response_data and len(response_data["content"]) > 0:
            response_text = response_data["content"][0]["text"]
            # Get just the HTML portion
            html_content = extract_html_from_response(response_text)
            debug_info["html_length"] = len(html_content)
            return html_content, debug_info
        else:
            debug_info["error"] = "No content in response"
            return None, debug_info

# HTML extraction - get just the HTML document from a response
def extract_html_from_response(response_text):
    """Extract a complete HTML document from the response text"""
    # Look for a complete HTML document
    html_pattern = r"<!DOCTYPE html>[\s\S]*?<\/html>"
    html_match = re.search(html_pattern, response_text, re.IGNORECASE)
    
    if html_match:
        return html_match.group(0)
    
    # If no match, check for HTML without doctype
    html_pattern = r"<html[\s\S]*?<\/html>"
    html_match = re.search(html_pattern, response_text, re.IGNORECASE)
    
    if html_match:
        return f"<!DOCTYPE html>\n{html_match.group(0)}"
    
    # If still no match, try to extract from code blocks
    code_pattern = r"```(?:html)?\s*([\s\S]*?)\s*```"
    code_matches = re.findall(code_pattern, response_text)
    
    if code_matches:
        # Check each code block for HTML content
        for code in code_matches:
            if "<html" in code.lower() or "<!doctype" in code.lower():
                if code.lower().startswith("<!doctype html>"):
                    return code
                elif code.lower().startswith("<html"):
                    return f"<!DOCTYPE html>\n{code}"
        
        # If no HTML found, use the first code block and wrap it
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated 3D Scene</title>
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
    <div id="info">Generated 3D Scene - Use mouse to navigate</div>
    <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
    <script>
    {code_matches[0]}
    </script>
</body>
</html>"""
    
    # Last resort - create a fallback scene
    return create_fallback_scene()

# Create a fallback scene if all else fails
def create_fallback_scene():
    """Create a basic fallback scene when extraction fails"""
    return """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fallback 3D Scene</title>
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
        #error {
            position: absolute;
            bottom: 20px;
            width: 100%;
            text-align: center;
            color: #ff4444;
            font-family: Arial, sans-serif;
            font-weight: bold;
            pointer-events: none;
            text-shadow: 1px 1px 1px black;
        }
    </style>
</head>
<body>
    <div id="info">Fallback 3D Scene</div>
    <div id="error">Scene generation failed - See debug info</div>
    <script src="https://unpkg.com/three@0.137.0/build/three.min.js"></script>
    <script src="https://unpkg.com/three@0.137.0/examples/js/controls/OrbitControls.js"></script>
    <script>
    // Create a basic scene with an error message
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x333344);
    
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(0, 5, 10);
    
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    document.body.appendChild(renderer.domElement);
    
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    
    // Add lights
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    scene.add(ambientLight);
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 7.5);
    scene.add(directionalLight);
    
    // Create a platform
    const platformGeometry = new THREE.CylinderGeometry(5, 5, 0.5, 32);
    const platformMaterial = new THREE.MeshPhongMaterial({ color: 0x888888 });
    const platform = new THREE.Mesh(platformGeometry, platformMaterial);
    platform.position.y = -0.25;
    scene.add(platform);
    
    // Create error message cube
    const cubeGeometry = new THREE.BoxGeometry(3, 3, 3);
    const cubeMaterial = new THREE.MeshPhongMaterial({ color: 0xff4444 });
    const cube = new THREE.Mesh(cubeGeometry, cubeMaterial);
    cube.position.y = 1.5;
    scene.add(cube);
    
    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        cube.rotation.y += 0.01;
        controls.update();
        renderer.render(scene, camera);
    }
    animate();
    
    // Handle window resize
    window.addEventListener('resize', function() {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    </script>
</body>
</html>"""

# Complete scene generation pipeline
async def generate_scene_from_prompt(basic_prompt):
    """Complete pipeline: enhance prompt then generate scene"""
    # Step 1: Enhance the prompt with more details
    enhanced_prompt, enhance_error = await enhance_prompt(basic_prompt)
    
    if enhance_error:
        st.warning(f"Warning: Using basic prompt because enhancement failed: {enhance_error}")
        prompt_to_use = basic_prompt
    else:
        prompt_to_use = enhanced_prompt
    
    # Step 2: Generate the scene with the enhanced prompt
    html_content, debug_info = await generate_scene(prompt_to_use)
    
    # Store both prompts and debug info
    debug_info["original_prompt"] = basic_prompt
    debug_info["enhanced_prompt"] = prompt_to_use
    
    return html_content, debug_info

# Main app UI
st.title("🎮 Instant 3D Scene Generator")
st.write("Describe any scene and see it in 3D instantly!")

# Main input form
with st.form("scene_generator_form"):
    user_prompt = st.text_area(
        "Describe your 3D scene:",
        placeholder="A cool city with many buildings",
        height=80
    )
    
    generate_button = st.form_submit_button("Generate 3D Scene")
    
    if generate_button and user_prompt:
        with st.spinner("Creating your 3D scene... (this may take up to a minute)"):
            html_content, debug_info = asyncio.run(generate_scene_from_prompt(user_prompt))
            
            if html_content:
                # Store the current scene
                st.session_state.current_scene = {
                    "prompt": user_prompt,
                    "enhanced_prompt": debug_info.get("enhanced_prompt", user_prompt),
                    "html": html_content,
                    "debug_info": debug_info
                }
                st.success("Scene generated successfully!")
            else:
                st.error("Failed to generate scene. See debug tab for details.")
                st.session_state.debug_info = debug_info

# Create tabs for the scene and debug info
tab1, tab2 = st.tabs(["3D Scene", "Scene Details"])

with tab1:
    # Display current scene if available
    if "current_scene" in st.session_state and st.session_state.current_scene:
        scene = st.session_state.current_scene
        
        # Show the scene in an HTML component
        st.components.v1.html(scene["html"], height=600)
        
        # Download button
        st.download_button(
            label="Download HTML",
            data=scene["html"],
            file_name="3d_scene.html",
            mime="text/html"
        )

with tab2:
    if "current_scene" in st.session_state and st.session_state.current_scene:
        scene = st.session_state.current_scene
        
        # Show the prompts
        st.subheader("Prompts")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Original Prompt")
            st.info(scene["prompt"])
        
        with col2:
            st.write("Enhanced Prompt")
            st.success(scene["enhanced_prompt"])
        
        # Show the HTML code
        st.subheader("Generated HTML")
        with st.expander("View HTML Code"):
            st.code(scene["html"], language="html")
        
        # Show debug info
        st.subheader("Debug Information")
        with st.expander("View Debug Info"):
            st.json(scene["debug_info"])

# Instructions
st.markdown("---")
st.markdown("""
### How to Use
1. Enter a simple description of the 3D scene you want to create
2. Click "Generate 3D Scene" and wait for the scene to load
3. Use your mouse to navigate the scene:
   - Left-click + drag: Rotate the camera
   - Right-click + drag: Pan the camera
   - Scroll: Zoom in/out
4. Download the HTML file to save your scene

### Tips for Good Results
- Keep descriptions simple but specific
- Focus on visual elements rather than behaviors
- Mention colors and positioning of key objects
- Describe the overall mood or environment
""")
